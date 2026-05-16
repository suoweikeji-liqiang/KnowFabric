# Phase 2.5 Facet Expansion Report

Run directory: `output/diagnostic/20260516T122643Z_phase2_5_facet_expansion`

## Scope

Phase 2.5 added demand-driven orthogonal facets to reduce the remaining Phase 2 over-merge cases without rerunning extraction and without changing schema, oracle, or persisted evidence contracts.

## Backups

- `/tmp/phase2_5_pre_regroup_20260516T122627Z.sql` (247 MB)
- `/tmp/phase2_5_pre_regroup_refined_20260516T130417Z.sql` (253 MB)
- `/tmp/phase2_5_pre_regroup_layer_summary_fix_20260516T134106Z.sql` (258 MB)

The final DB state corresponds to the third regroup after the layer-summary expansion fix.

## Facet Expansion

Reference-point tags now loaded: 99.

Orthogonal axes:

| Axis | Values |
| --- | --- |
| fault_polarity | high, low, loss, sensor_fault, range_out |
| refrigerant | R22, R134a, R410A, R407C, R32, Ammonia |
| subsystem | Oil_System, Water_System, Refrigerant_System, Electrical_System, Control_System, Bearing_System, Compressor_System |
| operating_condition | Outdoor_Air_Condition, Return_Air_Condition, Mixed_Air_Condition, Standard_Cooling_Condition, Standard_Heating_Condition, High_Temperature_Condition, Low_Temperature_Condition, Part_Load_Condition |
| document_type | Test_Method, Performance_Rating, Certification_Requirement, Energy_Efficiency_Class, Design_Guideline |

New/expanded reference-point coverage includes refrigerant-specific pressure, water/refrigerant working pressure, AHU air-flow/leakage/humidification, differential-pressure operating points, nominal heating/cooling/input-power distinctions, maintenance intervals, and fault-specific reference points.

A residual bug was fixed in `_ko_to_candidates`: regroup-expanded candidates now use their own layer summary/evidence text instead of inheriting stale aggregate KO summary. This was required to split previously over-merged KOs such as `External Current Limit Setpoint` mixed with chilled-water temperature settings.

## Regression Tests

Phase 2.5 added 13 regression cases total (8 requested + 5 residual-sample cases):

| Case | Result |
| --- | --- |
| 排气压力 R22 vs 排气压力 R134a | PASS, split |
| 制冷量 新风工况 vs 制冷量 回风工况 | PASS, split |
| 油压差报警 vs 水压差报警 | PASS, split |
| 油换周期 vs 滤芯更换 | PASS, split |
| Test_Method A/B | PASS, kept together |
| 制冷量 标准制冷工况 vs 部分负荷工况 | PASS, split |
| 油温高 fault vs 排气温度高 fault | PASS, split |
| 排气压力 without refrigerant markers | PASS, kept together |
| Line Voltage Percentage vs 限流百分比 | PASS, split |
| 名义制热量 vs nominal_cooling_input_power | PASS, split |
| 最大负载点 ΔP2 / 最小压差设定值 / 激活压差 | PASS, split into 3 |
| 冷冻水重设范围 vs 冷冻水出水温度设定 | PASS, split |
| 低油压报警 vs 油压差过低 | PASS, split |

Targeted regression command: `41 passed` for Phase 2.5, regroup, Brick/unit, and embedding tests.

## Regroup Metrics

Pre Phase 2.5 baseline was the Phase 2 DB state:

| Ontology | Pre total | Pre cross_pub | Pre material_conflict | Pre material % | Post total | Post cross_pub | Post material_conflict | Post material % | Post max_layers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| centrifugal_chiller | 2651 | 16 | 11 | 68.8 | 4987 | 18 | 12 | 66.7 | 8 |
| standard_reference | 764 | 0 | 0 | 0.0 | 724 | 0 | 0 | 0.0 | 8 |
| ahu | 667 | 6 | 4 | 66.7 | 745 | 9 | 7 | 77.8 | 8 |
| screw_chiller | 297 | 12 | 8 | 66.7 | 280 | 20 | 15 | 75.0 | 5 |
| chiller | 105 | 0 | 0 | 0.0 | 104 | 0 | 0 | 0.0 | 5 |
| water_source_heat_pump | 104 | 1 | 1 | 100.0 | 100 | 2 | 1 | 50.0 | 8 |
| air_cooled_modular_heat_pump | 84 | 1 | 1 | 100.0 | 77 | 1 | 1 | 100.0 | 8 |
| hot_water_plant | 42 | 0 | 0 | 0.0 | 51 | 0 | 0 | 0.0 | 5 |
| magnetic_bearing_chiller | 12 | 0 | 0 | 0.0 | 12 | 0 | 0 | 0.0 | 1 |
| variable_frequency_drive | 8 | 0 | 0 | 0.0 | 8 | 0 | 0 | 0.0 | 2 |

Global final structural checks:

| Metric | Value |
| --- | ---: |
| total KO | 7093 |
| prefix mismatch | 0 |
| CJK hash key count | 41 (0.6%) |
| degenerate canonical_key | 0 |
| max_layers | 8 |
| cross_pub KO | 50 |
| cross_pub material_conflict | 36 (72.0%) |

Material-conflict ratio did not fall to the requested target. The evidence sample below suggests the remaining material_conflict pool is now mostly true value/model/rating disagreement rather than confirmed over-merge.

## Sample10 Over-Merge Audit

Sample file: `material_conflict_sample10_phase2_5.csv`.

Codex initial classification:

| Bucket | Count | Notes |
| --- | ---: | --- |
| confirmed over-merge | 0 | No sample has clear mixed physical quantity/subsystem/reference point after final regroup. |
| likely true merge/conflict | 8 | Same concept with different model values, ranges, or procedure detail. |
| needs human review | 2 | Cooling-water entering temperature has a suspicious Carrier `-40..118℃` layer; oil temperature range has value/rating ambiguity. |

Conservative reading: confirmed over-merge = 0/10 (0%). If all human-review cases are treated as failures, worst-case sample over-merge = 2/10 (20%). Operator review is needed before claiming <7% with high confidence.

Known bad residual from the second regroup was fixed: `External Current Limit Setpoint` is now a single-layer Trane KO and no longer contains chilled-water temperature layers.

## Verification

| Gate | Result |
| --- | --- |
| Oracle `scripts/verify_cross_publisher_merge.py --skip-precheck` | PASS |
| `venv/bin/python -m pytest tests -q` | PASS, 421 passed |
| `bash scripts/check-all` | PASS, 4/4 gates |

## Honest Read

- Structure is healthy: prefix mismatch remains 0, degenerate keys remain 0, max_layers remains capped at 8, CJK hash ratio remains <1%.
- Phase 2.5 fixed a real regroup plumbing issue: stale aggregate summaries were contaminating layer-level facet detection.
- The requested material_conflict-ratio target is not met. The ratio remains high because same-concept cross-publisher KOs often carry different model/rating values and therefore correctly land in `material_conflict`.
- The sample-based over-merge signal is much better than the raw material_conflict ratio: 0/10 confirmed over-merge, 2/10 needs human review.
