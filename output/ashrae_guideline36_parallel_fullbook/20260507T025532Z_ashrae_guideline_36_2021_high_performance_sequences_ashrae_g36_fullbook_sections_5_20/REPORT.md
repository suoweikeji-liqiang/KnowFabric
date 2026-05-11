# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T025532Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_20
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.20
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 73298 |
| Extract calls | 1 |
| Extract input tokens | 74514 |
| Extract output tokens | 20509 |
| Judge calls | 1 |
| Judge total tokens | 19216 |
| Total cost | ¥0.2041 / ¥10.00 |
| Extract wallclock | 315.89s |
| Total wallclock | 579.38s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 74 |
| Anchor passed | 74 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 13 |
| Judge input | 61 |
| Judge accepted | 53 |
| Judge rejected | 8 |
| Judge rejection breakdown | unsupported: 8 |
| Final by type | operational_sequence: 37, fault_diagnostic_rule: 16 |
| L4 / L3 | 7 / 46 |

## Samples

### Accepted
- p172, §5.20.2.2, operational_sequence: Plant Enable Logic
- p172, §5.20.2.3, operational_sequence: Plant Disable Logic
- p175, §5.20.3.1, operational_sequence: WSE Enable Logic
- p176, §5.20.3.2, operational_sequence: WSE Disable Logic
- p176, §5.20.3.3, operational_sequence: PHXLWT Tuning - Decrease m
- p176, §5.20.3.3, operational_sequence: PHXLWT Tuning - Increase m
- p176, §5.20.3.5, operational_sequence: WSE HX Bypass Valve Modulation
- p176, §5.20.3.8, operational_sequence: WSE HX Pump Speed Reset Requests
- p176, §5.20.3.9, operational_sequence: WSE HX Pump Speed Trim & Respond
- p181, §5.20.4.15, operational_sequence: Chiller Stage Minimum Runtime
- p182, §5.20.4.15, operational_sequence: Stage Down Condition (Primary-Only without WSE)
- p182, §5.20.4.15, operational_sequence: Stage Down Condition (Primary-Secondary without WSE)
- p182, §5.20.4.15, operational_sequence: Stage Up Efficiency Condition (Primary-Only without WSE)
- p182, §5.20.4.15, operational_sequence: Stage Up Efficiency Condition (Primary-Secondary without WSE)
- p185, §5.20.4.15, operational_sequence: Stage Up Failsafe Condition (Primary-Secondary without WSE)

### Anchor Rejected
- §5.20.4.15: Stage Up Failsafe Condition (Primary-Only Parallel without WSE) | weak evidence_quote: section heading without supporting rule
- §5.20.6.7: Primary CHW Pump Staging (Headered Variable Speed, DP Control) | weak evidence_quote: introductory fragment without complete rule
- §5.20.7.3: Secondary CHW Pump Staging (Headered, DP Control) | weak evidence_quote: lacks rule/action signal
- §5.20.7.4: Coil Pump Staging (Poor Turndown) | weak evidence_quote: too short to support structured summary
- §5.20.7.4: Chiller Plant Requests from Coil Pumps | weak evidence_quote: too short to support structured summary
- §5.20.10.5: Head Pressure Control Mapping (WSE Disabled, with WSE Plant) | weak evidence_quote: introductory fragment without complete rule
- §5.20.12.3: Cooling Tower Bypass Valve - Open Condition | weak evidence_quote: lacks rule/action signal
- §5.20.12.3: Cooling Tower Bypass Valve - Close Conditions | weak evidence_quote: lacks rule/action signal
- §5.20.15.1: Tower Basin Heater Control | weak evidence_quote: too short to support structured summary
- §5.20.18.6: AFDD FC#16: Heat Exchanger Approach High | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.20.12.2: CWRT Control - CWRT Setpoint Calculation | unsupported: Evidence does not support the summary
- §5.20.12.2: CWRT Control - Tower Speed Command (Close Coupled) | unsupported: Evidence does not support the summary
- §5.20.12.2: CWRT Control - Tower Speed Command (Not Close Coupled) | unsupported: Evidence does not support the summary
- §5.20.12.2: Tower Fan Disable Logic (CWRT Control) | unsupported: Evidence does not support the summary
- §5.20.12.2: Tower Fan Enable Logic (CWRT Control) | unsupported: Evidence does not support the summary
- §5.20.12.2: CWST Control - Stepwise Reset Logic | unsupported: Evidence does not support the summary
- §5.20.12.2: WSE Mode - Integrated Operation Fan Speed | unsupported: Evidence does not support the summary
- §5.20.12.2: WSE Mode - WSE Only Fan Control | unsupported: Evidence does not support the summary

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (86.9%)
- G3 focused section run produced at least one verified candidate: PASS (53)
- G4 extract wallclock <= configured limit: PASS (315.89s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
