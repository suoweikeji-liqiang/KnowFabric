# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T022916Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_11
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.11
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 31283 |
| Extract calls | 1 |
| Extract input tokens | 32350 |
| Extract output tokens | 4492 |
| Judge calls | 1 |
| Judge total tokens | 4815 |
| Total cost | ¥0.0637 / ¥10.00 |
| Extract wallclock | 60.59s |
| Total wallclock | 130.76s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 12 |
| Anchor passed | 12 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 1 |
| Judge input | 11 |
| Judge accepted | 7 |
| Judge rejected | 4 |
| Judge rejection breakdown | unsupported: 4 |
| Final by type | operational_sequence: 4, fault_diagnostic_rule: 3 |
| L4 / L3 | 6 / 1 |

## Samples

### Accepted
- p75, §5.11.8.1, operational_sequence: Cooling SAT Reset Requests from Dual-Duct VAV Zone
- p81, §5.11.6.1, fault_diagnostic_rule: Low Airflow Alarm
- p91, §5.11.8.2, operational_sequence: Cold-Duct Static Pressure Reset Requests from Dual-Duct VAV Zone
- p98, §5.11.5.1, operational_sequence: Hot-Deck Supply Air Temperature Override for Heating Mode
- p98, §5.11.5.3, operational_sequence: Overriding Logic to Avoid Backflow
- p99, §5.11.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p99, §5.11.6.3, fault_diagnostic_rule: Leaking Damper Alarm

### Anchor Rejected
- §5.11.7: Testing/Commissioning Overrides for Dual-Duct VAV Zone | weak evidence_quote: commissioning evidence lacks procedure/check action

### Judge Rejected
- §5.11.5.1: Dual-Duct VAV Zone Control Logic with Dual Inlet Airflow Sensors | unsupported: Evidence quote does not match summary
- §5.11.5.2: Dual-Duct VAV Zone Control Logic with Single Discharge Airflow Sensor | unsupported: Evidence quote does not match summary
- §5.11.5.1: Cold-Deck Supply Air Temperature Override for Cooling Mode | unsupported: Evidence quote does not match summary
- §5.11.4: Endpoints as a Function of Zone Group Mode | unsupported: Evidence quote does not match summary

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (63.6%)
- G3 focused section run produced at least one verified candidate: PASS (7)
- G4 extract wallclock <= configured limit: PASS (60.59s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
