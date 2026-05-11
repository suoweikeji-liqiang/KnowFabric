# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T173624Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_22
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.22
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 33054 |
| Extract calls | 1 |
| Extract input tokens | 34253 |
| Extract output tokens | 15822 |
| Judge calls | 1 |
| Judge total tokens | 7241 |
| Total cost | ¥0.2275 / ¥10.00 |
| Extract wallclock | 361.99s |
| Total wallclock | 436.21s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 31 |
| Anchor passed | 28 |
| Anchor rejected | 3 |
| Weak evidence rejected before judge | 0 |
| Judge input | 28 |
| Judge accepted | 28 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 7, fault_diagnostic_rule: 8, parameter_spec: 4, application_guidance: 8, commissioning_step: 1 |
| L4 / L3 | 13 / 15 |

## Samples

### Accepted
- p79, §5.22.8.4, operational_sequence: FCU Heating Hot-Water Plant Request
- p134, §5.22.5.2, fault_diagnostic_rule: FCU Fan Status Mismatch Alarm
- p140, §5.22.6.5, parameter_spec: FCU AFDD ModeDelay Default
- p140, §5.22.6.5, parameter_spec: FCU AFDD TestModeDelay Default
- p145, §5.22.6.11, application_guidance: FCU AFDD Alarm Delay
- p145, §5.22.6.12, application_guidance: FCU AFDD Test Mode
- p146, §5.22.8.2, operational_sequence: FCU Chiller Plant Request
- p148, §5.22.5.1, fault_diagnostic_rule: FCU Fan Maintenance Interval Alarm
- p150, §5.22.6.5, parameter_spec: FCU AFDD AlarmDelay Default
- p153, §5.22.4.1, operational_sequence: FCU Supply Fan Enable
- p153, §5.22.4.2, parameter_spec: FCU Fan Speed Ramp Limit
- p161, §5.22.5.3, fault_diagnostic_rule: FCU Filter Pressure Drop Alarm
- p170, §5.22.7, commissioning_step: FCU Testing/Commissioning Override Switches
- p264, §5.22.4.3.c, operational_sequence: FCU Cooling Mode Sequence
- p264, §5.22.6.2, operational_sequence: FCU AFDD Operating State Definition

### Anchor Rejected
- §5.22.4.3.a: FCU Heating Mode Sequence | evidence_quote not verbatim in any chunk
- §5.22.4.3.b: FCU Deadband Mode Sequence | evidence_quote not verbatim in any chunk
- §5.22.6.7.d: FCU AFDD Fault Evaluation in OS#4 (Other) | evidence_quote not verbatim in any chunk

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (90.3%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (28)
- G4 extract wallclock <= configured limit: PASS (361.99s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
