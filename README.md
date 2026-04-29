# Phase 2 — Scada-LTS HMI + Network Segmentation

> **Branch:** `phase2/scadalts`
> **Status:** in progress
> **Target version:** v0.2.0

---

## Branch strategy

This work happens on a feature branch. Once Phase 2 is complete and tested, it merges back to `main`.

```
main (v0.1.0)
 └── phase2/scadalts ← you are here
```

### Working with the branch

```powershell
# Pull the latest main first
git checkout main
git pull

# Create the feature branch
git checkout -b phase2/scadalts

# Push it to GitHub so it's tracked remotely
git push -u origin phase2/scadalts
```

From now on, all Phase 2 commits go on `phase2/scadalts`. Don't touch `main` until we're ready to merge.

### When Phase 2 is done

```powershell
# Make sure everything is committed and tests pass
git add .
git commit -m "Phase 2 complete — Scada-LTS + DMZ"
git push

# Merge to main via GitHub PR (preferred) OR locally:
git checkout main
git merge phase2/scadalts
git tag v0.2.0
git push --tags
```

If you want a code review trail (good for PhD documentation), use GitHub's "Create pull request" — it gives you a permanent record of every change with commit messages, diffs, and merge timestamps. That's citable evidence in a thesis.

---

## What changes in Phase 2

### Architecture diff vs Phase 1

| | Phase 1 | Phase 2 |
|---|---------|---------|
| Networks | 1 (`ot-net`) | 2 (`ot-net` + `dmz-net`) |
| PLCs | 3 on `ot-net` | 3 on `ot-net` (unchanged) |
| HMI | None | Scada-LTS 2.7.1.1 on `dmz-net`, bridges to `ot-net` |
| HMI database | None | MySQL 8.0.32 on `dmz-net` |
| Agent | On `ot-net` | On `dmz-net` (more realistic threat model) |
| Tests | None | pytest suite (`test_phase1.py`, `test_phase2.py`) |
| Folder layout | Flat `agent/` | `agent/tools/` + `agent/scripts/` + `tests/` |

### Why these changes

**DMZ-net for HMI:** real plants put SCADA in a DMZ between corporate IT and the OT zone. The HMI legitimately needs to talk to PLCs (it shows their data and lets operators control them), so it bridges both networks. An attacker who gets into the DMZ can pivot to OT by attacking through the HMI. This matches the paper's threat model exactly.

**Agent on dmz-net:** simulates an attacker who has compromised the DMZ first. They can see Scada-LTS and the database directly, but PLCs are only reachable via the HMI bridge. Agent has to **discover** the path.

**Tests folder:** Phase 2 adds enough surface area that manual smoke-testing won't scale. Pytest runs the whole testbed validation in 30 seconds.

**Tools/scripts split:** when we build the agent loop in Phase 5, the LLM will discover available capabilities by listing `agent/tools/`. Keeping import-only modules separate from runnable scripts makes that introspection clean.

---

## Seeded vulnerability tracker

Aligns with the paper's six-vulnerability validation scenario.

| # | Vuln | Where it lives | Phase added | Status |
|---|------|----------------|-------------|--------|
| 1 | Default creds PLC #1 | plc1-intake (openplc/openplc) | 1 | ✅ |
| 2 | Default creds PLC #2 | plc2-treatment (openplc/openplc) | 1 | ✅ |
| 3 | Insecure Modbus | All PLCs (no auth on writable safety regs) | 1 | ✅ |
| 4 | Unpatched HMI | Scada-LTS 2.7.1.1 — CVE-2022-41976 (CVSS 9.9) | 2 | 🔨 building |
| 5 | Permissive firewall #1 | Cross-zone bridge | 4 | 📅 |
| 6 | Permissive firewall #2 | Cross-zone bridge | 4 | 📅 |

**CVE-2022-41976** (the Phase 2 vuln) — privilege escalation in Scada-LTS 2.7.1.1: a low-privileged user can promote themselves to admin by updating their own user profile. Documented in NVD, CVSS 9.9 Critical. Vendor confirmed; a real CVE, not a synthetic one.

---

## Build plan (5 stages)

| Stage | What | Time |
|-------|------|------|
| 2.1 | Network segmentation only — add dmz-net, move agent | ~15 min |
| 2.2 | Deploy Scada-LTS 2.7.1.1 + MySQL backend | ~30 min |
| 2.3 | Manual HMI configuration (data sources, dashboard) | ~45 min |
| 2.4 | Tools/scripts refactor + pytest suite | ~45 min |
| 2.5 | CVE-2022-41976 exploit script + verification | ~30 min |

We're doing **stages 2.1 and 2.2** today.

---

## Quick reference (after Phase 2 is complete)

### URLs

| Service | URL | Login |
|---------|-----|-------|
| PLC1 (Intake) | http://localhost:8081 | adm_struss / your-password |
| PLC2 (Treatment) | http://localhost:8082 | openplc / openplc (default — vuln #2) |
| PLC3 (Distribution) | http://localhost:8083 | openplc / openplc (default — vuln #1) |
| Scada-LTS HMI | http://localhost:9090/Scada-LTS | admin / admin |

### Common commands

```powershell
# Start everything
docker compose up -d

# Watch Scada-LTS boot (slow, takes ~2 min on first run)
docker logs scadalts -f

# Run process simulator (in second terminal)
docker exec -it agent python /app/scripts/process_simulator.py

# Initialise PLC defaults
docker exec agent python /app/scripts/init_defaults.py

# Run all tests
docker exec agent pytest /app/tests/ -v

# Run the seeded HMI exploit
docker exec agent python /app/scripts/exploit_cve_2022_41976.py
```

### Stop / restart

```powershell
docker compose down       # stops, keeps data
docker compose down -v    # stops AND wipes all volumes (nuclear option)
docker compose up -d      # restart
```

---

## Definition of done

Before merging `phase2/scadalts` → `main` and tagging v0.2.0:

- [ ] Stage 2.1: agent on dmz-net can still reach all 3 PLCs (no firewall yet, that's Phase 4)
- [ ] Stage 2.2: Scada-LTS web UI loads, login works
- [ ] Stage 2.3: HMI dashboard shows live values from all 3 PLCs
- [ ] Stage 2.4: `pytest /app/tests/` — green
- [ ] Stage 2.5: CVE-2022-41976 exploit lands successfully
- [ ] All Phase 1 functionality still works (regression)
- [ ] Documentation: README, PHASE2_PLAN, SCADALTS_SETUP all up to date
