# parameter_spec Vertical Run Report (Run 3 - Document-Level)

**Run ID:** 20260506T083330Z_trane_cvgf_400_1000_chiller_manual_parameter_spec
**Architecture:** single-call document-level (DeepSeek V4 1M context)
**Manual:** trane_cvgf_400_1000_chiller_manual.pdf
**Equipment class:** hvac:centrifugal_chiller
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro
**ontology_version:** 0.2.0

## Token / Cost

| Metric | Value |
|--------|-------|
| Input tokens (extract) | 31848 |
| Output tokens (extract) | 4541 |
| Judge tokens (input + output) | 32311 |
| Total cost | ¥0.1798 |
| Status | within |

## Extraction numbers

| Metric | Value |
|--------|-------|
| Manual chunks | 84 |
| Manual tokens (estimated) | 20568 |
| LLM extraction calls | 1 |
| Raw candidates returned | 44 |
| Anchor-rejected (hallucination) | 3 |
| Anchor-passed | 41 |
| L4 (>=2 chunk matches) | 6 |
| L3 (1 chunk match) | 35 |
## Judge pass

| Metric | Value |
|--------|-------|
| Judge calls | 41 |
| Accepted | 34 (82.9%) |
| Rejected | 6 (17.1%) |
| Rejection breakdown | other: 5, ui_behavior: 1 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 34 |
| L4 / L3 breakdown | 5 / 29 |
## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 34 |
| Rule only | 0 |
## Sample LLM-only finds (top 10)

- p15: 启动限制最低油温默认设定 | hvac:centrifugal_chiller:parameter:key_e54a7f3c66
- p15: 润滑油温度控制设定范围 | hvac:centrifugal_chiller:parameter:key_3e1ce6df9b
- p23: Active Current Limit Setpoint | hvac:centrifugal_chiller:parameter:active_current_limit_setpoint
- p25: Active Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:active_chilled_water_setpoint
- p25: Chilled Water Reset | hvac:centrifugal_chiller:parameter:chilled_water_reset
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: External Base Loading Setpoint | hvac:centrifugal_chiller:parameter:external_base_loading_setpoint
- p29: External Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:external_chilled_water_setpoint
- p29: External Current Limit Setpoint | hvac:centrifugal_chiller:parameter:external_current_limit_setpoint

## Sample anchor rejections (top 5)

- 高油温停机保护默认设定值: evidence_quote not verbatim in any chunk
- 启动温差设定: evidence_quote not verbatim in any chunk
- 停机温差设定: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Front Panel Base Load Command: other | 'Command' implies an action, not a persistent configurable parameter.
- Compressor Control Signal: other | Compressor Control Signal is an output signal label (Percent Vane Position), not a configurable setpoint or parameter.
- Evaporator Water Pump: other | Evaporator Water Pump is a component name, not a configurable operational parameter
- Condenser Water Pump: other | Condenser Water Pump is a component name, not a configurable setpoint or parameter
- Oil Pump: other | 'Oil Pump' is a component name, not a configurable operational parameter.
- Clear Restart Inhibit Timer: ui_behavior | This is a command/action to clear a timer, not a configurable parameter.
## Stability gates

- G1 chunk_anchor_match_rate >= 80%: PASS (93.2%)
- G2 judge_acceptance_rate >= 50%: PASS (82.9%)
- G3 L4 count > 0: PASS (5)
- G4 extraction wallclock < 60 seconds: PASS (57.88s)

## Compared to run 1

| Metric | Run 1 | Run 3 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 41 judge |
| Verified candidates | 9 | 34 |
| L4 count | 0 | 5 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
