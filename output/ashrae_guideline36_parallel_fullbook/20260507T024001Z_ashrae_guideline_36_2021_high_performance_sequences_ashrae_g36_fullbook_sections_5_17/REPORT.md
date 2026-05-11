# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T024001Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_17
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.17
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31746 |
| Extract calls | 1 |
| Extract input tokens | 32856 |
| Extract output tokens | 5258 |
| Judge calls | 1 |
| Judge total tokens | 4708 |
| Total cost | ¥0.0645 / ¥10.00 |
| Extract wallclock | 79.66s |
| Total wallclock | 139.02s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 19 |
| Anchor passed | 19 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 17 |
| Judge accepted | 17 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 10, operational_sequence: 7 |
| L4 / L3 | 7 / 10 |

## Samples

### Accepted
- p134, §5.17.3.2, fault_diagnostic_rule: Fan Status Mismatch Alarm
- p145, §5.17.4.7, fault_diagnostic_rule: AFDD: Evaluation Suspension Conditions
- p145, §5.17.4.8, fault_diagnostic_rule: AFDD: Alarm Delay for Fault Reporting
- p145, §5.17.4.9, fault_diagnostic_rule: AFDD: Test Mode for Instant Testing
- p146, §5.17.1.1, operational_sequence: Supply Fan Start/Stop
- p146, §5.17.1.1, operational_sequence: Totalize Airflow from VAV Boxes
- p146, §5.17.1.2, operational_sequence: Static Pressure Setpoint Reset using T&R Logic
- p147, §5.17.2.1, operational_sequence: Supply Air Temperature Control Loop Enable/Disable
- p147, §5.17.2.2, operational_sequence: Supply Air Temperature Setpoint Reset during Occupied Mode
- p148, §5.17.3.1, fault_diagnostic_rule: Maintenance Interval Alarm
- p148, §5.17.3.3, fault_diagnostic_rule: Filter Pressure Drop Alarm
- p148, §5.17.2.2, operational_sequence: Supply Air Temperature Setpoint during Warmup and Setback Modes
- p148, §5.17.2.3, operational_sequence: Supply Air Temperature Control via PID Loop
- p150, §5.17.4.5, fault_diagnostic_rule: AFDD: Duct Static Pressure Too Low with Fan at Full Speed (FC#1)
- p150, §5.17.4.5, fault_diagnostic_rule: AFDD: SAT Too Low in Full Heating (FC#2)

### Anchor Rejected
- §5.17.1.3: Static Pressure Control | weak evidence_quote: section heading without supporting rule
- §5.17.5: Testing/Commissioning Overrides for Hot Water Valve | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (17)
- G4 extract wallclock <= configured limit: PASS (79.66s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
