"""
One-shot initialiser for the testbed PLCs.

Writes sane default setpoints to each PLC's holding registers so that
the control logic has something realistic to work with. Run this once
after starting the testbed (or any time you want to reset to defaults).

Run from the agent container:
    docker exec agent python /app/scripts/init_defaults.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Make the parent (/app) importable so `tools.modbus_client` resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.modbus_client import PLCS, ModbusConnector  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("init_defaults")


# Holding-register defaults per PLC.
# (register_address, value, label)
DEFAULTS: dict[str, list[tuple[int, int, str]]] = {
    "intake": [
        (1, 0, "PumpHysteresis (start in OFF state)"),
    ],
    "treatment": [
        (0, 50, "ChlorineSetpoint (target chlorine level)"),
        (1, 65, "PhSetpointLow (pH lower bound)"),
        (2, 80, "PhSetpointHigh (pH upper bound)"),
    ],
    "distribution": [
        (0, 50, "PressureSetpoint (target distribution pressure)"),
        (1, 80, "PressureMax (relief valve trigger)"),
        (3, 0, "PumpStaging (start in OFF state)"),
    ],
}


def initialise() -> None:
    print("=" * 60)
    print("Initialising PLC holding-register defaults")
    print("=" * 60)
    for plc_key, defaults in DEFAULTS.items():
        target = PLCS[plc_key]
        print(f"\n[{target.name}]")
        try:
            with ModbusConnector(target) as c:
                for addr, value, label in defaults:
                    c.write_register(addr, value)
                    print(f"  reg[{addr}] = {value:>4}   ({label})")
        except Exception as e:
            log.error(f"Failed to init {target.name}: {e}")
    print("\n" + "=" * 60)
    print("Defaults set. PLCs are now in normal operating configuration.")


if __name__ == "__main__":
    initialise()
