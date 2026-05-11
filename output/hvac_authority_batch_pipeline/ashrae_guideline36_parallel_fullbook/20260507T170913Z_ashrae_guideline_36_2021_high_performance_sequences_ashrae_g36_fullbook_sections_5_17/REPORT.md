# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T170913Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_17
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
| Extract output tokens | 16582 |
| Judge calls | 1 |
| Judge total tokens | 7611 |
| Total cost | ¥0.2320 / ¥10.00 |
| Extract wallclock | 481.85s |
| Total wallclock | 588.87s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 25 |
| Anchor passed | 25 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 23 |
| Judge accepted | 22 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | fault_diagnostic_rule: 5, operational_sequence: 12, parameter_spec: 4, commissioning_step: 1 |
| L4 / L3 | 8 / 14 |

## Samples

### Accepted
- p134, §5.17.3.2, fault_diagnostic_rule: Fan Status Alarm
- p134, §5.17.3.3, fault_diagnostic_rule: Filter Pressure Drop Alarm
- p145, §5.17.4.6, operational_sequence: Fault Condition Alarm Suppression
- p145, §5.17.4.7, operational_sequence: Fault Condition Evaluation Suspension
- p145, §5.17.4.8, operational_sequence: Fault Condition Alarm Delay
- p145, §5.17.4.9, operational_sequence: AFDD Test Mode
- p146, §5.17.1.1, operational_sequence: Supply Fan Start/Stop Logic
- p146, §5.17.1.1, operational_sequence: Totalize VAV Airflow for Diagnostics
- p146, §5.17.1.2, operational_sequence: Static Pressure Setpoint Reset
- p147, §5.17.2.1, operational_sequence: Supply Air Temperature Control Loop Enable
- p147, §5.17.1.2, parameter_spec: Trim & Respond Parameters for Static Pressure Reset
- p148, §5.17.3.1, fault_diagnostic_rule: Fan Maintenance Interval Alarm
- p148, §5.17.2.2, operational_sequence: Heating SAT Setpoint in Warmup/Setback Modes
- p148, §5.17.2.3, operational_sequence: Heating Coil PID Control
- p148, §5.17.2.2, parameter_spec: Trim & Respond Parameters for Heating SAT Reset

### Anchor Rejected
- §5.17.1.3: Static Pressure Control via Supply Fan Speed | weak evidence_quote: section heading without supporting rule
- §5.17.2.2: Heating Supply Air Temperature Setpoint Reset (Occupied Mode) | weak evidence_quote: section heading without supporting rule

### Judge Rejected
- §5.17.4.5: Fault Condition 3: Temperature Rise Across Inactive Heating Coil | unsupported: Evidence quote does not support the specific fault condition; only references table.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (95.7%)
- G3 focused section run produced at least one verified candidate: PASS (22)
- G4 extract wallclock <= configured limit: PASS (481.85s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
