# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T165924Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_14
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.14
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30684 |
| Extract calls | 1 |
| Extract input tokens | 31796 |
| Extract output tokens | 16650 |
| Judge calls | 1 |
| Judge total tokens | 5286 |
| Total cost | ¥0.2179 / ¥10.00 |
| Extract wallclock | 475.48s |
| Total wallclock | 542.68s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 14 |
| Anchor passed | 14 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 13 |
| Judge accepted | 11 |
| Judge rejected | 2 |
| Judge rejection breakdown | unsupported: 2 |
| Final by type | application_guidance: 1, operational_sequence: 7, fault_diagnostic_rule: 3 |
| L4 / L3 | 8 / 3 |

## Samples

### Accepted
- p74, §5.14.6.3, application_guidance: Alarm Threshold Determination Based on Transducer Accuracy
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests
- p91, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests
- p98, §5.14.5.2, operational_sequence: Backflow Prevention Override
- p99, §5.14.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Fault
- p99, §5.14.6.3, fault_diagnostic_rule: Leaking Damper Fault
- p100, §5.14.8.3, operational_sequence: Heating SAT Reset Requests
- p101, §5.14.5.1, operational_sequence: Deadband State Temperature and Damper Control
- p102, §5.14.6.1, fault_diagnostic_rule: Low Airflow Alarms
- p108, §5.14.4, operational_sequence: Active Airflow Setpoint Endpoints by Zone Group Mode
- p110, §5.14.8.4, operational_sequence: Hot-Duct Static Pressure Reset Requests

### Anchor Rejected
- §5.14.7: Testing/Commissioning Override Switches | weak evidence_quote: too short to support structured summary

### Judge Rejected
- §5.14.5.1: Cooling State Temperature and Damper Control | unsupported: Evidence quote is only section heading, no operational details to support summary.
- §5.14.5.1: Heating State Temperature and Damper Control | unsupported: Evidence quote is only section heading, no operational details.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (84.6%)
- G3 focused section run produced at least one verified candidate: PASS (11)
- G4 extract wallclock <= configured limit: PASS (475.48s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
