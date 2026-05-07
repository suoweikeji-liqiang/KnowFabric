# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260507T010230Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_22
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** single-call full-book extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.22
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 196618 |
| Extract calls | 1 |
| Extract input tokens | 210512 |
| Extract output tokens | 10254 |
| Judge calls | 1 |
| Judge total tokens | 9757 |
| Total cost | ¥0.2795 / ¥10.00 |
| Extract wallclock | 131.43s |
| Total wallclock | 265.31s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 33 |
| Anchor passed | 33 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 32 |
| Judge accepted | 21 |
| Judge rejected | 11 |
| Judge rejection breakdown | unsupported: 11 |
| Final by type | operational_sequence: 17, fault_diagnostic_rule: 4 |
| L4 / L3 | 9 / 12 |

## Samples

### Accepted
- p79, §5.22.8.4, operational_sequence: FCU Heating Hot-Water Plant Requests
- p134, §5.22.5.2, fault_diagnostic_rule: FCU Fan Status Alarm
- p145, §5.22.6.10, operational_sequence: FCU AFDD - Non-Applicable Fault Conditions Not Evaluated
- p145, §5.22.6.11, operational_sequence: FCU AFDD - Alarm Delay
- p145, §5.22.6.12, operational_sequence: FCU AFDD - Test Mode
- p146, §5.22.8.2, operational_sequence: FCU Chiller Plant Requests
- p148, §5.22.5.1, fault_diagnostic_rule: FCU Maintenance Interval Alarm
- p153, §5.22.4.1, operational_sequence: FCU Supply Fan Run Condition
- p153, §5.22.4.2, operational_sequence: FCU Fan Speed Ramp Limitation
- p263, §5.22.4, operational_sequence: FCU Supply Fan Speed and Supply Air Temperature Control
- p264, §5.22.4.3, operational_sequence: FCU Fan Speed and SAT Control in Cooling Mode
- p264, §5.22.6.2, operational_sequence: FCU AFDD - Operating State Definition
- p267, §5.22.6.6, fault_diagnostic_rule: FCU AFDD - SAT Too High in Full Cooling
- p267, §5.22.6.6, fault_diagnostic_rule: FCU AFDD - SAT Too Low in Full Heating
- p268, §5.22.6.13, operational_sequence: FCU AFDD - Alarm Reporting

### Anchor Rejected
- §5.22.7: FCU Testing/Commissioning Overrides | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
- §5.22.4.3: FCU Fan Speed and SAT Control in Heating Mode | unsupported: Evidence only contains a section header, no operational details to support the claimed heating mode control logic.
- §5.22.4.3: FCU Fan Speed and SAT Control in Deadband Mode | unsupported: Evidence only contains a section header, no operational details to support the claimed deadband mode control logic.
- §5.22.5.3: FCU Filter Pressure Drop Alarm | unsupported: Evidence is truncated; does not support the specific filter pressure drop formula and threshold details given in the summary.
- §5.22.6.6: FCU AFDD - Too Many Changes in Operating State | unsupported: Evidence is truncated; does not confirm the rule about too many operating state changes.
- §5.22.6.6: FCU AFDD - Temperature Drop Across Inactive Cooling Coil | unsupported: Evidence only a section header; does not contain the specific temperature drop rule described.
- §5.22.6.6: FCU AFDD - Temperature Rise Across Inactive Heating Coil | unsupported: Evidence only a section header; does not contain the specific temperature rise rule described.
- §5.22.6.9: FCU AFDD - Evaluation Suspension on Mode Change | unsupported: Evidence is truncated; does not confirm the ModeDelay suspension rule.
- §5.22.6.3: FCU AFDD - Points Required | unsupported: Evidence only contains a section header; does not list the required points.
- §5.22.6.4: FCU AFDD - Calculated Values | unsupported: Evidence truncated; does not confirm the specific calculated values and sampling intervals.
- §5.22.6.5: FCU AFDD - Internal Variables | unsupported: Evidence refers to a table without listing the internal variables; summary details are unsupported.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (65.6%)
- G3 L4 count > 0: PASS (9)
- G4 extract wallclock <= configured limit: PASS (131.43s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
