# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260507T011128Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_1
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** single-call full-book extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.1
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 196618 |
| Extract calls | 1 |
| Extract input tokens | 223171 |
| Extract output tokens | 13482 |
| Judge calls | 1 |
| Judge total tokens | 13871 |
| Total cost | ¥0.3187 / ¥10.00 |
| Extract wallclock | 184.57s |
| Total wallclock | 383.76s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 46 |
| Anchor passed | 42 |
| Anchor rejected | 4 |
| Weak evidence rejected before judge | 1 |
| Judge input | 41 |
| Judge accepted | 30 |
| Judge rejected | 11 |
| Judge rejection breakdown | unsupported: 11 |
| Final by type | commissioning_step: 1, operational_sequence: 22, parameter_spec: 5, fault_diagnostic_rule: 2 |
| L4 / L3 | 0 / 30 |

## Samples

### Accepted
- p43, §5.1.11, commissioning_step: Override Capability for All Points
- p43, §5.1.2, operational_sequence: Control Loop Enable/Disable to Prevent Windup
- p43, §5.1.3, operational_sequence: Control Loop Initialization to Neutral Value
- p43, §5.1.4, operational_sequence: Neutral Control Loop Condition
- p43, §5.1.5.1, operational_sequence: Outdoor Air Temperature Sensor Validity
- p43, §5.1.5.2, operational_sequence: Global Outdoor Air Temperature Calculation
- p43, §5.1.7, operational_sequence: Software Point and Software Switch Definition
- p43, §5.1.8.1, operational_sequence: Proportional-Only Loops for Limiting Loops
- p43, §5.1.8.2, operational_sequence: Derivative Term Usage Restriction
- p43, §5.1.10, parameter_spec: Adjustability of Setpoints, Timers, Deadbands, PID Gains
- p43, §5.1.9, parameter_spec: Maximum Rate of Change for Control Loop Output
- p44, §5.1.12.2, operational_sequence: Maintenance Mode Alarm Suppression
- p44, §5.1.12.1, parameter_spec: Alarm Levels Definition
- p45, §5.1.12.5, parameter_spec: Post-Exit Suppression Period Defaults
- p45, §5.1.13.1, parameter_spec: VFD Speed Point Configuration

### Anchor Rejected
- §5.1.15.5.b.1.iv: Cooling Tower Fault Conditions | evidence_quote not verbatim in any chunk
- §5.1.15.5.b.2.i: Response to Fault for Fans, Pumps, and Cooling Towers | evidence_quote not verbatim in any chunk
- §5.1.15.5.b.2.ii: Response to Fault for Chillers and Boilers | evidence_quote not verbatim in any chunk
- §5.1.15.5.c.1.i: Hand Operation Detection for Fans and Pumps | evidence_quote not verbatim in any chunk
- §5.1.14.4: Trim & Respond Logic Execution | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.1.6: Proven ON/OFF Definition | unsupported: Evidence quote does not support the summary; appears to be mis-extracted.
- §5.1.12.3: Alarm Exit Hysteresis | unsupported: Evidence only shows section header; lacks details to support summary.
- §5.1.12.4: Alarm Latching Defaults | unsupported: Evidence truncated; does not confirm latching defaults.
- §5.1.13.2: VFD Minimum Speed Monitoring and Correction | unsupported: Evidence truncated; does not confirm monitoring frequency or alarm logic.
- §5.1.14.2: Trim & Respond Request Definition and Software Points | unsupported: Evidence truncated; does not cover software points and accumulator logic.
- §5.1.15.2: Runtime Points Definition | unsupported: Evidence only shows section header; no runtime point details.
- §5.1.15.5.b.1.ii: Chiller Fault Conditions | unsupported: Evidence only references other sections; does not confirm listed fault conditions.
- §5.1.15.5.b.1.iii: Boiler Fault Conditions | unsupported: Evidence truncated; does not confirm boiler fault conditions.
- §5.1.17.1: Economizer Disable Based on High Limit | unsupported: Evidence truncated; missing details on setpoint determination.
- §5.1.19.4: SystemOK FALSE Conditions | unsupported: Evidence truncated; does not confirm alarm inhibition details.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (91.3%)
- G2 judge_acceptance_rate >= 50%: PASS (73.2%)
- G3 focused section run produced at least one verified candidate: PASS (30)
- G4 extract wallclock <= configured limit: PASS (184.57s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
