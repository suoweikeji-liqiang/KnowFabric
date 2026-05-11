# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T162738Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_7
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.7
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30696 |
| Extract calls | 1 |
| Extract input tokens | 31866 |
| Extract output tokens | 11723 |
| Judge calls | 1 |
| Judge total tokens | 5084 |
| Total cost | ¥0.1873 / ¥10.00 |
| Extract wallclock | 340.55s |
| Total wallclock | 399.59s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 20 |
| Anchor passed | 20 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 3 |
| Judge input | 17 |
| Judge accepted | 17 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 2, fault_diagnostic_rule: 10, operational_sequence: 5 |
| L4 / L3 | 12 / 5 |

## Samples

### Accepted
- p74, §5.7.6.5, application_guidance: Airflow Alarm Threshold Determination
- p74, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (Level 3)
- p74, §5.7.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Fault
- p74, §5.7.6.5, fault_diagnostic_rule: Leaking Damper Alarm
- p77, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (Level 4)
- p77, §5.7.6.2, fault_diagnostic_rule: Low DAT Alarm Suppression for Zones with Zero Importance (HW Reset)
- p77, §5.7.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm (Level 3)
- p77, §5.7.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm (Level 4)
- p78, §5.7.6.6, fault_diagnostic_rule: Leaking Heating Valve Alarm
- p79, §5.7.4, operational_sequence: Active Endpoints Based on Zone Group Mode
- p81, §5.7.5.5, application_guidance: Designer Ventilation Sum Requirement
- p81, §5.7.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Zones with Zero Importance
- p81, §5.7.5.1, operational_sequence: Primary Airflow Setpoint in Cooling State
- p81, §5.7.5.2, operational_sequence: Primary Airflow Setpoint in Deadband State
- p81, §5.7.5.3, operational_sequence: Heating State Operation - Primary Airflow and Discharge Temperature Reset

### Anchor Rejected
- §5.7.5.5: Parallel Fan Control Logic | weak evidence_quote: too short to support structured summary
- §5.7.6.3: Fan Alarm - Commanded Off but Status On | weak evidence_quote: too short to support structured summary
- §5.7.7: Testing/Commissioning Override Switches | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (17)
- G4 extract wallclock <= configured limit: PASS (340.55s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
