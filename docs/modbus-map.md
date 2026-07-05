# Modbus Register Map

All sensors and setpoints live in **holding registers** (`%MW`, Modbus FC3 read /
FC6/FC16 write). Input registers (`%IW`) are not used because Modbus has no write
function code for them, and both the in-PLC simulation and the agent need to write
process values. Commands and alarms are **coils** (`%QX`, FC1 read / FC5 write).

Each PLC is an independent Modbus server, so register addresses repeat per device.
Connect to each PLC separately (ports 5021/5022/5023 on the host, or `:502` by
container name inside `ot-net`). Default unit/slave id is `1` (try `0` if reads
return no data).

**OpenPLC holding-register addressing (important):** OpenPLC does *not* map
`%MW0` to Modbus holding-register address 0. Its map is:

| PLC location | Modbus type | Modbus address |
|--------------|-------------|----------------|
| `%QX0.0`–`%QX99.7` | Coils | 0–799 |
| `%IX0.0`–`%IX99.7` | Discrete inputs | 0–799 |
| `%IW0`–`%IW1023` | Input registers | 0–1023 |
| `%QW0`–`%QW1023` | Holding registers | 0–1023 |
| **`%MW0`–`%MW1023`** | **Holding registers** | **1024–2047** |

So `%MW0` is read/written at Modbus holding-register address **1024**, `%MW1` at
1025, and so on. Coils (`%QX`) map directly from 0. The agent applies this base
automatically (`MW_BASE = 1024`).

Scaling: process values are integers. Chlorine and pH are in hundredths
(`200` = 2.00 mg/L, `700` = pH 7.00); pressure is in hundredths of bar
(`800` = 8.00 bar); levels and flow are 0–1000 / 0–200 ranges.

## PLC1 — Intake (host port 5021)

| Address | Type | Name | Access | Meaning | Safety relevance |
|--------|------|------|--------|---------|------------------|
| `%MW0` | Holding reg | `source_level` | R | Raw source reservoir level (0–1000) | Dry-run if < 50 |
| `%MW1` | Holding reg | `tank_level` | R | Treatment feed tank level (0–1000) | Overflow if ≥ 950 |
| `%MW2` | Holding reg | `intake_flow` | R | Current intake flow (0–200) | — |
| `%MW3` | Holding reg | `pump_status` | R | Intake pump running (0/1) | — |
| `%QX0.0` | Coil | `pump_cmd` | R/W | Intake pump run command | Writable, no auth |
| `%QX0.1` | Coil | `low_source_alarm` | R | Dry-run alarm | — |
| `%QX0.2` | Coil | `tank_high_alarm` | R | Feed tank overflow alarm | — |

## PLC2 — Treatment (host port 5022)

| Address | Type | Name | Access | Meaning | Safety relevance |
|--------|------|------|--------|---------|------------------|
| `%MW0` | Holding reg | `chlorine_level` | R | Measured residual chlorine (×0.01 mg/L) | Unsafe if < 50 |
| `%MW1` | Holding reg | `chlorine_setpoint` | R/W | Target residual — **attack writes 0** | Writable, no auth |
| `%MW2` | Holding reg | `ph_level` | R | Measured pH (×0.01) | Excursion outside 6.50–8.50 |
| `%MW3` | Holding reg | `ph_setpoint` | R/W | Target pH | Writable, no auth |
| `%MW4` | Holding reg | `dosing_status` | R | Dosing pump running (0/1) | — |
| `%QX0.0` | Coil | `dosing_enable` | R/W | Dosing pump enable | Writable, no auth |
| `%QX0.1` | Coil | `unsafe_water_alarm` | R | Chlorine below safe residual | Headline safety alarm |
| `%QX0.2` | Coil | `ph_excursion_alarm` | R | pH outside safe band | — |

## PLC3 — Distribution (host port 5023)

| Address | Type | Name | Access | Meaning | Safety relevance |
|--------|------|------|--------|---------|------------------|
| `%MW0` | Holding reg | `pressure` | R | Header pressure (×0.01 bar) | Overpressure if > 900 |
| `%MW1` | Holding reg | `pressure_max` | R/W | Relief setpoint — **attack raises to disable relief** | Writable, no auth |
| `%MW2` | Holding reg | `booster1_status` | R | Booster pump 1 running (0/1) | — |
| `%MW3` | Holding reg | `booster2_status` | R | Booster pump 2 running (0/1) | — |
| `%QX0.0` | Coil | `booster1_cmd` | R/W | Booster 1 run — **attack forces OFF** | Writable, no auth |
| `%QX0.1` | Coil | `booster2_cmd` | R/W | Booster 2 run — **attack forces OFF** | Writable, no auth |
| `%QX0.2` | Coil | `overpressure_alarm` | R | Pressure above hard limit | Physical-damage alarm |
| `%QX0.3` | Coil | `supply_fail_alarm` | R | Pressure too low to supply | Denial-of-supply alarm |

## Attack → effect summary

| Attack | Target | Write | Observable effect |
|--------|--------|-------|-------------------|
| Booster pumps OFF | PLC3 `%QX0.0`, `%QX0.1` → `FALSE` | Coil | `pressure` decays → `supply_fail_alarm` |
| Chlorine setpoint zeroed | PLC2 `%MW1` → `0` | Holding reg | `chlorine_level` decays to 0 → `unsafe_water_alarm` |
| Relief disabled | PLC3 `%MW1` → `1000` | Holding reg | `pressure` climbs > 900 → `overpressure_alarm` |
