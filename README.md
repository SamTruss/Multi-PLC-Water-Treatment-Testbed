# Phase 1 Testbed - Multi-PLC Water Treatment Plant

Three-PLC testbed simulating a water treatment plant. Foundation for the
agentic VAPT validation scenario described in the paper.

## Architecture

| Container | Role | Web UI | Modbus port (host) |
|-----------|------|--------|---------------------|
| plc1-intake | Water source intake | http://localhost:8081 | 5021 |
| plc2-treatment | Chlorine + pH dosing | http://localhost:8082 | 5022 |
| plc3-distribution | Pressure + supply | http://localhost:8083 | 5023 |
| agent | Python attacker | (no UI) | n/a |

All on Docker network `ot-net`. Within the network, agent reaches PLCs at
`plc1-intake:502`, `plc2-treatment:502`, `plc3-distribution:502`.

## Folder layout

```
testbed/
├── docker-compose.yml
├── plc1_intake.st          <- upload to plc1-intake web UI
├── plc2_treatment.st       <- upload to plc2-treatment web UI
├── plc3_distribution.st    <- upload to plc3-distribution web UI
└── agent/
    ├── modbus_client.py
    └── requirements.txt
```

## First-time setup

```powershell
# Bring everything down (clean slate from previous testbed)
docker compose down -v

# Bring up the new multi-PLC compose
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

## Run the multi-PLC smoke test

```powershell
docker exec agent python /app/modbus_client.py
```

You should see four sections:
1. Recon survey of all three PLCs
2. Distribution PLC booster pumps forced OFF
3. Treatment PLC chlorine setpoint zeroed
4. Distribution PLC pressure max raised to disable relief

## Seeded vulnerabilities (matches paper validation scenario)

| # | Vuln | Implementation |
|---|------|----------------|
| 1 | Default creds PLC #1 | plc1-intake left with openplc/openplc |
| 2 | Default creds PLC #2 | plc2-treatment left with openplc/openplc |
| 3 | Insecure Modbus | All PLCs - no auth, safety-critical regs writable |
| 4 | Unpatched HMI | (Phase 2 - Scada-LTS) |
| 5 | Permissive firewall #1 | (Phase 4 - cross-zone bridge) |
| 6 | Permissive firewall #2 | (Phase 4 - cross-zone bridge) |

Phase 1 covers vulns 1-3. Phases 2-4 add 4-6.
