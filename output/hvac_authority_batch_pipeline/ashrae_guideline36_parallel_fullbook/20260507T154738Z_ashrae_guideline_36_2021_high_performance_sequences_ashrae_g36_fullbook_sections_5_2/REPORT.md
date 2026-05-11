# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T154738Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_2
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
| Extract output tokens | 19661 |
| Judge calls | 1 |
| Judge total tokens | 5665 |
| Total cost | ¥0.2443 / ¥10.00 |
| Extract wallclock | 571.42s |
| Total wallclock | 639.66s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 22 |
| Anchor passed | 16 |
| Anchor rejected | 6 |
| Weak evidence rejected before judge | 1 |
| Judge input | 15 |
| Judge accepted | 15 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 2, parameter_spec: 2, operational_sequence: 9, fault_diagnostic_rule: 2 |
| L4 / L3 | 2 / 13 |

## Samples

### Accepted
- p7, §5.2.1.3.f.3, application_guidance: Occupied-Standby Mode Classification
- p59, §5.2, application_guidance: Selection Between ASHRAE 62.1 and Title 24 Ventilation Logic
- p59, §5.2.1.3.c, parameter_spec: Normal Population and Area Ventilation Components
- p60, §5.2.1.3.e, operational_sequence: Occupied Minimum Airflow Setpoint Vmin*
- p60, §5.2.1.3.f, operational_sequence: Zone Outdoor Airflow Voz Calculation and Override Priorities (ASHRAE 62.1)
- p60, §5.2.1.3.f.4.ii-iii, operational_sequence: CO2 Demand Controlled Ventilation Loop (P-only) for Zones
- p60, §5.2.1.3.f.4.iv.(a), operational_sequence: CO2 DCV Reset of Vmin* and Vbz-P* for Cooling-Only, Reheat, Series Fan-Powered, and Dual-Duct VAV Terminal Units
- p62, §5.2.1.3.f.4.vi.(a), operational_sequence: CO2 DCV Reset of Vbz-P* for SZVAV AHUs (ASHRAE 62.1)
- p63, §5.2.1.4.c, operational_sequence: Vmin Calculation (Title 24)
- p63, §5.2.1.4.b.2, parameter_spec: Zone-Des-OA-min Determination (Title 24)
- p65, §5.2.1.4.d.3.vi, operational_sequence: SZVAV MinOAsp Reset (Title 24)
- p66, §5.2.2.3.a, fault_diagnostic_rule: CO2 Sensor Low Reading or Unoccupied Elevated CO2 Alarm
- p66, §5.2.2.3.b, fault_diagnostic_rule: CO2 Concentration Exceeds Setpoint Alarm
- p66, §5.2.2.1, operational_sequence: Time-Averaged Ventilation Mode Entry and Pulse Width Modulation
- p66, §5.2.2.2, operational_sequence: TAV Mode Override of Vspt

### Anchor Rejected
- §5.2.1.3.d: Vmin Calculation with 100% Outdoor Air Detection | evidence_quote not verbatim in any chunk
- §5.2.1.3.f.4.v: CO2 DCV Reset of Vmin* and Vbz-P* for Parallel Fan-Powered Terminal Units | evidence_quote not verbatim in any chunk
- §5.2.1.4.b.1: Zone-Abs-OA-min Reset Priorities (Title 24) | evidence_quote not verbatim in any chunk
- §5.2.1.4.d: Occupied Minimum Airflow Vmin* with Overrides (Title 24) | evidence_quote not verbatim in any chunk
- §5.2.1.4.d.3.ii-iv.(a): CO2 DCV Loop and Vmin* Reset for Standard Terminal Units (Title 24) | evidence_quote not verbatim in any chunk
- §5.2.1.4.d.3.v: CO2 DCV Reset for Parallel Fan-Powered Terminal Units (Title 24) | evidence_quote not verbatim in any chunk
- §5.2.1.3.b: Zone Air Distribution Effectiveness Ez Determination (ASHRAE 62.1) | weak evidence_quote: too short to support structured summary

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: FAIL (72.7%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (15)
- G4 extract wallclock <= configured limit: PASS (571.42s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
