# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T233901Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_19
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.19
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 29190 |
| Extract calls | 1 |
| Extract input tokens | 30121 |
| Extract output tokens | 1339 |
| Judge calls | 1 |
| Judge total tokens | 1028 |
| Total cost | ¥0.1023 / ¥10.00 |
| Extract wallclock | 39.03s |
| Total wallclock | 47.91s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 6 |
| Anchor passed | 6 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 4 |
| Judge accepted | 4 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 1, fault_diagnostic_rule: 1, operational_sequence: 2 |
| L4 / L3 | 1 / 3 |

## Samples

### Accepted
- p171, §5.19.1.1, application_guidance: Room Temperature Control Method Applicability
- p171, §5.19.2.1, fault_diagnostic_rule: Maintenance Interval Alarm
- p171, §5.19.1.1, operational_sequence: Exhaust Fan Start/Stop – Option a (Zone Group Occupied Mode)
- p171, §5.19.1.1, operational_sequence: Exhaust Fan Start/Stop – Option b (Room Temperature Control)

### Anchor Rejected
- §5.19.2.2: Fan Status Mismatch Alarm – Commanded On, Status Off | weak evidence_quote: too short to support structured summary
- §5.19.2.2: Fan Status Mismatch Alarm – Commanded Off, Status Off | weak evidence_quote: too short to support structured summary

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (4)
- G4 extract wallclock <= configured limit: PASS (39.03s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
