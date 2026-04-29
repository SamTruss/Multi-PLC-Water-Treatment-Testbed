PROGRAM IntakeStation
  VAR
    SourceLevel AT %MW10 : INT;
    IntakeFlow AT %MW11 : INT;
    EmergencyStop AT %MW12 : INT;
    IntakePump AT %QX0.0 : BOOL;
    IntakeValve AT %QX0.1 : BOOL;
    LowSourceAlarm AT %QX0.2 : BOOL;
    HighFlowAlarm AT %QX0.3 : BOOL;
    PumpRuntime AT %MW0 : INT;
    PumpHysteresis AT %MW1 : INT;
    TotalIntake AT %MW2 : INT;
  END_VAR

  IF SourceLevel < 30 THEN
    PumpHysteresis := 0;
  ELSIF SourceLevel > 70 THEN
    PumpHysteresis := 1;
  END_IF;

  IntakePump := (PumpHysteresis = 1) AND (EmergencyStop = 0);
  IntakeValve := IntakePump;
  LowSourceAlarm := SourceLevel < 20;
  HighFlowAlarm := IntakeFlow > 90;

  IF IntakePump THEN
    PumpRuntime := PumpRuntime + 1;
    TotalIntake := TotalIntake + IntakeFlow;
  END_IF;

END_PROGRAM


CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK Main(INTERVAL := T#100ms, PRIORITY := 0);
    PROGRAM Inst0 WITH Main : IntakeStation;
  END_RESOURCE
END_CONFIGURATION
