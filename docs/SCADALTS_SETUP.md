# Scada-LTS HMI configuration walkthrough

This guide walks you through the manual Scada-LTS configuration that ships
with v0.2.1: three Modbus TCP data sources, the data points for each, and
a dashboard with gauges.

**Estimated time:** 45-60 minutes
**Prerequisite:** Stages 2.1-2.5 complete (HMI loads, login works, all 10 pytest tests pass)

---

## Open the HMI

```
http://localhost:9090/Scada-LTS
```

Login: `admin` / `admin`

You should see the Scada-LTS dashboard. Top menu has icons for Watch List, Data Sources, Data Points, Graphical Views, Users, etc.

---

## Step 1 — Add Modbus TCP data source for PLC1 (Intake)

1. Click **Data Sources** icon (top menu, looks like a power plug or database)
2. Click the **green plus (+)** button to add a new data source
3. From the dropdown choose **Modbus TCP** → click the green plus next to it
4. Fill in:

   **Configuration tab:**
   - **Name:** `PLC1 Intake`
   - **XID:** leave default (auto-generated)
   - **Update period:** `1 second`
   - **Quantize:** ticked
   - **Timeout:** `500 ms`
   - **Retries:** `2`
   - **Max read bit count:** `2000`
   - **Max read register count:** `125`
   - **Max write register count:** `120`
   - **Contiguous batches only:** unticked
   - **Create slave monitor points:** unticked

   **Modbus IP tab:**
   - **Host:** `plc1-intake`
   - **Port:** `502`
   - **Encapsulated:** unticked

5. Click the **green checkmark** to save
6. Click the **disabled/enabled toggle** (greyed-out lightning bolt icon) to enable the data source — it should turn yellow/green

> If the data source goes red after enabling, the PLC isn't running or
> Scada-LTS can't reach it. Check `docker ps` and that the program is launched.

---

## Step 2 — Add data points for PLC1

While viewing the PLC1 Intake data source page:

1. Click **green plus (+)** under "Data Points"
2. For each row in the table below, fill in and save:

| Name | Modbus type | Range | Offset | Data type | Settable |
|------|-------------|-------|--------|-----------|----------|
| SourceLevel | Holding Register | 1 | 10 | 2-byte signed integer | yes |
| IntakeFlow | Holding Register | 1 | 11 | 2-byte signed integer | yes |
| IntakePump | Coil | 1 | 0 | Binary | yes |
| IntakeValve | Coil | 1 | 1 | Binary | yes |
| LowSourceAlarm | Coil | 1 | 2 | Binary | no |
| HighFlowAlarm | Coil | 1 | 3 | Binary | no |
| PumpRuntime | Holding Register | 1 | 0 | 2-byte signed integer | yes |

For each data point:
- Tick **Enabled**
- Click the **green checkmark** to save

---

## Step 3 — Add data sources for PLC2 (Treatment) and PLC3 (Distribution)

Repeat Steps 1 and 2 for PLC2 and PLC3.

### PLC2 Treatment

**Modbus IP host:** `plc2-treatment` · port 502

| Name | Type | Offset |
|------|------|--------|
| TreatmentTankLevel | Holding Register | 10 |
| ChlorineLevel | Holding Register | 11 |
| PhLevel | Holding Register | 12 |
| ChlorineDoser | Coil | 0 |
| AcidDoser | Coil | 1 |
| BaseDoser | Coil | 2 |
| Mixer | Coil | 3 |
| ContaminationAlarm | Coil | 4 |
| PhAlarm | Coil | 5 |
| ChlorineSetpoint | Holding Register | 0 |
| PhSetpointLow | Holding Register | 1 |
| PhSetpointHigh | Holding Register | 2 |

### PLC3 Distribution

**Modbus IP host:** `plc3-distribution` · port 502

| Name | Type | Offset |
|------|------|--------|
| DistributionPressure | Holding Register | 10 |
| OutflowRate | Holding Register | 11 |
| ReservoirLevel | Holding Register | 12 |
| BoosterPump1 | Coil | 0 |
| BoosterPump2 | Coil | 1 |
| PressureReliefValve | Coil | 2 |
| SupplyValve | Coil | 3 |
| OverpressureAlarm | Coil | 4 |
| LowPressureAlarm | Coil | 5 |
| PressureSetpoint | Holding Register | 0 |
| PressureMax | Holding Register | 1 |

---

## Step 4 — Verify the data is flowing

1. Go to **Watch List** (eye icon, top menu)
2. Click the green plus and add a few data points (e.g. SourceLevel, ChlorineLevel, DistributionPressure)
3. You should see live values

If the simulator is running (Phase 3 work, not yet integrated), values will be moving. Without the simulator, values stay where the init_defaults script left them.

---

## Step 5 — Build the dashboard

1. Click **Graphical Views** icon (looks like a layered shape)
2. Click **Add a new graphical view** (green plus)
3. Name: `Water Treatment Plant Overview`
4. Add components:

### Suggested layout

**Top row — Intake Station**
- Analog gauge: `SourceLevel` (range 0-100, label "Source Reservoir %")
- Indicator light: `IntakePump` (green=on, red=off)
- Indicator light: `LowSourceAlarm` (red=alarm, off=ok)

**Middle row — Treatment Station**
- Analog gauge: `ChlorineLevel` (range 0-100, label "Chlorine ppm")
- Analog gauge: `PhLevel` (range 0-140, label "pH x10")
- Indicator: `ChlorineDoser`
- Indicator: `AcidDoser`
- Indicator: `BaseDoser`
- Indicator: `ContaminationAlarm`

**Bottom row — Distribution Station**
- Analog gauge: `DistributionPressure` (range 0-200, label "Pressure")
- Analog gauge: `ReservoirLevel` (range 0-100, label "Customer Reservoir %")
- Indicator: `BoosterPump1`
- Indicator: `BoosterPump2`
- Indicator: `PressureReliefValve` (yellow=open)
- Indicator: `OverpressureAlarm`

5. Click **Save** (disk icon)
6. The dashboard is now your operator view.

> **Tip:** for paper screenshots, use the browser's full-screen mode (F11)
> with the dashboard open. Crop in your image editor.

---

## Verification

Run the v0.2.1 acceptance tests:

```powershell
docker exec agent pytest /app/tests/test_phase2_hmi_config.py -v
```

If green: dashboard configured, ready for the Stuxnet demo (see `STUXNET_DEMO.md`).

---

## Troubleshooting

**Data source goes red after enabling**
- The PLC isn't running or Scada-LTS can't reach it.
- `docker ps` should show all 3 PLCs as Up.
- From inside Scada-LTS container: `docker exec scadalts sh -c "nslookup plc1-intake"` should resolve.

**Data points show "no value" forever**
- Check the data source itself is enabled (lightning-bolt icon green/yellow, not grey)
- Check the PLC has its program running and the holding registers exist (use the OpenPLC Monitoring page)
- Some Modbus offsets need tweaking in newer Scada-LTS — try offset+1 if values are off by one register

**Settings won't save**
- Default admin/admin credentials work but the session can time out. Re-login.

**Dashboard renders but values frozen**
- The PLC sensor inputs (`%MW10-12`) are written by `process_simulator.py`, which doesn't currently run on dmz-net. That's Phase 3.
- For now, manually write a value with the modbus exploit script to confirm the path works end-to-end:
  ```powershell
  docker exec scadalts sh -c "echo not yet - simulator runs from agent"
  ```
  (Once Phase 3 lands, the simulator will keep values moving.)
