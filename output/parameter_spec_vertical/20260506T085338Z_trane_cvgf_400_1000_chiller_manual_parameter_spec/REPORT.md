# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** 20260506T085338Z_trane_cvgf_400_1000_chiller_manual_parameter_spec
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
| Output tokens (extract) | 5551 |
| Judge tokens (input + output) | 38293 |
| Total cost | ¥0.2067 |
| Status | within |

## Extraction numbers

| Metric | Value |
|--------|-------|
| Manual chunks | 84 |
| Manual tokens (estimated) | 20568 |
| LLM extraction calls | 1 |
| Raw candidates returned | 53 |
| Anchor-rejected (hallucination) | 4 |
| Anchor-passed | 49 |
| L4 (>=2 chunk matches) | 6 |
| L3 (1 chunk match) | 43 |
## Judge pass

| Metric | Value |
|--------|-------|
| Judge calls | 49 |
| Accepted | 37 (75.5%) |
| Rejected | 7 (24.5%) |
| Rejection breakdown | other: 6, algorithm_internal: 1 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 37 |
| L4 / L3 breakdown | 7 / 30 |
## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 37 |
| Rule only | 0 |
## Sample LLM-only finds (top 10)

- p15: 启动限制最低油温默认设定 | hvac:centrifugal_chiller:parameter:key_e54a7f3c66
- p15: 润滑油温度控制设定范围 | hvac:centrifugal_chiller:parameter:key_3e1ce6df9b
- p23: Active Current Limit Setpoint | hvac:centrifugal_chiller:parameter:active_current_limit_setpoint
- p25: Active Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:active_chilled_water_setpoint
- p25: BAS Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:bas_chilled_water_setpoint
- p25: BAS Current Limit Setpoint | hvac:centrifugal_chiller:parameter:bas_current_limit_setpoint
- p25: Chilled Water Reset | hvac:centrifugal_chiller:parameter:chilled_water_reset
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: External Base Loading Setpoint | hvac:centrifugal_chiller:parameter:external_base_loading_setpoint

## Sample anchor rejections (top 5)

- 高油温停机保护设定: evidence_quote not verbatim in any chunk
- 启动温差设定: evidence_quote not verbatim in any chunk
- 停机温差设定: evidence_quote not verbatim in any chunk
- 外部冷冻水设定范围: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Front Panel Base Load Command: other | The label 'Front Panel Base Load Command' indicates a command/action rather than a configurable setpoint, limit, or mode selection.
- Compressor Control Signal: other | Compressor Control Signal is an analog output signal indicating vane position, not a configurable setpoint or parameter.
- Evaporator Water Pump: other | 'Evaporator Water Pump' appears to be a component or relay output label rather than a configurable setpoint, limit, or mode selection.
- Condenser Water Pump: other | Appears to be a component label, not a configurable parameter.
- Oil Pump: other | It is a component name, not a configurable parameter.
- Clear Restart Inhibit Timer: other | Clear Restart Inhibit Timer is a command/action, not a configurable setpoint or parameter.
- 冷凝器限制设定: algorithm_internal | Factory-set limit based on HPC percentage, not operator-configurable
## Stability gates

- G1 chunk_anchor_match_rate >= 80%: PASS (92.5%)
- G2 judge_acceptance_rate >= 50%: PASS (75.5%)
- G3 L4 count > 0: PASS (7)
- G4 extraction wallclock < 60 seconds: FAIL (71.05s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 49 judge |
| Verified candidates | 9 | 37 |
| L4 count | 0 | 7 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
