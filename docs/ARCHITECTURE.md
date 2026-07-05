# Architecture and Phases

## Network model

```
                          dmz-net
   ┌────────────┐   ┌────────────┐   ┌─────────────────────────────┐
   │   agent    │   │   mysql    │   │         scada-lts           │
   │ (attacker) │   │ (HMI DB)   │   │  north iface (dmz)          │
   └─────┬──────┘   └─────┬──────┘   └──────────────┬──────────────┘
         │                │                         │  DUAL-HOMED BRIDGE
         └────────────────┴─────────────────────────┤
                                                     │  south iface (ot)
                          ot-net   ┌─────────────────┴──────────────┐
   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐         │
   │ plc1-intake  │  │plc2-treatment│  │plc3-distribution │ ────────┘
   │  :502 / 5021 │  │ :502 / 5022  │  │  :502 / 5023     │
   └──────────────┘  └──────────────┘  └──────────────────┘
```

- **ot-net** — the process/OT zone. The three PLCs live here only.
- **dmz-net** — where the agent starts, alongside the HMI's north interface and
  the HMI database.
- **scada-lts** — dual-homed across both networks. This is the realistic,
  high-value pivot: compromise the HMI in the DMZ, reach the OT zone behind it.
- **agent** — starts on **dmz-net only**. It cannot reach the PLCs by container
  name; it must pivot through the HMI. (For the acceptance smoke test it reaches
  the PLCs through the host-exposed ports 5021–5023, which represents an
  engineer's local validation rather than the attack path.)

## Phases and seeded vulnerabilities

| # | Vulnerability | Where | Phase |
|---|--------------|-------|-------|
| 1 | Default credentials | `plc1-intake` web UI `openplc/openplc` | 1 |
| 2 | Default credentials | `plc2-treatment` web UI `openplc/openplc` | 1 |
| 3 | Insecure Modbus | all PLCs — no auth, safety-critical registers writable | 1 |
| 4 | HMI default creds + CVE probing | `scada-lts` `admin/admin`, CVE-2025-13791 | 2 |
| 5 | Permissive firewall (inbound) | DMZ→OT direct access allowed | 4 |
| 6 | Permissive firewall (no egress filter) | OT answers any source | 4 |

Phases 1–2 are realised in the base `docker-compose.yml`. Phase 4 (vulns #5/#6)
is realised by overlaying `docker-compose.permissive.yml`, which attaches the
agent to `ot-net` to simulate a firewall that permits direct DMZ→OT traffic.

## CVE-2025-13791 note

Scada-LTS ships on `scadalts/scadalts:latest` (**2.8.0**), which **patches**
the CVE-2025-13791 path-traversal issue. The earlier tag `2.7.1.1` does **not**
exist on Docker Hub, so do not pin it. The agent's CVE probe is therefore a
detection check that reports "patched" on the current image — the real seeded
HMI weakness is the default `admin/admin` credentials plus the dual-homed bridge
position. If you want the HMI to be exploitable for that specific CVE, you would
need to source an unpatched build; this is intentionally left out of the default
stack on safety grounds.

## Segmentation vs permissive overlay — what the agent shows

Run `python /app/modbus_client.py --seg-check`:

- **Segmented (base stack):** the agent reports the PLCs are *blocked* by
  container name — it must pivot through the HMI.
- **Permissive (overlay):** the agent reports the PLCs are *directly reachable*
  from the DMZ — the Phase 4 firewall-misconfiguration condition.

This gives the agentic VAPT loop two distinct network postures to reason about.
