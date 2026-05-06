# ASHRAE Guideline 36 Coverage Matrix

Generated: 2026-05-06T23:34:34+00:00
Manual: `ashrae_guideline_36_2021_high_performance_sequences.pdf`
Doc ID: `doc_4bbd3703c4f84be4`

## Executive Summary

- Top-level §5 sections: 22
- Covered or partial sections: 22
- Not-run sections: 0
- Accepted extraction candidates across passing runs: 235
- Type totals: application_guidance: 8, commissioning_procedure: 5, commissioning_step: 10, fault_diagnostic_rule: 80, operational_sequence: 129, parameter_spec: 3
- Trust totals: L3: 147, L4: 88
- Full-book run added: 75 accepted candidates, 100% anchor match, 76.5% judge acceptance, L4=18

## Coverage Matrix

| Section | Pages | Status | Accepted | Type breakdown | Notes |
|---|---:|---|---:|---|---|
| §5.1 General | 42-58 | partial | 8 | application_guidance: 4, commissioning_procedure: 1, fault_diagnostic_rule: 1, operational_sequence: 1, parameter_spec: 1 | requested: 5.1.14; full-book added cross-cutting guidance |
| §5.2 Generic Ventilation Zones | 59-66 | covered | 3 | fault_diagnostic_rule: 1, operational_sequence: 2 | requested: 5.2 |
| §5.3 Generic Thermal Zones | 67-70 | covered | 3 | fault_diagnostic_rule: 1, operational_sequence: 2 | requested: 5.3 |
| §5.4 Zone Groups | 71-71 | covered | 3 | commissioning_procedure: 1, operational_sequence: 2 | requested: 5.4 |
| §5.5 VAV Terminal Unit—Cooling Only | 72-74 | covered | 6 | commissioning_procedure: 1, fault_diagnostic_rule: 3, operational_sequence: 1, parameter_spec: 1 | requested: 5.5 |
| §5.6 VAV Terminal Unit with Reheat | 75-78 | covered | 23 | commissioning_procedure: 1, fault_diagnostic_rule: 10, operational_sequence: 11, parameter_spec: 1 | requested: 5.6; full-book added VAV reheat sequences/faults |
| §5.7 Parallel Fan-Powered Terminal Unit − Constant-Volume Fan | 79-82 | covered | 9 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 2 | requested: 5.7 |
| §5.8 Parallel Fan-Powered Terminal Unit −Variable-Volume Fan | 83-87 | covered | 14 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 7 | requested: 5.8 |
| §5.9 Series Fan-Powered Terminal Unit − Constant-Volume Fan | 88-90 | covered | 10 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 3 | requested: 5.9 |
| §5.10 Series Fan-Powered Terminal Unit − Variable-Volume Fan | 91-94 | covered | 10 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 3 | requested: 5.10 |
| §5.11 Dual-Duct VAV Terminal Unit − Snap-Acting Control | 95-99 | covered | 6 | fault_diagnostic_rule: 3, operational_sequence: 3 | requested: 5.11 |
| §5.12 Dual-Duct VAV Terminal Unit − Mixing Control with Inlet Airflow Sensors | 100-103 | covered | 10 | commissioning_step: 1, fault_diagnostic_rule: 3, operational_sequence: 6 | requested: 5.12 |
| §5.13 Dual-Duct VAV Terminal Unit − Mixing Control with Discharge Airflow Sensor | 104-106 | covered | 7 | commissioning_step: 1, fault_diagnostic_rule: 3, operational_sequence: 3 | requested: 5.13 |
| §5.14 Dual-Duct VAV Terminal Unit − Cold-Duct Minimum Control | 107-110 | covered | 11 | commissioning_step: 1, fault_diagnostic_rule: 3, operational_sequence: 7 | requested: 5.14 |
| §5.15 Air-Handling Unit System Modes | 111-111 | covered | 1 | operational_sequence: 1 | requested: 5.15 |
| §5.16 Multiple-Zone VAV Air-Handling Unit | 111-145 | covered | 38 | application_guidance: 2, commissioning_procedure: 1, fault_diagnostic_rule: 10, operational_sequence: 25 | requested: 5.16; full-book added AHU application guidance and reset/request logic |
| §5.17 Dual-Fan Dual-Duct Heating VAV Air-Handling Unit | 146-151 | covered | 3 | fault_diagnostic_rule: 1, operational_sequence: 2 | requested: 5.17 |
| §5.18 Single-Zone VAV Air-Handling Unit | 152-170 | covered | 12 | application_guidance: 1, fault_diagnostic_rule: 1, operational_sequence: 10 | requested: 5.18; full-book added SZVAV operating sequences |
| §5.19 General Constant Speed Exhaust Fan | 171-171 | covered | 1 | operational_sequence: 1 | requested: 5.19 |
| §5.20 Chilled Water Plant | 172-234 | covered | 23 | fault_diagnostic_rule: 6, operational_sequence: 17 | requested: 5.20; full-book added plant reset/staging/fault coverage |
| §5.21 Hot Water Plant | 235-261 | covered | 21 | fault_diagnostic_rule: 5, operational_sequence: 16 | requested: 5.21; full-book added hot-water plant fault coverage |
| §5.22 Fan Coil Unit | 262-292 | covered | 9 | fault_diagnostic_rule: 5, operational_sequence: 4 | requested: 5.22; full-book added FCU fault coverage |

