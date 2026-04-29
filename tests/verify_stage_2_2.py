"""
Stage 2.2 verification: Scada-LTS deployed and bridging dmz-net to ot-net.

Expected:
  - Agent on dmz-net CAN reach scadalts:8080 (same network)
  - Agent on dmz-net STILL CANNOT reach PLCs directly (regression check)
  - Scada-LTS HTTP responds (web UI is up)

Run from the agent container:
    docker exec agent python /app/tests/verify_stage_2_2.py
"""

from __future__ import annotations

import socket
import sys
import urllib.error
import urllib.request

PLC_HOSTS = ["plc1-intake", "plc2-treatment", "plc3-distribution"]


def can_reach(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.gaierror, socket.timeout, OSError):
        return False


def http_responds(url: str, timeout: float = 5.0) -> tuple[bool, int | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return True, resp.status
    except urllib.error.HTTPError as e:
        # 4xx/5xx still proves the server is up
        return True, e.code
    except (urllib.error.URLError, socket.timeout):
        return False, None


def main() -> int:
    print("=" * 60)
    print("Stage 2.2 verification: Scada-LTS + segmentation")
    print("=" * 60)

    results = []

    # Check 1: agent reaches scadalts (same dmz-net)
    ok = can_reach("scadalts", 8080)
    print(f"\n[1] agent -> scadalts:8080  ->  {'OK' if ok else 'FAIL'}")
    results.append(("agent reaches scadalts", ok))

    # Check 2: HMI web UI responding
    ok2, code = http_responds("http://scadalts:8080/Scada-LTS/")
    print(f"[2] HTTP GET /Scada-LTS/    ->  {'OK' if ok2 else 'FAIL'}  (status {code})")
    results.append(("scadalts web UI responds", ok2))

    # Check 3: PLCs still NOT reachable from agent (segmentation intact)
    leaks = [h for h in PLC_HOSTS if can_reach(h, 502)]
    no_leak = not leaks
    print(f"[3] agent -X-> PLC modbus   ->  {'OK (still blocked)' if no_leak else f'FAIL — leaked: {leaks}'}")
    results.append(("segmentation intact", no_leak))

    print("\n" + "-" * 60)
    all_ok = all(r[1] for r in results)
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("-" * 60)
    print("PASS — Stage 2.2 complete." if all_ok else "FAIL — see above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
