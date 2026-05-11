# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T233935Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_18
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.18
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 39665 |
| Extract calls | 1 |
| Extract input tokens | 41464 |
| Extract output tokens | 14075 |
| Judge calls | 1 |
| Judge total tokens | 9304 |
| Total cost | ¥0.2437 / ¥10.00 |
| Extract wallclock | 377.63s |
| Total wallclock | 443.31s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 43 |
| Anchor passed | 43 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 9 |
| Judge input | 34 |
| Judge accepted | 34 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 8, operational_sequence: 21, parameter_spec: 4, commissioning_step: 1 |
| L4 / L3 | 15 / 19 |

## Samples

### Accepted
- p134, §5.18.12.2, fault_diagnostic_rule: Fan Status Alarm
- p141, §5.18.13.6, fault_diagnostic_rule: AFDD Fault Condition FC#2: MAT too low
- p142, §5.18.13.6, fault_diagnostic_rule: AFDD Fault Condition FC#10: OAT and MAT not equal in mech+economizer cooling
- p148, §5.18.12.1, fault_diagnostic_rule: Fan Maintenance Alarm
- p153, §5.18.4.1, operational_sequence: Supply Fan Run Requirement
- p153, §5.18.4.2, operational_sequence: Fan Speed Ramp Limit
- p153, §5.18.4.3, parameter_spec: Fan Speed Setpoints
- p153, §5.18.4.4, parameter_spec: Supply Air Temperature Setpoint Deadband
- p154, §5.18.4.6, operational_sequence: Fan Speed and SAT Reset Based on Heating/Cooling Loop Signal
- p156, §5.18.5.2, operational_sequence: SATsp Control Loop Enable and Mapping
- p156, §5.18.5.3, operational_sequence: SATsp-C Control Loop Enable
- p157, §5.18.6.2, operational_sequence: Minimum Outdoor Air Damper Control without Airflow Station
- p158, §5.18.6.3, operational_sequence: Minimum Outdoor Air Control with Airflow Station
- p158, §5.18.7.1, operational_sequence: Economizer Lockout Sequencing
- p158, §5.18.7.2, operational_sequence: Economizer Re-enable Delay

### Anchor Rejected
- §5.18.13.6: AFDD Fault Condition FC#4: Too many OS changes | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#5: SAT too low in heating | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#6: OA fraction too high | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#8: SAT and MAT not equal in free cooling | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#9: OAT too high for free cooling | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#11: OAT too low for mechanical cooling | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#12: SAT too high | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#14: Temperature drop across inactive cooling coil | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#15: Temperature rise across inactive heating coil | weak evidence_quote: section heading without supporting rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (34)
- G4 extract wallclock <= configured limit: PASS (377.63s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
