"""
Pytest configuration for the testbed acceptance suite.

Adds /app to sys.path so tests can import `tools.modbus_client` etc.
Defines reusable fixtures for socket checks and HTTP sessions.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

# Make /app importable so `from tools.modbus_client import ...` works
APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))


# ── Helpers exposed as fixtures ───────────────────────────────────────

@pytest.fixture
def can_reach():
    """Fixture: function that returns True if TCP host:port is reachable."""
    def _can_reach(host: str, port: int, timeout: float = 2.0) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.gaierror, socket.timeout, OSError):
            return False
    return _can_reach


@pytest.fixture
def http_session():
    """Fixture: requests.Session with cookies persisted across calls."""
    import requests
    s = requests.Session()
    s.timeout = 10
    yield s
    s.close()


# ── PLC inventory (mirrors tools/modbus_client.py) ────────────────────

PLC_HOSTS = ["plc1-intake", "plc2-treatment", "plc3-distribution"]
SCADALTS_BASE = "http://scadalts:8080/Scada-LTS"
