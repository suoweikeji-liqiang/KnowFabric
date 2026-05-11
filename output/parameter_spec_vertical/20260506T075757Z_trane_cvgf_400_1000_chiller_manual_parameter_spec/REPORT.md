# parameter_spec Vertical Run Report (Run 2 - Document-Level)

**Run ID:** 20260506T075757Z_trane_cvgf_400_1000_chiller_manual_parameter_spec
**Architecture:** single-call document-level (DeepSeek V4 1M context)
**Manual:** trane_cvgf_400_1000_chiller_manual.pdf
**Equipment class:** hvac:centrifugal_chiller
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro
**ontology_version:** 0.2.0

## Token / Cost

| Metric | Value |
|--------|-------|
| Input tokens (extract) | 31747 |
| Output tokens (extract) | 5090 |
| Judge tokens (input + output) | 18330 |
| Total cost | ¥0.1267 |
| Status | within |

## Extraction numbers

| Metric | Value |
|--------|-------|
| Manual chunks | 84 |
| Manual tokens (estimated) | 20568 |
| LLM extraction calls | 1 |
| Raw candidates returned | 46 |
| Anchor-rejected (hallucination) | 20 |
| Anchor-passed | 26 |
| L4 (>=2 chunk matches) | 0 |
| L3 (1 chunk match) | 26 |
## Judge pass

| Metric | Value |
|--------|-------|
| Judge calls | 26 |
| Accepted | 24 (92.3%) |
| Rejected | 2 (7.7%) |
| Rejection breakdown | other: 2 |

## Final candidates

| Metric | Value |
|--------|-------|
| Verified | 24 |
| L4 / L3 breakdown | 0 / 24 |
## Rule baseline

| Metric | Value |
|--------|-------|
| Candidates | 0 |
| Notes on rule_compiler invocation | Used public per-chunk `detect_rule_knowledge_candidates`; no doc_id-level public API exists. |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule | 0 |
| LLM only | 24 |
| Rule only | 0 |
## Sample LLM-only finds (top 10)

- p25: Active Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:active_chilled_water_setpoint
- p25: Chilled Water Reset | hvac:centrifugal_chiller:parameter:chilled_water_reset
- p29: Differential to Start | hvac:centrifugal_chiller:parameter:differential_to_start
- p29: Differential to Stop | hvac:centrifugal_chiller:parameter:differential_to_stop
- p29: Front Panel Base Load Command | hvac:centrifugal_chiller:parameter:front_panel_base_load_command
- p29: Front Panel Base Load Setpoint | hvac:centrifugal_chiller:parameter:front_panel_base_load_setpoint
- p29: Front Panel Chilled Water Setpoint | hvac:centrifugal_chiller:parameter:front_panel_chilled_water_setpoint
- p29: Front Panel Current Limit Setpoint | hvac:centrifugal_chiller:parameter:front_panel_current_limit_setpoint
- p29: Outdoor Maximum Reset | hvac:centrifugal_chiller:parameter:outdoor_maximum_reset
- p29: Outdoor Reset Ratio | hvac:centrifugal_chiller:parameter:outdoor_reset_ratio

## Sample anchor rejections (top 5)

- Setpoint Source: evidence_quote not verbatim in any chunk
- Chilled Water Reset: evidence_quote not verbatim in any chunk
- External Chilled Water Setpoint: evidence_quote not verbatim in any chunk
- External Current Limit Setpoint: evidence_quote not verbatim in any chunk
- External Base Loading Setpoint: evidence_quote not verbatim in any chunk

## Sample judge rejections (top 10)

- Clear Restart Inhibit Timer: other | Clear Restart Inhibit Timer is a command/action, not a configurable parameter.
- 冷凝器限制设定: other | Manufacturer-set limit, not operator-configurable
## Stability gates

- G1 chunk_anchor_match_rate >= 80%: FAIL (56.5%)
- G2 judge_acceptance_rate >= 50%: PASS (92.3%)
- G3 L4 count > 0: FAIL (0)
- G4 extraction wallclock < 60 seconds: FAIL (72.54s)

## Compared to run 1

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| LLM calls | 8 | 1 + 26 judge |
| Verified candidates | 9 | 24 |
| L4 count | 0 | 0 |
| True precision (operator review) | 56% | pending |

## Operator review checklist

Reserved 20 random L3+ candidates for operator to mark accurate/inaccurate.
