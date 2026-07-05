(* =========================================================================
   PLC3 - DISTRIBUTION
   Multi-PLC Water Treatment Testbed
   ---------------------------------------------------------------------------
   Pressure management and supply via two booster pumps with a pressure-relief
   limit. Attacks: (a) pumps forced OFF -> supply failure; (b) pressure_max
   raised -> relief disabled -> overpressure.

   Scaling: pressure in hundredths of bar (800 = 8.00 bar). Safe hard limit
   = 900. Normal relief setpoint = 800.

   OpenPLC gotchas: located vs non-located in SEPARATE VAR blocks; located
   initial values are ignored at runtime, so seed them on first scan.
   See docs/modbus-map.md.
   ========================================================================= *)

PROGRAM prog0
  VAR
    (* --- Located variables (Modbus-exposed) - NO initial values here --- *)
    pressure           AT %MW0  : INT;
    pressure_max       AT %MW1  : INT;
    booster1_status    AT %MW2  : INT;
    booster2_status    AT %MW3  : INT;
    booster1_cmd       AT %QX0.0 : BOOL;
    booster2_cmd       AT %QX0.1 : BOOL;
    overpressure_alarm AT %QX0.2 : BOOL;
    supply_fail_alarm  AT %QX0.3 : BOOL;
  END_VAR

  VAR
    first_scan : BOOL := TRUE;
    pumps_on   : BOOL := FALSE;
    tick       : INT := 0;
  END_VAR

  IF first_scan THEN
    pressure        := 600;
    pressure_max    := 800;
    booster1_status := 1;
    booster2_status := 1;
    booster1_cmd    := TRUE;
    booster2_cmd    := TRUE;
    first_scan      := FALSE;
  END_IF;

  tick := tick + 1;
  IF tick >= 20 THEN
    tick := 0;

    pumps_on := booster1_cmd OR booster2_cmd;

    IF pumps_on THEN
      pressure := pressure + 30;
    ELSE
      pressure := pressure - 30;
    END_IF;

    (* Relief valve vents above the relief setpoint; raising pressure_max
       (attack) disables relief and lets pressure climb past the 900 limit. *)
    IF pressure > pressure_max THEN
      pressure := pressure_max;
    END_IF;
    IF pressure < 0 THEN pressure := 0; END_IF;

    (* Safety invariants *)
    IF pressure > 900 THEN
      overpressure_alarm := TRUE;
    ELSE
      overpressure_alarm := FALSE;
    END_IF;

    IF pressure < 100 THEN
      supply_fail_alarm := TRUE;
    ELSE
      supply_fail_alarm := FALSE;
    END_IF;

    (* Status mirrors *)
    IF booster1_cmd THEN booster1_status := 1; ELSE booster1_status := 0; END_IF;
    IF booster2_cmd THEN booster2_status := 1; ELSE booster2_status := 0; END_IF;
  END_IF;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#50ms, PRIORITY := 0);
    PROGRAM instance0 WITH task0 : prog0;
  END_RESOURCE
END_CONFIGURATION
