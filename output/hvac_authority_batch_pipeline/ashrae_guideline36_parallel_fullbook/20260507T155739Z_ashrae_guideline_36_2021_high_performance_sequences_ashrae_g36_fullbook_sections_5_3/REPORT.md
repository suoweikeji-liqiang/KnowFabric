# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T155739Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_3
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.3
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31900 |
| Extract calls | 1 |
| Extract input tokens | 32863 |
| Extract output tokens | 18154 |
| Judge calls | 1 |
| Judge total tokens | 5931 |
| Total cost | ¥0.2329 / ¥10.00 |
| Extract wallclock | 526.46s |
| Total wallclock | 600.63s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 25 |
| Anchor passed | 24 |
| Anchor rejected | 1 |
| Weak evidence rejected before judge | 3 |
| Judge input | 21 |
| Judge accepted | 21 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 13, parameter_spec: 2, fault_diagnostic_rule: 5, application_guidance: 1 |
| L4 / L3 | 0 / 21 |

## Samples

### Accepted
- p67, §5.3.2.3, operational_sequence: Active Setpoint Selection Based on Zone Group Mode
- p67, §5.3.2.4, operational_sequence: Setpoint Overlap and Limit Interlocks
- p67, §5.3.2.5.c, operational_sequence: Single Setpoint Adjustment Thermostat Behavior
- p67, §5.3.2.5.d, operational_sequence: Local Setpoint Adjustment Mode Restriction
- p67, §5.3.2.5.e, operational_sequence: Demand Limiting Freezes Local Setpoint Adjustment
- p67, §5.3.2.2, parameter_spec: Generic Zone Setpoint Separation
- p67, §5.3.2.5.b, parameter_spec: Default Local Setpoint Adjustment Limits
- p68, §5.3.2.8, fault_diagnostic_rule: Window Open During Non-Occupied Mode Alarm
- p68, §5.3.2.8, operational_sequence: Window Open Setpoint Override
- p69, §5.3.2.9.a, operational_sequence: Occupancy-Based Setpoint Setback
- p69, §5.3.2.9.b, operational_sequence: Occupancy Sensor Setpoint Restoration
- p69, §5.3.3, operational_sequence: Thermostat Override Button Calls Occupied Mode
- p70, §5.3.6.1, application_guidance: Consider Shorter Zone Temperature Alarm Delay for Critical Zones
- p70, §5.3.6.1.a.1, fault_diagnostic_rule: High Temperature Level 4 Alarm
- p70, §5.3.6.1.a.2, fault_diagnostic_rule: High Temperature Level 3 Alarm

### Anchor Rejected
- §5.3.6.1.c: Zone Temperature Alarm Suppression | evidence_quote not verbatim in any chunk
- §5.3.2.6: Cooling Demand-Limit Setpoint Increase | weak evidence_quote: lacks rule/action signal
- §5.3.2.7: Heating Demand-Limit Setpoint Decrease | weak evidence_quote: lacks rule/action signal
- §5.3.2.10: Setpoint Adjustment Hierarchy | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (96.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (21)
- G4 extract wallclock <= configured limit: PASS (526.46s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
