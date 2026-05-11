# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T022235Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_6
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.6
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31182 |
| Extract calls | 1 |
| Extract input tokens | 32305 |
| Extract output tokens | 5707 |
| Judge calls | 1 |
| Judge total tokens | 6352 |
| Total cost | ¥0.0729 / ¥10.00 |
| Extract wallclock | 74.66s |
| Total wallclock | 164.59s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 19 |
| Anchor passed | 19 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 17 |
| Judge accepted | 16 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | fault_diagnostic_rule: 9, operational_sequence: 7 |
| L4 / L3 | 12 / 4 |

## Samples

### Accepted
- p74, §5.6.6.1, fault_diagnostic_rule: Low Airflow Alarm Level 3
- p74, §5.6.6.1, fault_diagnostic_rule: Low Airflow Alarm Level 4
- p74, §5.6.6.3, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.6.6.4, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.6.5.5, operational_sequence: VAV Damper Modulation to Maintain Measured Airflow at Active Setpoint
- p75, §5.6.8.1, operational_sequence: Cooling SAT Reset Requests from Zone
- p76, §5.6.5.1, operational_sequence: Zone State Cooling Airflow Setpoint and Heating Coil Control
- p76, §5.6.5.2, operational_sequence: Zone State Deadband Airflow Setpoint and Heating Coil Control
- p77, §5.6.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Importance-Multiplier 0 Zones
- p77, §5.6.6.2, fault_diagnostic_rule: Low-DAT Alarm Suppression for Importance-Multiplier 0 Zones
- p77, §5.6.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm Level 3
- p77, §5.6.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm Level 4
- p77, §5.6.5.3, operational_sequence: Heating Coil Disabled During Pulse-Width Modulated Closed Periods
- p77, §5.6.5.4, operational_sequence: Heating Coil Minimum Discharge Air Temperature in Occupied Mode
- p78, §5.6.6.5, fault_diagnostic_rule: Leaking Valve Alarm

### Anchor Rejected
- §5.6.7: Testing/Commissioning Overrides for VAV Reheat Zone | weak evidence_quote: commissioning evidence lacks procedure/check action
- §5.6.4: Endpoints as a Function of Zone Group Mode | weak evidence_quote: section heading without supporting rule

### Judge Rejected
- §5.6.5.3: Zone State Heating Sequence with Discharge Air Temperature Reset and Airflow Increase | unsupported: Summary describes a complex sequence, but evidence quote is incomplete and does not support the detailed mapping.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (94.1%)
- G3 focused section run produced at least one verified candidate: PASS (16)
- G4 extract wallclock <= configured limit: PASS (74.66s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
