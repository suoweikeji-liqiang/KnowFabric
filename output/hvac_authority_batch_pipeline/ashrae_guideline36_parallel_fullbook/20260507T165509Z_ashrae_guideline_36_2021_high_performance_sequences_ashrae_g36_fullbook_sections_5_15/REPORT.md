# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T165509Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_15
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.15
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 50655 |
| Extract calls | 1 |
| Extract input tokens | 53380 |
| Extract output tokens | 2244 |
| Judge calls | 1 |
| Judge total tokens | 714 |
| Total cost | ¥0.1767 / ¥10.00 |
| Extract wallclock | 70.72s |
| Total wallclock | 81.57s |

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
- p111, §5.15.1, operational_sequence: AHU System Mode Determination

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (1)
- G4 extract wallclock <= configured limit: PASS (70.72s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
