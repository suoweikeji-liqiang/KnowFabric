# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T165021Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_13
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.13
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30364 |
| Extract calls | 1 |
| Extract input tokens | 31342 |
| Extract output tokens | 10410 |
| Judge calls | 1 |
| Judge total tokens | 4781 |
| Total cost | ¥0.1775 / ¥10.00 |
| Extract wallclock | 299.66s |
| Total wallclock | 364.32s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 16 |
| Anchor passed | 14 |
| Anchor rejected | 2 |
| Weak evidence rejected before judge | 0 |
| Judge input | 14 |
| Judge accepted | 14 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 1, fault_diagnostic_rule: 5, operational_sequence: 6, parameter_spec: 1, commissioning_step: 1 |
| L4 / L3 | 9 / 5 |

## Samples

### Accepted
- p74, §5.13.6.3, application_guidance: Airflow Alarm Threshold Determination
- p74, §5.13.6.1.b, fault_diagnostic_rule: Low Airflow Level 3 Alarm
- p77, §5.13.6.1.a, fault_diagnostic_rule: Low Airflow Level 4 Alarm
- p81, §5.13.6.1.c, fault_diagnostic_rule: Low Airflow Alarm Suppression for Non-Critical Zones
- p98, §5.13.5.2.a, operational_sequence: Override Close Heating Damper if Heating AHU Not Proven
- p98, §5.13.5.2.b, operational_sequence: Override Close Cooling Damper if Cooling AHU Not Proven
- p99, §5.13.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p99, §5.13.6.3, fault_diagnostic_rule: Leaking Damper Alarm
- p101, §5.13.5.1.b, operational_sequence: Deadband Mode Cold and Hot Damper Control
- p104, §5.13.4, parameter_spec: Endpoints as a Function of Zone Group Mode
- p105, §5.13.5.1.a, operational_sequence: Cooling Mode Cold Duct Airflow Reset
- p105, §5.13.5.1.c.1, operational_sequence: Heating Mode Hot Damper Close when Supply Air Colder than Room
- p106, §5.13.7, commissioning_step: Testing/Commissioning Overrides for Dual-Duct VAV Zone
- p106, §5.13.5.1.c.2, operational_sequence: Heating Mode Maximum Hot Duct Airflow Limiting Loop

### Anchor Rejected
- §5.13.5.1.a.1: Cooling Mode Cold Airflow Limitation when Supply Air Warmer than Room | evidence_quote not verbatim in any chunk
- §5.13.5.1.c: Heating Mode Hot and Cold Damper Control | evidence_quote not verbatim in any chunk

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (87.5%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (14)
- G4 extract wallclock <= configured limit: PASS (299.66s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
