# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T024635Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_18
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.18
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 39665 |
| Extract calls | 1 |
| Extract input tokens | 41428 |
| Extract output tokens | 15273 |
| Judge calls | 1 |
| Judge total tokens | 12357 |
| Total cost | ¥0.1289 / ¥10.00 |
| Extract wallclock | 221.94s |
| Total wallclock | 393.84s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 51 |
| Anchor passed | 51 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 14 |
| Judge input | 37 |
| Judge accepted | 32 |
| Judge rejected | 5 |
| Judge rejection breakdown | unsupported: 5 |
| Final by type | operational_sequence: 20, fault_diagnostic_rule: 12 |
| L4 / L3 | 11 / 21 |

## Samples

### Accepted
- p128, §5.18.8.1, operational_sequence: Relief Damper Enable for Direct Building Pressure Control
- p128, §5.18.8.1, operational_sequence: Relief Damper Modulation for Direct Building Pressure Control
- p134, §5.18.12.2, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p141, §5.18.13.6, fault_diagnostic_rule: AFDD Fault Condition FC#2
- p142, §5.18.13.6, fault_diagnostic_rule: AFDD Fault Condition FC#10
- p145, §5.18.13.11, fault_diagnostic_rule: AFDD Alarm Delay and Reporting
- p145, §5.18.13.12, fault_diagnostic_rule: AFDD Test Mode
- p145, §5.18.13.9, fault_diagnostic_rule: AFDD Evaluation Suspension Conditions
- p148, §5.18.12.1, fault_diagnostic_rule: Maintenance Interval Alarm
- p153, §5.18.4.1, operational_sequence: Supply Fan Run Condition
- p153, §5.18.4.2, operational_sequence: Fan Speed Ramp Limitation
- p153, §5.18.4.3, operational_sequence: Medium Fan Speed Reset Based on OAT
- p153, §5.18.4.4, operational_sequence: Supply Air Temperature Deadband Setpoint
- p153, §5.18.4.5, operational_sequence: Fan Speed and SAT Setpoint Control Map
- p154, §5.18.4.6, operational_sequence: Fan Speed Reset in Heating and Cooling

### Anchor Rejected
- §5.18.4.6: SATsp Reset in Heating and Cooling | weak evidence_quote: lacks rule/action signal
- §5.18.6.2: Minimum OA Damper Position Calculation without Flow Station | weak evidence_quote: section heading without supporting rule
- §5.18.6.2: Minimum OA Damper Position Setpoint without Flow Station | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#4 | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#5 | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#6 | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#8 | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#9 | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#11 | weak evidence_quote: section heading without supporting rule
- §5.18.13.6: AFDD Fault Condition FC#12 | weak evidence_quote: section heading without supporting rule

### Judge Rejected
- §5.18.10.1: Return Fan Speed Tracking Differential | unsupported: Insufficient evidence: only section heading provided, not operational content.
- §5.18.10.1: Active Differential Airflow Setpoint Calculation | unsupported: Insufficient evidence: only section heading provided, not operational content.
- §5.18.11.2: Freeze Protection Stage 2 | unsupported: Insufficient evidence: truncated quote does not support full summary.
- §5.18.11.3: Freeze Protection Stage 3 | unsupported: Insufficient evidence: truncated quote does not support full summary.
- §5.18.12.3: Filter Pressure Drop Alarm | unsupported: Insufficient evidence: truncated quote lacks full details of alarm.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (86.5%)
- G3 focused section run produced at least one verified candidate: PASS (32)
- G4 extract wallclock <= configured limit: PASS (221.94s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
