# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T022705Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_8
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.8
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31717 |
| Extract calls | 1 |
| Extract input tokens | 32868 |
| Extract output tokens | 12191 |
| Judge calls | 1 |
| Judge total tokens | 8346 |
| Total cost | ¥0.0936 / ¥10.00 |
| Extract wallclock | 172.61s |
| Total wallclock | 269.73s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 49 |
| Anchor passed | 49 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 18 |
| Judge input | 31 |
| Judge accepted | 31 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 8, operational_sequence: 20, application_guidance: 3 |
| L4 / L3 | 24 / 7 |

## Samples

### Accepted
- p74, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Level 3
- p75, §5.8.8.1, operational_sequence: Cooling SAT Reset Request - 0 Requests
- p75, §5.8.8.1, operational_sequence: Cooling SAT Reset Request - 1 Request
- p75, §5.8.8.1, operational_sequence: Cooling SAT Reset Request - 2 Requests
- p75, §5.8.8.1, operational_sequence: Cooling SAT Reset Request - 3 Requests
- p75, §5.8.8.2, operational_sequence: Static Pressure Reset Request - 0 Requests
- p75, §5.8.8.2, operational_sequence: Static Pressure Reset Request - 1 Request
- p75, §5.8.8.2, operational_sequence: Static Pressure Reset Request - 3 Requests
- p77, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm Level 4
- p77, §5.8.6.2, fault_diagnostic_rule: Low DAT Alarm Suppression for Importance-Multiplier 0
- p77, §5.8.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm Level 3
- p77, §5.8.6.2, fault_diagnostic_rule: Low Discharge Air Temperature Alarm Level 4
- p78, §5.8.8.2, operational_sequence: Static Pressure Reset Request - 2 Requests
- p79, §5.8.8.3, operational_sequence: Hot-Water Reset Request - 0 Requests
- p79, §5.8.8.3, operational_sequence: Hot-Water Reset Request - 1 Request

### Anchor Rejected
- §5.8.5.1: Cooling Mode Primary Airflow Setpoint Mapping | weak evidence_quote: section heading without supporting rule
- §5.8.5.1: Cooling Mode Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.8.5.1: Cooling Mode Parallel Fan Control for Title 24 | weak evidence_quote: section heading without supporting rule
- §5.8.5.2: Deadband Mode Heating Coil Off | weak evidence_quote: too short to support structured summary
- §5.8.5.2: Deadband Mode Parallel Fan Control for Title 24 | weak evidence_quote: section heading without supporting rule
- §5.8.5.3: Heating Mode Parallel Fan Run | weak evidence_quote: too short to support structured summary
- §5.8.5.3: Heating Mode Discharge Temperature Reset (0-50% Loop) | weak evidence_quote: section heading without supporting rule
- §5.8.5.3: Heating Mode Fan Airflow Reset (50-100% Loop) | weak evidence_quote: section heading without supporting rule
- §5.8.6.3: Fan Alarm - Commanded ON, Status OFF | weak evidence_quote: too short to support structured summary
- §5.8.6.3: Fan Alarm - Commanded OFF, Status ON | weak evidence_quote: too short to support structured summary

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (31)
- G4 extract wallclock <= configured limit: PASS (172.61s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
