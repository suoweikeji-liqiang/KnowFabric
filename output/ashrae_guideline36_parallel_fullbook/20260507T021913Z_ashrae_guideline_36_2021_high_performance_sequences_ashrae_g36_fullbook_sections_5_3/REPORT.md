# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T021913Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_3
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.3
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31900 |
| Extract calls | 1 |
| Extract input tokens | 32827 |
| Extract output tokens | 6441 |
| Judge calls | 1 |
| Judge total tokens | 5239 |
| Total cost | ¥0.0701 / ¥10.00 |
| Extract wallclock | 86.56s |
| Total wallclock | 160.50s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 23 |
| Anchor passed | 21 |
| Anchor rejected | 2 |
| Weak evidence rejected before judge | 5 |
| Judge input | 16 |
| Judge accepted | 16 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 14, fault_diagnostic_rule: 1, parameter_spec: 1 |
| L4 / L3 | 0 / 16 |

## Samples

### Accepted
- p67, §5.3.2.3, operational_sequence: Active Setpoint Selection by Zone Group Mode
- p67, §5.3.2.4, operational_sequence: Zone Setpoint Overlap Prevention
- p67, §5.3.2.5, operational_sequence: Local Setpoint Adjustment Limits
- p67, §5.3.2.5.c, operational_sequence: Single Setpoint Adjustment Moves Both Setpoints
- p67, §5.3.2.5.d, operational_sequence: Local Setpoint Adjustment Mode Restriction
- p67, §5.3.2.5.e, operational_sequence: Local Setpoint Adjustment Freeze During Demand Limiting
- p68, §5.3.2.5 (informative note), operational_sequence: Demand Limit Level Reset Condition
- p68, §5.3.2.5 (informative note), operational_sequence: Demand Limit Sliding Window Method
- p68, §5.3.2.8, operational_sequence: Window Switch Setpoint Override
- p69, §5.3.3, operational_sequence: Local Override Timer
- p70, §5.3.6.1.b, fault_diagnostic_rule: Low Temperature Zone Alarm
- p70, §5.3.4.1.a, operational_sequence: Heating Loop Enable/Disable
- p70, §5.3.4.1.b, operational_sequence: Cooling Loop Enable/Disable
- p70, §5.3.4.2, operational_sequence: Cooling Loop Output Range
- p70, §5.3.4.3, operational_sequence: Heating Loop Output Range

### Anchor Rejected
- §5.3.6.1.a: High Temperature Zone Alarm | evidence_quote not verbatim in any chunk
- §5.3.6.1.c: Zone Temperature Alarm Suppression Conditions | evidence_quote not verbatim in any chunk
- §5.3.2.6: Cooling Demand Limit Setpoint Adjustment | weak evidence_quote: lacks rule/action signal
- §5.3.2.7: Heating Demand Limit Setpoint Adjustment | weak evidence_quote: lacks rule/action signal
- §5.3.2.9: Occupancy Sensor Setpoint Adjustment | weak evidence_quote: lacks rule/action signal
- §5.3.2.10: Hierarchy of Set-Point Adjustments | weak evidence_quote: section heading without supporting rule
- §5.3.5: Zone State Determination | weak evidence_quote: section heading without supporting rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (91.3%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (16)
- G4 extract wallclock <= configured limit: PASS (86.56s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
