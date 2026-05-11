# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T163436Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_9
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
| Extract output tokens | 13047 |
| Judge calls | 1 |
| Judge total tokens | 2837 |
| Total cost | ¥0.1862 / ¥10.00 |
| Extract wallclock | 375.98s |
| Total wallclock | 418.42s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 14 |
| Anchor passed | 14 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 7 |
| Judge input | 7 |
| Judge accepted | 7 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 4, operational_sequence: 3 |
| L4 / L3 | 6 / 1 |

## Samples

### Accepted
- p74, §5.9.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Fault
- p74, §5.9.6.5, fault_diagnostic_rule: Leaking Damper Fault
- p82, §5.9.6.3, fault_diagnostic_rule: Fan Status Alarm
- p86, §5.9.6.6, fault_diagnostic_rule: Leaking Valve Fault
- p88, §5.9.4, operational_sequence: Active Primary Airflow Endpoints by Zone Group Mode
- p89, §5.9.5.4, operational_sequence: VAV Damper Control
- p89, §5.9.5.5, operational_sequence: Series Fan Control

### Anchor Rejected
- §5.9.5.1: Primary Airflow Setpoint in Cooling State | weak evidence_quote: section heading without supporting rule
- §5.9.5.2: Primary Airflow Setpoint in Deadband State | weak evidence_quote: section heading without supporting rule
- §5.9.5.3: Primary Airflow and Discharge Temperature Control in Heating State | weak evidence_quote: section heading without supporting rule
- §5.9.6.1: Low Primary Airflow Alarms | weak evidence_quote: section heading without supporting rule
- §5.9.6.2: Low Discharge Air Temperature Alarms | weak evidence_quote: section heading without supporting rule
- §5.9.7: Testing/Commissioning Overrides for Series Fan Terminal Unit | weak evidence_quote: section heading without supporting rule
- §5.9.8.1: Cooling SAT Reset Requests from Series Fan Terminal Units | weak evidence_quote: section heading without supporting rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (7)
- G4 extract wallclock <= configured limit: PASS (375.98s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