## Run Inventory

| Run | Mode | Sections | Raw | Accepted | Rejected | L4/L3 | Gates | Report |
|---|---|---|---:|---:|---:|---:|---|---|
| `20260506T101446Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36` | section | 5.1.14, 5.20, 5.21 | 29 | 22 | 2 | 3/19 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_vertical/20260506T101446Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36/REPORT.md` |
| `20260506T130150Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36` | section | 5.4, 5.5, 5.6, 5.15, 5.16 | 46 | 42 | 2 | 12/30 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_vertical/20260506T130150Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36/REPORT.md` |
| `20260506T152317Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36` | section | 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14 | 81 | 77 | 4 | 55/22 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_vertical/20260506T152317Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36/REPORT.md` |
| `20260506T161850Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36` | bundle | 5.2, 5.3, 5.17, 5.18, 5.19, 5.22 | 21 | 19 | 2 | 0/19 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_vertical/20260506T161850Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36/REPORT.md` |
| `20260506T181848Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook` | full-book | all sections | 130 | 75 | 55 | 18/57 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_fullbook/20260506T181848Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook/REPORT.md` |

## API Smoke Coverage

- `workspace/review_round_ashrae_g36/review_packs/api_smoke_report.json`: 5/5 passed
  - `chiller` / `application_guidance`: expected 1, visible 1, pass
  - `chiller` / `fault_diagnostic_rule`: expected 4, visible 4, pass
  - `chiller` / `operational_sequence`: expected 9, visible 9, pass
  - `chiller` / `parameter_spec`: expected 1, visible 1, pass
  - `hot_water_plant` / `operational_sequence`: expected 6, visible 6, pass
- `workspace/review_round_ashrae_g36_ahu_vav_model_review/review_packs/api_smoke_report.json`: 4/4 passed
  - `ahu` / `commissioning_step`: expected 4, visible 4, pass
  - `ahu` / `fault_diagnostic_rule`: expected 13, visible 13, pass
  - `ahu` / `operational_sequence`: expected 23, visible 23, pass
  - `ahu` / `parameter_spec`: expected 2, visible 2, pass
- `workspace/review_round_ashrae_g36_vav_terminal_model_review/review_packs/api_smoke_report.json`: 3/3 passed
  - `ahu` / `commissioning_step`: expected 7, visible 11, pass
  - `ahu` / `fault_diagnostic_rule`: expected 36, visible 49, pass
  - `ahu` / `operational_sequence`: expected 34, visible 57, pass
- `workspace/ashrae_g36_remaining_batch_pipeline/20260506T161155Z/remaining_high_value/review_packs/api_smoke_report.json`: 2/2 passed
  - `ahu` / `fault_diagnostic_rule`: expected 5, visible 57, pass
  - `ahu` / `operational_sequence`: expected 14, visible 82, pass
- `workspace/review_round_ashrae_g36_fullbook_model_review/review_packs/api_smoke_report.json`: 9/9 passed
  - `ahu` / `application_guidance`: expected 3, visible 4, pass
  - `ahu` / `fault_diagnostic_rule`: expected 14, visible 71, pass
  - `ahu` / `operational_sequence`: expected 24, visible 100, pass
  - `chiller` / `application_guidance`: expected 4, visible 5, pass
  - `chiller` / `commissioning_step`: expected 3, visible 3, pass
  - `chiller` / `fault_diagnostic_rule`: expected 3, visible 7, pass
  - `chiller` / `operational_sequence`: expected 9, visible 16, pass
  - `hot_water_plant` / `fault_diagnostic_rule`: expected 5, visible 5, pass
  - `hot_water_plant` / `operational_sequence`: expected 10, visible 16, pass

## Next Recommended Batches

1. `5.1 focused review` - Full-book extraction added useful cross-cutting guidance, but §5.1 is still partial because it has not had a dedicated review pass across all subsections.
2. `ontology split: terminal_unit, fan_coil_unit, exhaust_fan` - Current imports use hvac:ahu as the air-side bucket. Production ontology should split terminal units, FCUs, and exhaust fans.
3. `dedupe imported standard KOs` - Full-book extraction intentionally overlaps prior section/bundle runs. Before treating counts as production coverage, consolidate duplicate canonical rules across runs.

## Modeling Notes

- Only G3 PASS extraction runs are counted. Failed debugging runs are intentionally excluded.
- Section 5.1 is partial because only selected high-value cross-cutting items have been extracted/reviewed.
- Sections 5.7-5.14 and 5.22 are currently mapped to hvac:ahu until dedicated terminal/fan-coil ontology classes are added.
- Full-book counts are additive with earlier section/bundle runs and may include duplicate knowledge at different canonical granularity.

## Sample Finds by Covered Section

### §5.1 General
- `application_guidance` T&R Logic Application for VAV Static Pressure Control (L3, ASHRAE Guideline 36-2021 §5.1.14.4)
- `operational_sequence` Trim & Respond Set-Point Reset Logic (L3, ASHRAE Guideline 36-2021 §5.1.14)
- `commissioning_procedure` Request-Hours Accumulator Reset (L3, ASHRAE Guideline 36-2021 §5.1.14.2)

### §5.2 Generic Ventilation Zones
- `operational_sequence` Zone Minimum Outdoor Air and Minimum Airflow Setpoints (ASHRAE 62.1) (L3, ASHRAE Guideline 36-2021 §5.2.1.3)
- `fault_diagnostic_rule` CO2 Sensor Calibration Alarm for TAV Zones (L3, ASHRAE Guideline 36-2021 §5.2.2.3)
- `operational_sequence` Time-Averaged Ventilation (TAV) for Zones (L3, ASHRAE Guideline 36-2021 §5.2.2)

### §5.3 Generic Thermal Zones
- `operational_sequence` Zone Temperature Setpoint Adjustments and Limits (L3, ASHRAE Guideline 36-2021 §5.3.2)
- `fault_diagnostic_rule` Zone Temperature Alarms (L3, ASHRAE Guideline 36-2021 §5.3.6.1)
- `operational_sequence` Zone Control Loops and Zone State Determination (L3, ASHRAE Guideline 36-2021 §5.3.4)

### §5.4 Zone Groups
- `commissioning_procedure` Zone Group Testing/Commissioning Override Switches (L3, ASHRAE Guideline 36-2021 §5.4.5)
- `operational_sequence` Zone Group Definition and Mode Synchronization (L3, ASHRAE Guideline 36-2021 §5.4.1)
- `operational_sequence` Zone Group Occupied Mode Conditions (L3, ASHRAE Guideline 36-2021 §5.4.6.1)

### §5.5 VAV Terminal Unit—Cooling Only
- `parameter_spec` Active Airflow Setpoint Endpoints by Zone Group Mode (L3, ASHRAE Guideline 36-2021 §5.5.4)
- `commissioning_procedure` Testing/Commissioning Overrides for Cooling-Only VAV (L3, ASHRAE Guideline 36-2021 §5.5.7)
- `fault_diagnostic_rule` Low Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.5.6.1)

### §5.6 VAV Terminal Unit with Reheat
- `fault_diagnostic_rule` Low Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.6.6.1)
- `fault_diagnostic_rule` Airflow Sensor Calibration Alarm (L4, ASHRAE Guideline 36-2021 §5.6.6.3)
- `fault_diagnostic_rule` Leaking Damper Alarm (L4, ASHRAE Guideline 36-2021 §5.6.6.4)

### §5.7 Parallel Fan-Powered Terminal Unit − Constant-Volume Fan
- `fault_diagnostic_rule` Low Primary Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.7.6.1)
- `fault_diagnostic_rule` Airflow Sensor Calibration Alarm (L4, ASHRAE Guideline 36-2021 §5.7.6.4)
- `fault_diagnostic_rule` Leaking Damper Alarm (L4, ASHRAE Guideline 36-2021 §5.7.6.5)

### §5.8 Parallel Fan-Powered Terminal Unit −Variable-Volume Fan
- `fault_diagnostic_rule` Low Primary Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.8.6.1)
- `fault_diagnostic_rule` Airflow Sensor Calibration Alarm (L4, ASHRAE Guideline 36-2021 §5.8.6.4)
- `operational_sequence` Static Pressure Reset Requests (L4, ASHRAE Guideline 36-2021 §5.8.8.2)

### §5.9 Series Fan-Powered Terminal Unit − Constant-Volume Fan
- `fault_diagnostic_rule` Low Primary Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.9.6.1)
- `fault_diagnostic_rule` Airflow Sensor Calibration Alarm (L4, ASHRAE Guideline 36-2021 §5.9.6.4)
- `fault_diagnostic_rule` Leaking Damper Alarm (L4, ASHRAE Guideline 36-2021 §5.9.6.5)

### §5.10 Series Fan-Powered Terminal Unit − Variable-Volume Fan
- `fault_diagnostic_rule` Low Primary Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.10.6.1)
- `fault_diagnostic_rule` Airflow Sensor Calibration Alarm (L4, ASHRAE Guideline 36-2021 §5.10.6.4)
- `fault_diagnostic_rule` Leaking Damper Alarm (L4, ASHRAE Guideline 36-2021 §5.10.6.5)

### §5.11 Dual-Duct VAV Terminal Unit − Snap-Acting Control
- `fault_diagnostic_rule` Low Airflow Alarms (L4, ASHRAE Guideline 36-2021 §5.11.6.1)
- `operational_sequence` Cooling SAT Reset Requests (L4, ASHRAE Guideline 36-2021 §5.11.8.1)
- `operational_sequence` Cold-Duct Static Pressure Reset Requests (L4, ASHRAE Guideline 36-2021 §5.11.8.2)

### §5.12 Dual-Duct VAV Terminal Unit − Mixing Control with Inlet Airflow Sensors
- `fault_diagnostic_rule` Dual-Duct VAV Terminal Unit Low Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.12.6.1)
- `operational_sequence` Dual-Duct VAV Terminal Unit System Requests - Cooling SAT Reset (L4, ASHRAE Guideline 36-2021 §5.12.8.1)
- `operational_sequence` Dual-Duct VAV Terminal Unit System Requests - Cold-Duct Static Pressure Reset (L4, ASHRAE Guideline 36-2021 §5.12.8.2)

### §5.13 Dual-Duct VAV Terminal Unit − Mixing Control with Discharge Airflow Sensor
- `fault_diagnostic_rule` Low Airflow Alarms (L4, ASHRAE Guideline 36-2021 §5.13.6.1)
- `operational_sequence` Backflow Prevention Overrides (L4, ASHRAE Guideline 36-2021 §5.13.5.2)
- `fault_diagnostic_rule` Airflow Sensor Calibration Alarm (L4, ASHRAE Guideline 36-2021 §5.13.6.2)

### §5.14 Dual-Duct VAV Terminal Unit − Cold-Duct Minimum Control
- `fault_diagnostic_rule` Dual-Duct VAV Low Airflow Alarm (L4, ASHRAE Guideline 36-2021 §5.14.6.1)
- `operational_sequence` Dual-Duct VAV Cooling SAT Reset Requests (L4, ASHRAE Guideline 36-2021 §5.14.8.1)
- `operational_sequence` Dual-Duct VAV Cold-Duct Static Pressure Reset Requests (L4, ASHRAE Guideline 36-2021 §5.14.8.2)

### §5.15 Air-Handling Unit System Modes
- `operational_sequence` AHU System Mode Hierarchy (L3, ASHRAE Guideline 36-2021 §5.15.1)

### §5.16 Multiple-Zone VAV Air-Handling Unit
- `operational_sequence` Supply Fan Start/Stop (L3, ASHRAE Guideline 36-2021 §5.16.1.1)
- `operational_sequence` Static Pressure Setpoint Reset using Trim & Respond (L3, ASHRAE Guideline 36-2021 §5.16.1.2)
- `operational_sequence` Supply Air Temperature Control Loop Enable/Disable (L3, ASHRAE Guideline 36-2021 §5.16.2.1)

### §5.17 Dual-Fan Dual-Duct Heating VAV Air-Handling Unit
- `operational_sequence` Dual-Fan Dual-Duct Heating VAV AHU Static Pressure Setpoint Reset (L3, ASHRAE Guideline 36-2021 §5.17.1.2)
- `operational_sequence` Dual-Fan Dual-Duct Heating VAV AHU Supply Air Temperature Setpoint Reset (L3, ASHRAE Guideline 36-2021 §5.17.2.2)
- `fault_diagnostic_rule` Dual-Fan Dual-Duct Heating VAV AHU AFDD Fault Conditions (L3, ASHRAE Guideline 36-2021 §5.17.4.5)

### §5.18 Single-Zone VAV Air-Handling Unit
- `operational_sequence` SZVAV AHU Supply Fan Speed and SAT Setpoint Reset (L3, ASHRAE Guideline 36-2021 §5.18.4)
- `operational_sequence` SZVAV AHU Supply Air Temperature Control Loop Mapping (L3, ASHRAE Guideline 36-2021 §5.18.5.2)
- `operational_sequence` SZVAV AHU Minimum Outdoor Air Control without AFMS (L3, ASHRAE Guideline 36-2021 §5.18.6.2)

### §5.19 General Constant Speed Exhaust Fan
- `operational_sequence` General Constant Speed Exhaust Fan Control (L3, ASHRAE Guideline 36-2021 §5.19.1.1)

### §5.20 Chilled Water Plant
- `operational_sequence` Plant Enable Logic (L3, ASHRAE Guideline 36-2021 §5.20.2.2)
- `operational_sequence` Plant Disable Logic (L3, ASHRAE Guideline 36-2021 §5.20.2.3)
- `operational_sequence` Waterside Economizer Enable Logic (L3, ASHRAE Guideline 36-2021 §5.20.3.1)

### §5.21 Hot Water Plant
- `operational_sequence` Plant Enable/Disable (L3, ASHRAE Guideline 36-2021 §5.21.2.2)
- `operational_sequence` Plant Disable Logic (L3, ASHRAE Guideline 36-2021 §5.21.2.3)
- `operational_sequence` Primary Only Condensing Boiler Staging Down (L3, ASHRAE Guideline 36-2021 §5.21.3.9.g)

### §5.22 Fan Coil Unit
- `operational_sequence` Fan Coil Unit Supply Fan Speed and SAT Control (L3, ASHRAE Guideline 36-2021 §5.22.4)
- `fault_diagnostic_rule` Fan Coil Unit AFDD Fault Conditions (L3, ASHRAE Guideline 36-2021 §5.22.6.6)
- `operational_sequence` Fan Coil Unit Chilled-Water Reset Requests (L3, ASHRAE Guideline 36-2021 §5.22.8.1)
