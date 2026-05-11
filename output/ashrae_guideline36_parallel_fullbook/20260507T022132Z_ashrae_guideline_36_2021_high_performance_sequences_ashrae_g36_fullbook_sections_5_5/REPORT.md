# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T022132Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_5
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.5
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30098 |
| Extract calls | 1 |
| Extract input tokens | 31094 |
| Extract output tokens | 3780 |
| Judge calls | 1 |
| Judge total tokens | 4641 |
| Total cost | ¥0.0605 / ¥10.00 |
| Extract wallclock | 53.02s |
| Total wallclock | 138.15s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 14 |
| Anchor passed | 14 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 13 |
| Judge accepted | 12 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | application_guidance: 3, fault_diagnostic_rule: 5, operational_sequence: 4 |
| L4 / L3 | 6 / 6 |

## Samples

### Accepted
- p73, §5.5.3, application_guidance: DCV Not Provided for Cooling-Only Boxes Due to Overcooling Risk
- p73, §5.5.3, application_guidance: Heating Capability Condition for Cooling-Only Terminal Units
- p73, §5.5.3, application_guidance: Recommendation to Use Reheat Box When Minimum Ventilation Rate Exceeds 25% of Cooling Maximum or DCV is Used
- p74, §5.5.6.1.a, fault_diagnostic_rule: Low Airflow Alarm (70% of Setpoint for 10 Minutes)
- p74, §5.5.6.1.b, fault_diagnostic_rule: Low Airflow Alarm (50% of Setpoint for 10 Minutes)
- p74, §5.5.6.1.c, fault_diagnostic_rule: Low Airflow Alarm Suppression for Zero Importance Multiplier Zones
- p74, §5.5.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.5.6.3, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.5.5.1, operational_sequence: Cooling-Only VAV Zone State to Active Airflow Setpoint Mapping
- p74, §5.5.5.2, operational_sequence: Cooling-Only VAV Zone Deadband Active Airflow Setpoint
- p74, §5.5.5.3, operational_sequence: Cooling-Only VAV Zone Heating Active Airflow Setpoint Mapping
- p74, §5.5.5.4, operational_sequence: Cooling-Only VAV Damper Modulation to Maintain Active Airflow Setpoint

### Anchor Rejected
- §5.5.7: Testing/Commissioning Overrides for Cooling-Only VAV Box | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
- §5.5.4: Active Endpoints as Function of Zone Group Mode for Cooling-Only VAV | unsupported: Summary provides specific endpoint mappings not supported by truncated evidence quote.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (92.3%)
- G3 focused section run produced at least one verified candidate: PASS (12)
- G4 extract wallclock <= configured limit: PASS (53.02s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
