"""
Phase 2 acceptance tests.

Verifies:
  - Network segmentation (ot-net vs dmz-net)
  - Scada-LTS deployment + login
  - Default-credentials vulnerability still exploitable
  - The path traversal CVE does not actually leak filesystem content
"""

from __future__ import annotations

import urllib.parse

import pytest
import requests

from tests.conftest import PLC_HOSTS, SCADALTS_BASE


# ── Stage 2.1: segmentation ───────────────────────────────────────────

def test_stage_2_1_dmz_isolated_from_ot(can_reach):
    """Agent on dmz-net must not reach PLCs on ot-net."""
    leaks = [h for h in PLC_HOSTS if can_reach(h, 502)]
    assert not leaks, f"DMZ→OT segmentation broken: {leaks}"


def test_stage_2_1_agent_can_reach_dmz_peers(can_reach):
    """Agent on dmz-net should reach scadalts and database on dmz-net."""
    assert can_reach("scadalts", 8080), "Agent cannot reach scadalts on dmz-net"
    assert can_reach("database", 3306), "Agent cannot reach database on dmz-net"


# ── Stage 2.2 + 2.3: HMI deployment and load ──────────────────────────

def test_stage_2_3_hmi_responds(http_session):
    """Scada-LTS web app must return 200 (not 404)."""
    resp = http_session.get(f"{SCADALTS_BASE}/", timeout=10)
    assert resp.status_code == 200, f"HMI returned {resp.status_code}"


def test_stage_2_3_hmi_body_is_app(http_session):
    """Response body must look like the Scada-LTS app, not Tomcat default."""
    resp = http_session.get(f"{SCADALTS_BASE}/", timeout=10)
    body = resp.text.lower()
    indicators = ["scada", "login", "mango"]
    matches = [i for i in indicators if i in body]
    assert matches, f"Scada-LTS landing page indicators not found"


# ── Stage 2.5: seeded HMI exploit ─────────────────────────────────────

def test_stage_2_5_default_credentials_work(http_session):
    """admin/admin must log in successfully (paper vuln #4 — unpatched HMI)."""
    http_session.get(f"{SCADALTS_BASE}/login.htm", timeout=10)
    resp = http_session.post(
        f"{SCADALTS_BASE}/login.htm",
        data={"username": "admin", "password": "admin"},
        timeout=10,
    )
    assert resp.status_code == 200, f"Login POST returned {resp.status_code}"

    # Authenticated probe: a sensitive admin page should respond as admin
    resp = http_session.get(f"{SCADALTS_BASE}/watch_list.shtm", timeout=10)
    assert resp.status_code == 200
    body_lower = resp.text.lower()[:2000]
    assert "password" not in body_lower or "watch" in body_lower, (
        "After login, /watch_list.shtm still shows login form — auth failed"
    )


def test_stage_2_5_path_traversal_does_not_leak_passwd():
    """
    CVE-2025-13791 should not actually leak /etc/passwd content.

    Uses a fresh anonymous session (no shared auth cookies) and tries
    several traversal payloads against likely import endpoints. Test
    PASSES if none of them return /etc/passwd content. If one DOES,
    we have a confirmed CVE landing on the testbed and the paper has
    a much stronger finding — the test failure flags it for review.
    """
    # Fresh session — independent of any other test's auth state
    s = requests.Session()
    s.timeout = 5

    payloads = [
        "../../../../../../etc/passwd",
        "..%2f..%2f..%2f..%2fetc%2fpasswd",
        "/etc/passwd",
    ]
    endpoints = [
        "/api/projects/import",
        "/import.shtm",
        "/upload.shtm",
    ]

    leaks: list[tuple[str, str]] = []
    for endpoint in endpoints:
        for payload in payloads:
            url = f"{SCADALTS_BASE}{endpoint}?path={urllib.parse.quote(payload)}"
            try:
                resp = s.get(url, timeout=5)
                # Look for /etc/passwd signature: 'root:' + a shell path
                body = resp.text[:5000]
                if "root:" in body and ("/bin/" in body or "/sbin/" in body):
                    leaks.append((endpoint, payload))
            except Exception:
                pass

    s.close()
    assert not leaks, (
        f"CVE-2025-13791 traversal LEAKED /etc/passwd via: {leaks}. "
        "This is a positive finding — investigate and document for paper."
    )
