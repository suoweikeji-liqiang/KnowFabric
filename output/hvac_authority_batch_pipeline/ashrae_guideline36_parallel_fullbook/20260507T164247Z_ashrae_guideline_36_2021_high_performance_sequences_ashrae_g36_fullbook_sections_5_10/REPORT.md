# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T164247Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_10
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.10
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31091 |
| Extract calls | 1 |
| Extract input tokens | 32224 |
| Extract output tokens | 13297 |
| Judge calls | 1 |
| Judge total tokens | 6802 |
| Total cost | ¥0.2071 / ¥10.00 |
| Extract wallclock | 390.83s |
| Total wallclock | 489.90s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 20 |
| Anchor passed | 20 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 19 |
| Judge accepted | 16 |
| Judge rejected | 3 |
| Judge rejection breakdown | unsupported: 3 |
| Final by type | parameter_spec: 1, fault_diagnostic_rule: 10, operational_sequence: 5 |
| L4 / L3 | 14 / 2 |

## Samples

### Accepted
- p73, §5.10.4, parameter_spec: Endpoints as a Function of Zone Group Mode
- p74, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm – Level 3
- p74, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm – Level 4
- p74, §5.10.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.10.6.5, fault_diagnostic_rule: Leaking Damper Alarm
- p75, §5.10.8.1, operational_sequence: Cooling SAT Reset Request Generation
- p75, §5.10.8.2, operational_sequence: Static Pressure Reset Request Generation
- p77, §5.10.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm – Level 3
- p77, §5.10.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm – Level 4
- p77, §5.10.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm Suppression
- p82, §5.10.6.3, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p86, §5.10.6.6, fault_diagnostic_rule: Leaking Valve Alarm
- p89, §5.10.5.4, operational_sequence: VAV Damper Control
- p89, §5.10.5.5, operational_sequence: Series Fan Control Logic
- p92, §5.10.5.1, operational_sequence: Cooling State Control Sequence

### Anchor Rejected
- §5.10.7: Testing/Commissioning Overrides | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.10.5.2: Deadband State Control Sequence | unsupported: Summary not supported by evidence; quote is only section heading.
- §5.10.5.3: Heating State Control Sequence | unsupported: Summary not supported by evidence; quote is only section heading.
- §5.10.5: Heating Logic Design Guidance | unsupported: Evidence quote is incomplete introduction, does not contain the design guidance.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (84.2%)
- G3 focused section run produced at least one verified candidate: PASS (16)
- G4 extract wallclock <= configured limit: PASS (390.83s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
