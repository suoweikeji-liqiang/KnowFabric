# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T231451Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_8
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.8
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31717 |
| Extract calls | 1 |
| Extract input tokens | 32904 |
| Extract output tokens | 8846 |
| Judge calls | 1 |
| Judge total tokens | 6743 |
| Total cost | ¥0.1776 / ¥10.00 |
| Extract wallclock | 240.35s |
| Total wallclock | 284.48s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 32 |
| Anchor passed | 32 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 7 |
| Judge input | 25 |
| Judge accepted | 25 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 9, operational_sequence: 14, parameter_spec: 1, commissioning_step: 1 |
| L4 / L3 | 16 / 9 |

## Samples

### Accepted
- p74, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (Level 3)
- p77, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (Level 4)
- p77, §5.8.6.2, fault_diagnostic_rule: Low DAT Alarm Suppression for Importance-Multiplier 0
- p77, §5.8.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm (Level 3)
- p77, §5.8.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm (Level 4)
- p81, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Suppression for Importance-Multiplier 0
- p81, §5.8.5.2, operational_sequence: Deadband Zone State Primary Airflow Setpoint
- p81, §5.8.5.3, operational_sequence: Heating Zone State Primary Airflow Setpoint
- p83, §5.8.4, operational_sequence: Endpoints as a Function of Zone Group Mode
- p83, §5.8.3.1, parameter_spec: Pfan-z Definition
- p85, §5.8.5.1, operational_sequence: Cooling Zone State Parallel Fan Operation for ASHRAE 62.1 Ventilation
- p85, §5.8.5.1, operational_sequence: Cooling Zone State Parallel Fan Operation for California Title 24 Ventilation
- p85, §5.8.5.2, operational_sequence: Deadband Zone State Parallel Fan Operation for ASHRAE 62.1 Ventilation
- p85, §5.8.5.2, operational_sequence: Deadband Zone State Parallel Fan Operation for California Title 24 Ventilation
- p85, §5.8.5.3, operational_sequence: Heating Zone State Parallel Fan Airflow Reset (50-100% Heating Loop)

### Anchor Rejected
- §5.8.5.1: Cooling Zone State Airflow Setpoint Mapping | weak evidence_quote: section heading without supporting rule
- §5.8.5.1: Cooling Zone State Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.8.5.2: Deadband Zone State Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.8.5.3: Heating Zone State Parallel Fan On | weak evidence_quote: too short to support structured summary
- §5.8.5.3: Heating Zone State Discharge Temperature Reset (0-50% Heating Loop) | weak evidence_quote: section heading without supporting rule
- §5.8.6.3: Fan Alarm - Commanded ON, Status OFF | weak evidence_quote: too short to support structured summary
- §5.8.6.3: Fan Alarm - Commanded OFF, Status ON | weak evidence_quote: too short to support structured summary

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (25)
- G4 extract wallclock <= configured limit: PASS (240.35s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
