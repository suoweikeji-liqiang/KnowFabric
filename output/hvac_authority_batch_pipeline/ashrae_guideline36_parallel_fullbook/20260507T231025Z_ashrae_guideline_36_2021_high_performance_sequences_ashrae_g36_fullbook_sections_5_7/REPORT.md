# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T231025Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_7
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.7
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30696 |
| Extract calls | 1 |
| Extract input tokens | 31866 |
| Extract output tokens | 5543 |
| Judge calls | 1 |
| Judge total tokens | 4720 |
| Total cost | ¥0.1473 / ¥10.00 |
| Extract wallclock | 130.34s |
| Total wallclock | 165.03s |

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
| Final by type | fault_diagnostic_rule: 10, parameter_spec: 1, operational_sequence: 6, commissioning_step: 1 |
| L4 / L3 | 11 / 7 |

## Samples

### Accepted
- p74, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (Level 3)
- p74, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (Level 4)
- p74, §5.7.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.7.6.5, fault_diagnostic_rule: Leaking Damper Alarm
- p77, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Suppression
- p77, §5.7.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm (Level 3)
- p77, §5.7.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm (Level 4)
- p77, §5.7.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm Suppression
- p78, §5.7.6.6, fault_diagnostic_rule: Leaking Valve Alarm
- p79, §5.7.4, parameter_spec: Endpoints as a Function of Zone Group Mode
- p81, §5.7.5.1, operational_sequence: Cooling Mode Primary Airflow Setpoint Mapping
- p81, §5.7.5.2, operational_sequence: Deadband Mode Primary Airflow Setpoint
- p81, §5.7.5.4, operational_sequence: VAV Damper Modulation
- p81, §5.7.5.5, operational_sequence: Fan Control During Heating
- p81, §5.7.5.5, operational_sequence: Fan Control for Ventilation (ASHRAE 62.1)

### Anchor Rejected
- §5.7.5.3: Heating Mode Primary Airflow and Discharge Temperature Reset | weak evidence_quote: section heading without supporting rule

### Judge Rejected
- §5.7.6.3: Fan Alarm (Commanded Off, Status On) | unsupported: Evidence quote is incomplete; only mentions the alarm definition but does not include the specific rule for 'commanded off, status on' Level 4.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (94.7%)
- G3 focused section run produced at least one verified candidate: PASS (18)
- G4 extract wallclock <= configured limit: PASS (130.34s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
