PROGRAM DistributionStation
  VAR
    DistributionPressure AT %MW10 : INT;
    OutflowRate AT %MW11 : INT;
    ReservoirLevel AT %MW12 : INT;
    BoosterPump1 AT %QX0.0 : BOOL;
    BoosterPump2 AT %QX0.1 : BOOL;
    PressureReliefValve AT %QX0.2 : BOOL;
    SupplyValve AT %QX0.3 : BOOL;
    OverpressureAlarm AT %QX0.4 : BOOL;
    LowPressureAlarm AT %QX0.5 : BOOL;
    PressureSetpoint AT %MW0 : INT;
    PressureMax AT %MW1 : INT;
    DailyOutflow AT %MW2 : INT;
    PumpStaging AT %MW3 : INT;
  END_VAR

  IF DistributionPressure < PressureSetpoint THEN
    PumpStaging := 1;
  END_IF;
  IF DistributionPressure > (PressureSetpoint + 10) THEN
    PumpStaging := 0;
  END_IF;

  BoosterPump1 := (PumpStaging = 1) AND (ReservoirLevel > 20);
  BoosterPump2 := (PumpStaging = 1) AND (DistributionPressure < (PressureSetpoint - 10));
  PressureReliefValve := DistributionPressure > PressureMax;
  SupplyValve := (DistributionPressure >= 30) AND (DistributionPressure <= PressureMax);
  OverpressureAlarm := DistributionPressure > PressureMax;
  LowPressureAlarm := DistributionPressure < 20;

  IF SupplyValve THEN
    DailyOutflow := DailyOutflow + OutflowRate;
  END_IF;

END_PROGRAM


CONFIGURATION Config0
  RESOURCE Res0 ON PLC
    TASK Main(INTERVAL := T#100ms, PRIORITY := 0);
    PROGRAM Inst0 WITH Main : DistributionStation;
  END_RESOURCE
END_CONFIGURATION
