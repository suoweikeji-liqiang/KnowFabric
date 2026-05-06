# ASHRAE Guideline 36 Vertical Run Report

**Run ID:** 20260506T101446Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Sections:** 5.1.14, 5.20, 5.21
**Architecture:** section-level official-standard extraction + judge + verbatim chunk anchoring
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Extract input tokens | 66937 |
| Extract output tokens | 19830 |
| Judge total tokens | 17891 |
| Total cost | ¥0.1927 |
| Total wallclock | 617.23s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Section extraction calls | 3 |
| Raw candidates | 29 |
| Anchor passed | 24 |
| Anchor rejected | 5 |
| Judge accepted | 22 |
| Judge rejected | 2 |
| Judge rejection breakdown | unsupported: 2 |
| Final by type | application_guidance: 1, operational_sequence: 15, commissioning_procedure: 1, fault_diagnostic_rule: 4, parameter_spec: 1 |
| L4 / L3 | 3 / 19 |

## Section Coverage

- 5.1.14: covered
- 5.20: covered
- 5.21: covered

## Samples

### Accepted
- p46, §5.1.14.4, application_guidance: T&R Logic Application for VAV Static Pressure Control
- p46, §5.1.14, operational_sequence: Trim & Respond Set-Point Reset Logic
- p47, §5.1.14.2, commissioning_procedure: Request-Hours Accumulator Reset
- p47, §5.1.14.2, fault_diagnostic_rule: Rogue Zone Detection via Cumulative% Request-Hours
- p47, §5.1.14.3, parameter_spec: T&R Variables and Defaults
- p172, §5.20.2.2, operational_sequence: Plant Enable Logic
- p172, §5.20.2.3, operational_sequence: Plant Disable Logic
- p175, §5.20.3.1, operational_sequence: Waterside Economizer Enable Logic
- p176, §5.20.3.2, operational_sequence: Waterside Economizer Disable Logic
- p182, §5.20.4.15, operational_sequence: Chiller Staging – Stage Down Condition
- p182, §5.20.4.15, operational_sequence: Chiller Staging – Stage Up Efficiency Condition
- p199, §5.20.5.2, operational_sequence: Chilled Water Supply Temperature Reset (DP Controlled Loops)
- p204, §5.20.6.17, operational_sequence: Primary CHW Pump Speed Control (Variable Primary-Variable Secondary with Decoupler Flow Meter)
- p230, §5.20.18.6, fault_diagnostic_rule: AFDD – Chilled Water Supply Temperature Too High
- p230, §5.20.18.6, fault_diagnostic_rule: AFDD – Condenser Approach Too High

### Anchor Rejected
- §5.21.3.9.f: Primary Only Condensing Boiler Staging Up | evidence_quote not verbatim in any chunk
- §5.21.3.9.h: Variable Primary/Variable Secondary Condensing Boiler Staging Up | evidence_quote not verbatim in any chunk
- §5.21.3.9.j: Non-Condensing Boiler Staging Up | evidence_quote not verbatim in any chunk
- §5.21.3.9.l: Hybrid Boiler Staging Up (Condensing Next Stage) | evidence_quote not verbatim in any chunk
- §5.21.3.9.n: Hybrid Boiler Staging Up (Non-Condensing Next Stage) | evidence_quote not verbatim in any chunk

### Judge Rejected
- §5.20.12.2: Cooling Tower Fan Control – CWRT Control (Dynamic Load) | unsupported: Evidence mentions CWST sensor hardwiring, while the summary describes CWRT setpoint reset and control. The evidence does not support the summary content.
- §5.21.3.9: Boiler Staging - General Requirements | unsupported: Evidence does not support the summary; only section header provided without the actual operational details.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (82.8%)
- G2 judge_acceptance_rate >= 60%: PASS (91.7%)
- G3 every requested section has accepted knowledge: PASS ({'5.1.14': True, '5.20': True, '5.21': True})
- G4 total_wallclock < 900s: PASS (617.23s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and whether each item should map to sw_base_model control/operation semantics.
