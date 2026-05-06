# ASHRAE Guideline 36 Coverage Matrix

Generated: 2026-05-06T15:49:29.564612+00:00
Manual: `ashrae_guideline_36_2021_high_performance_sequences.pdf`
Doc ID: `doc_4bbd3703c4f84be4`

## Executive Summary

- Top-level §5 sections: 22
- Covered or partial sections: 16
- Not-run sections: 6
- Accepted extraction candidates across runs: 141
- Type totals: application_guidance: 1, commissioning_procedure: 5, commissioning_step: 7, fault_diagnostic_rule: 53, operational_sequence: 72, parameter_spec: 3
- Trust totals: L3: 71, L4: 70

## Coverage Matrix

| Section | Pages | Status | Accepted | Type breakdown | Notes |
|---|---:|---|---:|---|---|
| §5.1 General | 42-58 | partial | 5 | application_guidance: 1, commissioning_procedure: 1, fault_diagnostic_rule: 1, operational_sequence: 1, parameter_spec: 1 | requested: 5.1.14 |
| §5.2 Generic Ventilation Zones | 59-66 | not_run | 0 | - | requested: - |
| §5.3 Generic Thermal Zones | 67-70 | not_run | 0 | - | requested: - |
| §5.4 Zone Groups | 71-71 | covered | 3 | commissioning_procedure: 1, operational_sequence: 2 | requested: 5.4 |
| §5.5 VAV Terminal Unit—Cooling Only | 72-74 | covered | 6 | commissioning_procedure: 1, fault_diagnostic_rule: 3, operational_sequence: 1, parameter_spec: 1 | requested: 5.5 |
| §5.6 VAV Terminal Unit with Reheat | 75-78 | covered | 11 | commissioning_procedure: 1, fault_diagnostic_rule: 5, operational_sequence: 4, parameter_spec: 1 | requested: 5.6 |
| §5.7 Parallel Fan-Powered Terminal Unit − Constant-Volume Fan | 79-82 | covered | 9 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 2 | requested: 5.7 |
| §5.8 Parallel Fan-Powered Terminal Unit −Variable-Volume Fan | 83-87 | covered | 14 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 7 | requested: 5.8 |
| §5.9 Series Fan-Powered Terminal Unit − Constant-Volume Fan | 88-90 | covered | 10 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 3 | requested: 5.9 |
| §5.10 Series Fan-Powered Terminal Unit − Variable-Volume Fan | 91-94 | covered | 10 | commissioning_step: 1, fault_diagnostic_rule: 6, operational_sequence: 3 | requested: 5.10 |
| §5.11 Dual-Duct VAV Terminal Unit − Snap-Acting Control | 95-99 | covered | 6 | fault_diagnostic_rule: 3, operational_sequence: 3 | requested: 5.11 |
| §5.12 Dual-Duct VAV Terminal Unit − Mixing Control with Inlet Airflow Sensors | 100-103 | covered | 10 | commissioning_step: 1, fault_diagnostic_rule: 3, operational_sequence: 6 | requested: 5.12 |
| §5.13 Dual-Duct VAV Terminal Unit − Mixing Control with Discharge Airflow Sensor | 104-106 | covered | 7 | commissioning_step: 1, fault_diagnostic_rule: 3, operational_sequence: 3 | requested: 5.13 |
| §5.14 Dual-Duct VAV Terminal Unit − Cold-Duct Minimum Control | 107-110 | covered | 11 | commissioning_step: 1, fault_diagnostic_rule: 3, operational_sequence: 7 | requested: 5.14 |
| §5.15 Air-Handling Unit System Modes | 111-111 | covered | 1 | operational_sequence: 1 | requested: 5.15 |
| §5.16 Multiple-Zone VAV Air-Handling Unit | 111-145 | covered | 21 | commissioning_procedure: 1, fault_diagnostic_rule: 5, operational_sequence: 15 | requested: 5.16 |
| §5.17 Dual-Fan Dual-Duct Heating VAV Air-Handling Unit | 146-151 | not_run | 0 | - | requested: - |
| §5.18 Single-Zone VAV Air-Handling Unit | 152-170 | not_run | 0 | - | requested: - |
| §5.19 General Constant Speed Exhaust Fan | 171-171 | not_run | 0 | - | requested: - |
| §5.20 Chilled Water Plant | 172-234 | covered | 11 | fault_diagnostic_rule: 3, operational_sequence: 8 | requested: 5.20 |
| §5.21 Hot Water Plant | 235-261 | covered | 6 | operational_sequence: 6 | requested: 5.21 |
| §5.22 Fan Coil Unit | 262-292 | not_run | 0 | - | requested: - |

