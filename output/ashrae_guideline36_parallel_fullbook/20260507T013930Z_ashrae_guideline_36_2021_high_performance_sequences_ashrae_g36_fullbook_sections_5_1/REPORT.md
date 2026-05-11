# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260507T013930Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_1
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.1
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 28860 |
| Extract calls | 1 |
| Extract input tokens | 29724 |
| Extract output tokens | 12241 |
| Judge calls | 1 |
| Judge total tokens | 13860 |
| Total cost | ¥0.1187 / ¥10.00 |
| Extract wallclock | 170.03s |
| Total wallclock | 383.75s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 45 |
| Anchor passed | 43 |
| Anchor rejected | 2 |
| Weak evidence rejected before judge | 4 |
| Judge input | 39 |
| Judge accepted | 34 |
| Judge rejected | 5 |
| Judge rejection breakdown | unsupported: 5 |
| Final by type | commissioning_step: 1, operational_sequence: 18, parameter_spec: 8, fault_diagnostic_rule: 7 |
| L4 / L3 | 2 / 32 |

## Samples

### Accepted
- p43, §5.1.11, commissioning_step: Override Capability for Points
- p43, §5.1.2, operational_sequence: Control Loop Enable/Disable to Prevent Windup
- p43, §5.1.3, operational_sequence: Control Loop Initialization to Neutral
- p43, §5.1.4, operational_sequence: Neutral Control Loop Condition
- p43, §5.1.5, operational_sequence: Outdoor Air Temperature Sensor Selection
- p43, §5.1.5.1, operational_sequence: Outdoor Air Temperature Sensor Validity for Air-Handler Intakes
- p43, §5.1.5.2, operational_sequence: Outdoor Air Temperature Averaging for Global Sequences
- p43, §5.1.6, operational_sequence: Proven Status Definition
- p43, §5.1.8.1, operational_sequence: Proportional-Only Loops for Limiting Loops
- p43, §5.1.8.2, operational_sequence: Derivative Term Usage Restriction
- p43, §5.1.10, parameter_spec: Adjustability of Setpoints, Timers, Deadbands, PID Gains
- p43, §5.1.9, parameter_spec: Control Loop Output Rate of Change Limit
- p44, §5.1.12.2, operational_sequence: Maintenance Mode Alarm Suppression
- p44, §5.1.12.1, parameter_spec: Alarm Levels Definition
- p45, §5.1.12.5, parameter_spec: Post-Exit Suppression Period Defaults

### Anchor Rejected
- §5.1.15.5.b.2.i: Fault Response for Fans, Pumps, Cooling Towers | evidence_quote not verbatim in any chunk
- §5.1.15.5.b.2.ii: Fault Response for Chillers and Boilers | evidence_quote not verbatim in any chunk
- §5.1.14.4: Trim & Respond Logic General Operation | weak evidence_quote: lacks rule/action signal
- §5.1.15.5.b.1.ii.b: Chiller Fault Condition - Manual Shut Off | weak evidence_quote: lacks rule/action signal
- §5.1.15.5.b.1.iv.a: Cooling Tower Fault Condition - Fan Failure | weak evidence_quote: too short to support structured summary
- §5.1.18.2: Damper/Valve Position Determination Methods | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.1.12.3: Alarm Exit Hysteresis Parameters | unsupported: Summary content not supported by provided evidence quote (only section heading).
- §5.1.12.4: Alarm Latching Defaults | unsupported: Summary details not evidenced by the partial quote provided.
- §5.1.13.2: VFD Minimum Speed Synchronization | unsupported: Evidence quote truncated; does not support key details of minimum speed synchronization.
- §5.1.17.1: Economizer Disable Based on High Limit | unsupported: Evidence quote truncated, missing details on automatic setpoint determination.
- §5.1.19.4: SystemOK FALSE Conditions | unsupported: Evidence incomplete; does not support the detailed conditions for SystemOK FALSE.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (95.6%)
- G2 judge_acceptance_rate >= 50%: PASS (87.2%)
- G3 focused section run produced at least one verified candidate: PASS (34)
- G4 extract wallclock <= configured limit: PASS (170.03s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
