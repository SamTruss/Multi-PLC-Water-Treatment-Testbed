(* =========================================================================
   PLC2 - TREATMENT
   Multi-PLC Water Treatment Testbed
   ---------------------------------------------------------------------------
   Safety-critical stage: chlorine residual dosing and pH correction.
   Headline attack: zeroing chlorine_setpoint drives chlorine to 0 and raises
   unsafe_water_alarm.

   Scaling: chlorine/pH in hundredths (200 = 2.00 mg/L, 700 = pH 7.00).
   Safe chlorine residual >= 0.50 mg/L (value >= 50).

   OpenPLC gotchas: located vs non-located in SEPARATE VAR blocks; located
   initial values are ignored at runtime, so seed them on first scan.
   See docs/modbus-map.md.
   ========================================================================= *)

PROGRAM prog0
  VAR
    (* --- Located variables (Modbus-exposed) - NO initial values here --- *)
    chlorine_level     AT %MW0  : INT;
    chlorine_setpoint  AT %MW1  : INT;
    ph_level           AT %MW2  : INT;
    ph_setpoint        AT %MW3  : INT;
    dosing_status      AT %MW4  : INT;
    dosing_enable      AT %QX0.0 : BOOL;
    unsafe_water_alarm AT %QX0.1 : BOOL;
    ph_excursion_alarm AT %QX0.2 : BOOL;
  END_VAR

  VAR
    first_scan : BOOL := TRUE;
    tick       : INT := 0;
  END_VAR

  IF first_scan THEN
    chlorine_level    := 200;
    chlorine_setpoint := 200;
    ph_level          := 700;
    ph_setpoint       := 700;
    dosing_status     := 1;
    dosing_enable     := TRUE;
    first_scan        := FALSE;
  END_IF;

  tick := tick + 1;
  IF tick >= 20 THEN
    tick := 0;

    (* Chlorine trends toward setpoint while dosing enabled; setpoint 0 -> decay *)
    IF dosing_enable THEN
      dosing_status := 1;
      IF chlorine_level < chlorine_setpoint THEN
        chlorine_level := chlorine_level + 5;
      ELSIF chlorine_level > chlorine_setpoint THEN
        chlorine_level := chlorine_level - 5;
      END_IF;
    ELSE
      dosing_status := 0;
      IF chlorine_level > 0 THEN chlorine_level := chlorine_level - 5; END_IF;
    END_IF;
    IF chlorine_level < 0 THEN chlorine_level := 0; END_IF;

    (* pH correction trends toward setpoint *)
    IF ph_level < ph_setpoint THEN
      ph_level := ph_level + 2;
    ELSIF ph_level > ph_setpoint THEN
      ph_level := ph_level - 2;
    END_IF;

    (* Safety invariants *)
    IF chlorine_level < 50 THEN
      unsafe_water_alarm := TRUE;
    ELSE
      unsafe_water_alarm := FALSE;
    END_IF;

    IF (ph_level < 650) OR (ph_level > 850) THEN
      ph_excursion_alarm := TRUE;
    ELSE
      ph_excursion_alarm := FALSE;
    END_IF;
  END_IF;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#50ms, PRIORITY := 0);
    PROGRAM instance0 WITH task0 : prog0;
  END_RESOURCE
END_CONFIGURATION
