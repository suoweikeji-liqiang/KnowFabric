# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T165347Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_12
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.12
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30856 |
| Extract calls | 1 |
| Extract input tokens | 31964 |
| Extract output tokens | 20090 |
| Judge calls | 1 |
| Judge total tokens | 8336 |
| Total cost | ¥0.2502 / ¥10.00 |
| Extract wallclock | 577.29s |
| Total wallclock | 660.29s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 32 |
| Anchor passed | 32 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 0 |
| Judge input | 32 |
| Judge accepted | 32 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 2, fault_diagnostic_rule: 5, operational_sequence: 23, parameter_spec: 1, commissioning_step: 1 |
| L4 / L3 | 27 / 5 |

## Samples

### Accepted
- p74, §5.12.6.3, application_guidance: Constant Value Thresholds for Airflow Sensor Alarms
- p74, §5.12.6.1, fault_diagnostic_rule: Low Airflow Alarm (<70% of setpoint)
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request (0 requests)
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request (1 request, high Cooling Loop)
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request (2 requests, moderate temperature excess)
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request (3 requests, large temperature excess)
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request (0 requests)
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request (1 request, high damper)
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request (2 requests, moderate low airflow)
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request (3 requests, low airflow)
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request (0 requests)
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request (1 request, high damper)
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request (2 requests, moderate low airflow)
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request (3 requests, low airflow)
- p77, §5.12.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Importance-Multiplier 0

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (32)
- G4 extract wallclock <= configured limit: PASS (577.29s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
