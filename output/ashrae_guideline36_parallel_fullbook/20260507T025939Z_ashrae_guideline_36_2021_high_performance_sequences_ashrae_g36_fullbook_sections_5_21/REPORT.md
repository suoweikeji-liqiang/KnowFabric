# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T025939Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_21
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.21
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 47600 |
| Extract calls | 1 |
| Extract input tokens | 47933 |
| Extract output tokens | 26219 |
| Judge calls | 1 |
| Judge total tokens | 28744 |
| Total cost | ¥0.2377 / ¥10.00 |
| Extract wallclock | 400.97s |
| Total wallclock | 784.33s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 92 |
| Anchor passed | 87 |
| Anchor rejected | 5 |
| Weak evidence rejected before judge | 7 |
| Judge input | 80 |
| Judge accepted | 65 |
| Judge rejected | 15 |
| Judge rejection breakdown | unsupported: 15 |
| Final by type | operational_sequence: 48, fault_diagnostic_rule: 17 |
| L4 / L3 | 9 / 56 |

## Samples

### Accepted
- p176, §5.21.6.14, operational_sequence: Primary Hot Water Pumps - Temperature-Based Request Generation
- p221, §5.21.10.1, fault_diagnostic_rule: Alarm - Pump Maintenance Interval
- p222, §5.21.10.7, fault_diagnostic_rule: Alarm - Modulating Valve Position Mismatch
- p235, §5.21.2.2, operational_sequence: Plant Enable/Disable - Enable Logic
- p235, §5.21.2.3, operational_sequence: Plant Enable/Disable - Disable Logic
- p236, §5.21.2.4, operational_sequence: Plant Enable - Lead Boiler and Pump Staging
- p236, §5.21.2.5, operational_sequence: Plant Disable - Shutdown Sequence
- p236, §5.21.3.1, operational_sequence: Boiler Staging - Stage Definition
- p237, §5.21.3.2, operational_sequence: Boiler Staging - Lead/Lag for Interchangeable Boilers
- p237, §5.21.3.3, operational_sequence: Boiler Staging - Alarm Response for Headered Pumps
- p237, §5.21.3.4, operational_sequence: Boiler Staging - Alarm Response for Dedicated Pumps
- p237, §5.21.3.7, operational_sequence: Boiler Staging - B-STAGE MIN Calculation
- p237, §5.21.3.8, operational_sequence: Boiler Staging - Stage Availability
- p238, §5.21.3.9.g, operational_sequence: Boiler Staging - Primary Only Condensing: Stage Down
- p239, §5.21.3.9.i, operational_sequence: Boiler Staging - Variable Primary/Variable Secondary Condensing: Stage Down

### Anchor Rejected
- §5.21.3.9.f: Boiler Staging - Primary Only Condensing: Stage Up | evidence_quote not verbatim in any chunk
- §5.21.3.9.j: Boiler Staging - Non-Condensing: Stage Up | evidence_quote not verbatim in any chunk
- §5.21.3.9.n: Boiler Staging - Hybrid: Stage Up to Non-Condensing Stage | evidence_quote not verbatim in any chunk
- §5.21.3.10.g: Lag Boiler Enable - Pony Boiler Transition | evidence_quote not verbatim in any chunk
- §5.21.3.11.a: Lag Boiler Disable - Pony Boiler Transition | evidence_quote not verbatim in any chunk
- §5.21.3.12: Hybrid - Enable Lag Condensing Boiler | weak evidence_quote: lacks rule/action signal
- §5.21.3.17: Hybrid - Disable Lag Condensing Boiler | weak evidence_quote: lacks rule/action signal
- §5.21.7.3: Secondary Hot Water Pumps - Staging by Flow Ratio | weak evidence_quote: introductory fragment without complete rule
- §5.21.8.1: Minimum Flow Bypass Valve - Setpoint Calculation | weak evidence_quote: section heading without supporting rule
- §5.21.11.6: AFDD - FC#12: Too Many Operating State Changes | weak evidence_quote: fault evidence lacks the specific FC item

### Judge Rejected
- §5.21.3.5: Boiler Staging - Qrequired Calculation (Primary Flow) | unsupported: Summary of Qrequired calculation not supported by provided evidence (heading only)
- §5.21.3.6: Boiler Staging - Qrequired Calculation (Secondary Flow) | unsupported: Summary of Qrequired calculation not supported by provided evidence (heading only)
- §5.21.3.9: Boiler Staging - General Staging Requirements | unsupported: Summary of staging requirements not supported by evidence (heading only)
- §5.21.3.10: Lag Boiler Enable - General Sequence | unsupported: Summary of lag boiler enable sequence not supported by evidence (heading only)
- §5.21.3.11: Lag Boiler Disable - General Sequence | unsupported: Summary of lag boiler disable sequence not supported by evidence (heading only)
- §5.21.3.13: Hybrid - Enable First Non-Condensing Boiler | unsupported: Summary of enabling first non-condensing boiler not supported by evidence (heading only)
- §5.21.3.14: Hybrid - Enable Other Non-Condensing Boiler | unsupported: Summary of enabling other non-condensing boilers not supported by evidence (heading only)
- §5.21.3.15: Hybrid - Disable Non-Lead Non-Condensing Boiler | unsupported: Summary of disabling non-lead non-condensing boilers not supported by evidence (heading only)
- §5.21.3.16: Hybrid - Disable Lead Non-Condensing Boiler | unsupported: Summary of disabling lead non-condensing boiler not supported by evidence (heading only)
- §5.21.5.4: Non-Condensing Boiler Condensation Control - Enable/Disable Secondary Pump Speed Loop | unsupported: Summary of enable/disable conditions not fully supported by evidence (cut off)

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (94.6%)
- G2 judge_acceptance_rate >= 50%: PASS (81.2%)
- G3 focused section run produced at least one verified candidate: PASS (65)
- G4 extract wallclock <= configured limit: PASS (400.97s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
