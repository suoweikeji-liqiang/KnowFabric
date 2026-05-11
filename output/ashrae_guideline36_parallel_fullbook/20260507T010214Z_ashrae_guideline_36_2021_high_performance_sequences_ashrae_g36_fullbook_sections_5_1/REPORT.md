# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260507T010214Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_1
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** single-call full-book extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.1
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 196618 |
| Extract calls | 1 |
| Extract input tokens | 210512 |
| Extract output tokens | 18644 |
| Judge calls | 1 |
| Judge total tokens | 507 |
| Total cost | ¥0.2553 / ¥10.00 |
| Extract wallclock | 242.75s |
| Total wallclock | 249.12s |

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
- p179, §5.1.15.5.b.1.ii, operational_sequence: Chiller Fault Detection (Safety Shutdown)

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 L4 count > 0: FAIL (0)
- G4 extract wallclock <= configured limit: PASS (242.75s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
