"""
Process simulator for the water treatment testbed.

Runs in a loop, every second:
    1. Reads the current pump/valve/doser states from each PLC
    2. Updates simulated physical state (tank levels, pressures, etc.)
    3. Writes the new sensor readings back to the PLCs' input registers

This makes the plant come alive: open the intake pump and the treatment
tank fills; raise the chlorine doser and ChlorineLevel rises; etc.

Run with:
    docker exec agent python /app/process_simulator.py

Stop with Ctrl+C (or `docker exec agent pkill -f process_simulator`).
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from dataclasses import dataclass, field

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from modbus_client import PLCS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("process_sim")

# ── physical model state ─────────────────────────────────────────────

@dataclass
class PlantState:
    """Continuous state of the simulated physical plant."""
    # Intake station
    source_level: float = 100.0       # source reservoir 0-100%
    intake_flow: float = 0.0          # current flow rate

    # Treatment station
    treatment_tank_level: float = 50.0  # treatment tank 0-100%
    chlorine_level: float = 50.0       # ppm-equivalent
    ph_level: float = 70.0             # pH * 10 (so 70 = pH 7.0)

    # Distribution station
    distribution_pressure: float = 50.0   # pressure setpoint matched
    outflow_rate: float = 30.0
    reservoir_level: float = 60.0

    def clamp(self) -> None:
        """Keep physical values in plausible ranges."""
        self.source_level = max(0, min(100, self.source_level))
        self.intake_flow = max(0, min(100, self.intake_flow))
        self.treatment_tank_level = max(0, min(100, self.treatment_tank_level))
        self.chlorine_level = max(0, min(100, self.chlorine_level))
        self.ph_level = max(0, min(140, self.ph_level))  # pH 0-14 * 10
        self.distribution_pressure = max(0, min(200, self.distribution_pressure))
        self.outflow_rate = max(0, min(100, self.outflow_rate))
        self.reservoir_level = max(0, min(100, self.reservoir_level))


# ── helpers to talk to a PLC ─────────────────────────────────────────

def write_input_register(host: str, address: int, value: int) -> None:
    """OpenPLC accepts holding-register-style writes that map to %IW."""
    client = ModbusTcpClient(host=host, port=502, timeout=2)
    try:
        if not client.connect():
            return
        # OpenPLC maps %IW into the same Modbus 'holding register' space
        # at offset 1024 (input register block). We write coil-style instead.
        client.write_register(address=1024 + address, value=value, slave=1)
    except ModbusException:
        pass
    finally:
        client.close()


def read_coil(host: str, address: int) -> bool:
    client = ModbusTcpClient(host=host, port=502, timeout=2)
    try:
        if not client.connect():
            return False
        rr = client.read_coils(address=address, count=1, slave=1)
        if rr.isError():
            return False
        return bool(rr.bits[0])
    except ModbusException:
        return False
    finally:
        client.close()


def read_holding(host: str, address: int) -> int:
    client = ModbusTcpClient(host=host, port=502, timeout=2)
    try:
        if not client.connect():
            return 0
        rr = client.read_holding_registers(address=address, count=1, slave=1)
        if rr.isError():
            return 0
        return rr.registers[0]
    except ModbusException:
        return 0
    finally:
        client.close()


# ── physical model: update state based on PLC actions ────────────────

def step(state: PlantState) -> PlantState:
    """Advance the physical model by one tick (1 second)."""
    # Read what each PLC is currently doing
    intake_pump = read_coil(PLCS["intake"].host, 0)
    intake_valve = read_coil(PLCS["intake"].host, 1)

    chlorine_doser = read_coil(PLCS["treatment"].host, 0)
    acid_doser = read_coil(PLCS["treatment"].host, 1)
    base_doser = read_coil(PLCS["treatment"].host, 2)

    booster1 = read_coil(PLCS["distribution"].host, 0)
    booster2 = read_coil(PLCS["distribution"].host, 1)
    relief_valve = read_coil(PLCS["distribution"].host, 2)
    supply_valve = read_coil(PLCS["distribution"].host, 3)

    # ── INTAKE PHYSICS ──
    if intake_pump and intake_valve and state.source_level > 5:
        state.intake_flow = 50.0          # pump flowing
        state.source_level -= 0.3         # source slowly depletes
        state.treatment_tank_level += 1.0  # treatment tank fills
    else:
        state.intake_flow = max(0, state.intake_flow - 5)

    # Source naturally refills (rain/river)
    state.source_level += 0.1

    # ── TREATMENT PHYSICS ──
    # Chlorine consumed by water passing through; doser replenishes
    state.chlorine_level -= 0.5  # natural decay
    if chlorine_doser:
        state.chlorine_level += 2.0

    # pH drifts; acid/base correct it
    state.ph_level += 0.2  # naturally drifts up
    if acid_doser:
        state.ph_level -= 1.0
    if base_doser:
        state.ph_level += 1.0

    # ── DISTRIBUTION PHYSICS ──
    # Pressure rises with booster pumps, falls with consumption
    pressure_change = 0.0
    if booster1:
        pressure_change += 2.0
    if booster2:
        pressure_change += 2.0
    if relief_valve:
        pressure_change -= 8.0  # safety dump
    if supply_valve:
        pressure_change -= 1.0  # consumption

    state.distribution_pressure += pressure_change

    # Reservoir empties as supply valve flows
    if supply_valve:
        state.reservoir_level -= 0.2
    # Reservoir refills from treatment tank
    if state.treatment_tank_level > 30:
        state.reservoir_level += 0.3
        state.treatment_tank_level -= 0.3

    # Outflow rate = how much customers are drawing
    state.outflow_rate = 30 + (10 if supply_valve else 0)

    state.clamp()
    return state


def push_to_plcs(state: PlantState) -> None:
    """Write current physical readings to the PLCs' input registers."""
    # Intake
    write_input_register(PLCS["intake"].host, 0, int(state.source_level))
    write_input_register(PLCS["intake"].host, 1, int(state.intake_flow))

    # Treatment
    write_input_register(PLCS["treatment"].host, 0, int(state.treatment_tank_level))
    write_input_register(PLCS["treatment"].host, 1, int(state.chlorine_level))
    write_input_register(PLCS["treatment"].host, 2, int(state.ph_level))

    # Distribution
    write_input_register(PLCS["distribution"].host, 0, int(state.distribution_pressure))
    write_input_register(PLCS["distribution"].host, 1, int(state.outflow_rate))
    write_input_register(PLCS["distribution"].host, 2, int(state.reservoir_level))


def print_state(state: PlantState) -> None:
    print(
        f"src={state.source_level:5.1f}  "
        f"flow={state.intake_flow:5.1f}  "
        f"tank={state.treatment_tank_level:5.1f}  "
        f"cl={state.chlorine_level:5.1f}  "
        f"ph={state.ph_level/10:4.1f}  "
        f"press={state.distribution_pressure:5.1f}  "
        f"res={state.reservoir_level:5.1f}"
    )


# ── main loop ────────────────────────────────────────────────────────

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
