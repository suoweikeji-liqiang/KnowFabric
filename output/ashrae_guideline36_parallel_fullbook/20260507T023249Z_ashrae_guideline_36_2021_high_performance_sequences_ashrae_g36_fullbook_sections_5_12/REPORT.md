# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T023249Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_12
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.12
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 30856 |
| Extract calls | 1 |
| Extract input tokens | 31928 |
| Extract output tokens | 8787 |
| Judge calls | 1 |
| Judge total tokens | 7498 |
| Total cost | ¥0.0816 / ¥10.00 |
| Extract wallclock | 128.57s |
| Total wallclock | 212.29s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 36 |
| Anchor passed | 36 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 8 |
| Judge input | 28 |
| Judge accepted | 28 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | fault_diagnostic_rule: 5, operational_sequence: 23 |
| L4 / L3 | 24 / 4 |

## Samples

### Accepted
- p74, §5.12.6.1, fault_diagnostic_rule: Low Airflow Alarm - 70% of Setpoint
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request - 0 Requests
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request - 1 Request
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request - 2 Requests
- p75, §5.12.8.1, operational_sequence: Cooling SAT Reset Request - 3 Requests
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request - 0 Requests
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request - 1 Request
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request - 2 Requests
- p75, §5.12.8.2, operational_sequence: Cold-Duct Static Pressure Reset Request - 3 Requests
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request - 0 Requests
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request - 1 Request
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request - 2 Requests
- p75, §5.12.8.4, operational_sequence: Hot-Duct Static Pressure Reset Request - 3 Requests
- p77, §5.12.6.1, fault_diagnostic_rule: Low Airflow Alarm Suppression for Importance-Multiplier 0
- p98, §5.12.5.2, operational_sequence: Override Logic - Cooling Fan Not Proven

### Anchor Rejected
- §5.12.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Zero | weak evidence_quote: commissioning evidence lacks procedure/check action
- §5.12.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Vcool-max | weak evidence_quote: lacks rule/action signal
- §5.12.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Vmin | weak evidence_quote: lacks rule/action signal
- §5.12.7: Testing/Commissioning Overrides - Force Zone Airflow Setpoint to Vheat-max | weak evidence_quote: lacks rule/action signal
- §5.12.7: Testing/Commissioning Overrides - Force Cooling Damper Full Closed/Open | weak evidence_quote: lacks rule/action signal
- §5.12.7: Testing/Commissioning Overrides - Force Heating Damper Full Closed/Open | weak evidence_quote: lacks rule/action signal
- §5.12.7: Testing/Commissioning Overrides - Reset Request-Hours Accumulator | weak evidence_quote: lacks rule/action signal
- §5.12.4: Endpoints as a Function of Zone Group Mode | weak evidence_quote: section heading without supporting rule

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (28)
- G4 extract wallclock <= configured limit: PASS (128.57s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
