# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** 20260429T143611Z_trane_cvgf_400_1000_chiller_manual_parameter_spec
**Architecture:** single-call document-level (DeepSeek V4 1M context)
**Manual:** trane_cvgf_400_1000_chiller_manual.pdf
**Equipment class:** hvac:centrifugal_chiller
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-r1-judge / deepseek-reasoner
**ontology_version:** 0.2.0

## Token / Cost

| Metric | Value |
|--------|-------|
| Input tokens (extract) | 31589 |
| Output tokens (extract) | 4623 |
| Judge tokens (input + output) | 12527 |
| Total cost | ¥0.1694 |
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
| Accepted | 30 (75.0%) |
| Rejected | 10 (25.0%) |
| Rejection breakdown | other: 6, ui_behavior: 4 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 30 |
| L4 / L3 breakdown | 4 / 26 |

## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 30 |
| Rule only | 0 |

## Sample LLM-only finds (top 10)

- p25: Chilled Water Reset | hvac:centrifugal_chiller:parameter:chilled_water_reset
- p27: Date | hvac:centrifugal_chiller:parameter:date
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: External Base Loading Setpoint | hvac:centrifugal_chiller:parameter:external_base_loading_setpoint
- p29: External Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:external_chilled_water_setpoint
- p29: External Current Limit Setpoint | hvac:centrifugal_chiller:parameter:external_current_limit_setpoint
- p29: Front Panel Base Load Command | hvac:centrifugal_chiller:parameter:front_panel_base_load_command
- p29: Front Panel Base Load Setpoint | hvac:centrifugal_chiller:parameter:front_panel_base_load_setpoint
- p29: Front Panel Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:front_panel_chilled_water_setpoint

## Sample anchor rejections (top 5)

- 启动温差: evidence_quote not verbatim in any chunk
- 停机温差: evidence_quote not verbatim in any chunk
- 出水温度停机保护设定: evidence_quote not verbatim in any chunk
- 低油温起动抑制设定: evidence_quote not verbatim in any chunk
- 高油温停机设定: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Compressor Control Signal: other | No value or unit provided; ambiguous whether configurable.
- Evaporator Water Pump: other | The evidence 'Evaporator Water Pump' is a component name, not a configurable operational parameter. It lacks a value and unit, and refers to a physical device rather than a parameter that can be set.
- Condenser Water Pump: other | Condenser Water Pump is a component name, not a configurable operational parameter with a value and unit.
- Oil Pump: other | Oil Pump appears to be a component name, not a configurable operational parameter.
- Date Format: ui_behavior | Date Format is a UI display setting, not an HVAC operational parameter.
- Time Format: ui_behavior | Time Format is a display setting, not a direct operational parameter for HVAC control.
- Time of Day: other | Time of Day is a generic concept, not a configurable parameter.
- Display Units: ui_behavior | Display Units is a user interface setting, not an operational parameter that controls system operation.
- Language: ui_behavior | Language selection is a UI behavior, not an HVAC operational parameter.
- 冷凝器限制设定: other | Factory-set limit (HPC's 93%), not adjustable by operator

## Stability gates

- G1 chunk_anchor_match_rate >= 80%: PASS (87.0%)
- G2 judge_acceptance_rate >= 50%: PASS (75.0%)
- G3 L4 count > 0: PASS (4)
- G4 extraction wallclock < 60 seconds: PASS (52.94s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 40 judge |
| Verified candidates | 9 | 30 |
| L4 count | 0 | 4 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
