# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** 20260506T082341Z_trane_cvgf_400_1000_chiller_manual_parameter_spec
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
| Output tokens (extract) | 5631 |
| Judge tokens (input + output) | 34409 |
| Total cost | ¥0.1931 |
| Status | within |

## Extraction numbers

| Metric | Value |
|--------|-------|
| Manual chunks | 84 |
| Manual tokens (estimated) | 20568 |
| LLM extraction calls | 1 |
| Raw candidates returned | 53 |
| Anchor-rejected (hallucination) | 11 |
| Anchor-passed | 42 |
| L4 (>=2 chunk matches) | 4 |
| L3 (1 chunk match) | 38 |
## Judge pass

| Metric | Value |
|--------|-------|
| Judge calls | 42 |
| Accepted | 29 (69.0%) |
| Rejected | 8 (31.0%) |
| Rejection breakdown | other: 6, algorithm_internal: 2 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 29 |
| L4 / L3 breakdown | 5 / 24 |
## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 29 |
| Rule only | 0 |
## Sample LLM-only finds (top 10)

- p25: Active Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:active_chilled_water_setpoint
- p25: BAS Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:bas_chilled_water_setpoint
- p25: BAS Current Limit Setpoint | hvac:centrifugal_chiller:parameter:bas_current_limit_setpoint
- p25: Chilled Water Reset | hvac:centrifugal_chiller:parameter:chilled_water_reset
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: External Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:external_chilled_water_setpoint
- p29: External Current Limit Setpoint | hvac:centrifugal_chiller:parameter:external_current_limit_setpoint
- p29: Front Panel Base Load Setpoint | hvac:centrifugal_chiller:parameter:front_panel_base_load_setpoint
- p29: Front Panel Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:front_panel_chilled_water_setpoint

## Sample anchor rejections (top 5)

- Active Current Limit Setpoint: evidence_quote not verbatim in any chunk
- 启动限制最低油温默认设定: evidence_quote not verbatim in any chunk
- 润滑油温度控制设定范围: evidence_quote not verbatim in any chunk
- 低油温起动抑制设定: evidence_quote not verbatim in any chunk
- 高油温停机保护默认设定值: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Front Panel Base Load Command: other | The item is labeled as a 'Command', which suggests an action or control output rather than a configurable setpoint or parameter. No evidence of a setpoint value, unit, or adjustable range is provided.
- External Base Loading Setpoint: other | The evidence is solely a signal label name without setpoint semantics per explicit rejection example.
- Compressor Control Signal: algorithm_internal | Compressor Control Signal is an output control signal (Percent Vane Position) commanding the compressor vane position, not an operator-configurable setpoint, limit, or mode selection.
- Evaporator Water Pump: other | Evaporator Water Pump is a component or output label, not a configurable operational parameter.
- Condenser Water Pump: other | Component name, not a configurable parameter
- Oil Pump: other | Component name, not a configurable parameter
- Clear Restart Inhibit Timer: other | Clear Restart Inhibit Timer is a command/action to clear a timer, not a configurable operational parameter.
- 冷凝器限制设定: algorithm_internal | This is a factory-set limit (93% of HPC) and is not configurable by the operator.
## Stability gates

- G1 chunk_anchor_match_rate >= 80%: FAIL (79.2%)
- G2 judge_acceptance_rate >= 50%: PASS (69.0%)
- G3 L4 count > 0: PASS (5)
- G4 extraction wallclock < 60 seconds: FAIL (78.60s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 42 judge |
| Verified candidates | 9 | 29 |
| L4 count | 0 | 5 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
