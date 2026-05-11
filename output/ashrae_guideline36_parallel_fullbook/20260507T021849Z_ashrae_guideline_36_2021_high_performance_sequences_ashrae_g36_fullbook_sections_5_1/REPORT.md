# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T021849Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_1
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.1
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 28860 |
| Extract calls | 1 |
| Extract input tokens | 29726 |
| Extract output tokens | 12903 |
| Judge calls | 1 |
| Judge total tokens | 12567 |
| Total cost | ¥0.1116 / ¥10.00 |
| Extract wallclock | 170.69s |
| Total wallclock | 311.68s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 47 |
| Anchor passed | 47 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 6 |
| Judge input | 41 |
| Judge accepted | 33 |
| Judge rejected | 8 |
| Judge rejection breakdown | unsupported: 8 |
| Final by type | operational_sequence: 21, parameter_spec: 10, fault_diagnostic_rule: 2 |
| L4 / L3 | 0 / 33 |

## Samples

### Accepted
- p43, §5.1.2, operational_sequence: Control Loop Enable/Disable Based on System Status
- p43, §5.1.3, operational_sequence: Control Loop Initialization on Enable/Reenable
- p43, §5.1.4, operational_sequence: Neutral Control Loop Condition
- p43, §5.1.5, operational_sequence: Outdoor Air Temperature Sensor Selection
- p43, §5.1.5.1, operational_sequence: Outdoor Air Temperature Sensor Validity for Air-Handler Intakes
- p43, §5.1.5.2, operational_sequence: Outdoor Air Temperature Averaging for Global Sequences
- p43, §5.1.8.1, operational_sequence: Proportional-Only Loops for Limiting Loops
- p43, §5.1.8.2, operational_sequence: Derivative Term Usage Restriction
- p43, §5.1.10, parameter_spec: Adjustability of Setpoints, Timers, Deadbands, PID Gains
- p43, §5.1.11, parameter_spec: Override Capability for Points
- p43, §5.1.9, parameter_spec: Control Loop Output Rate of Change Limit
- p44, §5.1.12.2, operational_sequence: Maintenance Mode Alarm Suppression
- p44, §5.1.12, parameter_spec: Alarm Configuration Requirements
- p44, §5.1.12.1, parameter_spec: Alarm Levels Definition
- p44, §5.1.12.3, parameter_spec: Alarm Exit Hysteresis (Time-Based)

### Anchor Rejected
- §5.1.14.4: Trim & Respond Logic General Operation | weak evidence_quote: lacks rule/action signal
- §5.1.15.5: Faulted Equipment Detection for Chillers | weak evidence_quote: lacks rule/action signal
- §5.1.15.5: Faulted Equipment Detection for Boilers | weak evidence_quote: lacks rule/action signal
- §5.1.15.5: Faulted Equipment Detection for Cooling Towers | weak evidence_quote: lacks rule/action signal
- §5.1.15.5: Response to Faulted Fan, Pump, or Cooling Tower | weak evidence_quote: lacks rule/action signal
- §5.1.15.5: Response to Faulted Chiller or Boiler | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.1.6: Proven ON/OFF Definition | unsupported: Evidence quote does not match the proven ON/OFF definition; unsupported extraction.
- §5.1.12.3: Alarm Exit Hysteresis (Percent-of-Limit-Based) | unsupported: Evidence quote is only a section heading; percent-of-limit hysteresis details not provided.
- §5.1.12.4: Alarm Latching Defaults | unsupported: Evidence quote is truncated and does not include the default latching statuses.
- §5.1.13.2: VFD Minimum Speed Synchronization | unsupported: Evidence quote is incomplete; minimum speed synchronization details are missing.
- §5.1.15.2: Runtime Points Definition | unsupported: Evidence quote is only a section heading; runtime points definition details are missing.
- §5.1.17.1: Economizer Disable Based on High Limit | unsupported: Evidence quote is incomplete; economizer disable details are missing.
- §5.1.19.4: SystemOK FALSE Conditions | unsupported: Evidence quote is truncated; full FALSE conditions not provided.
- §5.1.20.1: Time-Based Suppression Delay After Setpoint Change | unsupported: Evidence quote is incomplete; time-based suppression delay defaults are missing.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (80.5%)
- G3 focused section run produced at least one verified candidate: PASS (33)
- G4 extract wallclock <= configured limit: PASS (170.69s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
