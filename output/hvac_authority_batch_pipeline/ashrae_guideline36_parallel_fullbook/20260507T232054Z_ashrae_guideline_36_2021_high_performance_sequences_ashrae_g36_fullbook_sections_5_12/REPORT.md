# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T232054Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_12
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.12
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30856 |
| Extract calls | 1 |
| Extract input tokens | 31964 |
| Extract output tokens | 7684 |
| Judge calls | 1 |
| Judge total tokens | 7055 |
| Total cost | ¥0.1689 / ¥10.00 |
| Extract wallclock | 200.81s |
| Total wallclock | 256.71s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 28 |
| Anchor passed | 28 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 0 |
| Judge input | 28 |
| Judge accepted | 24 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 5, operational_sequence: 17, parameter_spec: 1, commissioning_step: 1 |
| L4 / L3 | 21 / 3 |

## Samples

### Accepted
- p74, §5.12.6.1, fault_diagnostic_rule: Low Airflow Alarm – 70% Threshold
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Requests – 3°F Deviation
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Requests – 5°F Deviation
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Requests – Cooling Loop > 95%
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests – 50% Airflow and Damper > 95%
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests – 70% Airflow and Damper > 95%
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests – Damper > 95%
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Requests – 50% Airflow and Damper > 95%
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Requests – 70% Airflow and Damper > 95%
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Requests – Damper > 95%
- p77, §5.12.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Zones with Importance-Multiplier 0
- p98, §5.12.5.2, operational_sequence: Override to Prevent Backflow – Cooling Damper
- p98, §5.12.5.2, operational_sequence: Override to Prevent Backflow – Heating Damper
- p99, §5.12.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p99, §5.12.6.3, fault_diagnostic_rule: Leaking Damper Alarm

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (85.7%)
- G3 focused section run produced at least one verified candidate: PASS (24)
- G4 extract wallclock <= configured limit: PASS (200.81s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
