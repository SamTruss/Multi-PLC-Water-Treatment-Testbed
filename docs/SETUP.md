# Setup Guide — get the full testbed running this evening

Target: a clean bring-up of all three PLCs, the Scada-LTS HMI, and the agent,
with the full acceptance run passing. Allow ~30–45 minutes, most of which is the
one-time OpenPLC image build.

> **⚠️ Intentionally vulnerable.** Run this only on an isolated host (a VM or an
> air-gapped machine). Do not place it on any network reachable by untrusted
> hosts.

## 0. Prerequisites

- Docker Desktop running (Windows/macOS) or Docker Engine + Compose v2 (Linux).
- ~4 GB free RAM (Scada-LTS/Tomcat wants ~1 GB; mysql ~512 MB).
- Ports free on the host: `8081 8082 8083 8088 5021 5022 5023`.

Drop all the testbed files into one folder, preserving this layout:

```
testbed/
├── docker-compose.yml
├── docker-compose.permissive.yml
├── openplc/Dockerfile
├── agent/{Dockerfile,modbus_client.py,requirements.txt}
├── plc1_intake.st  plc2_treatment.st  plc3_distribution.st
└── docs/
```

> If your existing Phase 1–2 OpenPLC image already works, skip the build: edit
> `docker-compose.yml` and replace each `build: ./openplc` with
> `image: <your-openplc-image>`. Likewise, if you have a known-good `scada-lts`
> service block, keep it and just ensure `networks: [ot-net, dmz-net]`.

## 1. Bring the stack up

```bash
cd testbed

# Clean slate (removes any previous testbed volumes)
docker compose down -v

# Build + start everything. First run compiles OpenPLC — be patient.
docker compose up -d --build

# Watch until mysql is healthy and scada-lts has started
docker compose ps
```

Expect five containers up: `plc1-intake`, `plc2-treatment`, `plc3-distribution`,
`scada-mysql` (healthy), `scada-lts`, plus `agent`. Scada-LTS can take 1–2
minutes after MySQL is healthy before its web UI answers.

## 2. Load each PLC program

For **each** PLC, in turn:

| PLC | Web UI | Program file |
|-----|--------|--------------|
| Intake | http://localhost:8081 | `plc1_intake.st` |
| Treatment | http://localhost:8082 | `plc2_treatment.st` |
| Distribution | http://localhost:8083 | `plc3_distribution.st` |

1. Log in with `openplc` / `openplc`.
2. **Programs → Upload Program** → choose the matching `.st` file → **Upload**.
3. Click the uploaded program → **Launch program**.
4. **Settings →** ensure **Modbus** server is enabled (it is by default).
5. The status indicator should go green / *Running*.

## 3. Run the Phase 1 acceptance test (OT)

```bash
docker exec agent python /app/modbus_client.py --recon
```

You should see all 3 PLCs reachable with live register values. If a PLC connects
but returns no registers, set the unit id: `docker exec -e MODBUS_UNIT=0 agent
python /app/modbus_client.py --recon`.

Then the full attack run:

```bash
docker exec agent python /app/modbus_client.py
```

Expected, in order:

1. **Recon** — three PLCs surveyed.
2. **Pumps OFF** — `supply_fail_alarm` raises as pressure decays.
3. **Chlorine zeroed** — `unsafe_water_alarm` raises as chlorine decays to 0.
4. **Relief disabled** — `pressure` climbs past 900, `overpressure_alarm` raises.
5. **HMI** — Scada-LTS reachable, default creds check, CVE-2025-13791 reported
   patched.
6. **Segmentation check** — PLCs reported *blocked* by container name (segmented).

## 4. Phase 2 — the HMI

Open http://localhost:8088/Scada-LTS and log in with `admin` / `admin`. This is
the dual-homed bridge. From here an operator (or attacker) can see and command
the OT zone. Build watch lists / graphical views against the PLC data points as
needed for your scenarios.

## 5. Phase 4 — permissive firewall scenario

Collapse the segmentation to simulate a misconfigured firewall (vulns #5/#6):

```bash
docker compose -f docker-compose.yml -f docker-compose.permissive.yml up -d
docker exec -e PLC1_HOST=plc1-intake -e PLC1_PORT=502 \
            -e PLC2_HOST=plc2-treatment -e PLC2_PORT=502 \
            -e PLC3_HOST=plc3-distribution -e PLC3_PORT=502 \
            agent python /app/modbus_client.py --seg-check
```

Now the agent reaches the PLCs **directly** from the DMZ. Restore segmentation by
bringing the stack up with the base compose file alone.

## 6. Resetting process state

The simulation runs continuously, so alarms latch on attacked values. To reset a
PLC's process to nominal, restart it (re-launch its program in the web UI) or:

```bash
docker compose restart plc2-treatment   # then re-launch its program in the UI
```

## 7. Teardown

```bash
docker compose down -v
```

## Troubleshooting

- **Scada-LTS won't start / `dataSource is required` / schema errors** — the
  `scadalts/scadalts` image connects to its database at hostname **`database`**
  as **root/root** against a **`scadalts`** DB, and its schema migrations require
  **MySQL 5.7** with **latin1** (MySQL 8.0 defaults to utf8mb4 and its stricter
  SQL rejects the `ViewsHierarchy` migration). The compose already encodes this:
  `mysql:5.7`, `--character-set-server=latin1`, and a `database` network alias.
  If migration half-completes, always `docker compose down -v` before retrying so
  the schema imports into a clean database.
- **All `%MW` registers read 0 even though a program is "uploaded"** — a
  silently-failed web-UI upload leaves OpenPLC running `blank_program.st`, which
  has no `%MW` variables, so every holding register reads 0. This looks exactly
  like a Modbus addressing bug but isn't. Verify what's actually loaded:
  `docker exec plc1-intake sh -c "ls -la /OpenPLC_v3/webserver/st_files/"` — you
  should see your `.st` (and a `.st.dbg` after compile), not just
  `blank_program.st`. Re-upload, then click the program and **Launch** it
  (uploading alone does not swap the running logic).
- **`%MW` addressing** — OpenPLC maps `%MW0` to Modbus holding register **1024**,
  not 0 (address 0 is `%QW0`). The agent applies this base automatically; a raw
  client must read at `1024 + offset`.
- **Located variable initial values are ignored** — OpenPLC zeroes I/O memory at
  start-up, so `AT %MW0 : INT := 800` does nothing. Seed located variables in the
  program body on the first scan via a non-located `first_scan` flag.
- **`host.docker.internal` not resolving (Linux)** — the compose sets
  `extra_hosts: host-gateway`, which works on Compose v2; if not, run the smoke
  test with the permissive overlay and container-name env vars instead (step 5).
- **No Modbus register response** — try `MODBUS_UNIT=0`. Confirm the program is
  *Running* and the Modbus server is enabled in OpenPLC Settings.
- **Port already in use** — change the host side of the port mapping in
  `docker-compose.yml` (e.g. `"9081:8080"`).
- **OpenPLC build fails** — substitute your existing working OpenPLC image per
  the note in step 0.
