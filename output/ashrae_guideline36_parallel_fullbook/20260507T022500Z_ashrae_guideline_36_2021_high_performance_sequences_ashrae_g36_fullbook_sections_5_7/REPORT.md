# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T022500Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_7
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.7
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30696 |
| Extract calls | 1 |
| Extract input tokens | 31830 |
| Extract output tokens | 7892 |
| Judge calls | 1 |
| Judge total tokens | 7749 |
| Total cost | ¥0.0845 / ¥10.00 |
| Extract wallclock | 103.44s |
| Total wallclock | 207.70s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 33 |
| Anchor passed | 33 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 12 |
| Judge input | 21 |
| Judge accepted | 20 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | application_guidance: 4, fault_diagnostic_rule: 9, operational_sequence: 7 |
| L4 / L3 | 10 / 10 |

## Samples

### Accepted
- p74, §5.7.6.4, application_guidance: Airflow Sensor Calibration Threshold Determination
- p74, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Level 3
- p77, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Level 4
- p77, §5.7.6.2, fault_diagnostic_rule: Low-DAT Alarm Suppression for Importance-Multiplier 0
- p77, §5.7.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm Level 3
- p77, §5.7.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm Level 4
- p79, §5.7.4, application_guidance: Endpoints as Function of Zone Group Mode
- p81, §5.7.5.3, application_guidance: MaxΔT Limit per ASHRAE 90.1
- p81, §5.7.5.5, application_guidance: Designer Must Ensure Ventilation Compliance
- p81, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Suppression for Importance-Multiplier 0
- p81, §5.7.5.1, operational_sequence: Cooling Mode Primary Airflow Setpoint Mapping
- p81, §5.7.5.2, operational_sequence: Deadband Mode Primary Airflow Setpoint
- p81, §5.7.5.3, operational_sequence: Heating Mode Coil Modulation
- p81, §5.7.5.3, operational_sequence: Heating Mode Primary Airflow Setpoint
- p81, §5.7.5.4, operational_sequence: VAV Damper Modulation

### Anchor Rejected
- §5.7.5.1: Cooling Mode Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.7.5.2: Deadband Mode Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.7.5.3: Heating Mode Discharge Temperature Reset | weak evidence_quote: section heading without supporting rule
- §5.7.5.5: Fan Run During Deadband and Cooling (California Title 24) | weak evidence_quote: section heading without supporting rule
- §5.7.6.5: Leaking Damper Alarm | weak evidence_quote: section heading without supporting rule
- §5.7.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Zero | weak evidence_quote: introductory fragment without complete rule
- §5.7.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Vcool-max | weak evidence_quote: lacks rule/action signal
- §5.7.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Vmin | weak evidence_quote: lacks rule/action signal
- §5.7.7: Testing/Commissioning Overrides - Force Damper Full Closed/Open | weak evidence_quote: lacks rule/action signal
- §5.7.7: Testing/Commissioning Overrides - Force Heating to OFF/Closed | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.7.6.3: Fan Alarm - Commanded Off, Status On | unsupported: Evidence quote is truncated and does not support the claimed Level 4 alarm for commanded off, status on.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (95.2%)
- G3 focused section run produced at least one verified candidate: PASS (20)
- G4 extract wallclock <= configured limit: PASS (103.44s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
