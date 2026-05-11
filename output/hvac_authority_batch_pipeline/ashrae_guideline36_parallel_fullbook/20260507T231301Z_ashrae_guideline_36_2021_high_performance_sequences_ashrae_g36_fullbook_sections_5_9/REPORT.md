# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T231301Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_9
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.9
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30592 |
| Extract calls | 1 |
| Extract input tokens | 31726 |
| Extract output tokens | 4850 |
| Judge calls | 1 |
| Judge total tokens | 3582 |
| Total cost | ¥0.1376 / ¥10.00 |
| Extract wallclock | 130.64s |
| Total wallclock | 155.54s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 14 |
| Anchor passed | 14 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 13 |
| Judge accepted | 13 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 6, operational_sequence: 6, commissioning_step: 1 |
| L4 / L3 | 10 / 3 |

## Samples

### Accepted
- p74, §5.9.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.9.6.5, fault_diagnostic_rule: Leaking Damper Alarm
- p75, §5.9.8.1, operational_sequence: Cooling SAT Reset Requests
- p77, §5.9.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm
- p81, §5.9.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm
- p82, §5.9.6.3, fault_diagnostic_rule: Fan Alarm
- p85, §5.9.5.2, operational_sequence: Deadband State Primary Airflow Setpoint
- p86, §5.9.6.6, fault_diagnostic_rule: Leaking Valve Alarm
- p88, §5.9.5.1, operational_sequence: Cooling State Primary Airflow Setpoint
- p89, §5.9.5.3, operational_sequence: Heating State Primary Airflow and Discharge Temperature Control
- p89, §5.9.5.4, operational_sequence: VAV Damper Control
- p89, §5.9.5.5, operational_sequence: Fan Control
- p90, §5.9.7, commissioning_step: Testing/Commissioning Overrides

### Anchor Rejected
- §5.9.4: Active Endpoints Based on Zone Group Mode | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (13)
- G4 extract wallclock <= configured limit: PASS (130.64s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
