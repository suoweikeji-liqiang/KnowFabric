# ASHRAE Guideline 36 Full-Book Run Report

**Run ID:** 20260506T171812Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** single-call full-book extraction + single-call batch judge + verbatim chunk anchoring
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 196618 |
| Extract calls | 1 |
| Extract input tokens | 210307 |
| Extract output tokens | 29248 |
| Judge calls | 1 |
| Judge total tokens | 30334 |
| Total cost | ¥0.4080 / ¥30.00 |
| Extract wallclock | 445.93s |
| Total wallclock | 838.39s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 96 |
| Anchor passed | 96 |
| Anchor rejected | 0 |
| Judge accepted | 63 |
| Judge rejected | 33 |
| Judge rejection breakdown | unsupported: 33 |
| Final by type | operational_sequence: 47, fault_diagnostic_rule: 16 |
| L4 / L3 | 6 / 57 |

## Samples

### Accepted
- p172, §5.20.2.3, operational_sequence: Chiller Plant Disable Logic
- p175, §5.20.3.1, operational_sequence: Waterside Economizer Enable Logic
- p176, §5.20.3.2, operational_sequence: Waterside Economizer Disable Logic
- p182, §5.20.4.15, operational_sequence: Chiller Stage Down Condition
- p182, §5.20.4.15, operational_sequence: Chiller Stage Up Failsafe Condition (Parallel Plants)
- p200, §5.20.5.2, operational_sequence: Chilled Water Supply Temperature Reset via Trim & Respond
- p202, §5.20.6.2, operational_sequence: Primary CHW Pump Enable (Parallel Chillers, Headered Pumps, No WSE)
- p202, §5.20.6.3, operational_sequence: Primary CHW Pump Enable (Parallel Chillers, Headered Pumps, with WSE)
- p202, §5.20.6.4, operational_sequence: Primary CHW Pump Enable (Series Chillers, Headered Pumps, No WSE)
- p202, §5.20.6.5, operational_sequence: Primary CHW Pump Enable (Series Chillers, Headered Pumps, with WSE)
- p202, §5.20.6.6, operational_sequence: Primary CHW Pump Enable (Dedicated Pumps)
- p203, §5.20.6.11, operational_sequence: Primary CHW Pump Speed Control with Cascaded Local DP
- p203, §5.20.6.13, operational_sequence: Primary CHW Pump Staging with Chillers (Non-DP Controlled)
- p203, §5.20.6.8, operational_sequence: Primary CHW Pump DP Control (Hardwired Remote Sensor)
- p203, §5.20.6.9, operational_sequence: Primary CHW Pump DP Control with Multiple Sensors

### Anchor Rejected
None

### Judge Rejected
- §5.20.2.2: Chiller Plant Enable Logic | unsupported: Summary not supported by provided evidence (evidence only contains partial sentence)
- §5.20.2.4: Chiller Plant Enable with Waterside Economizer | unsupported: Evidence is only an editorial note to retain/delete section, not operational content
- §5.20.2.5: Chiller Plant Disable Sequence | unsupported: Evidence is only an editorial note, not supporting the operational summary
- §5.20.4.15: Chiller Stage Up Efficiency Condition | unsupported: Evidence only contains a fragmentary conditional, missing the detailed stage-up criteria
- §5.20.12.2: Condenser Water Return Temperature Control for Tower Fans | unsupported: Evidence only contains an incomplete conditional statement, not the CWRT control logic
- §5.20.12.2: Tower Fan Disable Logic | unsupported: Same incomplete evidence as previous; summary not supported
- §5.20.12.2: Tower Fan Enable Logic | unsupported: Same incomplete evidence; summary not supported
- §5.20.10.5: Head Pressure Control with Waterside Economizer (WSE Disabled) | unsupported: Evidence is only section heading, missing the detailed mapping
- §5.20.6.7: Primary CHW Pump Staging by Flow (Headered Variable Speed) | unsupported: Evidence only contains introductory phrase, missing staging formulas
- §5.20.6.10: Primary CHW Pump DP Control with Cascaded Remote Sensor | unsupported: Evidence is only section heading, missing remote DP setpoint reset details

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (65.6%)
- G3 L4 count > 0: PASS (6)
- G4 extract wallclock <= configured limit: PASS (445.93s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