## Run Inventory

| Run | Sections | Raw | Accepted | Rejected | L4/L3 | Gates | Report |
|---|---|---:|---:|---:|---:|---|---|
| `20260506T101446Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36` | 5.1.14, 5.20, 5.21 | 29 | 22 | 2 | 3/19 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_vertical/20260506T101446Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36/REPORT.md` |
| `20260506T130150Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36` | 5.4, 5.5, 5.6, 5.15, 5.16 | 46 | 42 | 2 | 12/30 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_vertical/20260506T130150Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36/REPORT.md` |
| `20260506T152317Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36` | 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14 | 81 | 77 | 4 | 55/22 | G1:PASS, G2:PASS, G3:PASS, G4:PASS | `output/ashrae_guideline36_vertical/20260506T152317Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36/REPORT.md` |

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

## Next Recommended Batches

1. `5.2, 5.3` - Generic ventilation and thermal zone logic. These clauses define zone minimum airflow, temperature setpoint hierarchy, demand-limit adjustments, local overrides, control loops, and zone alarms. They are reused by many terminal/AHU sections.
2. `5.17, 5.18, 5.19` - Remaining air-side equipment sections: dual-fan dual-duct AHU, single-zone VAV AHU, and constant-speed exhaust fan. High operational value and likely API-demo friendly.
3. `5.22` - Fan coil unit section. Useful independent terminal-equipment class; should probably not be forced into AHU long-term.
4. `5.1 except 5.1.14` - General control philosophy, alarm handling, VFD speed points, equipment staging/rotation, economizer limits, alarm suppression. Important cross-cutting knowledge, but needs careful type mapping to avoid overly generic KOs.

## Modeling Notes

- Section 5.1 is marked partial because only 5.1.14 Trim & Respond has been extracted so far.
- The first G36 plant run produced one commissioning_procedure item while the later import path uses commissioning_step; API smoke shows 21 visible KOs from that run rather than the 22 model-accepted extraction total.
- Sections 5.7-5.14 are currently mapped to hvac:ahu as a pragmatic import target; ONTOLOGY_GAPS.md records the future terminal-unit ontology need.

## Sample Finds by Covered Section

### §5.1 General
- `application_guidance` T&R Logic Application for VAV Static Pressure Control (L3, ASHRAE Guideline 36-2021 §5.1.14.4)
- `operational_sequence` Trim & Respond Set-Point Reset Logic (L3, ASHRAE Guideline 36-2021 §5.1.14)
- `commissioning_procedure` Request-Hours Accumulator Reset (L3, ASHRAE Guideline 36-2021 §5.1.14.2)

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

### §5.20 Chilled Water Plant
- `operational_sequence` Plant Enable Logic (L3, ASHRAE Guideline 36-2021 §5.20.2.2)
- `operational_sequence` Plant Disable Logic (L3, ASHRAE Guideline 36-2021 §5.20.2.3)
- `operational_sequence` Waterside Economizer Enable Logic (L3, ASHRAE Guideline 36-2021 §5.20.3.1)

### §5.21 Hot Water Plant
- `operational_sequence` Plant Enable/Disable (L3, ASHRAE Guideline 36-2021 §5.21.2.2)
- `operational_sequence` Plant Disable Logic (L3, ASHRAE Guideline 36-2021 §5.21.2.3)
- `operational_sequence` Primary Only Condensing Boiler Staging Down (L3, ASHRAE Guideline 36-2021 §5.21.3.9.g)
