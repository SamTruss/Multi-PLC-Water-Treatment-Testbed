PROGRAM TreatmentStation
  VAR
    TreatmentTankLevel AT %MW10 : INT;
    ChlorineLevel AT %MW11 : INT;
    PhLevel AT %MW12 : INT;

    ChlorineDoser AT %QX0.0 : BOOL;
    AcidDoser AT %QX0.1 : BOOL;
    BaseDoser AT %QX0.2 : BOOL;
    Mixer AT %QX0.3 : BOOL;
    ContaminationAlarm AT %QX0.4 : BOOL;
    PhAlarm AT %QX0.5 : BOOL;

    ChlorineSetpoint AT %MW0 : INT;
    PhSetpointLow AT %MW1 : INT;
    PhSetpointHigh AT %MW2 : INT;
    DosingCycles AT %MW3 : INT;
  END_VAR

  ChlorineDoser := ChlorineLevel < ChlorineSetpoint;
  AcidDoser := PhLevel > PhSetpointHigh;
  BaseDoser := PhLevel < PhSetpointLow;
  Mixer := ChlorineDoser OR AcidDoser OR BaseDoser;
  ContaminationAlarm := ChlorineLevel < 10;
  PhAlarm := (PhLevel < 60) OR (PhLevel > 80);

  IF Mixer THEN
    DosingCycles := DosingCycles + 1;
  END_IF;

END_PROGRAM


CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK Main(INTERVAL := T#100ms, PRIORITY := 0);
    PROGRAM Inst0 WITH Main : TreatmentStation;
  END_RESOURCE
END_CONFIGURATION
