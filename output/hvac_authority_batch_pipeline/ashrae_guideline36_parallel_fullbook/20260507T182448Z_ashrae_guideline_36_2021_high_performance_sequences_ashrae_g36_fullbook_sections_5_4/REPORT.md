# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T182448Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_4
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.4
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 29697 |
| Extract calls | 1 |
| Extract input tokens | 30538 |
| Extract output tokens | 7258 |
| Judge calls | 1 |
| Judge total tokens | 2642 |
| Total cost | ¥0.1474 / ¥10.00 |
| Extract wallclock | 169.54s |
| Total wallclock | 211.57s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 9 |
| Anchor passed | 9 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 7 |
| Judge accepted | 7 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 1, operational_sequence: 5, parameter_spec: 1 |
| L4 / L3 | 0 / 7 |

## Samples

### Accepted
- p71, §5.4.1, application_guidance: Zone Group Composition
- p71, §5.4.2, operational_sequence: Zone Group Independent Schedules and Modes
- p71, §5.4.3, operational_sequence: Occupied-Standby Mode Exclusion
- p71, §5.4.3, operational_sequence: Zone Group Mode Propagation
- p71, §5.4.5, operational_sequence: Zone Group Override Switch Change Behavior
- p71, §5.4.6.1, operational_sequence: Zone Group Occupied Mode Determination
- p71, §5.4.6, parameter_spec: Zone Group Operating Modes Requirement

### Anchor Rejected
- §5.4.4: Zone Group Exclusive Mode | weak evidence_quote: lacks rule/action signal
- §5.4.5: Zone Group Commissioning Override Switches Provision | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (7)
- G4 extract wallclock <= configured limit: PASS (169.54s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
