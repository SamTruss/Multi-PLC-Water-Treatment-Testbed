"""
Phase 1 regression tests.

These verify Phase 1 functionality still works after Phase 2's network
changes. Note: PLCs are now on ot-net, agent is on dmz-net, so the
agent CANNOT reach PLCs directly. These tests therefore check from
the perspective of *the bridge* (Scada-LTS), which IS dual-homed.

For tests that need direct PLC access (e.g. running modbus_client.py
attacks), the script must be run from inside the scadalts container,
not the agent container, until Phase 4 sets up proper firewall rules.

Tests in this file are network-only (TCP reachability checks) and run
from the agent container.
"""

from __future__ import annotations

import pytest

from tests.conftest import PLC_HOSTS


def test_plcs_unreachable_from_dmz(can_reach):
    """Agent on dmz-net should NOT reach PLCs on ot-net (Phase 2 segmentation)."""
    leaks = [h for h in PLC_HOSTS if can_reach(h, 502)]
    assert not leaks, f"Network leak — agent reached PLCs on ot-net: {leaks}"


def test_plc_count_matches_expected():
    """We declare 3 PLCs in the testbed inventory."""
    assert len(PLC_HOSTS) == 3, "Expected exactly 3 PLCs in inventory"


def test_modbus_client_module_importable():
    """The agent's modbus_client tool module must import cleanly."""
    from tools.modbus_client import PLCS, ModbusConnector
    assert "intake" in PLCS
    assert "treatment" in PLCS
    assert "distribution" in PLCS


def test_modbus_client_address_maps_complete():
    """Each PLC target should have at least one coil and one holding register."""
    from tools.modbus_client import PLCS
    for key, target in PLCS.items():
        assert target.coils, f"{key}: no coil mappings declared"
        assert target.holding_registers, f"{key}: no holding-register mappings declared"
