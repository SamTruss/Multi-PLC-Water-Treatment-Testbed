"""
Stage 2.3 verification: Scada-LTS app loads cleanly and is reachable.

Expected:
  - GET /Scada-LTS/ returns 200 (not 404 — webapp deployed properly)
  - Response body contains 'Scada-LTS' or 'login' (it's the real app, not Tomcat default)
  - Capture and report the version string for the paper

Run:
    docker exec agent python /app/tests/verify_stage_2_3.py
"""

from __future__ import annotations

import re
import socket
import sys
import urllib.error
import urllib.request


def http_get(url: str, timeout: float = 10.0) -> tuple[int | None, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return e.code, body
    except (urllib.error.URLError, socket.timeout) as e:
        return None, str(e)


def main() -> int:
    print("=" * 60)
    print("Stage 2.3 verification: Scada-LTS app fully deployed")
    print("=" * 60)

    results: list[tuple[str, bool]] = []

    # Check 1: webapp returns 200 (not 404)
    status, body = http_get("http://scadalts:8080/Scada-LTS/")
    ok_status = status == 200
    print(f"\n[1] GET /Scada-LTS/  ->  status {status}  ({'OK' if ok_status else 'FAIL'})")
    results.append(("webapp returns 200", ok_status))

    # Check 2: it's the real Scada-LTS app, not a Tomcat error page
    looks_like_app = ("scada" in body.lower()) or ("login" in body.lower()) or ("mango" in body.lower())
    print(f"[2] Body looks like app  ->  {'OK' if looks_like_app else 'FAIL (got Tomcat default?)'}")
    results.append(("body content looks like app", looks_like_app))

    # Check 3: try to extract a version string
    version = None
    for pattern in [
        r"Scada-LTS[^<>]*?(\d+\.\d+\.\d+(?:\.\d+)?)",
        r"version[^<>]*?(\d+\.\d+\.\d+(?:\.\d+)?)",
    ]:
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            version = m.group(1)
            break
    if version:
        print(f"[3] Detected version       ->  {version}")
    else:
        print(f"[3] Detected version       ->  not found in landing page")

    print("\n" + "-" * 60)
    all_ok = all(r[1] for r in results)
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("-" * 60)
    print("PASS — Stage 2.3 complete." if all_ok else "FAIL — see above.")

    if version:
        print(f"\nRecord this in docs/SCADALTS_VERSION.md:  Scada-LTS {version}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
