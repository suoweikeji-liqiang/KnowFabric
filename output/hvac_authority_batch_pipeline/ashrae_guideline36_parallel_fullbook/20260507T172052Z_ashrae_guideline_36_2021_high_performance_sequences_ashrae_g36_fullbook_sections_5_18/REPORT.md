# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T172052Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_18
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
| Extract output tokens | 23983 |
| Judge calls | 1 |
| Judge total tokens | 12425 |
| Total cost | ¥0.3195 / ¥10.00 |
| Extract wallclock | 687.54s |
| Total wallclock | 819.72s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 40 |
| Anchor passed | 40 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 39 |
| Judge accepted | 36 |
| Judge rejected | 3 |
| Judge rejection breakdown | unsupported: 3 |
| Final by type | fault_diagnostic_rule: 16, operational_sequence: 19, parameter_spec: 1 |
| L4 / L3 | 13 / 23 |

## Samples

### Accepted
- p134, §5.18.12.2, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p141, §5.18.13.6, fault_diagnostic_rule: FC#2: MAT Too Low
- p141, §5.18.13.6, fault_diagnostic_rule: FC#4: Too Many Operating State Changes
- p141, §5.18.13.6, fault_diagnostic_rule: FC#5: SAT Too Low in Heating
- p142, §5.18.13.6, fault_diagnostic_rule: FC#10: OAT and MAT Not Approximately Equal
- p142, §5.18.13.6, fault_diagnostic_rule: FC#12: SAT Too High; Should Be Less Than MAT
- p143, §5.18.13.6, fault_diagnostic_rule: FC#14: Temperature Drop Across Inactive Cooling Coil
- p145, §5.18.13.10, operational_sequence: AFDD Fault Evaluation Based on OS
- p145, §5.18.13.11, operational_sequence: AFDD Fault Alarm Delay
- p145, §5.18.13.9, operational_sequence: AFDD Evaluation Suspension Conditions
- p148, §5.18.12.1, fault_diagnostic_rule: Fan Maintenance Interval Alarm
- p153, §5.18.4.1, operational_sequence: Supply Fan Run for Non-Unoccupied Modes
- p153, §5.18.4.3, operational_sequence: Medium Fan Speed Reset Based on Outdoor Air Temperature
- p153, §5.18.4.4, operational_sequence: Supply Air Temperature Setpoint Deadband
- p153, §5.18.4.2, parameter_spec: Supply Fan Speed Ramp Limit

### Anchor Rejected
- §5.18.4.6: Supply Air Temperature Setpoint Mapping from Heating/Cooling Loop Signals | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.18.8.2: Relief Dampers Passive Building Pressure Control | unsupported: Evidence quote only provides section title, not the operational details in summary. Unsupported extraction.
- §5.18.11.2: Second-Stage Freeze Protection | unsupported: Evidence quote is incomplete and does not cover the full operational details (e.g., 1-hour delay, Level 3 alarm). Unsupported.
- §5.18.12.3: Filter Pressure Drop Alarm | unsupported: Evidence quote is truncated and does not support the full summary (e.g., alarm limit formula). Unsupported extraction.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (92.3%)
- G3 focused section run produced at least one verified candidate: PASS (36)
- G4 extract wallclock <= configured limit: PASS (687.54s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
