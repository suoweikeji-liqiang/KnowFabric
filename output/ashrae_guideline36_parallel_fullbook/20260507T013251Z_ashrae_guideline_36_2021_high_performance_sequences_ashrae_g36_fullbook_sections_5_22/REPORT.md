# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260507T013251Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_22
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.22
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 33054 |
| Extract calls | 1 |
| Extract input tokens | 34215 |
| Extract output tokens | 8430 |
| Judge calls | 1 |
| Judge total tokens | 8239 |
| Total cost | ¥0.0890 / ¥10.00 |
| Extract wallclock | 121.93s |
| Total wallclock | 238.54s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 31 |
| Anchor passed | 29 |
| Anchor rejected | 2 |
| Weak evidence rejected before judge | 4 |
| Judge input | 25 |
| Judge accepted | 25 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 18, fault_diagnostic_rule: 6, parameter_spec: 1 |
| L4 / L3 | 10 / 15 |

## Samples

### Accepted
- p79, §5.22.8.4, operational_sequence: Heating Hot-Water Plant Request Logic
- p134, §5.22.5.2, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p145, §5.22.6.10, operational_sequence: AFDD Non-Applicable Fault Conditions
- p145, §5.22.6.11, operational_sequence: AFDD Alarm Delay Requirement
- p145, §5.22.6.12, operational_sequence: AFDD Test Mode
- p146, §5.22.8.2, operational_sequence: Chiller Plant Request Logic
- p148, §5.22.5.1, fault_diagnostic_rule: Fan Maintenance Interval Alarm
- p153, §5.22.4.1, operational_sequence: Supply Fan Operation in Unoccupied Mode
- p153, §5.22.4.2, operational_sequence: Fan Speed Ramp Limitation
- p161, §5.22.5.3, fault_diagnostic_rule: Filter Pressure Drop Alarm
- p264, §5.22.4.4.c, operational_sequence: Cooling Mode Fan Speed and SAT Control
- p264, §5.22.6.2, operational_sequence: AFDD Operating State Definition
- p265, §5.22.6.3, operational_sequence: AFDD Required Points
- p266, §5.22.6.4, operational_sequence: AFDD Rolling Averages Calculation
- p266, §5.22.6.5, parameter_spec: AFDD Internal Variables Default Values

### Anchor Rejected
- §5.22.4.4.a: Heating Mode Fan Speed and SAT Control | evidence_quote not verbatim in any chunk
- §5.22.4.4.b: Deadband Mode Fan Speed and Coil Control | evidence_quote not verbatim in any chunk
- §5.22.6.6: FC#1: Too Many OS Changes | weak evidence_quote: fault evidence lacks the specific FC item
- §5.22.6.6: FC#4: Temperature Drop Across Inactive Cooling Coil | weak evidence_quote: fault evidence lacks the specific FC item
- §5.22.6.6: FC#5: Temperature Rise Across Inactive Heating Coil | weak evidence_quote: fault evidence lacks the specific FC item
- §5.22.7: Testing/Commissioning Overrides for Valves | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (93.5%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (25)
- G4 extract wallclock <= configured limit: PASS (121.93s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
