# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T235659Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_21
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.21
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 47600 |
| Extract calls | 1 |
| Extract input tokens | 47969 |
| Extract output tokens | 37861 |
| Judge calls | 1 |
| Judge total tokens | 21736 |
| Total cost | ¥0.4511 / ¥10.00 |
| Extract wallclock | 903.02s |
| Total wallclock | 1044.08s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 80 |
| Anchor passed | 78 |
| Anchor rejected | 2 |
| Weak evidence rejected before judge | 1 |
| Judge input | 77 |
| Judge accepted | 77 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 75, parameter_spec: 2 |
| L4 / L3 | 22 / 55 |

## Samples

### Accepted
- p219, §5.21.9.1, operational_sequence: Performance Monitoring Calculation Frequency
- p235, §5.21.2.1, operational_sequence: Boiler Plant Enable/Disable Schedule
- p235, §5.21.2.2, operational_sequence: Boiler Plant Enable Conditions
- p235, §5.21.2.3, operational_sequence: Boiler Plant Disable Conditions
- p236, §5.21.2.4, operational_sequence: Plant Enable Actions for Headered Primary HW Pumps
- p236, §5.21.2.4, operational_sequence: Plant Enable Actions for Primary-Only Plants
- p236, §5.21.2.5, operational_sequence: Plant Disable Actions
- p236, §5.21.3.1, operational_sequence: Boiler Stage Definition
- p237, §5.21.3.2, operational_sequence: Lead/Lag Control for Interchangeable Boilers
- p237, §5.21.3.3, operational_sequence: Boiler Alarm Response with Headered Pumps and Isolation Valves
- p237, §5.21.3.4, operational_sequence: Boiler Alarm Response with Dedicated Primary Pumps
- p237, §5.21.3.5, operational_sequence: Qrequired Calculation for Primary-Only and Primary-Secondary without Secondary Flow Meters
- p237, §5.21.3.6, operational_sequence: Qrequired Calculation for Primary-Secondary with Flow Meters in All Secondary Loops
- p237, §5.21.3.7, operational_sequence: B-STAGE MIN Calculation for Condensing Boilers
- p237, §5.21.3.8, operational_sequence: Stage Availability Definition

### Anchor Rejected
- §5.21.3.9.j: Non-Condensing Boiler Stage Up Conditions | evidence_quote not verbatim in any chunk
- §5.21.3.9.n: Hybrid Plant Non-Condensing Boiler Stage Up Conditions | evidence_quote not verbatim in any chunk
- §5.21.7.3: Secondary HW Pump Staging on Flow | weak evidence_quote: introductory fragment without complete rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (97.5%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (77)
- G4 extract wallclock <= configured limit: PASS (903.02s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
