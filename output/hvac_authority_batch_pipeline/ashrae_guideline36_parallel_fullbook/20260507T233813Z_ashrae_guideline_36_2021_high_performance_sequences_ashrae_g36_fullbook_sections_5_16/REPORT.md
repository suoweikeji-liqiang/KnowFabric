# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T233813Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_16
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
| Extract output tokens | 31094 |
| Judge calls | 1 |
| Judge total tokens | 19948 |
| Total cost | ¥0.4223 / ¥10.00 |
| Extract wallclock | 721.47s |
| Total wallclock | 871.25s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 80 |
| Anchor passed | 80 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 5 |
| Judge input | 75 |
| Judge accepted | 72 |
| Judge rejected | 3 |
| Judge rejection breakdown | unsupported: 3 |
| Final by type | operational_sequence: 68, parameter_spec: 2, fault_diagnostic_rule: 2 |
| L4 / L3 | 28 / 44 |

## Samples

### Accepted
- p111, §5.16.1.1, operational_sequence: Supply Fan Start/Stop
- p111, §5.16.1.1, operational_sequence: Totalize VAV Box Airflow to Vps
- p112, §5.16.1.3, operational_sequence: Supply Fan Speed Control to Maintain DSP
- p112, §5.16.2.1, operational_sequence: Supply Air Temperature Control Loop Enable
- p112, §5.16.1.2, parameter_spec: Static Pressure Setpoint Reset T&R Parameters
- p113, §5.16.2.2, operational_sequence: Occupied/Setup Mode SAT Setpoint Reset
- p113, §5.16.2.2, parameter_spec: SAT T&R Reset Parameters
- p114, §5.16.2.2, operational_sequence: Cooldown Mode SAT Setpoint
- p114, §5.16.2.2, operational_sequence: Warmup/Setback Mode SAT Setpoint
- p114, §5.16.2.3, operational_sequence: Relief Damper/Fan Units: Economizer Min Position and Return Air Max Position for Minimum OA
- p114, §5.16.2.3, operational_sequence: Return Fan Units: Return Air Damper Max Position for Minimum OA
- p114, §5.16.2.3, operational_sequence: SAT Control Loop Output Mapping
- p114, §5.16.2.3, operational_sequence: Separate Minimum OA Damper: Economizer Min Position 0%
- p114, §5.16.2.3, operational_sequence: Single Common Damper: Economizer and Return Damper Modulation for Minimum OA
- p115, §5.16.2.3, operational_sequence: SAT Loop Mapping with Return Fan and Airflow Tracking

### Anchor Rejected
- §5.16.2.3: SAT Loop Mapping with Relief Damper or Relief Fan | weak evidence_quote: lacks rule/action signal
- §5.16.4.4: Return Fan Units: Minimum Outdoor Air Control Sequence | weak evidence_quote: lacks rule/action signal
- §5.16.4.4: Relief Damper/Fan Units: Minimum Outdoor Air Control Sequence | weak evidence_quote: lacks rule/action signal
- §5.16.5.4: Return Fan Units with AFMS: Minimum Outdoor Air Control Sequence | weak evidence_quote: lacks rule/action signal
- §5.16.5.4: Relief Damper/Fan Units with AFMS: Minimum Outdoor Air Control Sequence | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.16.5.4: Return Fan Units with AFMS: Minimum Outdoor Air Control Disable | unsupported: Evidence quote contains a condition opposite to the summary: 'economizer high limit conditions are exceeded' vs 'not exceeded'. Inconsistency renders item unreliable.
- §5.16.10.5: Building Pressure Control Loop and Sequencing | unsupported: Summary cannot be verified from the provided evidence quote, which is only a fragment of a sentence.
- §5.16.12.3: Freeze Protection Stage 3 | unsupported: Evidence quote is truncated and incomplete; unable to validate the summary.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (96.0%)
- G3 focused section run produced at least one verified candidate: PASS (72)
- G4 extract wallclock <= configured limit: PASS (721.47s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
