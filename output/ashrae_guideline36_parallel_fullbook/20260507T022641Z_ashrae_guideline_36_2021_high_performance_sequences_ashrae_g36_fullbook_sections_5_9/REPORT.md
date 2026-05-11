# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T022641Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_9
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.9
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30592 |
| Extract calls | 1 |
| Extract input tokens | 31690 |
| Extract output tokens | 4429 |
| Judge calls | 1 |
| Judge total tokens | 4074 |
| Total cost | ¥0.0587 / ¥10.00 |
| Extract wallclock | 59.16s |
| Total wallclock | 101.34s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 14 |
| Anchor passed | 14 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 3 |
| Judge input | 11 |
| Judge accepted | 10 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | fault_diagnostic_rule: 6, operational_sequence: 4 |
| L4 / L3 | 10 / 0 |

## Samples

### Accepted
- p74, §5.9.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.9.6.5, fault_diagnostic_rule: Leaking Damper Alarm
- p75, §5.9.8.1, operational_sequence: Cooling SAT Reset Requests
- p77, §5.9.6.2, fault_diagnostic_rule: Low-Discharge Air Temperature Alarm
- p81, §5.9.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm
- p82, §5.9.6.3, fault_diagnostic_rule: Fan Alarm (Status Mismatch)
- p85, §5.9.5.2, operational_sequence: Deadband Mode Primary Airflow Setpoint
- p86, §5.9.6.6, fault_diagnostic_rule: Leaking Valve Alarm
- p89, §5.9.5.4, operational_sequence: VAV Damper Modulation to Maintain Airflow Setpoint
- p89, §5.9.5.5, operational_sequence: Fan Control Logic

### Anchor Rejected
- §5.9.5.1: Cooling Mode Primary Airflow Setpoint Mapping | weak evidence_quote: section heading without supporting rule
- §5.9.5.3: Heating Mode Primary Airflow and Discharge Temperature Control | weak evidence_quote: section heading without supporting rule
- §5.9.7: Testing/Commissioning Overrides | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
- §5.9.4: Endpoints as Function of Zone Group Mode | unsupported: Summary not supported by evidence; provided quote only mentions active endpoints vary, lacking specific mappings.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (90.9%)
- G3 focused section run produced at least one verified candidate: PASS (10)
- G4 extract wallclock <= configured limit: PASS (59.16s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
