# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T230114Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_2
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.2
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 32783 |
| Extract calls | 1 |
| Extract input tokens | 34130 |
| Extract output tokens | 4253 |
| Judge calls | 1 |
| Judge total tokens | 1461 |
| Total cost | ¥0.1333 / ¥10.00 |
| Extract wallclock | 106.13s |
| Total wallclock | 118.01s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 5 |
| Anchor passed | 5 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 4 |
| Judge accepted | 4 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 3, fault_diagnostic_rule: 1 |
| L4 / L3 | 0 / 4 |

## Samples

### Accepted
- p59, §5.2.1.3, operational_sequence: Zone Minimum Outdoor Air and Minimum Airflow Setpoints – ASHRAE 62.1 Compliance
- p66, §5.2.2.3, fault_diagnostic_rule: CO2 Sensor Fault Alarms
- p66, §5.2.2.1, operational_sequence: Time-Averaged Ventilation (TAV) Pulse Width Modulation
- p66, §5.2.2.2, operational_sequence: TAV Mode Override of Active Airflow Setpoint

### Anchor Rejected
- §5.2.1.4: Zone Minimum Outdoor Air and Minimum Airflow Setpoints – California Title 24 Compliance | weak evidence_quote: section heading without supporting rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (4)
- G4 extract wallclock <= configured limit: PASS (106.13s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
