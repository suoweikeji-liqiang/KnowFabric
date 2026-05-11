# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T230740Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_1
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
| Extract output tokens | 14792 |
| Judge calls | 1 |
| Judge total tokens | 12526 |
| Total cost | ¥0.2262 / ¥10.00 |
| Extract wallclock | 417.05s |
| Total wallclock | 503.83s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 49 |
| Anchor passed | 46 |
| Anchor rejected | 3 |
| Weak evidence rejected before judge | 1 |
| Judge input | 45 |
| Judge accepted | 45 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 3, operational_sequence: 22, parameter_spec: 16, fault_diagnostic_rule: 4 |
| L4 / L3 | 5 / 40 |

## Samples

### Accepted
- p43, §5.1.8.1, application_guidance: Use Proportional-Only Loops for Limiting Loops
- p43, §5.1.8.2, application_guidance: Avoid Derivative Term in Control Loops
- p43, §5.1.2, operational_sequence: Control Loop Enable/Disable Based on System Status
- p43, §5.1.3, operational_sequence: Control Loop Initialization to Neutral Value
- p43, §5.1.4, operational_sequence: Neutral Control Loop Corresponds to Minimum Control Effect
- p43, §5.1.5, operational_sequence: Outdoor Air Temperature Sensor Selection
- p43, §5.1.5.1, operational_sequence: Validity of Outdoor Air Temperature Sensors at Air-Handler Intakes
- p43, §5.1.5.2, operational_sequence: Outdoor Air Temperature Averaging for Global Sequences
- p43, §5.1.10, parameter_spec: Adjustability of Setpoints, Timers, Deadbands, PID Gains
- p43, §5.1.11, parameter_spec: Override Capability for All Points
- p43, §5.1.6, parameter_spec: Definition of 'Proven' Status
- p43, §5.1.7, parameter_spec: Definition of Software Point and Software Switch
- p43, §5.1.9, parameter_spec: Maximum Rate of Change for Control Loop Output
- p44, §5.1.12.2, operational_sequence: Maintenance Mode Alarm Suppression
- p44, §5.1.12.1, parameter_spec: Alarm Levels Definition

### Anchor Rejected
- §5.1.15.5.b.1.iv: Cooling Tower Fault Conditions | evidence_quote not verbatim in any chunk
- §5.1.15.5.b.2.ii: Fault Response for Chillers and Boilers | evidence_quote not verbatim in any chunk
- §5.1.15.5.c: Hand Operation Detection and Response | evidence_quote not verbatim in any chunk
- §5.1.15.4: Lead/Standby Alternation for Redundant Equipment | weak evidence_quote: too short to support structured summary

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (93.9%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (45)
- G4 extract wallclock <= configured limit: PASS (417.05s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
