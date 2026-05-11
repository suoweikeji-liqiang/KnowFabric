# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T154934Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_1
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.1
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 28860 |
| Extract calls | 1 |
| Extract input tokens | 29762 |
| Extract output tokens | 21271 |
| Judge calls | 1 |
| Judge total tokens | 8743 |
| Total cost | ¥0.2570 / ¥10.00 |
| Extract wallclock | 621.02s |
| Total wallclock | 755.53s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 36 |
| Anchor passed | 33 |
| Anchor rejected | 3 |
| Weak evidence rejected before judge | 8 |
| Judge input | 25 |
| Judge accepted | 17 |
| Judge rejected | 8 |
| Judge rejection breakdown | unsupported: 8 |
| Final by type | application_guidance: 2, operational_sequence: 9, parameter_spec: 3, fault_diagnostic_rule: 3 |
| L4 / L3 | 0 / 17 |

## Samples

### Accepted
- p43, §5.1.2, application_guidance: Control Loop Enable Based on System Status
- p43, §5.1.3, operational_sequence: Control Loop Initialization to Neutral
- p43, §5.1.5.1, operational_sequence: Outdoor Air Temperature Sensor Validity at AHU Intake
- p43, §5.1.5.2, operational_sequence: Global Outdoor Air Temperature Calculation
- p43, §5.1.9, parameter_spec: Control Loop Output Rate-of-Change Limit
- p44, §5.1.12.1, parameter_spec: Alarm Levels Definition
- p45, §5.1.13.1, parameter_spec: VFD Speed Output Configuration
- p47, §5.1.14.2.a.6, fault_diagnostic_rule: Rogue Zone Detection via T&R Request Hours
- p50, §5.1.15.1, application_guidance: Parallel Equipment Rotation Requirement
- p50, §5.1.15.3, operational_sequence: Lead/Lag Equipment Rotation
- p51, §5.1.15.5.b.1.i.a, fault_diagnostic_rule: Fan/Pump Fault Detection
- p51, §5.1.15.4.a, operational_sequence: Lead/Standby Rotation When Equipment Off
- p51, §5.1.15.4.b, operational_sequence: Lead/Standby Rotation for Continuously Running Equipment
- p52, §5.1.15.5.b.1.iv, fault_diagnostic_rule: Cooling Tower Fault Conditions
- p55, §5.1.17.2, operational_sequence: ASHRAE 90.1 Differential Dry Bulb Economizer High Limit

### Anchor Rejected
- §5.1.15.5.b.2.i: Fault Response for Fans, Pumps, and Cooling Towers | evidence_quote not verbatim in any chunk
- §5.1.15.5.b.2.ii: Fault Response for Chillers and Boilers | evidence_quote not verbatim in any chunk
- §5.1.15.5.c.1.i: Fan/Pump Hand Operation Detection | evidence_quote not verbatim in any chunk
- §5.1.12.2: Maintenance Mode Alarm Suppression | weak evidence_quote: too short to support structured summary
- §5.1.14.4: Trim & Respond Setpoint Reset Logic | weak evidence_quote: lacks rule/action signal
- §5.1.14.2.c: Trim & Respond Request Multiplication and Sending | weak evidence_quote: lacks rule/action signal
- §5.1.17.2: ASHRAE 90.1 Fixed Dry Bulb Economizer High Limit (Majority Climates) | weak evidence_quote: lacks rule/action signal
- §5.1.17.2: ASHRAE 90.1 Fixed Enthalpy + Fixed Dry Bulb Economizer High Limit | weak evidence_quote: lacks rule/action signal
- §5.1.17.3: Title 24 Fixed Dry Bulb Economizer High Limit (California Zones 1,3,5,11-16) | weak evidence_quote: lacks rule/action signal
- §5.1.17.3: Title 24 Fixed Enthalpy + Fixed Dry Bulb Economizer High Limit | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.1.12.3: Alarm Exit Hysteresis Defaults | unsupported: Summary unsupported by evidence (only a section heading quoted).
- §5.1.12.4: Alarm Latching Defaults | unsupported: Summary unsupported by evidence (incomplete quote).
- §5.1.12.5: Post-Exit Alarm Suppression Periods | unsupported: Summary unsupported by evidence (incomplete quote).
- §5.1.13.2: VFD Minimum Speed Mismatch Detection | unsupported: Summary unsupported by evidence (incomplete quote).
- §5.1.15.5.b.1.ii: Chiller Fault Conditions | unsupported: Summary unsupported by evidence (incomplete quote).
- §5.1.15.5.b.1.iii: Boiler Fault Conditions | unsupported: Summary unsupported by evidence (incomplete quote).
- §5.1.19.4: SystemOK FALSE Conditions | unsupported: Summary unsupported by evidence (incomplete quote).
- §5.1.19.5: Hierarchical Alarm Suppression Rules | unsupported: Summary unsupported by evidence (incomplete quote).

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (91.7%)
- G2 judge_acceptance_rate >= 50%: PASS (68.0%)
- G3 focused section run produced at least one verified candidate: PASS (17)
- G4 extract wallclock <= configured limit: PASS (621.02s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
