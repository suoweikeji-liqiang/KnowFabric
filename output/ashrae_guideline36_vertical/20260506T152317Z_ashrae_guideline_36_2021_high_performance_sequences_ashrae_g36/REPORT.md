# ASHRAE Guideline 36 Vertical Run Report

**Run ID:** 20260506T152317Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Sections:** 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14
**Architecture:** section-level official-standard extraction + judge + verbatim chunk anchoring
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Extract input tokens | 21376 |
| Extract output tokens | 24620 |
| Judge total tokens | 61616 |
| Total cost | ¥0.3574 |
| Total wallclock | 1409.19s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Section extraction calls | 8 |
| Raw candidates | 81 |
| Anchor passed | 81 |
| Anchor rejected | 0 |
| Judge accepted | 77 |
| Judge rejected | 4 |
| Judge rejection breakdown | unsupported: 4 |
| Final by type | fault_diagnostic_rule: 36, operational_sequence: 34, commissioning_step: 7 |
| L4 / L3 | 55 / 22 |

## Section Coverage

- 5.7: covered
- 5.8: covered
- 5.9: covered
- 5.10: covered
- 5.11: covered
- 5.12: covered
- 5.13: covered
- 5.14: covered

## Samples

### Accepted
- p74, §5.10.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm
- p74, §5.10.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.10.6.5, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.11.6.1, fault_diagnostic_rule: Low Airflow Alarms
- p74, §5.12.6.1, fault_diagnostic_rule: Dual-Duct VAV Terminal Unit Low Airflow Alarm
- p74, §5.13.6.1, fault_diagnostic_rule: Low Airflow Alarms
- p74, §5.14.6.1, fault_diagnostic_rule: Dual-Duct VAV Low Airflow Alarm
- p74, §5.7.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm
- p74, §5.7.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.7.6.5, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.8.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm
- p74, §5.8.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.9.6.1, fault_diagnostic_rule: Low Primary Airflow Alarm
- p74, §5.9.6.4, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.9.6.5, fault_diagnostic_rule: Leaking Damper Alarm

### Anchor Rejected
None

### Judge Rejected
- §5.8.5: Parallel Fan-Powered Terminal Unit Control Logic | unsupported: Evidence is only a section heading overview, not the actual control sequence details; unsupported.
- §5.11.5.2: Snap-Acting Dual-Duct VAV Terminal Unit Control Logic (Single Discharge Sensor) | unsupported: Evidence does not support the summary; the provided snippet mentions runtime points unrelated to dual-duct control logic.
- §5.11.5.3: Overriding Logic to Avoid Backflow | unsupported: Evidence only supports heating damper interlock, not cooling damper interlock as stated in summary.
- §5.11.7: Testing/Commissioning Overrides | unsupported: Evidence does not support the summary; evidence references section 5.1.17 Air Economizer High Limits, not Testing/Commissioning Overrides.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 60%: PASS (95.1%)
- G3 every requested section has accepted knowledge: PASS ({'5.7': True, '5.8': True, '5.9': True, '5.10': True, '5.11': True, '5.12': True, '5.13': True, '5.14': True})
- G4 total_wallclock within scaled budget: PASS (1409.19s / 1820s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and whether each item should map to sw_base_model control/operation semantics.
