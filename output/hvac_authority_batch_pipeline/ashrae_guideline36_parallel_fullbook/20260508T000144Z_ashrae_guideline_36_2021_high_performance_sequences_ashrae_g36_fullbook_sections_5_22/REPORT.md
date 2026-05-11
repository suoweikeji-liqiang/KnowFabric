# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260508T000144Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_22
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.22
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 33054 |
| Extract calls | 1 |
| Extract input tokens | 34253 |
| Extract output tokens | 8851 |
| Judge calls | 1 |
| Judge total tokens | 6965 |
| Total cost | ¥0.1822 / ¥10.00 |
| Extract wallclock | 240.11s |
| Total wallclock | 284.66s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 31 |
| Anchor passed | 30 |
| Anchor rejected | 1 |
| Weak evidence rejected before judge | 3 |
| Judge input | 27 |
| Judge accepted | 25 |
| Judge rejected | 2 |
| Judge rejection breakdown | generic_definition: 1, unsupported: 1 |
| Final by type | operational_sequence: 17, fault_diagnostic_rule: 6, commissioning_step: 1, parameter_spec: 1 |
| L4 / L3 | 13 / 12 |

## Samples

### Accepted
- p79, §5.22.8.4, operational_sequence: Heating Hot-Water Plant Request Generation
- p134, §5.22.5.2, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p145, §5.22.6.10, operational_sequence: AFDD Fault Condition Evaluation Restriction
- p145, §5.22.6.11, operational_sequence: AFDD Alarm Delay Requirement
- p145, §5.22.6.12, operational_sequence: AFDD Test Mode
- p146, §5.22.8.2, operational_sequence: Chiller Plant Request Generation
- p148, §5.22.5.1, fault_diagnostic_rule: Maintenance Interval Alarm for Fan
- p153, §5.22.4.1, operational_sequence: Supply Fan Run Requirement
- p153, §5.22.4.2, operational_sequence: Fan Speed Ramp Limit
- p161, §5.22.5.3, fault_diagnostic_rule: Filter Pressure Drop Alarm
- p170, §5.22.7, commissioning_step: Testing/Commissioning Overrides for Valves
- p263, §5.22.4.3.a, operational_sequence: Heating Mode Fan and SAT Control
- p264, §5.22.4.3.c, operational_sequence: Cooling Mode Fan and SAT Control
- p264, §5.22.6.2, operational_sequence: FCU Operating State Definition
- p266, §5.22.6.5, parameter_spec: AFDD Internal Variables Default Values

### Anchor Rejected
- §5.22.4.3.b: Deadband Mode Fan and Coil Control | evidence_quote not verbatim in any chunk
- §5.22.6.6: FC#1: Too Many Changes in Operating State | weak evidence_quote: fault evidence lacks the specific FC item
- §5.22.6.6: FC#4: Temperature Drop Across Inactive Cooling Coil | weak evidence_quote: fault evidence lacks the specific FC item
- §5.22.6.6: FC#5: Temperature Rise Across Inactive Heating Coil | weak evidence_quote: fault evidence lacks the specific FC item

### Judge Rejected
- §5.22.6.3: AFDD Required Points | generic_definition: Only states points must be available, lacks specific operational content; too generic.
- §5.22.6.4: AFDD Rolling Averages Calculation | unsupported: Summary mentions rolling averages but evidence quote is incomplete; unsupported extraction.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (96.8%)
- G2 judge_acceptance_rate >= 50%: PASS (92.6%)
- G3 focused section run produced at least one verified candidate: PASS (25)
- G4 extract wallclock <= configured limit: PASS (240.11s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
