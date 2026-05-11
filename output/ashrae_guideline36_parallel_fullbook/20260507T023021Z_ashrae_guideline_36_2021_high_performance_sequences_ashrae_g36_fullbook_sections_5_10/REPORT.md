# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T023021Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_10
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.10
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31091 |
| Extract calls | 1 |
| Extract input tokens | 32188 |
| Extract output tokens | 9509 |
| Judge calls | 1 |
| Judge total tokens | 7635 |
| Total cost | ¥0.0848 / ¥10.00 |
| Extract wallclock | 126.73s |
| Total wallclock | 219.89s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 40 |
| Anchor passed | 40 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 14 |
| Judge input | 26 |
| Judge accepted | 25 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | application_guidance: 5, fault_diagnostic_rule: 7, operational_sequence: 13 |
| L4 / L3 | 13 / 12 |

## Samples

### Accepted
- p74, §5.10.6.5, application_guidance: Constant Value Thresholds for Airflow Alarms
- p74, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm - Level 3
- p75, §5.10.8.1, operational_sequence: Cooling SAT Reset Requests - 0 Requests (Cooling Loop < 95%)
- p75, §5.10.8.1, operational_sequence: Cooling SAT Reset Requests - 1 Request (Cooling Loop > 95%)
- p75, §5.10.8.1, operational_sequence: Cooling SAT Reset Requests - 2 Requests
- p75, §5.10.8.1, operational_sequence: Cooling SAT Reset Requests - 3 Requests
- p75, §5.10.8.2, operational_sequence: Static Pressure Reset Requests - 3 Requests
- p77, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm - Level 4
- p77, §5.10.6.2, fault_diagnostic_rule: Low-DAT Alarm Suppression for Importance-Multiplier 0
- p77, §5.10.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm - Level 3
- p77, §5.10.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm - Level 4
- p78, §5.10.7, application_guidance: Heating Hot-Water Plant Start/Stop Logic
- p81, §5.10.5.3, application_guidance: Standard 90.1 Overhead Supply Air Temperature Limit
- p81, §5.10.5.2, operational_sequence: Deadband Zone State - Primary Airflow Setpoint
- p89, §5.10.5.3, operational_sequence: Heating Zone State - Heating Coil Modulation

### Anchor Rejected
- §5.10.5.1: Cooling Zone State - Heating Coil OFF | weak evidence_quote: too short to support structured summary
- §5.10.5.2: Deadband Zone State - Heating Coil OFF | weak evidence_quote: too short to support structured summary
- §5.10.5.3: Heating Zone State - First Stage (0-50% Heating Loop) | weak evidence_quote: section heading without supporting rule
- §5.10.6.1: Low Primary Airflow Alarm Suppression for Importance-Multiplier 0 | weak evidence_quote: section heading without supporting rule
- §5.10.6.3: Fan Alarm - Commanded ON, Status OFF (Level 2) | weak evidence_quote: too short to support structured summary
- §5.10.6.3: Fan Alarm - Commanded OFF, Status ON (Level 4) | weak evidence_quote: too short to support structured summary
- §5.10.6.4: Airflow Sensor Calibration Alarm | weak evidence_quote: section heading without supporting rule
- §5.10.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Zero | weak evidence_quote: commissioning evidence lacks procedure/check action
- §5.10.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Vcool-max | weak evidence_quote: commissioning evidence lacks procedure/check action
- §5.10.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Vmin | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
- §5.10.5: Heating Logic Presumption - Plenum Temperature | unsupported: Evidence quote incomplete, does not support summary

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (96.2%)
- G3 focused section run produced at least one verified candidate: PASS (25)
- G4 extract wallclock <= configured limit: PASS (126.73s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
