# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** 20260429T145634Z_trane_cvgf_400_1000_chiller_manual_parameter_spec_v4_pro_judge
**Architecture:** single-call document-level (DeepSeek V4 1M context)
**Manual:** trane_cvgf_400_1000_chiller_manual.pdf
**Equipment class:** hvac:centrifugal_chiller
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro
**ontology_version:** 0.2.0

## Token / Cost

| Metric | Value |
|--------|-------|
| Input tokens (extract) | 31589 |
| Output tokens (extract) | 4623 |
| Judge tokens (input + output) | 21641 |
| Total cost | ¥0.1528 |
| Status | within |

## Extraction numbers

| Metric | Value |
|--------|-------|
| Manual chunks | 84 |
| Manual tokens (estimated) | 20568 |
| LLM extraction calls | 1 |
| Raw candidates returned | 46 |
| Anchor-rejected (hallucination) | 6 |
| Anchor-passed | 40 |
| L4 (>=2 chunk matches) | 5 |
| L3 (1 chunk match) | 35 |
## Judge pass

| Metric | Value |
|--------|-------|
| Judge calls | 40 |
| Accepted | 25 (62.5%) |
| Rejected | 15 (37.5%) |
| Rejection breakdown | ui_behavior: 9, other: 4, algorithm_internal: 2 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 25 |
| L4 / L3 breakdown | 3 / 22 |
## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 25 |
| Rule only | 0 |
## Sample LLM-only finds (top 10)

- p27: Date | hvac:centrifugal_chiller:parameter:date
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: External Base Loading Setpoint | hvac:centrifugal_chiller:parameter:external_base_loading_setpoint
- p29: External Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:external_chilled_water_setpoint
- p29: External Current Limit Setpoint | hvac:centrifugal_chiller:parameter:external_current_limit_setpoint
- p29: Front Panel Base Load Setpoint | hvac:centrifugal_chiller:parameter:front_panel_base_load_setpoint
- p29: Front Panel Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:front_panel_chilled_water_setpoint
- p29: Front Panel Current Limit Setpoint | hvac:centrifugal_chiller:parameter:front_panel_current_limit_setpoint
- p29: Outdoor Maximum Reset | hvac:centrifugal_chiller:parameter:outdoor_maximum_reset

## Sample anchor rejections (top 5)

- 启动温差: evidence_quote not verbatim in any chunk
- 停机温差: evidence_quote not verbatim in any chunk
- 出水温度停机保护设定: evidence_quote not verbatim in any chunk
- 低油温起动抑制设定: evidence_quote not verbatim in any chunk
- 高油温停机设定: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Front Panel Base Load Command: ui_behavior | The name 'Front Panel Base Load Command' indicates a user-initiated command from the front panel interface, not a configurable operational parameter with a value and unit.
- Chilled Water Reset: other | Chilled Water Reset is typically a function or control strategy, not a specific configurable parameter; missing value and unit indicate it's a category error.
- Return Start Reset: ui_behavior | Return Start Reset is a command or action (likely a UI button), not a configurable parameter with a value.
- Outdoor Start Reset: ui_behavior | Name suggests a reset function rather than a configurable parameter; no value or unit provided.
- Compressor Control Signal: algorithm_internal | Compressor Control Signal is an internal control output, not a user-configurable operational parameter.
- Evaporator Water Pump: other | This is a component name, not a configurable operational parameter.
- Condenser Water Pump: other | Not a parameter; it is a component name.
- Oil Pump: other | Oil Pump is a component name, not a configurable parameter with value and unit.
- Clear Restart Inhibit Timer: ui_behavior | It is an action/command to clear a timer, not a configurable parameter with a settable value.
- Date Format: ui_behavior | Date format is a user interface display setting, not an operational parameter.
## Stability gates

- G1 chunk_anchor_match_rate >= 80%: PASS (87.0%)
- G2 judge_acceptance_rate >= 50%: PASS (62.5%)
- G3 L4 count > 0: PASS (3)
- G4 extraction wallclock < 60 seconds: PASS (52.94s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 40 judge |
| Verified candidates | 9 | 25 |
| L4 count | 0 | 3 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.

## V4 Pro Judge Rerun Note

This run reused extraction artifacts from `20260429T143611Z_trane_cvgf_400_1000_chiller_manual_parameter_spec` and reran only the judge pass with `deepseek-v4-pro-judge` / `deepseek-v4-pro`. Judge wallclock: 497.41s. Judge errors after retry: 0.
