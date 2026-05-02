# v0.2.1 — Phase 2 polish (HMI dashboard + Stuxnet demo)

> Branch: `phase2/hmi-polish`
> Base: v0.2.0
> Estimated time: 1-2 hours of clicking + 1 commit cycle

## What v0.2.1 adds

- **`docs/SCADALTS_SETUP.md`** — full step-by-step manual for configuring data sources, data points, and the dashboard
- **`docs/STUXNET_DEMO.md`** — paper-grade demo procedure
- **`tests/test_phase2_hmi_config.py`** — pytest verification that the dashboard is configured
- **Manual HMI configuration** (the click work)
- **README.md update** — reference the new docs

## What v0.2.1 does NOT add

- New code (no Python changes beyond the test file)
- Network architecture changes
- New seeded vulnerabilities

This is a polish release. The agent's attack surface is unchanged.

## Branch + ship workflow

```powershell
# Create the branch
git checkout main
git pull
git checkout -b phase2/hmi-polish
git push -u origin phase2/hmi-polish

# Drop in the new docs and tests
# (you'll do the manual HMI clicks too — see SCADALTS_SETUP.md)

# Verify
docker exec agent pytest /app/tests/ -v
# All previous tests still pass + 4 new tests for HMI config

# Commit
git add docs/SCADALTS_SETUP.md docs/STUXNET_DEMO.md tests/test_phase2_hmi_config.py README.md
git commit -m "v0.2.1: HMI manual configuration + Stuxnet demo"
git push

# Merge + tag
git checkout main
git merge phase2/hmi-polish
git tag -a v0.2.1 -m "HMI dashboard polish + Stuxnet-style demo"
git push --tags
```

## Definition of done

- [ ] Three Modbus TCP data sources visible in Scada-LTS, all enabled and green
- [ ] At least 3 data points reading values per data source
- [ ] "Water Treatment Plant Overview" dashboard renders with gauges
- [ ] All 14 pytest tests green (10 from v0.2.0 + 4 new HMI config tests)
- [ ] `docs/SCADALTS_SETUP.md` walks a fresh user through it in under 60 minutes
- [ ] Paper figure captured: before/after operator-view screenshots
- [ ] README updated to mention the dashboard
- [ ] Tag pushed: `v0.2.1`

## What comes after

Next is **v0.3.0 / Phase 3** — moving the process simulator so it can drive PLC sensor values across the dmz-net/ot-net boundary. With the dashboard in place from v0.2.1, the simulator's effect will be visible in real-time, which makes Phase 3's testing much more satisfying.
