# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T024553Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_19
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.19
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 29190 |
| Extract calls | 1 |
| Extract input tokens | 30085 |
| Extract output tokens | 1215 |
| Judge calls | 1 |
| Judge total tokens | 1991 |
| Total cost | ¥0.0429 / ¥10.00 |
| Extract wallclock | 20.59s |
| Total wallclock | 51.71s |

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
| Final by type | application_guidance: 1, fault_diagnostic_rule: 2, operational_sequence: 1 |
| L4 / L3 | 0 / 4 |

## Samples

### Accepted
- p171, §5.19.1.1, application_guidance: Room Temperature Control Method Application
- p171, §5.19.2.1, fault_diagnostic_rule: Maintenance Interval Alarm
- p171, §5.19.2.2, fault_diagnostic_rule: Fan Alarm - Status/Command Mismatch
- p171, §5.19.1.1, operational_sequence: Exhaust Fan Start/Stop - Option b: Cycle to Maintain Room Temperature

### Anchor Rejected
- §5.19.1.1: Exhaust Fan Start/Stop - Option a: Operate with Associated Zone Groups | weak evidence_quote: section heading without supporting rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (4)
- G4 extract wallclock <= configured limit: PASS (20.59s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
