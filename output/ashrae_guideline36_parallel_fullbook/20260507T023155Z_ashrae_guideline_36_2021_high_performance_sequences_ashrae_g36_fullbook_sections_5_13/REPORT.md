# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T023155Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_13
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.13
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30364 |
| Extract calls | 1 |
| Extract input tokens | 31306 |
| Extract output tokens | 3435 |
| Judge calls | 1 |
| Judge total tokens | 3406 |
| Total cost | ¥0.0546 / ¥10.00 |
| Extract wallclock | 48.15s |
| Total wallclock | 93.50s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 12 |
| Anchor passed | 12 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 4 |
| Judge input | 8 |
| Judge accepted | 8 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 5, operational_sequence: 2, parameter_spec: 1 |
| L4 / L3 | 6 / 2 |

## Samples

### Accepted
- p74, §5.13.6.1, fault_diagnostic_rule: Dual-Duct VAV Low Airflow Alarm - Level 3
- p74, §5.13.6.1, fault_diagnostic_rule: Dual-Duct VAV Low Airflow Alarm - Level 4
- p77, §5.13.6.1, fault_diagnostic_rule: Dual-Duct VAV Low Airflow Alarm Suppression for Importance-Multiplier 0
- p99, §5.13.6.2, fault_diagnostic_rule: Dual-Duct VAV Airflow Sensor Calibration Alarm
- p99, §5.13.6.3, fault_diagnostic_rule: Dual-Duct VAV Leaking Damper Alarm
- p101, §5.13.5.1, operational_sequence: Dual-Duct VAV Temperature Control - Deadband Mode
- p104, §5.13.4, parameter_spec: Dual-Duct VAV Endpoints as Function of Zone Group Mode
- p106, §5.13.5.1, operational_sequence: Dual-Duct VAV Maximum Hot Duct Airflow Limiting

### Anchor Rejected
- §5.13.5.1: Dual-Duct VAV Temperature Control - Cooling Mode | weak evidence_quote: section heading without supporting rule
- §5.13.5.1: Dual-Duct VAV Temperature Control - Heating Mode | weak evidence_quote: section heading without supporting rule
- §5.13.5.2: Dual-Duct VAV Override to Avoid Backflow | weak evidence_quote: section heading without supporting rule
- §5.13.7: Dual-Duct VAV Testing/Commissioning Overrides | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (8)
- G4 extract wallclock <= configured limit: PASS (48.15s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
