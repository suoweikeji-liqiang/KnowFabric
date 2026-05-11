# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T230703Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_5
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.5
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30098 |
| Extract calls | 1 |
| Extract input tokens | 31130 |
| Extract output tokens | 3785 |
| Judge calls | 1 |
| Judge total tokens | 3425 |
| Total cost | ¥0.1291 / ¥10.00 |
| Extract wallclock | 92.23s |
| Total wallclock | 119.46s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 13 |
| Anchor passed | 13 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 0 |
| Judge input | 13 |
| Judge accepted | 13 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | application_guidance: 2, parameter_spec: 1, commissioning_step: 1, fault_diagnostic_rule: 5, operational_sequence: 4 |
| L4 / L3 | 6 / 7 |

## Samples

### Accepted
- p73, §5.5.3, application_guidance: Cooling-only terminal units can provide heating only when AHU supply air temperature is more than 3°C (5°F) above room temperature
- p73, §5.5.3, application_guidance: Recommendation for reheat box when minimum ventilation rate is high or DCV is used
- p73, §5.5.4, parameter_spec: Active endpoints as a function of Zone Group mode for cooling-only VAV terminal unit
- p74, §5.5.7, commissioning_step: Testing/commissioning overrides for cooling-only VAV terminal unit
- p74, §5.5.6.1, fault_diagnostic_rule: Low airflow alarm at 50% of setpoint for 10 minutes
- p74, §5.5.6.1, fault_diagnostic_rule: Low airflow alarm at 70% of setpoint for 10 minutes
- p74, §5.5.6.1, fault_diagnostic_rule: Suppression of low airflow alarms for zones with importance multiplier of 0
- p74, §5.5.6.2, fault_diagnostic_rule: Airflow sensor calibration alarm
- p74, §5.5.6.3, fault_diagnostic_rule: Leaking damper alarm
- p74, §5.5.5.1, operational_sequence: Cooling-only VAV terminal unit airflow setpoint mapping in cooling state
- p74, §5.5.5.2, operational_sequence: Cooling-only VAV terminal unit airflow setpoint in deadband state
- p74, §5.5.5.3, operational_sequence: Cooling-only VAV terminal unit airflow setpoint mapping in heating state
- p74, §5.5.5.4, operational_sequence: VAV damper modulation to maintain measured airflow at active setpoint

### Anchor Rejected
None

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (13)
- G4 extract wallclock <= configured limit: PASS (92.23s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
