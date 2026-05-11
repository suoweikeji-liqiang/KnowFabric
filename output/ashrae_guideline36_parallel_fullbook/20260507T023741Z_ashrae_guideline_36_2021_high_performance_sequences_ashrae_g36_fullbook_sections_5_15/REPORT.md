# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T023741Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_15
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.15
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 50655 |
| Extract calls | 1 |
| Extract input tokens | 53344 |
| Extract output tokens | 18551 |
| Judge calls | 1 |
| Judge total tokens | 730 |
| Total cost | ¥0.0958 / ¥10.00 |
| Extract wallclock | 279.58s |
| Total wallclock | 291.98s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 1 |
| Anchor passed | 1 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 0 |
| Judge input | 1 |
| Judge accepted | 1 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 1 |
| L4 / L3 | 0 / 1 |

## Samples

### Accepted
- p111, §5.15.1, operational_sequence: AHU Mode Hierarchy

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (1)
- G4 extract wallclock <= configured limit: PASS (279.58s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
