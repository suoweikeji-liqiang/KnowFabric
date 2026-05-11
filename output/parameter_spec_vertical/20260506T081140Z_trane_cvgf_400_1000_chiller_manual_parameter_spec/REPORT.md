# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** 20260506T081140Z_trane_cvgf_400_1000_chiller_manual_parameter_spec
**Architecture:** single-call document-level (DeepSeek V4 1M context)
**Manual:** trane_cvgf_400_1000_chiller_manual.pdf
**Equipment class:** hvac:centrifugal_chiller
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro
**ontology_version:** 0.2.0

## Token / Cost

| Metric | Value |
|--------|-------|
| Input tokens (extract) | 31812 |
| Output tokens (extract) | 6730 |
| Judge tokens (input + output) | 36088 |
| Total cost | ¥0.2106 |
| Status | within |

## Extraction numbers

| Metric | Value |
|--------|-------|
| Manual chunks | 84 |
| Manual tokens (estimated) | 20568 |
| LLM extraction calls | 1 |
| Raw candidates returned | 62 |
| Anchor-rejected (hallucination) | 10 |
| Anchor-passed | 52 |
| L4 (>=2 chunk matches) | 7 |
| L3 (1 chunk match) | 45 |
## Judge pass

| Metric | Value |
|--------|-------|
| Judge calls | 52 |
| Accepted | 39 (75.0%) |
| Rejected | 9 (25.0%) |
| Rejection breakdown | other: 7, ui_behavior: 1, algorithm_internal: 1 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 39 |
| L4 / L3 breakdown | 7 / 32 |
## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 39 |
| Rule only | 0 |
## Sample LLM-only finds (top 10)

- p23: Active Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:active_chilled_water_setpoint
- p23: Active Current Limit Setpoint | hvac:centrifugal_chiller:parameter:active_current_limit_setpoint
- p25: BAS Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:bas_chilled_water_setpoint
- p25: BAS Current Limit Setpoint | hvac:centrifugal_chiller:parameter:bas_current_limit_setpoint
- p25: Chilled Water Reset | hvac:centrifugal_chiller:parameter:chilled_water_reset
- p25: External Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:external_chilled_water_setpoint
- p27: Date | hvac:centrifugal_chiller:parameter:date
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: External Current Limit Setpoint | hvac:centrifugal_chiller:parameter:external_current_limit_setpoint

## Sample anchor rejections (top 5)

- 启动限制最低油温默认设定: evidence_quote not verbatim in any chunk
- 润滑油温度控制设定范围: evidence_quote not verbatim in any chunk
- 低油温起动抑制设定: evidence_quote not verbatim in any chunk
- 高油温停机保护设定: evidence_quote not verbatim in any chunk
- 启动温差设定: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Front Panel Base Load Command: other | It is a command/action, not a configurable parameter.
- External Chilled Water Setpoint: other | External Chilled Water Setpoint is an input signal label, not a configurable operational parameter.
- External Base Loading Setpoint: other | External Base Loading Setpoint is an input signal label, not a configurable parameter
- Compressor Control Signal: other | This is a control signal output, not a configurable setpoint or limit.
- Evaporator Water Pump: other | This is a component name, not a configurable operational parameter.
- Condenser Water Pump: other | It is a component/module name, not a configurable operational parameter.
- Oil Pump: other | Oil Pump appears to be a component or status label, not a configurable parameter.
- Clear Restart Inhibit Timer: ui_behavior | Command/action to clear a timer, not a configurable operational parameter.
- 冷凝器限制设定: algorithm_internal | Factory-set limit, not operator-configurable.
## Stability gates

- G1 chunk_anchor_match_rate >= 80%: PASS (83.9%)
- G2 judge_acceptance_rate >= 50%: PASS (75.0%)
- G3 L4 count > 0: PASS (7)
- G4 extraction wallclock < 60 seconds: FAIL (90.42s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 52 judge |
| Verified candidates | 9 | 39 |
| L4 count | 0 | 7 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
