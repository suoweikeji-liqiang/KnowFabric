# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T231807Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_11
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
| Extract output tokens | 6070 |
| Judge calls | 1 |
| Judge total tokens | 4733 |
| Total cost | ¥0.1508 / ¥10.00 |
| Extract wallclock | 167.13s |
| Total wallclock | 195.92s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 17 |
| Anchor passed | 17 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 16 |
| Judge accepted | 16 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 5, operational_sequence: 10, commissioning_step: 1 |
| L4 / L3 | 11 / 5 |

## Samples

### Accepted
- p74, §5.11.6.1, fault_diagnostic_rule: Low Airflow Alarm Level 3
- p75, §5.11.8.1, operational_sequence: Cooling SAT Reset Requests for Dual-Duct VAV
- p77, §5.11.6.1, fault_diagnostic_rule: Low Airflow Alarm Level 4
- p81, §5.11.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Zones with Importance-Multiplier 0
- p91, §5.11.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests for Dual-Duct VAV
- p95, §5.11.4, operational_sequence: Dual-Duct VAV Endpoints by Zone Group Mode
- p97, §5.11.5.1, operational_sequence: Dual-Duct VAV Cooling Mode with Dual Inlet Sensors
- p97, §5.11.5.1, operational_sequence: Dual-Duct VAV Deadband Mode with Dual Inlet Sensors
- p98, §5.11.5.1, operational_sequence: Dual-Duct VAV Heating Mode with Dual Inlet Sensors
- p98, §5.11.5.2, operational_sequence: Dual-Duct VAV Cooling Mode with Single Discharge Sensor
- p98, §5.11.5.2, operational_sequence: Dual-Duct VAV Deadband Mode with Single Discharge Sensor
- p98, §5.11.5.2, operational_sequence: Dual-Duct VAV Heating Mode with Single Discharge Sensor
- p98, §5.11.5.3, operational_sequence: Dual-Duct VAV Override to Prevent Backflow
- p99, §5.11.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p99, §5.11.6.3, fault_diagnostic_rule: Leaking Damper Alarm

### Anchor Rejected
- §5.11.4: Dual-Duct VAV Endpoints Table | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (16)
- G4 extract wallclock <= configured limit: PASS (167.13s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
