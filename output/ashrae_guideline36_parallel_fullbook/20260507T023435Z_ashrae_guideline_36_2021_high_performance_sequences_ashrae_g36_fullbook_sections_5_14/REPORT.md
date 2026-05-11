# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T023435Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_14
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.14
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30684 |
| Extract calls | 1 |
| Extract input tokens | 31760 |
| Extract output tokens | 6527 |
| Judge calls | 1 |
| Judge total tokens | 5924 |
| Total cost | ¥0.0706 / ¥10.00 |
| Extract wallclock | 99.59s |
| Total wallclock | 159.65s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 25 |
| Anchor passed | 25 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 4 |
| Judge input | 21 |
| Judge accepted | 20 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | fault_diagnostic_rule: 5, operational_sequence: 15 |
| L4 / L3 | 18 / 2 |

## Samples

### Accepted
- p74, §5.14.6.1, fault_diagnostic_rule: Low Airflow Alarm - 70% of Setpoint
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests - High Deviation
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests - High Loop Signal
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests - Low Loop Signal
- p75, §5.14.8.1, operational_sequence: Cooling SAT Reset Requests - Moderate Deviation
- p75, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests - High Damper Position
- p75, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests - High Demand
- p75, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests - Low Damper Position
- p75, §5.14.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests - Moderate Demand
- p77, §5.14.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Zero Importance-Multiplier Zones
- p99, §5.14.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p99, §5.14.6.3, fault_diagnostic_rule: Leaking Damper Alarm
- p100, §5.14.8.3, operational_sequence: Heating SAT Reset Requests - High Deviation
- p100, §5.14.8.3, operational_sequence: Heating SAT Reset Requests - High Loop Signal
- p100, §5.14.8.3, operational_sequence: Heating SAT Reset Requests - Low Loop Signal

### Anchor Rejected
- §5.14.5.1: Dual-Duct VAV Zone Temperature and Damper Control - Cooling Mode | weak evidence_quote: section heading without supporting rule
- §5.14.5.1: Dual-Duct VAV Zone Temperature and Damper Control - Heating Mode | weak evidence_quote: section heading without supporting rule
- §5.14.5.2: Dual-Duct VAV Override Logic to Avoid Backflow | weak evidence_quote: section heading without supporting rule
- §5.14.7: Testing/Commissioning Overrides for Dual-Duct VAV | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
- §5.14.4: Endpoints as a Function of Zone Group Mode | unsupported: Summary provides detailed endpoint mappings not present in the quoted evidence; evidence only states endpoints vary by mode.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (95.2%)
- G3 focused section run produced at least one verified candidate: PASS (20)
- G4 extract wallclock <= configured limit: PASS (99.59s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
