# ASHRAE Guideline 36 Vertical Run Report

**Run ID:** 20260506T130150Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Sections:** 5.4, 5.5, 5.6, 5.15, 5.16
**Architecture:** section-level official-standard extraction + judge + verbatim chunk anchoring
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Extract input tokens | 53842 |
| Extract output tokens | 15799 |
| Judge total tokens | 34580 |
| Total cost | ¥0.2487 |
| Total wallclock | 839.87s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Section extraction calls | 5 |
| Raw candidates | 46 |
| Anchor passed | 46 |
| Anchor rejected | 0 |
| Judge accepted | 42 |
| Judge rejected | 2 |
| Judge rejection breakdown | unsupported: 2 |
| Final by type | commissioning_procedure: 4, operational_sequence: 23, parameter_spec: 2, fault_diagnostic_rule: 13 |
| L4 / L3 | 12 / 30 |

## Section Coverage

- 5.4: covered
- 5.5: covered
- 5.6: covered
- 5.15: covered
- 5.16: covered

## Samples

### Accepted
- p71, §5.4.5, commissioning_procedure: Zone Group Testing/Commissioning Override Switches
- p71, §5.4.1, operational_sequence: Zone Group Definition and Mode Synchronization
- p71, §5.4.6.1, operational_sequence: Zone Group Occupied Mode Conditions
- p73, §5.5.4, parameter_spec: Active Airflow Setpoint Endpoints by Zone Group Mode
- p74, §5.5.7, commissioning_procedure: Testing/Commissioning Overrides for Cooling-Only VAV
- p74, §5.5.6.1, fault_diagnostic_rule: Low Airflow Alarm
- p74, §5.5.6.2, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.5.6.3, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.6.6.1, fault_diagnostic_rule: Low Airflow Alarm
- p74, §5.6.6.3, fault_diagnostic_rule: Airflow Sensor Calibration Alarm
- p74, §5.6.6.4, fault_diagnostic_rule: Leaking Damper Alarm
- p74, §5.5.5, operational_sequence: Cooling-Only VAV Zone Control Logic
- p75, §5.6.8.1, operational_sequence: System Requests for Cooling SAT Reset
- p75, §5.6.8.2, operational_sequence: System Requests for Static Pressure Reset
- p75, §5.6.4, parameter_spec: Endpoints as Function of Zone Group Mode

### Anchor Rejected
None

### Judge Rejected
- §5.16.1.1: Supply Fan Start/Stop | unsupported: Evidence does not support the summary; it discusses S-R-DIFF airflow differential, not fan start/stop modes.
- §5.16.9.7: Relief Fan Control - Staging | unsupported: Evidence does not support the staging thresholds and timers described in the summary.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 60%: PASS (91.3%)
- G3 every requested section has accepted knowledge: PASS ({'5.4': True, '5.5': True, '5.6': True, '5.15': True, '5.16': True})
- G4 total_wallclock < 900s: PASS (839.87s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and whether each item should map to sw_base_model control/operation semantics.
