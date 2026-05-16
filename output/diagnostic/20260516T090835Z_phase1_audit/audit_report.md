# Phase 1 KEEP_TEXT Quality Audit

Run: `20260516T090835Z_phase1_audit`

Scope is read-only: SQL inspection, review-pack source lookup, existing report review, and `_slugify_part` function checks. No KO/evidence/schema/code changes were made.

## Inputs

- Phase 1 report: `output/diagnostic/20260515T173143Z_phase1_keep_text/REPORT.md`
- Material sample CSV: `output/diagnostic/20260516T090835Z_phase1_audit/material_conflict_samples.csv`
- Boundary trace: `output/diagnostic/20260516T090835Z_phase1_audit/canonical_key_boundary_trace.md`
- Slugifier regression: `output/diagnostic/20260516T090835Z_phase1_audit/slugifier_zh_regression.md`

## Task A: material_conflict Samples

Sample method followed the requested stratification: 30 cross-publisher `material_conflict` KOs, preferring larger layer counts.

| ontology_class_id | sampled KOs |
|---|---:|
| centrifugal_chiller | 10 |
| ahu | 8 |
| screw_chiller | 8 |
| water_source_heat_pump | 2 |
| standard_reference | 1 |
| air_cooled_modular_heat_pump | 1 |

The CSV contains 140 layer/evidence rows. Each row has KO id, publisher, source name, structured value fields, unit, doc id, page number, full evidence text, and an empty `human_audit_verdict` column.

### Pool Context

Current cross-publisher material-conflict ratios are high:

| ontology_class_id | cross_pub | cross_pub material_conflict | ratio |
|---|---:|---:|---:|
| screw_chiller | 37 | 31 | 84% |
| centrifugal_chiller | 37 | 29 | 78% |
| ahu | 31 | 24 | 77% |
| water_source_heat_pump | 9 | 6 | 67% |
| air_cooled_modular_heat_pump | 7 | 6 | 86% |
| standard_reference | 2 | 2 | 100% |

### First-Pass Quality Read

This is a first-pass evidence read from source names, value summaries, and evidence text, not a replacement for operator review.

- Likely true/acceptable value diversity: about 5/30. Examples: `power_supply`, `能量调节范围`, `油加热器预热时间`, `环境温度`, `安装空间要求`.
- Mixed but not clean publisher disagreement: about 7/30. Examples: `制冷量` has real capacity values but also includes `压缩机输入功率`; `COP` has real COP values but also includes `capacity_range`.
- Likely semantic over-merge: about 18/30. Examples: `air_flow_range` includes air leakage and humidification; `face_velocity_limits` includes subcooling and cooling condition; `排水管接口尺寸` includes evaporator/condenser pipe concepts and flow/pressure requirement.

Conclusion: material_conflict is mostly a merge-quality signal in this batch, not mostly true cross-vendor engineering disagreement. The CSV is suitable for operator hand-labeling; I would not use these material_conflict KOs as GA consensus evidence until reviewed.

## Task B: Canonical Key Boundary Trace

No `grouping_trace.jsonl` exists under `output/diagnostic/20260515T173143Z_phase1_keep_text/`, so cluster-level trace for this exact phase1 run is unavailable. The boundary trace therefore uses persisted KO state, evidence, and source review-pack candidates. Source lookup includes phase1 accepted packs and earlier visual accepted packs because some authority layers predate phase1.

### ko_0d07e38beb2cde12

- DB ontology: `centrifugal_chiller`
- Canonical key: `hvac:ahu:performance_spec:key_bc82deec2d`
- Source candidates found in review packs route to `centrifugal_chiller`.
- Persisted KO ontology is also `centrifugal_chiller`.
- Mismatch: only final canonical_key prefix is `hvac:ahu`.

Judgement: bug, likely merge/upsert canonical_key inheritance. It is not explained by extraction routing. Also contains a semantic bad layer: `压缩机输入功率(制冷)` merged into `制冷量`.

### ko_43f6959cb535869f

- DB ontology: `centrifugal_chiller`
- Canonical key: `hvac:screw_chiller:performance_spec:cop`
- Source candidates found in review packs route to `centrifugal_chiller`.
- Persisted KO ontology is also `centrifugal_chiller`.
- Mismatch: only final canonical_key prefix is `hvac:screw_chiller`.

Judgement: bug, likely merge/upsert canonical_key inheritance. It is not explained by extraction routing. Also contains a semantic bad layer: `capacity_range` merged into COP.

### ko_05cadbc5549457f3

- DB ontology: `standard_reference`
- Canonical key: `hvac:standard_reference:application:method_of_testing_thermal_storage_devices`
- Prefix matches ontology.
- The problematic layer is semantic: a Trane design-guide `ASHRAE 90.1-2001` heat-recovery condition merged into ASHRAE standard method listings.

Judgement: not a canonical-prefix boundary bug. It is a semantic over-merge within `standard_reference`.

### Wider Prefix Check

Across the current DB, prefix mismatches are not isolated to the three report examples:

| ontology_class_id | prefix_mismatch count |
|---|---:|
| screw_chiller | 16 |
| air_cooled_modular_heat_pump | 9 |
| water_source_heat_pump | 5 |
| centrifugal_chiller | 3 |
| chiller | 2 |
| ahu | 2 |
| magnetic_bearing_chiller | 1 |

Conclusion: canonical_key prefix/ontology mismatch is a real bug class, not a feature.

## Task C: Slugifier Chinese Regression

20 actual Chinese hash-key KO names were tested with `_slugify_part`.

Result: 20/20 fell through to hash fallback because `_slugify_part` keeps only `[a-zA-Z0-9]`, so pure Chinese names collapse to an empty intermediate slug.

Examples:

| input | `_slugify_part` | fallback reason | fallback slug |
|---|---|---|---|
| 启动电流 | empty | empty_after_ascii_regex | `key_9fc1319bb1` |
| 制冷剂 | empty | empty_after_ascii_regex | `key_b45c97cb55` |
| 油加热器预热时间 | empty | empty_after_ascii_regex | `key_d4a11fbe9e` |
| 排气压力 | empty | empty_after_ascii_regex | `key_6428129801` |
| 重启抑制时间设定值 | empty | empty_after_ascii_regex | `key_42f5d7a8ec` |

Verdict: `needs_fix`. This is systematic for Chinese, not a corner case. The fallback avoids degenerate numeric keys, but it is too aggressive for CJK text because it does not transliterate or preserve CJK tokens.

## Total Judgement

- material_conflict: mostly merge-quality noise / over-merge in this batch, with a minority of true or acceptable value diversity. Needs operator sample review before treating Phase 1 KEEP_TEXT cross_pub as production-quality consensus.
- canonical_key boundary: bug. At least two concrete cases show source and KO ontology are `centrifugal_chiller` but final canonical_key kept another ontology prefix. Wider SQL found 38 prefix mismatches across classes.
- slugifier: bug for Chinese canonical readability. 100% of the 20 tested Chinese cases hash because the slug regex strips all CJK characters.

Recommended next engineering sequence before scanned visual track:

1. Fix canonical_key prefix normalization at merge/upsert boundaries so persisted `ontology_class_id` and canonical_key prefix cannot diverge.
2. Fix Chinese slug strategy: preserve CJK tokens or add deterministic transliteration before hash fallback.
3. Add a read-only/material_conflict audit gate that flags clusters where source names span unrelated facets or where evidence values are model-table rows rather than same conceptual parameter across publishers.
4. Re-run a small regroup/apply smoke after fixes before launching the 93 scanned visual PDFs.
