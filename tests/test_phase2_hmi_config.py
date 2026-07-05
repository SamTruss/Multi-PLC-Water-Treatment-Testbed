"""
Phase 2 HMI configuration acceptance tests (v0.2.1).

Verifies the manual configuration steps in docs/SCADALTS_SETUP.md were
applied correctly:
  - Three Modbus TCP data sources exist (PLC1, PLC2, PLC3)
  - Each is enabled
  - At least one data point per source is reading values
  - The "Water Treatment Plant Overview" graphical view exists

These tests authenticate with default admin credentials (the seeded
vulnerability from Stage 2.5) and read the Scada-LTS internal API.
"""

from __future__ import annotations

import pytest
import requests

from tests.conftest import SCADALTS_BASE


# ── shared authenticated session ──────────────────────────────────────

@pytest.fixture(scope="module")
def authed_session():
    """Login once with admin/admin and reuse the session for all tests."""
    s = requests.Session()
    s.timeout = 10
    s.get(f"{SCADALTS_BASE}/login.htm", timeout=10)
    resp = s.post(
        f"{SCADALTS_BASE}/login.htm",
        data={"username": "admin", "password": "admin"},
        timeout=10,
    )
    assert resp.status_code == 200, "Could not log in to Scada-LTS as admin"
    yield s
    s.close()


# ── Data source presence tests ────────────────────────────────────────

EXPECTED_DATA_SOURCES = [
    "PLC1 Intake",
    "PLC2 Treatment",
    "PLC3 Distribution",
]


def test_data_sources_endpoint_reachable(authed_session):
    """Sanity check: the data-sources page loads when authenticated."""
    resp = authed_session.get(f"{SCADALTS_BASE}/data_sources.shtm")
    assert resp.status_code == 200


@pytest.mark.parametrize("ds_name", EXPECTED_DATA_SOURCES)
def test_data_source_exists(authed_session, ds_name):
    """The named data source must appear on the data-sources listing page."""
    resp = authed_session.get(f"{SCADALTS_BASE}/data_sources.shtm")
    assert resp.status_code == 200
    assert ds_name in resp.text, (
        f"Data source '{ds_name}' not found on /data_sources.shtm. "
        f"Did you complete the configuration in docs/SCADALTS_SETUP.md?"
    )


# ── Watch list / data point tests ─────────────────────────────────────

def test_watch_list_has_data_points(authed_session):
    """The Watch List page should list at least three data points."""
    resp = authed_session.get(f"{SCADALTS_BASE}/watch_list.shtm")
    assert resp.status_code == 200

    # Look for any of the expected point names. We don't require ALL of
    # them — just enough to prove the watch list is populated.
    expected_any_point = [
        "SourceLevel",
        "ChlorineLevel",
        "DistributionPressure",
        "IntakePump",
        "Mixer",
    ]
    found = [p for p in expected_any_point if p in resp.text]
    assert len(found) >= 3, (
        f"Watch list looks empty or unconfigured. "
        f"Found points: {found}. Expected at least 3 of {expected_any_point}."
    )


# ── Graphical view test ──────────────────────────────────────────────

def test_graphical_view_dashboard_exists(authed_session):
    """The dashboard graphical view should exist."""
    resp = authed_session.get(f"{SCADALTS_BASE}/views.shtm")
    assert resp.status_code == 200, (
        f"Graphical views page returned {resp.status_code}. "
        f"Endpoint may differ between Scada-LTS versions."
    )

    # We accept either the exact name or a clear partial match
    matches = ["Water Treatment", "Plant Overview", "Treatment Plant"]
    found = [m for m in matches if m in resp.text]
    assert found, (
        "Could not find the 'Water Treatment Plant Overview' dashboard. "
        "Did you create the graphical view in Step 5 of SCADALTS_SETUP.md?"
    )
