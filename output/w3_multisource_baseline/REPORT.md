# W3 D5 Multi-Source Regression Report (D1+D2 Re-run 2026-05-11)

**Status**: D1+D2 FIXED. D3 cross-brand merge blocked by corpus gap.

## D1: Over-merge Fixed

- Added `_split_conflicting_groups` post-processing: detects conflicting qualifiers
  (Front Panel/External, 水侧/制冷剂侧, Max/Min, Start/Stop) and forces split.
- Result: "Front Panel Chilled Water" and "External Chilled Water" now in SEPARATE groups.
  Only 1 multi-name group remains: 安全阀压力设置 + 安全阀设定压力 (correct merge).

## D2: doc_id Fixed

- `merge_candidates` now reads `doc_id` from `candidate["evidence"][0]["doc_id"]`.
- All authority_layers[].doc_id now match `^doc_[a-f0-9]+$` format.
- Verified: `SELECT * FROM document WHERE doc_id = layer.doc_id` returns rows.

## Metrics (Post D1+D2)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| multi-source rate (≥2 layers) | ≥20% | 7.8% (5/64) | BELOW |
| partial_conflict | ≥3 | **1** | BELOW |
| material_conflict | ≥1 | **2** | MET |
| agreed | ≥5 | **2** | BELOW |

## Multi-Layer KOs

| KO | Layers | Consensus | Publishers | doc_ids OK |
|----|--------|-----------|------------|------------|
| external_chilled_water_setpoint | 2 | agreed | Trane, Trane | ✓ doc_883... |
| front_panel_chilled_water_setpoint | 2 | agreed | Trane, Trane | ✓ doc_883... |
| chilled_water_setpoint | 2 | material_conflict | Trane, Trane | ✓ doc_883... |
| current_limit_setpoint | 3 | material_conflict | Trane, Trane, Trane | ✓ doc_883... |
| safety_valve_pressure_setting | 3 | partial_conflict | McQuay, McQuay, McQuay | ✓ doc_366, doc_7c4 |

## D3: Cross-Brand Merge Blocked

Corpus gap: Trane CVGF (23 EN/ZH names) and McQuay (15 ZH names) describe
DIFFERENT parameter sets with no semantic overlap. No EN-EN pair like
"Chilled Water Setpoint" across two brands exists in current corpus.

**Required to unlock**: extract parameter_spec from York YK, Carrier 19XR, or
Daikin centrifugal manuals (all have English-heavy parameter names).

## What Works (Post D1+D2)

- D1: Conflicting qualifier detection/splitting ✓
- D2: doc_id from evidence, doc_xxx format verified ✓
- `group_and_normalize` + `_split_conflicting_groups` pipeline ✓
- `merge_candidates` consensus_state computation ✓
- DB authority_summary_json with correct doc_ids ✓
- API returns multi-layer KOs with authority_layers ✓
