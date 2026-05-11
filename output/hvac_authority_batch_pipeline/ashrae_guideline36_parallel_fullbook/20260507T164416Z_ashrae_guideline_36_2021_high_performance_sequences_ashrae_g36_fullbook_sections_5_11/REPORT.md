# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T164416Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_11
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.11
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31283 |
| Extract calls | 1 |
| Extract input tokens | 32386 |
| Extract output tokens | 12970 |
| Judge calls | 1 |
| Judge total tokens | 7305 |
| Total cost | ¥0.2086 / ¥10.00 |
| Extract wallclock | 378.88s |
| Total wallclock | 490.43s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 19 |
| Anchor passed | 19 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 18 |
| Judge accepted | 15 |
| Judge rejected | 3 |
| Judge rejection breakdown | unsupported: 3 |
| Final by type | application_guidance: 2, fault_diagnostic_rule: 5, operational_sequence: 7, commissioning_step: 1 |
| L4 / L3 | 8 / 7 |

## Samples

### Accepted
- p74, §5.11.6.3, application_guidance: Custom Thresholds Based on Sensor Accuracy
- p74, §5.11.6.1, fault_diagnostic_rule: Low Airflow Alarm (50% threshold)
- p74, §5.11.6.1, fault_diagnostic_rule: Low Airflow Alarm (70% threshold)
- p77, §5.11.6.1, fault_diagnostic_rule: Suppress Low Airflow Alarms for Zones with Importance-Multiplier = 0
- p97, §5.11.5, application_guidance: Airflow Sensor Configuration Selection
- p97, §5.11.5.1, operational_sequence: Deadband Mode Damper Control with Dual Inlet Airflow Sensors
- p98, §5.11.5.1, operational_sequence: Heating Mode Damper Control with Dual Inlet Airflow Sensors
- p98, §5.11.5.2, operational_sequence: Cooling Mode Damper Control with Single Discharge Airflow Sensor
- p98, §5.11.5.2, operational_sequence: Heating Mode Damper Control with Single Discharge Airflow Sensor
- p98, §5.11.5.3, operational_sequence: Override to Prevent Backflow (Cooling AHU Not Proven On)
- p98, §5.11.5.3, operational_sequence: Override to Prevent Backflow (Heating AHU Not Proven On)
- p99, §5.11.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p99, §5.11.6.3, fault_diagnostic_rule: Leaking Damper Alarm
- p99, §5.11.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests
- p106, §5.11.7, commissioning_step: Testing/Commissioning Overrides

### Anchor Rejected
- §5.11.4: Active Endpoints Based on Zone Group Mode | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.11.5.1: Cooling Mode Damper Control with Dual Inlet Airflow Sensors | unsupported: The evidence quote does not support the summary; it is about lead/lag rotation of equipment, not cooling mode damper control with dual inlet sensors.
- §5.11.5.2: Deadband Mode Damper Control with Single Discharge Airflow Sensor | unsupported: The evidence quote is about runtime points, not deadband mode damper control with a single discharge sensor.
- §5.11.8.1: Cooling SAT Reset Requests | unsupported: The evidence quote is about damper and valve position knowledge, not cooling SAT reset requests.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (83.3%)
- G3 focused section run produced at least one verified candidate: PASS (15)
- G4 extract wallclock <= configured limit: PASS (378.88s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
