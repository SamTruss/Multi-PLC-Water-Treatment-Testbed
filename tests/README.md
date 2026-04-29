# Test suite

One-command validation of the testbed.

## Setup (one time)

```powershell
docker exec agent pip install -r /app/requirements.txt
```

## Run all tests

```powershell
docker exec agent pytest /app/tests/ -v
```

## Run a single phase

```powershell
docker exec agent pytest /app/tests/test_phase1.py -v
docker exec agent pytest /app/tests/test_phase2.py -v
```

## What's covered

| File | What |
|---|---|
| `test_phase1.py` | Phase 1 regression — Modbus client imports, address maps complete, segmentation respected |
| `test_phase2.py` | Phase 2 acceptance — segmentation, HMI loads, default-creds vuln present, CVE-2025-13791 endpoints absent |

## What's NOT covered (yet)

- Direct PLC Modbus operations from the agent (impossible by design after Phase 2 segmentation; will be reachable from inside scadalts container, or from agent after Phase 4 firewall rules).
- Live HMI dashboard rendering (Stage 2.4 manual config).
- Process simulator running (it broke when we segmented; needs to move into a container that can reach ot-net).

## Adding tests

Drop a new `test_*.py` file in `/tests/`. Use the `can_reach` and
`http_session` fixtures from `conftest.py`.
