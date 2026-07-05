(* =========================================================================
   PLC1 - INTAKE
   Multi-PLC Water Treatment Testbed
   ---------------------------------------------------------------------------
   Raw-water source intake. Controls the intake pump that fills the treatment
   feed tank, with self-contained process simulation.

   OpenPLC / MatIEC gotchas encoded below:
     1. Located vars (AT %...) and non-located helpers MUST be in SEPARATE
        VAR blocks, else "invalid located variable declaration".
     2. OpenPLC IGNORES initial values on located vars (I/O memory is zeroed
        at start-up). Initialise them in the body on the first scan instead,
        gated by a NON-located first_scan flag (non-located inits ARE honoured).

   Modbus: %MWn -> Holding Register n; %QXn -> Coil. See docs/modbus-map.md.
   ========================================================================= *)

PROGRAM prog0
  VAR
    (* --- Located variables (Modbus-exposed) - NO initial values here --- *)
    source_level     AT %MW0  : INT;
    tank_level       AT %MW1  : INT;
    intake_flow      AT %MW2  : INT;
    pump_status      AT %MW3  : INT;
    pump_cmd         AT %QX0.0 : BOOL;
    low_source_alarm AT %QX0.1 : BOOL;
    tank_high_alarm  AT %QX0.2 : BOOL;
  END_VAR

  VAR
    (* --- Non-located helpers (separate block; inits honoured) --- *)
    first_scan : BOOL := TRUE;
    tick       : INT := 0;
  END_VAR

  (* First-scan initialisation - the only reliable way to seed located vars *)
  IF first_scan THEN
    source_level := 800;
    tank_level   := 300;
    pump_cmd     := TRUE;
    first_scan   := FALSE;
  END_IF;

  tick := tick + 1;
  IF tick >= 20 THEN          (* update process model ~1 Hz at 50 ms scan *)
    tick := 0;

    (* Dry-run protection *)
    IF source_level < 50 THEN
      low_source_alarm := TRUE;
    ELSE
      low_source_alarm := FALSE;
    END_IF;

    (* Pump moves water from source to feed tank when commanded and safe *)
    IF pump_cmd AND (source_level >= 50) THEN
      intake_flow := 100;
      pump_status := 1;
      IF source_level > 0 THEN source_level := source_level - 1; END_IF;
      IF tank_level < 1000 THEN tank_level := tank_level + 2; END_IF;
    ELSE
      intake_flow := 0;
      pump_status := 0;
    END_IF;

    (* Feed tank drains downstream *)
    IF tank_level > 0 THEN tank_level := tank_level - 1; END_IF;

    (* Overflow alarm *)
    IF tank_level >= 950 THEN
      tank_high_alarm := TRUE;
    ELSE
      tank_high_alarm := FALSE;
    END_IF;
  END_IF;
END_PROGRAM

CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#50ms, PRIORITY := 0);
    PROGRAM instance0 WITH task0 : prog0;
  END_RESOURCE
END_CONFIGURATION
