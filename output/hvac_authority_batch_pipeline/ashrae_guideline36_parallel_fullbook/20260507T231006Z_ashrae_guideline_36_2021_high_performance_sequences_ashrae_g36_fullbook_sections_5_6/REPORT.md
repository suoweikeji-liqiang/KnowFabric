# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T231006Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_6
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.6
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31182 |
| Extract calls | 1 |
| Extract input tokens | 32341 |
| Extract output tokens | 6209 |
| Judge calls | 1 |
| Judge total tokens | 4888 |
| Total cost | ¥0.1526 / ¥10.00 |
| Extract wallclock | 146.14s |
| Total wallclock | 182.55s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 20 |
| Anchor passed | 20 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 19 |
| Judge accepted | 18 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | fault_diagnostic_rule: 9, operational_sequence: 8, commissioning_step: 1 |
| L4 / L3 | 13 / 5 |

## Samples

### Accepted
- p74, §5.6.6.1, fault_diagnostic_rule: Low Airflow Alarm – Level 3
- p74, §5.6.6.3, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.6.6.4, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.6.5.5, operational_sequence: VAV Damper Modulation to Airflow Setpoint
- p75, §5.6.8.1, operational_sequence: Cooling SAT Reset Requests
- p76, §5.6.5.1, operational_sequence: Cooling State Airflow Setpoint Mapping
- p76, §5.6.5.2, operational_sequence: Deadband State Airflow Setpoint
- p77, §5.6.6.1, fault_diagnostic_rule: Low Airflow Alarm – Level 4
- p77, §5.6.6.2, fault_diagnostic_rule: Low-DAT Alarm Suppression for Importance-Multiplier 0
- p77, §5.6.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm – Level 3
- p77, §5.6.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm – Level 4
- p77, §5.6.5.3, operational_sequence: Heating Coil Modulation and PWM Interlock
- p77, §5.6.5.3, operational_sequence: Heating State Sequence – Airflow Reset (51-100%)
- p77, §5.6.5.4, operational_sequence: Occupied Mode Minimum DAT Control
- p78, §5.6.7, commissioning_step: Testing/Commissioning Overrides

### Anchor Rejected
- §5.6.4: VAV Reheat Zone Endpoints by Zone Group Mode | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.6.5.3: Heating State Sequence – Discharge Temperature Reset (0-50%) | unsupported: Summary is unsupported; evidence quote is incomplete and does not describe 0-50% reset.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (94.7%)
- G3 focused section run produced at least one verified candidate: PASS (18)
- G4 extract wallclock <= configured limit: PASS (146.14s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
