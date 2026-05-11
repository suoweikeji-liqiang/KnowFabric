# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T171213Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_19
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
| Extract output tokens | 4653 |
| Judge calls | 1 |
| Judge total tokens | 2387 |
| Total cost | ¥0.1299 / ¥10.00 |
| Extract wallclock | 136.70s |
| Total wallclock | 180.17s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 5 |
| Anchor passed | 5 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 0 |
| Judge input | 5 |
| Judge accepted | 5 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 1, fault_diagnostic_rule: 2, operational_sequence: 2 |
| L4 / L3 | 0 / 5 |

## Samples

### Accepted
- p171, §5.19.1.1, application_guidance: Room Temperature Control Method Restriction
- p171, §5.19.2.1, fault_diagnostic_rule: Fan Maintenance Interval Alarm
- p171, §5.19.2.2, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p171, §5.19.1.1, operational_sequence: Exhaust Fan Start/Stop - Room Temperature Cycling
- p171, §5.19.1.1, operational_sequence: Exhaust Fan Start/Stop - Zone Group Occupancy

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (5)
- G4 extract wallclock <= configured limit: PASS (136.70s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
