# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T230406Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_3
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.3
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31900 |
| Extract calls | 1 |
| Extract input tokens | 32863 |
| Extract output tokens | 5272 |
| Judge calls | 1 |
| Judge total tokens | 3061 |
| Total cost | ¥0.1420 / ¥10.00 |
| Extract wallclock | 149.54s |
| Total wallclock | 171.68s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 18 |
| Anchor passed | 18 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 6 |
| Judge input | 12 |
| Judge accepted | 11 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | operational_sequence: 7, parameter_spec: 4 |
| L4 / L3 | 2 / 9 |

## Samples

### Accepted
- p67, §5.3.2.3, operational_sequence: Zone Setpoint Mode Determination
- p67, §5.3.2.4, parameter_spec: Setpoint Overlap Prevention
- p68, §5.3.2.8, operational_sequence: Window Switch Setpoint Override
- p69, §5.3.2.10, operational_sequence: Setpoint Adjustment Priority Hierarchy
- p69, §5.3.3, operational_sequence: Local Override Occupied Mode Call
- p70, §5.3.4.1, operational_sequence: Cooling Loop Enable/Disable
- p70, §5.3.4.1, operational_sequence: Heating Loop Enable/Disable
- p70, §5.3.6.1, operational_sequence: Zone Temperature Alarm Suppression
- p70, §5.3.4.2, parameter_spec: Cooling Loop Output Range
- p70, §5.3.4.3, parameter_spec: Heating Loop Output Range
- p70, §5.3.4.4, parameter_spec: Control Loop Type Requirement

### Anchor Rejected
- §5.3.2.6: Cooling Demand Limit Setpoint Adjustment | weak evidence_quote: lacks rule/action signal
- §5.3.2.7: Heating Demand Limit Setpoint Adjustment | weak evidence_quote: lacks rule/action signal
- §5.3.2.9: Occupancy Sensor Setback/Setup | weak evidence_quote: lacks rule/action signal
- §5.3.5: Zone State Determination | weak evidence_quote: section heading without supporting rule
- §5.3.6.1: High Zone Temperature Alarm | weak evidence_quote: too short to support structured summary
- §5.3.6.1: Low Zone Temperature Alarm | weak evidence_quote: too short to support structured summary

### Judge Rejected
- §5.3.2.5: Local Setpoint Adjustment Limits | unsupported: Evidence quote is section heading only, no detailed content to support the summary.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (91.7%)
- G3 focused section run produced at least one verified candidate: PASS (11)
- G4 extract wallclock <= configured limit: PASS (149.54s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
