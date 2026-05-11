# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T183143Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_2
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.2
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 32783 |
| Extract calls | 1 |
| Extract input tokens | 34130 |
| Extract output tokens | 23833 |
| Judge calls | 1 |
| Judge total tokens | 5244 |
| Total cost | ¥0.2687 / ¥10.00 |
| Extract wallclock | 552.00s |
| Total wallclock | 626.26s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 20 |
| Anchor passed | 14 |
| Anchor rejected | 6 |
| Weak evidence rejected before judge | 1 |
| Judge input | 13 |
| Judge accepted | 13 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 1, parameter_spec: 3, operational_sequence: 8, fault_diagnostic_rule: 1 |
| L4 / L3 | 1 / 12 |

## Samples

### Accepted
- p59, §5.2.1, application_guidance: Selection Between Ventilation Compliance Standards
- p59, §5.2.1.3.b.1, parameter_spec: Default EzC Value
- p59, §5.2.1.3.b.2, parameter_spec: Default EzH Value
- p60, §5.2.1.3.f, operational_sequence: Zone Outdoor Airflow Calculation and Priority Overrides (ASHRAE 62.1)
- p60, §5.2.1.3.f.4.ii-iii, operational_sequence: CO2 Demand Controlled Ventilation Loop (ASHRAE 62.1)
- p60, §5.2.1.3.f.4.iv, operational_sequence: CO2 DCV Reset for Cooling-Only/Reheat/Series Fan/Dual-Duct Terminal Units (ASHRAE 62.1)
- p63, §5.2.1.4.c, operational_sequence: Zone Minimum Airflow Vmin Calculation (Title 24)
- p64, §5.2.1.4.d.3.iv, operational_sequence: CO2 DCV Reset for Cooling-Only/Reheat/Series Fan/Dual-Duct Under Title 24
- p65, §5.2.1.4.d.3.vi, operational_sequence: CO2 DCV Reset for SZVAV Under Title 24
- p66, §5.2.2.3, fault_diagnostic_rule: CO2 Sensor Fault Detection Alarms
- p66, §5.2.2.1, operational_sequence: Time-Averaged Ventilation (TAV) Pulse Width Modulation Sequence
- p66, §5.2.2.2, operational_sequence: Active Airflow Setpoint Override in TAV Mode
- p66, §5.2.2.1.b, parameter_spec: Time-Averaged Ventilation Cycle Time Default

### Anchor Rejected
- §5.2.1.3.d: Zone Minimum Airflow Vmin Calculation (ASHRAE 62.1) | evidence_quote not verbatim in any chunk
- §5.2.1.3.f.4.v: CO2 DCV Reset for Parallel Fan-Powered Terminal Units (ASHRAE 62.1) | evidence_quote not verbatim in any chunk
- §5.2.1.3.f.4.vi: CO2 DCV Reset for Single-Zone VAV AHUs (ASHRAE 62.1) | evidence_quote not verbatim in any chunk
- §5.2.1.4.b: Zone Minimum Outdoor Air Setpoints Calculation (California Title 24) | evidence_quote not verbatim in any chunk
- §5.2.1.4.d.1-2: Occupied Minimum Airflow Override Priorities (Title 24) | evidence_quote not verbatim in any chunk
- §5.2.1.4.d.3.v: CO2 DCV Reset for Parallel Fan-Powered Under Title 24 | evidence_quote not verbatim in any chunk
- §5.2.1.3.b: Zone Air Distribution Effectiveness Determination (ASHRAE 62.1) | weak evidence_quote: too short to support structured summary

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: FAIL (70.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (13)
- G4 extract wallclock <= configured limit: PASS (552.00s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
