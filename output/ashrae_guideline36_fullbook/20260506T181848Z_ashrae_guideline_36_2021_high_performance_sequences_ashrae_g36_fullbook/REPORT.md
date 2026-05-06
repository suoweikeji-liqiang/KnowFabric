# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260506T181848Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** single-call full-book extraction + single-call batch judge + verbatim chunk anchoring
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 196618 |
| Extract calls | 1 |
| Extract input tokens | 210447 |
| Extract output tokens | 40558 |
| Judge calls | 1 |
| Judge total tokens | 35660 |
| Total cost | ¥0.4544 / ¥30.00 |
| Extract wallclock | 514.53s |
| Total wallclock | 972.45s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 130 |
| Anchor passed | 130 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 32 |
| Judge input | 98 |
| Judge accepted | 75 |
| Judge rejected | 23 |
| Judge rejection breakdown | unsupported: 23 |
| Final by type | application_guidance: 7, commissioning_step: 3, fault_diagnostic_rule: 22, operational_sequence: 43 |
| L4 / L3 | 18 / 57 |

## Samples

### Accepted
- p6, §3.1.1.1, application_guidance: Default Zone Temperature Setpoints
- p20, §3.2.1.2, commissioning_step: TAB – Minimum Fan Speed Determination
- p21, §3.2.1.3, commissioning_step: TAB – Minimum Outdoor Air DP Setpoint (Standard 62.1)
- p23, §3.2.3.4, commissioning_step: TAB – Minimum Head Pressure Control Valve Position (Constant Speed CW Pumps)
- p50, §5.1.15.3, application_guidance: Equipment Staging and Rotation – Lead/Lag
- p55, §5.1.17.2, application_guidance: Economizer High Limit Selection (ASHRAE 90.1)
- p55, §5.1.17.3, application_guidance: Economizer High Limit Selection (Title 24)
- p74, §5.6.6.3, fault_diagnostic_rule: VAV Reheat Zone – Airflow Sensor Calibration Alarm
- p75, §5.6.8.1, operational_sequence: VAV Reheat Zone – Cooling SAT Reset Requests
- p76, §5.6.5.1, operational_sequence: VAV Reheat Zone – Cooling Sequence
- p76, §5.6.5.2, operational_sequence: VAV Reheat Zone – Deadband Sequence
- p77, §5.6.6.1, fault_diagnostic_rule: VAV Reheat Zone – Low Airflow Alarm
- p77, §5.6.6.2, fault_diagnostic_rule: VAV Reheat Zone – Low Discharge Air Temperature Alarm
- p77, §5.6.5.4, operational_sequence: VAV Reheat Zone – Low DAT Protection
- p78, §5.6.6.5, fault_diagnostic_rule: VAV Reheat Zone – Leaking Valve Alarm

### Anchor Rejected
- §5.20.4.15: Chiller Stage Up – Failsafe Condition (Parallel Plants) | weak evidence_quote: section heading without supporting rule
- §5.20.10.3: Head Pressure Control – Fixed Speed CW Pumps | weak evidence_quote: introductory fragment without complete rule
- §5.20.10.4: Head Pressure Control – Variable Speed CW Pumps (No WSE) | weak evidence_quote: introductory fragment without complete rule
- §5.16.14.8: VAV AHU – FC#6: OA Fraction Error | weak evidence_quote: section heading without supporting rule
- §5.16.14.8: VAV AHU – FC#4: Too Many Operating State Changes | weak evidence_quote: section heading without supporting rule
- §5.20.18.6: CHW Plant – FC#9: Evaporator Approach Too High | weak evidence_quote: lacks rule/action signal
- §5.20.18.6: CHW Plant – FC#19: Too Many Chiller Starts | weak evidence_quote: fault evidence lacks the specific FC item
- §5.21.11.6: HW Plant – FC#13: Too Many Boiler Starts | weak evidence_quote: fault evidence lacks the specific FC item
- §5.3.6.1: Zone Temperature Alarms | weak evidence_quote: section heading without supporting rule
- §5.20.17.3: CHW Plant – Chiller Alarm | weak evidence_quote: too short to support structured summary

### Judge Rejected
- §5.20.12.2: Cooling Tower Fan Control – CWRT Control (Close Coupled) | unsupported: Evidence quote refers to CWST control, not CWRT, and does not support summary details.
- §5.20.12.2: Cooling Tower Fan Enable/Disable (CWRT Control) | unsupported: Same incorrect evidence quote; summary not supported.
- §5.21.5.5: Non-Condensing Boiler Condensation Control – Primary-Secondary with Variable Speed Primary Pumps | unsupported: Evidence quote incomplete; summary details not supported.
- §5.6.5.3: VAV Reheat Zone – Heating Sequence | unsupported: Only section title provided; summary specifics not evidenced.
- §5.16.16.1: Multiple-Zone VAV AHU – Chilled-Water Reset Requests | unsupported: Only section heading provided; detailed reset request logic not evidenced.
- §5.16.16.4: Multiple-Zone VAV AHU – Heating Hot-Water Plant Requests | unsupported: Incomplete evidence; summary of heating hot-water plant requests unsupported.
- §5.18.15.1: Single-Zone VAV AHU – Chilled-Water Reset Requests | unsupported: Only section heading; chilled-water reset request details not supported.
- §5.18.15.4: Single-Zone VAV AHU – Heating Hot-Water Plant Requests | unsupported: Incomplete evidence; heating hot-water plant requests summary unsupported.
- §5.22.4.3: Fan Coil Unit – Heating Sequence | unsupported: Only section intro; FCU heating sequence details not evidenced.
- §5.22.4.3: Fan Coil Unit – Deadband Sequence | unsupported: Incomplete evidence; deadband sequence specifics not supported.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (76.5%)
- G3 L4 count > 0: PASS (18)
- G4 extract wallclock <= configured limit: PASS (514.53s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
