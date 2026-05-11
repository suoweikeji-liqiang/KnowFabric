# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T233211Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_17
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.17
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31746 |
| Extract calls | 1 |
| Extract input tokens | 32892 |
| Extract output tokens | 6244 |
| Judge calls | 1 |
| Judge total tokens | 5305 |
| Total cost | ¥0.1567 / ¥10.00 |
| Extract wallclock | 166.53s |
| Total wallclock | 209.95s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 24 |
| Anchor passed | 24 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 23 |
| Judge accepted | 23 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 12, fault_diagnostic_rule: 6, parameter_spec: 4, commissioning_step: 1 |
| L4 / L3 | 11 / 12 |

## Samples

### Accepted
- p111, §5.17.1.1, operational_sequence: Totalize VAV Box Airflow
- p112, §5.17.1.3, operational_sequence: Static Pressure Control
- p134, §5.17.3.2, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p134, §5.17.3.3, fault_diagnostic_rule: Filter Pressure Drop Alarm
- p145, §5.17.4.6, operational_sequence: AFDD Fault Condition Alarm Suppression by Operator
- p145, §5.17.4.7, operational_sequence: AFDD Fault Evaluation Suspension Conditions
- p145, §5.17.4.8, operational_sequence: AFDD Fault Condition Persistence Requirement
- p145, §5.17.4.9, operational_sequence: AFDD Test Mode
- p146, §5.17.1.1, operational_sequence: Supply Fan Start/Stop
- p146, §5.17.1.2, parameter_spec: Static Pressure Setpoint Reset T&R Parameters
- p147, §5.17.2.1, operational_sequence: Supply Air Temperature Control Enable
- p147, §5.17.2.2, parameter_spec: Occupied Mode Supply Air Temperature Setpoint Reset T&R Parameters
- p148, §5.17.3.1, fault_diagnostic_rule: Fan Maintenance Interval Alarm
- p148, §5.17.2.2, operational_sequence: Warmup and Setback Mode Supply Air Temperature Setpoint
- p148, §5.17.2.3, operational_sequence: Supply Air Temperature PID Control

### Anchor Rejected
- §5.17.4.1: AFDD Conditions Evaluated Continuously | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (23)
- G4 extract wallclock <= configured limit: PASS (166.53s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
