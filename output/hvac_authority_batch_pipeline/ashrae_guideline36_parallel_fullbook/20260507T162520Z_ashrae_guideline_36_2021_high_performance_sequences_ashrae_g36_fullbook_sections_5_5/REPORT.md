# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T162520Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_5
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.5
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30098 |
| Extract calls | 1 |
| Extract input tokens | 31130 |
| Extract output tokens | 12569 |
| Judge calls | 1 |
| Judge total tokens | 6103 |
| Total cost | ¥0.1977 / ¥10.00 |
| Extract wallclock | 1556.83s |
| Total wallclock | 1660.62s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 16 |
| Anchor passed | 16 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 14 |
| Judge accepted | 13 |
| Judge rejected | 1 |
| Judge rejection breakdown | duplicate: 1 |
| Final by type | application_guidance: 2, operational_sequence: 5, commissioning_step: 1, fault_diagnostic_rule: 5 |
| L4 / L3 | 5 / 8 |

## Samples

### Accepted
- p73, §5.5.3, application_guidance: Recommendation for reheat when minimum ventilation is high
- p73, §5.5.3, operational_sequence: Heating capability condition for cooling-only terminals
- p74, §5.5.6.3, application_guidance: Airflow alarm threshold determination
- p74, §5.5.7, commissioning_step: Commissioning override switches
- p74, §5.5.6.1, fault_diagnostic_rule: Low airflow Level 3 alarm
- p74, §5.5.6.1, fault_diagnostic_rule: Suppression of low airflow alarms for zones with importance multiplier 0
- p74, §5.5.6.2, fault_diagnostic_rule: Airflow sensor calibration fault
- p74, §5.5.6.3, fault_diagnostic_rule: Leaking damper detection
- p74, §5.5.5.1, operational_sequence: Airflow setpoint mapping in cooling state
- p74, §5.5.5.2, operational_sequence: Airflow setpoint in deadband state
- p74, §5.5.5.3, operational_sequence: Airflow setpoint mapping in heating state
- p74, §5.5.5.4, operational_sequence: VAV damper modulation for airflow control
- p77, §5.5.6.1, fault_diagnostic_rule: Low airflow Level 4 alarm

### Anchor Rejected
- §5.5.4: Endpoint assignments by Zone Group mode | weak evidence_quote: lacks rule/action signal
- §5.5.7: Leaking damper commissioning check | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
- §5.5: Recommendation to include heating with CO2 DCV | duplicate: Duplicate of cand_3eb93d212c60d3f2; same recommendation from same page.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (92.9%)
- G3 focused section run produced at least one verified candidate: PASS (13)
- G4 extract wallclock <= configured limit: FAIL (1556.83s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
