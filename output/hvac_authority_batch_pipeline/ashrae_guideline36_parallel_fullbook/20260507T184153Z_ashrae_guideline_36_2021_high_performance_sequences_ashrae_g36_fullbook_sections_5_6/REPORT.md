# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T184153Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_6
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.6
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31182 |
| Extract calls | 1 |
| Extract input tokens | 32341 |
| Extract output tokens | 20914 |
| Judge calls | 1 |
| Judge total tokens | 10481 |
| Total cost | ¥0.2689 / ¥10.00 |
| Extract wallclock | 588.02s |
| Total wallclock | 705.73s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 34 |
| Anchor passed | 34 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 33 |
| Judge accepted | 32 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | application_guidance: 6, fault_diagnostic_rule: 9, operational_sequence: 16, parameter_spec: 1 |
| L4 / L3 | 20 / 12 |

## Samples

### Accepted
- p74, §5.6.6.4, application_guidance: Airflow sensor calibration and leaking damper alarm threshold note
- p74, §5.6.6.1, fault_diagnostic_rule: Low Airflow Level 3 alarm
- p74, §5.6.6.1, fault_diagnostic_rule: Low Airflow Level 4 alarm
- p74, §5.6.6.3, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.6.6.4, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.6.5.1, operational_sequence: Cooling zone state with SAT > room temperature
- p74, §5.6.5.5, operational_sequence: VAV damper modulation to maintain airflow setpoint
- p75, §5.6.8.1, operational_sequence: Cooling SAT reset request – 0 requests
- p75, §5.6.8.1, operational_sequence: Cooling SAT reset request – 1 request from Cooling Loop
- p75, §5.6.8.1, operational_sequence: Cooling SAT reset request – 2 requests
- p75, §5.6.8.1, operational_sequence: Cooling SAT reset request – 3 requests
- p75, §5.6.8.2, operational_sequence: Static pressure reset request – 0 requests
- p75, §5.6.8.2, operational_sequence: Static pressure reset request – 1 request
- p75, §5.6.8.2, operational_sequence: Static pressure reset request – 2 requests
- p75, §5.6.8.2, operational_sequence: Static pressure reset request – 3 requests

### Anchor Rejected
- §5.6.7: Testing/Commissioning Overrides | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.6.5.3: Heating loop 0-50% – discharge temperature reset | unsupported: Evidence quote is truncated and does not support the detailed summary of discharge temperature reset.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (97.0%)
- G3 focused section run produced at least one verified candidate: PASS (32)
- G4 extract wallclock <= configured limit: PASS (588.02s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
