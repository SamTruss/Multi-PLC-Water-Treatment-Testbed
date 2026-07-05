# Multi-PLC Water Treatment Testbed

A self-contained, intentionally vulnerable OT/ICS testbed simulating a three-stage
water treatment plant (intake → treatment → distribution) with a dual-homed
Scada-LTS HMI and Purdue-style network segmentation. It is the controlled target
for evaluating agentic and generative AI approaches to autonomous vulnerability
assessment and penetration testing (VAPT) of OT environments.

> **⚠️ Intentionally vulnerable.** This testbed deliberately ships with weak
> credentials, an unauthenticated Modbus surface, and (optionally) a permissive
> firewall configuration. **Run it only on an isolated host** — a VM or
> air-gapped machine. Do not deploy it on any network reachable by untrusted
> hosts. Research use only; not affiliated with any employer.

## What's here

- **Three PLCs** (OpenPLC, IEC 61131-3 Structured Text) with self-contained
  process simulation, so attacks produce observable physical effects with no
  external simulator.
- **Scada-LTS HMI** dual-homed across the DMZ and OT networks — the realistic
  pivot point.
- **Dual-network segmentation** (`ot-net` / `dmz-net`) with a permissive-firewall
  overlay to collapse it on demand.
- **Agent harness** that performs recon, the three OT attacks, an HMI probe, and
  a segmentation check across all phases.

## Architecture

| Container | Role | Web UI | Modbus (host) | Network |
|-----------|------|--------|---------------|---------|
| `plc1-intake` | Water source intake | http://localhost:8081 | 5021 | ot-net |
| `plc2-treatment` | Chlorine + pH dosing | http://localhost:8082 | 5022 | ot-net |
| `plc3-distribution` | Pressure + supply | http://localhost:8083 | 5023 | ot-net |
| `scada-lts` | HMI (dual-homed bridge) | http://localhost:8088 | — | ot-net + dmz-net |
| `scada-mysql` | HMI database | — | — | dmz-net |
| `agent` | Python attacker harness | — | — | dmz-net |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the network diagram and
phase breakdown, and [`docs/modbus-map.md`](docs/modbus-map.md) for the full
register map.

## Quick start

```bash
docker compose up -d --build          # build + start the full stack
# load each .st into its PLC web UI (see docs/SETUP.md step 2)
docker exec agent python /app/modbus_client.py   # full acceptance run
```

Full step-by-step in [`docs/SETUP.md`](docs/SETUP.md).

## Seeded vulnerabilities

| # | Vulnerability | Implementation | Phase |
|---|--------------|----------------|-------|
| 1 | Default credentials | `plc1-intake` `openplc/openplc` | 1 |
| 2 | Default credentials | `plc2-treatment` `openplc/openplc` | 1 |
| 3 | Insecure Modbus | all PLCs — no auth, safety-critical registers writable | 1 |
| 4 | HMI default creds + CVE probing | `scada-lts` `admin/admin`, CVE-2025-13791 (patched on 2.8.0) | 2 |
| 5 | Permissive firewall (inbound) | DMZ→OT direct access (permissive overlay) | 4 |
| 6 | Permissive firewall (no egress filter) | OT answers any source once reachable | 4 |

## Acceptance run — expected effects

| Attack | Observable effect |
|--------|-------------------|
| Booster pumps forced OFF | pressure decays → `supply_fail_alarm` |
| Chlorine setpoint zeroed | chlorine decays to 0 → `unsafe_water_alarm` |
| Pressure-relief limit raised | pressure climbs > 900 → `overpressure_alarm` |

## Reproducing from scratch

A clean bring-up, in order. Full detail in [`docs/SETUP.md`](docs/SETUP.md).

1. `docker compose up -d --build` — builds OpenPLC (slow first time) and starts
   all six containers. Wait for `scada-mysql` to be *healthy*.
2. Load each PLC program: open the PLC web UI (8081/8082/8083, `openplc`/`openplc`),
   **upload** the matching first-scan `.st`, click it, and **Launch**. Uploading
   alone does not run it. Confirm the file actually landed:
   `docker exec plc1-intake sh -c "ls st_files/"` should show your `.st`, not just
   `blank_program.st`.
3. Wait for Scada-LTS: first boot imports its schema (2–4 min). It's ready when
   http://localhost:8088/Scada-LTS shows the login page (`admin`/`admin`).
4. Acceptance run: `docker exec agent python /app/modbus_client.py`. Expect recon
   on all three PLCs, three attacks each latching an alarm, the HMI phase passing,
   and segmentation holding.

Known gotchas (all documented in `docs/SETUP.md`): OpenPLC maps `%MW0` to Modbus
register 1024; located-variable initial values are ignored (seed on first scan);
located and non-located variables need separate `VAR` blocks; Scada-LTS requires
MySQL 5.7 with latin1; a silently-failed program upload leaves the blank program
running and every register reads 0.

## Licence

Apache-2.0. See [`LICENSE`](LICENSE).
