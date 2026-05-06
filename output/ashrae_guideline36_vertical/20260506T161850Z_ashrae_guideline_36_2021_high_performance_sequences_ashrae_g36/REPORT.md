# ASHRAE Guideline 36 Vertical Run Report

**Run ID:** 20260506T161850Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Sections:** 5.2, 5.3, 5.17, 5.18, 5.19, 5.22
**Architecture:** bundle official-standard extraction + judge + verbatim chunk anchoring
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Extract input tokens | 27577 |
| Extract output tokens | 7852 |
| Judge total tokens | 15811 |
| Total cost | ¥0.1205 |
| Total wallclock | 414.14s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Extraction calls | 1 |
| Raw candidates | 21 |
| Anchor passed | 21 |
| Anchor rejected | 0 |
| Judge accepted | 19 |
| Judge rejected | 2 |
| Judge rejection breakdown | unsupported: 2 |
| Final by type | operational_sequence: 14, fault_diagnostic_rule: 5 |
| L4 / L3 | 0 / 19 |

## Section Coverage

- 5.2: covered
- 5.3: covered
- 5.17: covered
- 5.18: covered
- 5.19: covered
- 5.22: covered

## Samples

### Accepted
- p54, §5.2.1.3, operational_sequence: Zone Minimum Outdoor Air and Minimum Airflow Setpoints (ASHRAE 62.1)
- p66, §5.2.2.3, fault_diagnostic_rule: CO2 Sensor Calibration Alarm for TAV Zones
- p66, §5.2.2, operational_sequence: Time-Averaged Ventilation (TAV) for Zones
- p67, §5.3.2, operational_sequence: Zone Temperature Setpoint Adjustments and Limits
- p70, §5.3.6.1, fault_diagnostic_rule: Zone Temperature Alarms
- p70, §5.3.4, operational_sequence: Zone Control Loops and Zone State Determination
- p146, §5.17.1.2, operational_sequence: Dual-Fan Dual-Duct Heating VAV AHU Static Pressure Setpoint Reset
- p147, §5.17.2.2, operational_sequence: Dual-Fan Dual-Duct Heating VAV AHU Supply Air Temperature Setpoint Reset
- p150, §5.17.4.5, fault_diagnostic_rule: Dual-Fan Dual-Duct Heating VAV AHU AFDD Fault Conditions
- p154, §5.18.4, operational_sequence: SZVAV AHU Supply Fan Speed and SAT Setpoint Reset
- p156, §5.18.5.2, operational_sequence: SZVAV AHU Supply Air Temperature Control Loop Mapping
- p157, §5.18.6.2, operational_sequence: SZVAV AHU Minimum Outdoor Air Control without AFMS
- p162, §5.18.13.6, fault_diagnostic_rule: SZVAV AHU AFDD Fault Conditions
- p170, §5.18.15.1, operational_sequence: SZVAV AHU Chilled-Water Reset Requests
- p171, §5.19.1.1, operational_sequence: General Constant Speed Exhaust Fan Control

### Anchor Rejected
None

### Judge Rejected
- §5.2.1.4: Zone Minimum Outdoor Air and Minimum Airflow Setpoints (California Title 24) | unsupported: Section 5.2.1.4 has been deleted from Guideline 36, so this sequence is not part of the operational knowledge.
- §5.18.11: SZVAV AHU Freeze Protection Stages | unsupported: Evidence only supports stage 1 modulating action, not stage 2 closure for 1 hour or stage 3 shutdown.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 60%: PASS (90.5%)
- G3 every requested section has accepted knowledge: PASS ({'5.2': True, '5.3': True, '5.17': True, '5.18': True, '5.19': True, '5.22': True})
- G4 total_wallclock within scaled budget: PASS (414.14s / 900s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and whether each item should map to sw_base_model control/operation semantics.
