"""
Stage 2.1 verification: network segmentation.

Confirms the network model is correct for Stage 2.1:
  - Agent (on dmz-net) CANNOT reach PLCs (on ot-net) directly.
  - This is intentional. Scada-LTS will bridge the gap in Stage 2.2.

Run from the agent container:
    docker exec agent python /app/tests/verify_stage_2_1.py
"""

from __future__ import annotations

import socket
import sys

PLC_HOSTS = ["plc1-intake", "plc2-treatment", "plc3-distribution"]
MODBUS_PORT = 502


def can_reach(host: str, port: int, timeout: float = 2.0) -> bool:
    """Return True if a TCP connect to host:port succeeds within timeout."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.gaierror, socket.timeout, OSError):
        return False


def main() -> int:
    print("=" * 60)
    print("Stage 2.1 verification: network isolation")
    print("=" * 60)
    print("\nExpected: agent on dmz-net cannot reach PLCs on ot-net.\n")

    failures: list[str] = []
    for host in PLC_HOSTS:
        reachable = can_reach(host, MODBUS_PORT)
        marker = "REACHABLE (BAD)" if reachable else "blocked (good)"
        print(f"  {host}:{MODBUS_PORT}  ->  {marker}")
        if reachable:
            failures.append(host)

    print()
    if failures:
        print("FAIL: networks are NOT isolated.")
        print(f"      Agent could reach {failures}.")
        print("      The compose file likely still has the agent dual-homed.")
        return 1
    print("PASS: agent is correctly isolated on dmz-net.")
    print("      Scada-LTS will bridge to ot-net in Stage 2.2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
