# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T021950Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_4
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.4
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 29697 |
| Extract calls | 1 |
| Extract input tokens | 30502 |
| Extract output tokens | 1978 |
| Judge calls | 1 |
| Judge total tokens | 2086 |
| Total cost | ¥0.0448 / ¥10.00 |
| Extract wallclock | 27.66s |
| Total wallclock | 61.29s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 8 |
| Anchor passed | 8 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 6 |
| Judge accepted | 4 |
| Judge rejected | 2 |
| Judge rejection breakdown | unsupported: 2 |
| Final by type | operational_sequence: 4 |
| L4 / L3 | 0 / 4 |

## Samples

### Accepted
- p71, §5.4.1, operational_sequence: Zone Group Definition
- p71, §5.4.2, operational_sequence: Zone Group Independent Schedules and Modes
- p71, §5.4.3, operational_sequence: Occupied-Standby Mode Not a Zone-Group Mode
- p71, §5.4.3, operational_sequence: Zone Group Mode Consistency

### Anchor Rejected
- §5.4.4: Zone Group Single Mode Constraint | weak evidence_quote: lacks rule/action signal
- §5.4.5: Zone Group Testing/Commissioning Override Switches | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.4.6.1: Occupied Mode Condition - Scheduled Time | unsupported: Summary claims specific condition (scheduled time) not present in provided evidence quote.
- §5.4.6.1: Occupied Mode Condition - Override | unsupported: Summary cites override condition not supported by evidence quote, which only introduces the section.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (66.7%)
- G3 focused section run produced at least one verified candidate: PASS (4)
- G4 extract wallclock <= configured limit: PASS (27.66s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
