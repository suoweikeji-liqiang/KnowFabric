# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T170712Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_16
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.16
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 50503 |
| Extract calls | 1 |
| Extract input tokens | 53218 |
| Extract output tokens | 27882 |
| Judge calls | 1 |
| Judge total tokens | 9691 |
| Total cost | ¥0.3681 / ¥10.00 |
| Extract wallclock | 607.71s |
| Total wallclock | 722.86s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 40 |
| Anchor passed | 40 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 6 |
| Judge input | 34 |
| Judge accepted | 34 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 33, parameter_spec: 1 |
| L4 / L3 | 7 / 27 |

## Samples

### Accepted
- p111, §5.16.1.1, operational_sequence: Supply fan shall run in Cooldown, Setup, or Occupied modes
- p111, §5.16.1.1, operational_sequence: Supply fan shall run with perimeter VAV-reheat in Setback/Warmup
- p111, §5.16.1.1, operational_sequence: Totalize VAV box airflow to Vps
- p112, §5.16.2.1, operational_sequence: SAT control loop enable/disable
- p112, §5.16.1.2, parameter_spec: Static pressure setpoint reset T&R parameters
- p113, §5.16.2.2, operational_sequence: Occupied/Setup SAT setpoint reset with OAT
- p114, §5.16.2.2, operational_sequence: Cooldown SAT setpoint
- p114, §5.16.2.2, operational_sequence: Warmup and Setback SAT setpoint
- p114, §5.16.2.3, operational_sequence: Relief damper/fan MinOA-P and/or MaxRA-P modulation for min OA
- p114, §5.16.2.3, operational_sequence: Return fan MaxRA-P modulated for minimum OA
- p114, §5.16.2.3, operational_sequence: SAT control loop output mapping to coil and damper sequencing
- p114, §5.16.2.3, operational_sequence: Separate min OA damper: economizer damper MinOA-P = 0%
- p114, §5.16.2.3, operational_sequence: Single common damper: MaxRA-P and MinOA-P modulated
- p118, §5.16.3.2, operational_sequence: AbsMinOA* calculation for Title 24
- p118, §5.16.3.2, operational_sequence: DesMinOA* calculation for Title 24

### Anchor Rejected
- §5.16.1.3: Supply fan speed controlled to maintain DSP at setpoint | weak evidence_quote: section heading without supporting rule
- §5.16.2.2: T-max reset T&R parameters | weak evidence_quote: section heading without supporting rule
- §5.16.3.1: Vou calculation per ASHRAE 62.1 | weak evidence_quote: too short to support structured summary
- §5.16.3.1: MinOAsp calculation per ASHRAE 62.1 | weak evidence_quote: too short to support structured summary
- §5.16.4.1: MinDPsp calculation for ASHRAE 62.1 | weak evidence_quote: too short to support structured summary
- §5.16.4.4: Minimum OA control enabled sequence for return fans (DP) | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (34)
- G4 extract wallclock <= configured limit: PASS (607.71s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
