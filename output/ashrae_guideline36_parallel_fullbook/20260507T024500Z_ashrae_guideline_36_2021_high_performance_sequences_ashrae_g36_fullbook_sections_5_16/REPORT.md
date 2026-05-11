# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T024500Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_16
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.16
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 50503 |
| Extract calls | 1 |
| Extract input tokens | 53182 |
| Extract output tokens | 25449 |
| Judge calls | 1 |
| Judge total tokens | 14927 |
| Total cost | ¥0.1757 / ¥10.00 |
| Extract wallclock | 390.06s |
| Total wallclock | 624.83s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 69 |
| Anchor passed | 69 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 27 |
| Judge input | 42 |
| Judge accepted | 36 |
| Judge rejected | 6 |
| Judge rejection breakdown | unsupported: 6 |
| Final by type | operational_sequence: 27, fault_diagnostic_rule: 9 |
| L4 / L3 | 6 / 30 |

## Samples

### Accepted
- p111, §5.16.1.1, operational_sequence: Totalize VAV Box Airflow to Vps
- p111, §5.16.1.2, operational_sequence: Static Pressure Setpoint Reset using T&R Logic
- p112, §5.16.2.1, operational_sequence: SAT Control Loop Enable/Disable
- p114, §5.16.2.2, operational_sequence: Cooldown Mode SAT Setpoint
- p114, §5.16.2.2, operational_sequence: Warmup/Setback Mode SAT Setpoint
- p114, §5.16.2.3, operational_sequence: SAT Control Loop Output Mapping
- p119, §5.16.4.3, operational_sequence: Minimum Outdoor Air Damper Open/Close (Separate Damper, DP Control)
- p121, §5.16.4.4, operational_sequence: Minimum Outdoor Air Control Disable Sequence for Units with Return Fans (DP Control)
- p121, §5.16.5.4, operational_sequence: Minimum Outdoor Air Control Disable Sequence for Units with Return Fans (AFMS Control)
- p123, §5.16.5.3, operational_sequence: Minimum Outdoor Air Damper Open/Close (Separate Damper, AFMS Control)
- p126, §5.16.6.3, operational_sequence: Minimum Outdoor Air Control Loop Enable/Disable (Single Common Damper, AFMS)
- p126, §5.16.6.3, operational_sequence: Minimum Outdoor Air Control Release for Units with Return Fans (Single Common Damper, AFMS)
- p128, §5.16.8.1, operational_sequence: Relief Damper Control (Without Fans)
- p128, §5.16.8.2, operational_sequence: Relief Damper Modulation (Without Fans)
- p129, §5.16.9.2, operational_sequence: Relief Fan Lead/Lag Alternation

### Anchor Rejected
- §5.16.1.3: Static Pressure Control | weak evidence_quote: section heading without supporting rule
- §5.16.2.2: Occupied/Setup Mode SAT Setpoint Reset | weak evidence_quote: section heading without supporting rule
- §5.16.4.4: Minimum Outdoor Air Control Enable/Disable for Units with Return Fans (DP Control) | weak evidence_quote: lacks rule/action signal
- §5.16.4.4: Minimum Outdoor Air Control Sequence for Units with Return Fans (DP Control) | weak evidence_quote: lacks rule/action signal
- §5.16.4.4: Minimum Outdoor Air Control Enable/Disable for Units with Relief Dampers/Fans (DP Control) | weak evidence_quote: lacks rule/action signal
- §5.16.4.4: Minimum Outdoor Air Control Sequence for Units with Relief Dampers/Fans (DP Control) | weak evidence_quote: lacks rule/action signal
- §5.16.5.4: Minimum Outdoor Air Control Enable/Disable for Units with Return Fans (AFMS Control) | weak evidence_quote: lacks rule/action signal
- §5.16.5.4: Minimum Outdoor Air Control Sequence for Units with Return Fans (AFMS Control) | weak evidence_quote: lacks rule/action signal
- §5.16.5.4: Minimum Outdoor Air Control Enable/Disable for Units with Relief Dampers/Fans (AFMS Control) | weak evidence_quote: lacks rule/action signal
- §5.16.5.4: Minimum Outdoor Air Control Sequence for Units with Relief Dampers/Fans (AFMS Control) | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.16.1.1: Supply Fan Start/Stop | unsupported: Evidence quote is mismatched and does not support the summary; appears to be noisy extraction.
- §5.16.9.6: Relief Fan P-Only Control Loop | unsupported: Evidence quote is truncated and does not include the 12 Pa setpoint or other details in the summary.
- §5.16.10.5: Building Pressure Control Loop for Return Fan (Direct Building Pressure) | unsupported: Evidence quote is truncated and does not support the detailed summary regarding exhaust dampers and setpoint reset range.
- §5.16.12.2: Freeze Protection Stage 2 | unsupported: Evidence quote is truncated and does not include the 1-hour closure and alarm details.
- §5.16.12.3: Freeze Protection Stage 3 | unsupported: Evidence quote is truncated and does not support the detailed Stage 3 actions.
- §5.16.13.3: Filter Pressure Drop Alarm | unsupported: Evidence quote is truncated and does not include the airflow threshold or formula.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (85.7%)
- G3 focused section run produced at least one verified candidate: PASS (36)
- G4 extract wallclock <= configured limit: PASS (390.06s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
