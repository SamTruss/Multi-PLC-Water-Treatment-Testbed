"""
Process simulator for the water treatment testbed.

Runs in a loop, every second:
  1. Reads each PLC's pump/valve/doser states
  2. Updates a simulated physical model (tank levels, pressure, etc.)
  3. Writes new sensor readings back to the PLCs' holding registers
     (sensors live at %MW10-12 since %IW is read-only over Modbus)

Run with:
    docker exec -it agent python /app/scripts/process_simulator.py
Stop with Ctrl+C.
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Make the parent (/app) importable so `tools.modbus_client` resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymodbus.client import ModbusTcpClient  # noqa: E402
from pymodbus.exceptions import ModbusException  # noqa: E402

from tools.modbus_client import PLCS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("process_sim")


@dataclass
class PlantState:
    source_level: float = 100.0
    intake_flow: float = 0.0
    treatment_tank_level: float = 50.0
    chlorine_level: float = 50.0
    ph_level: float = 70.0
    distribution_pressure: float = 50.0
    outflow_rate: float = 30.0
    reservoir_level: float = 60.0

    def clamp(self) -> None:
        self.source_level = max(0, min(100, self.source_level))
        self.intake_flow = max(0, min(100, self.intake_flow))
        self.treatment_tank_level = max(0, min(100, self.treatment_tank_level))
        self.chlorine_level = max(0, min(200, self.chlorine_level))
        self.ph_level = max(0, min(140, self.ph_level))
        self.distribution_pressure = max(0, min(200, self.distribution_pressure))
        self.outflow_rate = max(0, min(100, self.outflow_rate))
        self.reservoir_level = max(0, min(100, self.reservoir_level))


def _client(host: str) -> ModbusTcpClient:
    return ModbusTcpClient(host=host, port=502, timeout=2)


def write_register(host: str, address: int, value: int) -> None:
    c = _client(host)
    try:
        if c.connect():
            c.write_register(address=address, value=value, slave=1)
    except ModbusException:
        pass
    finally:
        c.close()


def read_coil(host: str, address: int) -> bool:
    c = _client(host)
    try:
        if not c.connect():
            return False
        rr = c.read_coils(address=address, count=1, slave=1)
        return False if rr.isError() else bool(rr.bits[0])
    except ModbusException:
        return False
    finally:
        c.close()


def step(state: PlantState) -> PlantState:
    intake_pump = read_coil(PLCS["intake"].host, 0)
    intake_valve = read_coil(PLCS["intake"].host, 1)

    chlorine_doser = read_coil(PLCS["treatment"].host, 0)
    acid_doser = read_coil(PLCS["treatment"].host, 1)
    base_doser = read_coil(PLCS["treatment"].host, 2)

    booster1 = read_coil(PLCS["distribution"].host, 0)
    booster2 = read_coil(PLCS["distribution"].host, 1)
    relief_valve = read_coil(PLCS["distribution"].host, 2)
    supply_valve = read_coil(PLCS["distribution"].host, 3)

    # INTAKE
    if intake_pump and intake_valve and state.source_level > 5:
        state.intake_flow = 50.0
        state.source_level -= 0.3
        state.treatment_tank_level += 1.0
    else:
        state.intake_flow = max(0, state.intake_flow - 5)
    state.source_level += 0.1

    # TREATMENT
    state.chlorine_level -= 0.5
    if chlorine_doser:
        state.chlorine_level += 2.0
    state.ph_level += 0.2
    if acid_doser:
        state.ph_level -= 1.0
    if base_doser:
        state.ph_level += 1.0

    # DISTRIBUTION
    pressure_change = 0.0
    if booster1: pressure_change += 2.0
    if booster2: pressure_change += 2.0
    if relief_valve: pressure_change -= 8.0
    if supply_valve: pressure_change -= 1.0
    state.distribution_pressure += pressure_change

    if supply_valve:
        state.reservoir_level -= 0.2
    if state.treatment_tank_level > 30:
        state.reservoir_level += 0.3
        state.treatment_tank_level -= 0.3

    state.outflow_rate = 30 + (10 if supply_valve else 0)
    state.clamp()
    return state


def push_to_plcs(state: PlantState) -> None:
    write_register(PLCS["intake"].host, 10, int(state.source_level))
    write_register(PLCS["intake"].host, 11, int(state.intake_flow))
    write_register(PLCS["treatment"].host, 10, int(state.treatment_tank_level))
    write_register(PLCS["treatment"].host, 11, int(state.chlorine_level))
    write_register(PLCS["treatment"].host, 12, int(state.ph_level))
    write_register(PLCS["distribution"].host, 10, int(state.distribution_pressure))
    write_register(PLCS["distribution"].host, 11, int(state.outflow_rate))
    write_register(PLCS["distribution"].host, 12, int(state.reservoir_level))


def print_state(state: PlantState) -> None:
    print(
        f"src={state.source_level:5.1f}  flow={state.intake_flow:5.1f}  "
        f"tank={state.treatment_tank_level:5.1f}  cl={state.chlorine_level:5.1f}  "
        f"ph={state.ph_level/10:4.1f}  press={state.distribution_pressure:5.1f}  "
        f"res={state.reservoir_level:5.1f}",
        flush=True,
    )


def main() -> None:
    print("=" * 70)
    print("Process simulator running. Ctrl+C to stop.")
    print("=" * 70)

    state = PlantState()

    def shutdown(*_):
        print("\nShutting down simulator.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    tick = 0
    while True:
        state = step(state)
        push_to_plcs(state)
        if tick % 5 == 0:
            print_state(state)
        tick += 1
        time.sleep(1)


if __name__ == "__main__":
    main()
