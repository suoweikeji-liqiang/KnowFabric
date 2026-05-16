# Phase 2 FIX Report

Run directory: `output/diagnostic/20260516T190832Z_phase2_fix`

## Summary

Phase 2A structural fixes are effective: CJK slug fallback is 0/20 in the regression sample, canonical-key prefix mismatch is 0 globally, hash-key share is 0.9%, degenerate canonical keys are 0, and max layers is 8.

Phase 2B over-merge mitigation is partial. The six named regression KOs are no longer large mixed clusters, but the global `material_conflict` ratio is still 69.4% (25/36). The 10-KO sample shows 1/10 clear over-merge, 2/10 needing human review, and most remaining conflicts are value disagreements inside apparently same concepts. So the current label is no longer a reliable over-merge proxy.

## Backups

- `/tmp/phase2_pre_regroup_20260516T103427Z.sql`
- `/tmp/phase2_failed_regroup_20260516T190757Z.sql`
- `/tmp/phase2_pre_regroup2_20260516T190832Z.sql`
- `/tmp/phase2_pre_extra_rekey_*.sql`

## Structural Metrics

| metric | value |
|---|---:|
| total KO | 4737 |
| prefix mismatch | 0 |
| hash key count | 43 (0.9%) |
| degenerate canonical key | 0 |
| max layers | 8 |
| cross_pub KO | 36 |
| cross_pub material_conflict | 25 (69.4%) |

## Per-Class Metrics

| ontology_class | total | cross_pub | material_conflict | material_pct | max_layers |
|---|---:|---:|---:|---:|---:|
| centrifugal_chiller | 2651 | 16 | 11 | 68.8 | 8 |
| standard_reference | 764 | 0 | 0 |  | 8 |
| ahu | 667 | 6 | 4 | 66.7 | 8 |
| screw_chiller | 297 | 12 | 8 | 66.7 | 8 |
| chiller | 105 | 0 | 0 |  | 5 |
| water_source_heat_pump | 104 | 1 | 1 | 100.0 | 8 |
| air_cooled_modular_heat_pump | 84 | 1 | 1 | 100.0 | 8 |
| hot_water_plant | 42 | 0 | 0 |  | 6 |
| magnetic_bearing_chiller | 12 | 0 | 0 |  | 1 |
| variable_frequency_drive | 8 | 0 | 0 |  | 2 |
| condenser_water_pump | 1 | 0 | 0 |  | 2 |
| cooling_tower | 1 | 0 | 0 |  | 1 |
| chilled_water_pump | 1 | 0 | 0 |  | 2 |

## Slugifier CJK Regression

- `启动电流` -> `启动电流` fallback=False
- `制冷剂` -> `制冷剂` fallback=False
- `油加热器预热时间` -> `油加热器预热时间` fallback=False
- `排气压力` -> `排气压力` fallback=False
- `重启抑制时间设定值` -> `重启抑制时间设定值` fallback=False
- `全自动启动顺序` -> `全自动启动顺序` fallback=False
- `排水管接口尺寸` -> `排水管接口尺寸` fallback=False
- `能量调节范围` -> `能量调节范围` fallback=False
- `性能系数` -> `性能系数` fallback=False
- `油压差报警/保护` -> `油压差报警_保护` fallback=False
- `推力轴承—油温传感器` -> `推力轴承_油温传感器` fallback=False
- `重启抑制时间设定值` -> `重启抑制时间设定值` fallback=False
- `进口温度` -> `进口温度` fallback=False
- `蒸发器制冷剂温度` -> `蒸发器制冷剂温度` fallback=False
- `水侧承压` -> `水侧承压` fallback=False
- `导流叶片控制模式` -> `导流叶片控制模式` fallback=False
- `冷凝器冻结点温度` -> `冷凝器冻结点温度` fallback=False
- `转速` -> `转速` fallback=False
- `油压` -> `油压` fallback=False
- `盘管进出水管径` -> `盘管进出水管径` fallback=False

Full table: `slugifier_zh_regression.md`.

## Canonical Prefix Normalization

Implemented existing-KO re-key pre-pass in `merge_with_existing`. It uses a two-phase temp-key move to avoid PostgreSQL unique-key swap collisions.

Result: prefix mismatch 91 at restored baseline, 0 after final regroup/re-key.

## Brick Facet Map

`brick_facet_map.yaml` now has 75 `brick_reference_points`. It covers the requested pressure, temperature, flow, fault polarity, and Phase 1 boundary concepts. Added chilled-water setpoint keywords so the oracle Trane/McQuay chilled-water pair is a deterministic same-subtype merge.

## LLM Arbiter Strict Mode

Strict prompt is enabled for clusters larger than 3, with `merge` / `split_groups` JSON handling and cache version `phase2_strict_v1`. Runtime trigger counts were not persisted separately; traces are in `grouping_trace_r2/`, `grouping_trace_extra/`, `upsert_trace_r2/`, and `upsert_trace_extra/`.

## Six Regression KOs

| KO | title | state | layers | pubs | canonical_key |
|---|---|---|---:|---|---|
| ko_3fde94ba89d7abd8 | 排水管接口尺寸 | single_source | 1 | ['York'] | `hvac:centrifugal_chiller:performance_spec:排水管接口尺寸` |
| ko_13be08b257cfe5ef | 排气压力 | single_source | 1 | ['天加'] | `hvac:screw_chiller:performance_spec:排气压力` |
| ko_ac1ec4ada2e33a7b | air_flow_range | single_source | 1 | ['Carrier'] | `hvac:ahu:performance_spec:air_flow_range` |
| ko_1c30a6cbb8f911c0 | 能量调节范围 | single_source | 1 | ['Haier'] | `hvac:water_source_heat_pump:parameter:能量调节范围` |
| ko_0aa4c474998d9d3b | Room temperature and humidity limits | agreed | 2 | ['盾安'] | `hvac:centrifugal_chiller:application:room_temperature_and_humidity_limits` |
| ko_02e2749573080a28 | 推力轴承—油温传感器 | single_source | 1 | ['York'] | `hvac:centrifugal_chiller:fault_code:推力轴承_油温传感器` |

Interpretation: the five problematic over-merge examples are now single-source or small clean KOs. `Room temperature and humidity limits` remains a small agreed KO, but only within publisher `盾安` in the current DB.

## Material Conflict Sample

Sample CSV: `material_conflict_sample10.csv`.

First-pass verdict: 1/10 clear over-merge, 2/10 needs human review, 7/10 appear to be true same-concept value disagreements or clean procedural/fault merges with differing values.

## Verification

- Oracle: PASS.
- Pytest: 407 passed.
- Gates: `bash scripts/check-all` PASS, 4/4 gates.

## Final Read

Done: slugifier, prefix normalization, Brick expansion, strict arbiter, 0.90 generic threshold with 0.85 same-facet recluster, fault-code split path, regression tests, oracle, pytest, gates.

Not done: global `material_conflict` ratio target <30%; final is 69.4%. Next fix should either split material-conflict KOs with a dedicated second arbiter pass or separate ordinary `value_disagreement` from semantic over-merge in consensus labeling.
