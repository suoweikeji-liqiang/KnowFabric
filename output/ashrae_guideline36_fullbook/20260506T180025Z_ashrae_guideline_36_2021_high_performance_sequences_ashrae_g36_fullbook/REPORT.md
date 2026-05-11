# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260506T180025Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook
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
| Extract output tokens | 15781 |
| Judge calls | 1 |
| Judge total tokens | 16287 |
| Total cost | ¥0.3194 / ¥30.00 |
| Extract wallclock | 199.00s |
| Total wallclock | 380.04s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 50 |
| Anchor passed | 50 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 4 |
| Judge input | 46 |
| Judge accepted | 34 |
| Judge rejected | 12 |
| Judge rejection breakdown | unsupported: 12 |
| Final by type | commissioning_step: 3, operational_sequence: 17, application_guidance: 9, fault_diagnostic_rule: 5 |
| L4 / L3 | 3 / 31 |

## Samples

### Accepted
- p23, §3.2.3.4, commissioning_step: Establish MinCWVlvPos (Constant Speed CW Pumps)
- p24, §3.2.3.5, commissioning_step: Establish MinCWPspeed (Variable Speed CW Pumps)
- p24, §3.2.3.6, commissioning_step: Establish HxPumpDesSpd
- p172, §5.20.2.2, operational_sequence: Chiller Plant Enable
- p172, §5.20.2.3, operational_sequence: Chiller Plant Disable
- p175, §5.20.3.1, operational_sequence: Waterside Economizer Enable
- p176, §5.20.3.2, operational_sequence: Waterside Economizer Disable
- p179, §5.20.4.14, application_guidance: Staging Rules – Chiller Type Precedence
- p180, §5.20.4.14, application_guidance: Variable Speed Centrifugal Chiller Staging Point Reset with Lift
- p182, §5.20.4.15, operational_sequence: Chiller Stage Down – Efficiency Condition
- p182, §5.20.4.15, operational_sequence: Chiller Stage Up – Efficiency Condition
- p184, §5.20.4.15, application_guidance: Primary-Secondary Staging – Avoid Secondary Recirculation
- p199, §5.20.5.2, application_guidance: CHW Plant Reset Logic – DP First, Then Temperature
- p200, §5.20.5.2, application_guidance: CHW Plant Reset – Starting Point
- p200, §5.20.5.2, operational_sequence: Chilled Water Supply Temperature Reset – Differential Pressure Controlled Loops

### Anchor Rejected
- §5.20.7.3: Secondary CHW Pump Staging – Headered Pumps | weak evidence_quote: lacks rule/action signal
- §5.20.15.1: Tower Basin Heater Control | weak evidence_quote: too short to support structured summary
- §5.20.18.6: CHW Plant AFDD – FC#9: Evaporator approach too high | weak evidence_quote: lacks rule/action signal
- §5.20.18.6: CHW Plant AFDD – FC#16: Heat exchanger approach high | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.20.10.5: Head Pressure Control – With Waterside Economizer (WSE Disabled) | unsupported: Evidence quote only provides section heading, not the operational rule.
- §5.20.6.7: Primary CHW Pump Staging – Headered Pumps | unsupported: Evidence quote only provides section heading, not the operational rule.
- §5.20.12.2: Tower Fan Enable/Disable – CWRT Control | unsupported: Evidence quote is about sensor wiring, not the enable/disable conditions described in summary.
- §5.20.18.6: CHW Plant AFDD – FC#18: Too many OS changes | unsupported: Evidence quote is a generic section heading, not the specific fault condition description.
- §5.20.18.6: CHW Plant AFDD – FC#19: Too many chiller starts | unsupported: Evidence quote is a generic section heading, not the specific fault condition description.
- §5.20.18.6: CHW Plant AFDD – FC#20: Too many stage changes | unsupported: Evidence quote is a generic section heading, not the specific fault condition description.
- §3.2.3.1: Establish CHW-DPmax | unsupported: Evidence quote only provides a definition/heading, not the commissioning procedure described.
- §3.2.3.3: Establish Cw-DesPumpSpdStage | unsupported: Evidence quote only provides a definition/heading, not the commissioning procedure described.
- §3.2.3.7: Establish Ch-MaxPriPumpSpdStage | unsupported: Evidence quote only provides a definition/heading, not the commissioning procedure described.
- §3.2.3.8: Establish Ch-MinPriPumpSpdStage | unsupported: Evidence quote only provides a definition/heading, not the commissioning procedure described.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (73.9%)
- G3 L4 count > 0: PASS (3)
- G4 extract wallclock <= configured limit: PASS (199.00s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
