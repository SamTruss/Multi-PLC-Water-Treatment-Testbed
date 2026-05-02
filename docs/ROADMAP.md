# Roadmap

## Released

### v0.1.0 — Phase 1: Multi-PLC OT testbed
- Three OpenPLC instances simulating a water treatment plant (intake / treatment / distribution)
- Real ladder logic in Structured Text
- Modbus client tooling and process simulator
- Seeded vulnerabilities: default credentials (×2), insecure Modbus

### v0.2.0 — Phase 2: SCADA HMI + network segmentation
- Scada-LTS HMI deployed (bridges DMZ ↔ OT)
- Network segmentation: ot-net (172.28.10.0/24) + dmz-net (172.28.20.0/24)
- Seeded vulnerability: unpatched HMI / default credentials (CWE-798)
- Negative finding: CVE-2025-13791 patched in Scada-LTS 2.8.0
- Pytest acceptance suite (10 tests)
- Exploit script demonstrates programmatic HMI compromise

## Planned

### v0.2.1 — Phase 2 polish
**Manual HMI configuration to make the operator-facing dashboard usable:**

- Add three Modbus TCP data sources (one per PLC) inside Scada-LTS
- Wire up data points for each PLC variable (TankLevel, Pump, ChlorineLevel, Pressure, etc.)
- Build a dashboard with gauges + indicator lights for the three stations
- Stretch goal: "Stuxnet-style" demo figure — agent tampers with PLC values via Modbus while HMI dashboard continues to show pre-attack readings (paper-grade visual)

This is operator-facing polish. The agent's attack surface and the test suite are unaffected; this is purely for visualisation in the paper and live demos.

### v0.3.0 — Phase 3: Process simulator on dmz-net
- Migrate process_simulator.py to a container that can reach ot-net (likely scadalts as bridge, or new sim service)
- Restore live process dynamics (pumps fill tanks, dosers adjust pH, etc.)
- Acceptance test: simulator drives sensor values; PLCs respond; HMI sees changes

### v0.4.0 — Phase 4: Firewall and remaining seeded vulnerabilities
- Add an `it-net` zone for a third network tier (it / dmz / ot)
- iptables rules between zones (real segmentation, not just Docker bridges)
- Two **deliberately permissive** firewall rules = paper vulns #5 and #6
- Move the agent to it-net so it must traverse multiple boundaries

### v0.5.0 — Phase 5: Vulnerable services
- Optional FTP / Telnet / weak SSH on the network for nmap-discoverable surface
- Increases coverage scoring potential for the agent benchmark
