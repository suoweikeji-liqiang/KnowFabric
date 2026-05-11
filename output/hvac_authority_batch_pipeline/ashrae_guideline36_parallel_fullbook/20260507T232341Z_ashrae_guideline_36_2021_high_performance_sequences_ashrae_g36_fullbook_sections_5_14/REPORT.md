# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T232341Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_14
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
| Extract output tokens | 7065 |
| Judge calls | 1 |
| Judge total tokens | 6141 |
| Total cost | ¥0.1611 / ¥10.00 |
| Extract wallclock | 186.70s |
| Total wallclock | 231.06s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 26 |
| Anchor passed | 26 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 25 |
| Judge accepted | 22 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 15, fault_diagnostic_rule: 5, commissioning_step: 1, parameter_spec: 1 |
| L4 / L3 | 18 / 4 |

## Samples

### Accepted
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests – 2°C (3°F) Exceedance
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests – 3°C (5°F) Exceedance
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests – Cooling Loop > 95%
- p75, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests – Airflow < 50% and Damper > 95%
- p75, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests – Damper > 95%
- p77, §5.14.6.1, fault_diagnostic_rule: Low Airflow Alarm – 70% Threshold
- p78, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests – Airflow < 70% and Damper > 95%
- p81, §5.14.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Zones with Importance-Multiplier of 0
- p98, §5.14.5.2, operational_sequence: Override to Prevent Backflow – Cooling Damper
- p98, §5.14.5.2, operational_sequence: Override to Prevent Backflow – Heating Damper
- p99, §5.14.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p99, §5.14.6.3, fault_diagnostic_rule: Leaking Damper Alarm
- p100, §5.14.8.3, operational_sequence: Heating SAT Reset Requests – 2°C (3°F) Below Setpoint
- p100, §5.14.8.3, operational_sequence: Heating SAT Reset Requests – 3°C (5°F) Below Setpoint
- p100, §5.14.8.3, operational_sequence: Heating SAT Reset Requests – Heating Loop > 95%

### Anchor Rejected
- §5.14.5.1: Cooling Mode Damper Control | weak evidence_quote: section heading without supporting rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (88.0%)
- G3 focused section run produced at least one verified candidate: PASS (22)
- G4 extract wallclock <= configured limit: PASS (186.70s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
