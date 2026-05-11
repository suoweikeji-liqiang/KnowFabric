# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T173350Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_21
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.21
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 47600 |
| Extract calls | 1 |
| Extract input tokens | 47969 |
| Extract output tokens | 21951 |
| Judge calls | 1 |
| Judge total tokens | 11697 |
| Total cost | ¥0.3276 / ¥10.00 |
| Extract wallclock | 621.08s |
| Total wallclock | 777.09s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 43 |
| Anchor passed | 38 |
| Anchor rejected | 5 |
| Weak evidence rejected before judge | 3 |
| Judge input | 35 |
| Judge accepted | 28 |
| Judge rejected | 7 |
| Judge rejection breakdown | unsupported: 7 |
| Final by type | operational_sequence: 22, parameter_spec: 2, fault_diagnostic_rule: 4 |
| L4 / L3 | 1 / 27 |

## Samples

### Accepted
- p235, §5.21.2.2, operational_sequence: Plant Enable Condition
- p235, §5.21.2.3, operational_sequence: Plant Disable Condition
- p236, §5.21.2.4, operational_sequence: Open Lead Boiler Isolation Valve
- p236, §5.21.2.4, operational_sequence: Plant Enable Sequence for Primary-Only Plants
- p236, §5.21.2.4, operational_sequence: Plant Enable Sequence for Primary-Secondary Plants
- p236, §5.21.2.5, operational_sequence: Plant Disable - Close Isolation Valves and Disable Pumps (Headered)
- p236, §5.21.2.5, operational_sequence: Plant Disable - Disable Dedicated Primary Pumps
- p236, §5.21.2.5, operational_sequence: Plant Disable - Disable Secondary Pumps
- p237, §5.21.3.8, operational_sequence: Stage Availability
- p237, §5.21.3.9, operational_sequence: General Staging Restrictions
- p237, §5.21.3.5, parameter_spec: Qrequired Calculation (Primary-Only/Primary-Secondary without Secondary Flow Meters)
- p237, §5.21.3.7, parameter_spec: B-STAGE MIN Calculation
- p238, §5.21.3.9.g, operational_sequence: Stage Down - Primary-Only Condensing Boiler
- p239, §5.21.3.9.i, operational_sequence: Stage Down - Variable Primary/Variable Secondary Condensing Boiler
- p240, §5.21.3.9.k, operational_sequence: Stage Down - Non-Condensing Boiler

### Anchor Rejected
- §5.21.3.9.f: Stage Up - Primary-Only Condensing Boiler | evidence_quote not verbatim in any chunk
- §5.21.3.9.h: Stage Up - Variable Primary/Variable Secondary Condensing Boiler | evidence_quote not verbatim in any chunk
- §5.21.3.9.j: Stage Up - Non-Condensing Boiler | evidence_quote not verbatim in any chunk
- §5.21.3.9.m: Stage Down - Hybrid Plant, Current Stage Condensing | evidence_quote not verbatim in any chunk
- §5.21.3.9.n: Stage Up - Hybrid Plant, Next Higher Stage Non-Condensing | evidence_quote not verbatim in any chunk
- §5.21.2.5: Plant Disable - Shut Off Boilers | weak evidence_quote: too short to support structured summary
- §5.21.7.3: Secondary Pump Staging Based on Flow Ratio | weak evidence_quote: introductory fragment without complete rule
- §5.21.8.1: Minimum Flow Bypass Valve Setpoint Calculation | weak evidence_quote: section heading without supporting rule

### Judge Rejected
- §5.21.3.6: Qrequired Calculation (Primary-Secondary with Secondary Flow Meters) | unsupported: Summary includes formula not present in the provided evidence; evidence only introductory sentence.
- §5.21.4.1: HW Supply Temperature Reset (Trim & Respond) Parameters | unsupported: Evidence provides only section header; detailed parameters in summary are not directly supported.
- §5.21.5.1: Condensation Control - MinFlow Bypass Valve (Primary-Only Non-Condensing) | unsupported: Summary details P-only loop specifics, but evidence only shows section header.
- §5.21.5.3: Condensation Control - Max Secondary Pump Speed (Constant Primary, Variable Secondary) | unsupported: Summary elaborates on condensation control loop; evidence only section header.
- §5.21.5.5: Condensation Control - Variable Primary Pumps (P-only Loop with Split Output) | unsupported: Summary adds split output details not present in the header-only evidence.
- §5.21.6.4: Primary Pump Staging Based on Flow Ratio | unsupported: Summary provides staging formula, but evidence is just the section header.
- §5.21.8.6: Minimum Flow Bypass Valve Startup Bias | unsupported: Summary adds 'initially bias loop to 100% open' not found in evidence which only states loop enable.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (88.4%)
- G2 judge_acceptance_rate >= 50%: PASS (80.0%)
- G3 focused section run produced at least one verified candidate: PASS (28)
- G4 extract wallclock <= configured limit: PASS (621.08s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
