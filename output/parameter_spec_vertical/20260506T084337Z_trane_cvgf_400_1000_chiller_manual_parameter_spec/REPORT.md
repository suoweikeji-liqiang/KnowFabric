# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** 20260506T084337Z_trane_cvgf_400_1000_chiller_manual_parameter_spec
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
| Output tokens (extract) | 4600 |
| Judge tokens (input + output) | 33416 |
| Total cost | ¥0.1865 |
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
| Accepted | 32 (78.0%) |
| Rejected | 8 (22.0%) |
| Rejection breakdown | other: 6, ui_behavior: 1, algorithm_internal: 1 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 32 |
| L4 / L3 breakdown | 5 / 27 |
## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 32 |
| Rule only | 0 |
## Sample LLM-only finds (top 10)

- p15: 启动限制最低油温默认设定 | hvac:centrifugal_chiller:parameter:key_e54a7f3c66
- p15: 润滑油温度控制设定范围 | hvac:centrifugal_chiller:parameter:key_3e1ce6df9b
- p23: Active Current Limit Setpoint | hvac:centrifugal_chiller:parameter:active_current_limit_setpoint
- p25: Active Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:active_chilled_water_setpoint
- p25: Chilled Water Reset | hvac:centrifugal_chiller:parameter:chilled_water_reset
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: External Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:external_chilled_water_setpoint
- p29: External Current Limit Setpoint | hvac:centrifugal_chiller:parameter:external_current_limit_setpoint
- p29: Front Panel Base Load Setpoint | hvac:centrifugal_chiller:parameter:front_panel_base_load_setpoint

## Sample anchor rejections (top 5)

- 高油温停机保护默认设定值: evidence_quote not verbatim in any chunk
- 启动温差设定: evidence_quote not verbatim in any chunk
- 停机温差设定: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Front Panel Base Load Command: other | Item is a command/action rather than a configurable setpoint, limit, or mode selection.
- External Base Loading Setpoint: other | The evidence is solely a signal label 'External Base Loading Setpoint' without setpoint semantics or indication that it is a configurable operational parameter. It appears to be an analog input signal label, which is explicitly cited as a category error example.
- Compressor Control Signal: other | Compressor Control Signal is a control output signal, not a configurable setpoint or parameter.
- Evaporator Water Pump: other | Item is a component or equipment label, not a configurable setpoint, limit, or mode selection.
- Condenser Water Pump: other | Condenser Water Pump is a component name, not a configurable parameter.
- Oil Pump: other | Oil Pump is a component name, not a configurable operational parameter.
- Clear Restart Inhibit Timer: ui_behavior | This is a command/action to clear an inhibit timer, not a configurable operational parameter.
- 冷凝器限制设定: algorithm_internal | Manufacturer-set fixed limit, not operator-configurable
## Stability gates

- G1 chunk_anchor_match_rate >= 80%: PASS (93.2%)
- G2 judge_acceptance_rate >= 50%: PASS (78.0%)
- G3 L4 count > 0: PASS (5)
- G4 extraction wallclock < 60 seconds: FAIL (62.93s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 41 judge |
| Verified candidates | 9 | 32 |
| L4 count | 0 | 5 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
