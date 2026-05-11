# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T231637Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_10
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
| Extract output tokens | 6571 |
| Judge calls | 1 |
| Judge total tokens | 4765 |
| Total cost | ¥0.1542 / ¥10.00 |
| Extract wallclock | 181.42s |
| Total wallclock | 215.62s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 25 |
| Anchor passed | 25 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 5 |
| Judge input | 20 |
| Judge accepted | 20 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 9, operational_sequence: 10, commissioning_step: 1 |
| L4 / L3 | 10 / 10 |

## Samples

### Accepted
- p74, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Level 3
- p75, §5.10.8.1, operational_sequence: Cooling SAT Reset Requests
- p75, §5.10.8.2, operational_sequence: Static Pressure Reset Requests
- p77, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Level 4
- p77, §5.10.6.2, fault_diagnostic_rule: Low DAT Alarm Suppression for Importance-Multiplier 0
- p77, §5.10.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm Level 3
- p77, §5.10.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm Level 4
- p81, §5.10.5.2, operational_sequence: Deadband Zone State Primary Airflow Setpoint
- p89, §5.10.5.3, operational_sequence: Heating Zone State Heating Coil Modulation
- p92, §5.10.5.1, operational_sequence: Cooling Zone State Primary Airflow Setpoint Mapping
- p92, §5.10.5.1, operational_sequence: Cooling Zone State Series Fan Airflow Setpoint Mapping
- p93, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Suppression for Importance-Multiplier 0
- p93, §5.10.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p93, §5.10.5.2, operational_sequence: Deadband Zone State Series Fan Airflow Setpoint
- p93, §5.10.5.3, operational_sequence: Heating Zone State Second Stage: Series Fan Airflow Reset

### Anchor Rejected
- §5.10.5.1: Cooling Zone State Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.10.5.2: Deadband Zone State Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.10.5.3: Heating Zone State First Stage: Discharge Temperature Reset | weak evidence_quote: section heading without supporting rule
- §5.10.6.3: Fan Alarm Commanded ON Status OFF Level 2 | weak evidence_quote: too short to support structured summary
- §5.10.6.3: Fan Alarm Commanded OFF Status ON Level 4 | weak evidence_quote: too short to support structured summary

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (20)
- G4 extract wallclock <= configured limit: PASS (181.42s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
