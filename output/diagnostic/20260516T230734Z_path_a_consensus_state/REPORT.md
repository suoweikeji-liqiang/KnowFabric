# Path A Consensus State Split Report

Generated: 2026-05-17 07:08 CST

## Summary

Path A split the legacy `material_conflict` bucket into explicit consumer-facing states:

- `value_disagreement`: same concept/facet, different publisher values; sw_base_model may display as real OEM disagreement.
- `over_merge`: facet/reference/subsystem mismatch; KnowFabric quality issue, route to review queue and do not surface.
- `material_conflict`: retained as legacy fallback; retag run leaves none in the current DB.

DB column check: `knowledge_object.consensus_state` is `character varying` / `varchar`, so no migration was required.

Backup before write: `/tmp/path_a_pre_retag_20260516T230758Z.sql`.

## Retag Distribution

| state | before in retag set | after in retag set |
| --- | --- | --- |
| material_conflict | 1025 | 0 |
| over_merge | 0 | 48 |
| partial_conflict | 0 | 253 |
| value_disagreement | 0 | 724 |

Changed rows: 1025. Current full DB state after retag: `agreed=6223`, `single_source=2529`, `partial_conflict=457`, `value_disagreement=724`, `over_merge=48`, `material_conflict=0`.

## Retag By Ontology

| ontology_class_id | value_disagreement | partial_conflict | over_merge |
| --- | --- | --- | --- |
| (blank) | 213 | 46 | 8 |
| ahu | 61 | 27 | 7 |
| air_cooled_modular_heat_pump | 30 | 7 | 4 |
| centrifugal_chiller | 68 | 37 | 9 |
| chiller | 2 | 3 | 0 |
| hot_water_plant | 4 | 0 | 2 |
| magnetic_bearing_chiller | 0 | 1 | 0 |
| screw_chiller | 220 | 75 | 12 |
| standard_reference | 24 | 30 | 4 |
| variable_frequency_drive | 1 | 0 | 0 |
| water_source_heat_pump | 101 | 27 | 2 |

Notes:

- `over_merge=48`, under the requested full-library ceiling of 50.
- `partial_conflict=253` from legacy `material_conflict` reflects cases with missing facet axes; these were intentionally not forced into `over_merge`.
- Retag idempotency dry-run after the write returned `updated=0`.

## Contract And Code Changes

- Added `VALUE_DISAGREEMENT` and `OVER_MERGE` to `ConsensusState` in `packages/core/semantic_contract_v2.py`.
- Updated merger consensus classification in `packages/compiler/cross_source_merger.py`.
- Added idempotent retag CLI `scripts/retag_consensus_state.py`.
- Updated KnowFabric and co-located sw_base_model contract mirror wording for `consensus_state`.
- Updated contract mirror SHA baseline because this was an intentional contract change.

## Samples

Full CSV outputs:

- `retag_report.csv`
- `value_disagreement_sample10.csv` (restricted to KO with at least two known, non-unknown publishers)
- `over_merge_sample.csv`

### value_disagreement Sample 10

| ko_id | ontology | title | publishers | layers |
| --- | --- | --- | --- | --- |
| ko_3ac3ed118a4deba0 | (blank) | 压缩机输入功率 | 国祥; 日立; 美意 | 6 |
| ko_c318e02787c079a7 | (blank) | 机组重量 | 特灵; 麦克维尔 | 8 |
| ko_02deaee3cba9f419 | centrifugal_chiller | 冷却水进水温度 | 格力; Carrier; unknown | 4 |
| ko_b78884e814b4c143 | ahu | 机组重量 | 特灵; 美意; unknown | 6 |
| ko_2e68cf6fae21614f | water_source_heat_pump | 启动方式 | 美意; 麦克维尔 | 8 |
| ko_17f0b96529e22232 | ahu | 防冻措施 | 格力; 特灵; 美的; unknown | 5 |
| ko_ba9da9570cc0a8eb | (blank) | 启动电流 | 美意; 麦克维尔 | 8 |
| ko_2522ef9d2da1235a | (blank) | 制热量 | 美意; 麦克维尔 | 8 |
| ko_007c216c7e472be1 | centrifugal_chiller | 压缩机停机再启动间隔 | 日立; 格力; unknown | 3 |
| ko_e1c18677570a9686 | (blank) | 制冷剂充灌量 | 特灵; 美意; 麦克维尔; unknown | 8 |

### over_merge Sample 10

| ko_id | ontology | title | publishers | layers |
| --- | --- | --- | --- | --- |
| ko_11becc6d84e45ec3 | (blank) | 制冷量 | 特灵; 美意 | 8 |
| ko_2a48a81c382ba634 | (blank) | 制冷量 | 日立; 美意; unknown | 8 |
| ko_591ae739b27c71b9 | (blank) | 制冷额定总输入功率 | 麦克维尔 | 4 |
| ko_eb13c84bd93a04e3 | (blank) | 制热量 | 美意 | 6 |
| ko_4e94733f46e8b8a1 | (blank) | 名义制冷量 | 美意; 麦克维尔; unknown | 8 |
| ko_33a96a59e127e69a | (blank) | 名义制热量 | 美意; 麦克维尔; unknown | 8 |
| ko_6718ae939ea97fff | (blank) | 最大允许压力 | 日立 | 2 |
| ko_4f473c89ca544582 | (blank) | 水流量 | 特灵; 美意; unknown | 8 |
| ko_e0075dafbff580a7 | ahu | 制冷量 | 特灵; 美意 | 5 |
| ko_2ba76711e02b5977 | ahu | 制热量 | 美意 | 4 |

## Verification

- Oracle: PASS (`scripts/verify_cross_publisher_merge.py --skip-precheck`).
- Pytest: PASS (`433 passed`).
- Gates: PASS (`bash scripts/check-all`).

## Operator Review Pointers

- Inspect `over_merge_sample.csv` first; these 48 are likely Phase 2.5 facet gaps or historical clusters that should enter review.
- Inspect `value_disagreement_sample10.csv` for the new sw_base_model semantics: these should represent true OEM/source value differences, not hidden merge bugs.
