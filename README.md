# Phase 2 Testbed - Multi-PLC Water Treatment Plant + SCADA HMI

Three-PLC testbed simulating a water treatment plant, now with a Scada-LTS
HMI layer and network segmentation.

## Architecture

| Container | Role | Web UI | Modbus port (host) | Network |
|-----------|------|--------|---------------------|---------|
| plc1-intake | Water source intake | http://localhost:8081 | 5021 | ot-net |
| plc2-treatment | Chlorine + pH dosing | http://localhost:8082 | 5022 | ot-net |
| plc3-distribution | Pressure + supply | http://localhost:8083 | 5023 | ot-net |
| scadalts | Scada-LTS HMI (DMZ ↔ OT bridge) | http://localhost:9090/Scada-LTS | n/a | dmz-net + ot-net |
| database | MySQL backend for HMI | (no UI) | n/a | dmz-net |
| agent | Python attacker | (no UI) | n/a | dmz-net |

Two Docker networks:
- `ot-net` (172.28.10.0/24) — PLCs only
- `dmz-net` (172.28.20.0/24) — agent, HMI, database

The agent on dmz-net cannot reach PLCs on ot-net directly. Scada-LTS is
dual-homed and is the legitimate bridge between zones.

## Folder layout

```
.
├── docker-compose.yml
├── plc1_intake.st          <- upload to plc1-intake web UI
├── plc2_treatment.st       <- upload to plc2-treatment web UI
├── plc3_distribution.st    <- upload to plc3-distribution web UI
├── agent/
│   ├── tools/
│   │   └── modbus_client.py
│   ├── scripts/
│   │   ├── init_defaults.py
│   │   ├── process_simulator.py
│   │   └── exploit_seeded_hmi.py
│   └── requirements.txt
├── tests/
│   ├── conftest.py
│   ├── test_phase1.py
│   └── test_phase2.py
└── docs/
    ├── ROADMAP.md
    └── PHASE2_PLAN.md
```

## First-time setup

```powershell
# Bring everything down (clean slate from previous testbed)
docker compose down -v

# Bring up the multi-PLC + HMI compose
docker compose up -d

# Install agent dependencies
docker exec agent pip install -r /app/requirements.txt
```

Then for each PLC:
1. Open its web UI (8081, 8082, 8083 in turn)
2. Default login: openplc / openplc
3. Go to Programs -> upload the matching .st file
4. Click the program -> Launch program
5. Status should turn green / Running

For the HMI:
1. Open http://localhost:9090/Scada-LTS
2. Default login: admin / admin
3. The HMI is functional but data sources are unconfigured by default
   (manual configuration deferred to v0.2.1)

## Run the acceptance test suite

```powershell
docker exec agent pytest /app/tests/ -v
```

Ten tests covering:
- Phase 1 regression (Modbus tooling, address maps, segmentation)
- Phase 2 acceptance (DMZ isolation, HMI deployment, default-creds vuln, CVE-2025-13791 patched)

## Run the seeded HMI exploit

```powershell
docker exec agent python /app/scripts/exploit_seeded_hmi.py
```

You should see two attack sections:
1. Default credentials accepted - authenticated admin session established (CWE-798)
2. CVE-2025-13791 path traversal probe - documented as patched in Scada-LTS 2.8.0

## Seeded vulnerabilities

| # | Vuln | Implementation | Status |
|---|------|----------------|--------|
| 1 | Default creds PLC #1 | plc1-intake left with openplc/openplc | Phase 1 |
| 2 | Default creds PLC #2 | plc2-treatment left with openplc/openplc | Phase 1 |
| 3 | Insecure Modbus | All PLCs - no auth, safety-critical regs writable | Phase 1 |
| 4 | Unpatched HMI | Scada-LTS default credentials (CWE-798) | Phase 2 |
| 5 | Permissive firewall #1 | Cross-zone bridge | Phase 4 |
| 6 | Permissive firewall #2 | Cross-zone bridge | Phase 4 |

Phase 2 covers vulns 1-4. Phases 3-4 will complete the seeded set.

See `docs/ROADMAP.md` for the full release plan.

Research use only. Not affiliated with any employer.

⚠️ Intentionally vulnerable. This testbed deliberately ships with weak credentials, insecure Modbus configuration, and a default-credentials HMI. Do not deploy on any network reachable by untrusted hosts. Use an isolated VM or air-gapped host.
