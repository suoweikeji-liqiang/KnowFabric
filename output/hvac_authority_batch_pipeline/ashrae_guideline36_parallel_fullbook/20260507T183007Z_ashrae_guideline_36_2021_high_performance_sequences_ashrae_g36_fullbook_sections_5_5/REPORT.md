# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T183007Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_5
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.5
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30098 |
| Extract calls | 1 |
| Extract input tokens | 31130 |
| Extract output tokens | 10721 |
| Judge calls | 1 |
| Judge total tokens | 5795 |
| Total cost | ¥0.1826 / ¥10.00 |
| Extract wallclock | 246.47s |
| Total wallclock | 318.82s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 20 |
| Anchor passed | 20 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 0 |
| Judge input | 20 |
| Judge accepted | 20 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 5, parameter_spec: 3, commissioning_step: 1, fault_diagnostic_rule: 5, operational_sequence: 6 |
| L4 / L3 | 10 / 10 |

## Samples

### Accepted
- p73, §5.5.3, application_guidance: CO2 DCV Overcooling Risk
- p73, §5.5.3, application_guidance: DCV Logic Not Provided for Cooling-Only Boxes
- p73, §5.5.3, application_guidance: Heating Capability of Cooling-Only Terminal Units
- p73, §5.5.3, application_guidance: Reheat Box Recommended for High Minimum Ventilation or DCV
- p73, §5.5.4, parameter_spec: Cooling Maximum Endpoint per Zone Group Mode
- p73, §5.5.4, parameter_spec: Heating Maximum Endpoint per Zone Group Mode
- p73, §5.5.4, parameter_spec: Minimum Endpoint per Zone Group Mode
- p74, §5.5.6.3, application_guidance: Airflow Alarm Threshold Determination
- p74, §5.5.7, commissioning_step: Testing/Commissioning Overrides
- p74, §5.5.6.1, fault_diagnostic_rule: Low Airflow Alarm Level 3
- p74, §5.5.6.1, fault_diagnostic_rule: Low Airflow Alarm Level 4
- p74, §5.5.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Importance Multiplier Zero
- p74, §5.5.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.5.6.3, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.5.5.1, operational_sequence: Cooling State Airflow Setpoint Limit when Supply Air Warmer than Room

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (20)
- G4 extract wallclock <= configured limit: PASS (246.47s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
