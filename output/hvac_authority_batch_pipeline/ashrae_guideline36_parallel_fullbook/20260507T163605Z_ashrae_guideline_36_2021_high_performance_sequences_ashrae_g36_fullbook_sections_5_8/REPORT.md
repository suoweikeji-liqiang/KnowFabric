# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T163605Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_8
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
| Extract output tokens | 17968 |
| Judge calls | 1 |
| Judge total tokens | 8907 |
| Total cost | ¥0.2469 / ¥10.00 |
| Extract wallclock | 514.98s |
| Total wallclock | 645.35s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 33 |
| Anchor passed | 33 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 7 |
| Judge input | 26 |
| Judge accepted | 22 |
| Judge rejected | 4 |
| Judge rejection breakdown | unsupported: 4 |
| Final by type | fault_diagnostic_rule: 9, operational_sequence: 10, parameter_spec: 2, application_guidance: 1 |
| L4 / L3 | 9 / 13 |

## Samples

### Accepted
- p74, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (50%)
- p77, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm (70%)
- p77, §5.8.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm (17°C / 30°F)
- p77, §5.8.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm (8.3°C / 15°F)
- p77, §5.8.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm Suppression
- p81, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Suppression
- p81, §5.8.5.2, operational_sequence: Deadband State: Primary Airflow Setpoint
- p81, §5.8.5.3, operational_sequence: Heating State: Primary Airflow Setpoint
- p83, §5.8.3.1, parameter_spec: Parallel Fan Minimum Airflow Setpoint (Pfan-z)
- p84, §5.8.5.1, operational_sequence: Cooling State: Airflow Setpoint Mapping to Cooling Loop Output
- p84, §5.8.4, parameter_spec: Active Endpoints as a Function of Zone Group Mode
- p85, §5.8.5.3, application_guidance: Electric Reheat Minimum Airflow Requirement
- p85, §5.8.5.1, operational_sequence: Cooling State: Parallel Fan Control for Ventilation (ASHRAE 62.1)
- p85, §5.8.5.1, operational_sequence: Cooling State: Supply Air Temperature Above Room Temperature Limits Airflow
- p85, §5.8.5.2, operational_sequence: Deadband State: Parallel Fan Ventilation (ASHRAE 62.1)

### Anchor Rejected
- §5.8.5.1: Cooling State: Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.8.5.2: Deadband State: Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.8.5.3: Heating State: Parallel Fan On | weak evidence_quote: too short to support structured summary
- §5.8.6.5: Leaking Damper Alarm | weak evidence_quote: too short to support structured summary
- §5.8.7: Testing/Commissioning Overrides | weak evidence_quote: lacks rule/action signal
- §5.8.8.1: Cooling SAT Reset Requests | weak evidence_quote: section heading without supporting rule
- §5.8.8.2: Static Pressure Reset Requests | weak evidence_quote: section heading without supporting rule

### Judge Rejected
- §5.8.5.1: Cooling State: Parallel Fan Control for Ventilation (Title 24) | unsupported: Evidence is only the section header, not the actual content.
- §5.8.5.2: Deadband State: Parallel Fan Ventilation (Title 24) | unsupported: Evidence is only the section header.
- §5.8.5.3: Heating State: Discharge Temperature Reset (0-50% heating loop) | unsupported: Evidence is only the section header.
- §5.8.5.3: Heating State: Fan Airflow Reset (50-100% heating loop) | unsupported: Evidence is only the section header.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (84.6%)
- G3 focused section run produced at least one verified candidate: PASS (22)
- G4 extract wallclock <= configured limit: PASS (514.98s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
