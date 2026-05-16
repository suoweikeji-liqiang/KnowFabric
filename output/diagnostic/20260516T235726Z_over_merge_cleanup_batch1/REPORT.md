# Over-merge Cleanup Batch 1 Report

Generated: 2026-05-17 07:59 CST

## Summary

- Backup before write: `/tmp/cleanup_batch1_pre_20260516T235745Z.sql`
- Structural KO repair: 685 empty-ontology KO repaired in total, including the 8 audit-listed `over_merge` structural KOs.
- False-positive state correction: 7 KO -> `value_disagreement`, 2 KO -> `agreed`.
- Extraction garbage soft-drop: 2 KO `review_status='rejected'`.
- `ontology_class_id=''`: 685 -> 0.
- `canonical_key LIKE 'hvac::%'`: 685 -> 0.
- `over_merge`: total 48 -> 31; active/non-rejected 48 -> 29.

## Root Cause Diagnosis

Path A retag is not the culprit: commit 72f31b3 retag_consensus_state.py only updates consensus_state, and the Path A retag report already carried blank ontology/canonical fields through as input evidence. The bad rows all have created_at on 2026-05-16 and evidence chunks named visual_page_..., so they came from the scanned visual apply path before this cleanup. The proximate structural cause was that earlier review packs/upsert allowed an empty equipment_class_id to reach merger persistence; _normalize_canonical_key_for_anchor then produced hvac::... keys because no assertion rejected the empty ontology segment. Current run_visual_parameter_batch.py routing no longer returns empty scope, and this batch adds fail-fast identity assertions in both merger upsert and retag.

## Structural Repair Scope

The prompt named 8 structural KOs, but the pre-cleanup SQL showed 685 rows with `ontology_class_id=''` and `canonical_key LIKE 'hvac::%'`. Fixing only 8 would leave the explicit acceptance check failing, so the cleanup script repaired the full structural class. The 8 audit-listed KOs are itemized below.

Structural route distribution for all 685 repaired rows:

| ontology_class_id | count |
| --- | --- |
| ahu | 116 |
| air_cooled_modular_heat_pump | 91 |
| centrifugal_chiller | 55 |
| chiller | 2 |
| screw_chiller | 329 |
| water_source_heat_pump | 92 |

### Audit-listed 8 Structural KOs

| ko_id | title | new ontology | old canonical excerpt | new canonical | primary file |
| --- | --- | --- | --- | --- | --- |
| ko_11becc6d84e45ec3 | 制冷量 | water_source_heat_pump | hvac::performance_spec:hvac::performance_spec:制冷量_制冷 | hvac:water_source_heat_pump:performance_spec:制冷量 | 莫问系列R134a满液式水水螺杆水源热泵冷水机组样本.pdf |
| ko_2a48a81c382ba634 | 制冷量 | screw_chiller | hvac::performance_spec:hvac::performance_spec:制冷量_制冷 | hvac:screw_chiller:performance_spec:制冷量_2 | 干式风冷螺杆式冷（热）水机组.pdf |
| ko_33a96a59e127e69a | 名义制热量 | screw_chiller | hvac::performance_spec:hvac::performance_spec:名义制热量_ | hvac:screw_chiller:performance_spec:名义制热量_2 | MAS风冷螺杆样本.pdf |
| ko_4e94733f46e8b8a1 | 名义制冷量 | screw_chiller | hvac::performance_spec:hvac::performance_spec:名义制冷量_ | hvac:screw_chiller:performance_spec:名义制冷量 | 7，水冷螺杆冷水.pdf |
| ko_4f473c89ca544582 | 水流量 | water_source_heat_pump | hvac::performance_spec:水流量_水流量_5 | hvac:water_source_heat_pump:performance_spec:水流量 | 满液螺杆式水地源热泵样本DJ-17-CD-01A.pdf |
| ko_591ae739b27c71b9 | 制冷额定总输入功率 | air_cooled_modular_heat_pump | hvac::performance_spec:制冷额定总输入功率 | hvac:air_cooled_modular_heat_pump:performance_spec:制冷额定总输入 | MCZ_MHZ系列_涡旋式风冷冷水（热泵）机组样本.pdf |
| ko_6718ae939ea97fff | 最大允许压力 | screw_chiller | hvac::performance_spec:最大允许压力 | hvac:screw_chiller:performance_spec:最大允许压力_2 | 水冷低温螺杆式冷水机组手册.pdf |
| ko_eb13c84bd93a04e3 | 制热量 | water_source_heat_pump | hvac::performance_spec:hvac::performance_spec:制热量_制热 | hvac:water_source_heat_pump:performance_spec:制热量_4 | 莫问系列R134a满液式水水螺杆水源热泵冷水机组样本.pdf |

Full structural CSV: `structural_changes.csv`.
Audit-listed subset CSV: `structural_audit8_before_after.csv`.

## State Corrections

| ko_id | title | before | after |
| --- | --- | --- | --- |
| ko_1d071b6223568b3b | 水流量 | over_merge | value_disagreement |
| ko_2d3b188217c0b0d4 | 压差/压力 | over_merge | value_disagreement |
| ko_4fe798a5fee250e2 | 频率上限控制模式 | over_merge | value_disagreement |
| ko_534fd0c2b1bac8ab | 水流量 | over_merge | value_disagreement |
| ko_bd10ecd70736fb0b | 最低运行噪音 | over_merge | value_disagreement |
| ko_bdb23b9ca27b48e5 | 标准制冷量 | over_merge | value_disagreement |
| ko_d9a76c77bbe67132 | 供油压力与油箱压力差 | over_merge | value_disagreement |
| ko_206163c136ed5d4b | Totalize Airflow from VAV Boxes | over_merge | agreed |
| ko_2b176becc0c0144b | 加油泵压力要求 | over_merge | agreed |

## Extraction Garbage Soft Drop

| ko_id | title | before review_status | after review_status | consensus_state |
| --- | --- | --- | --- | --- |
| ko_01a4a4047927d344 | Evap High Press | conflict_review_required | rejected | over_merge |
| ko_75c3a5d18c8eaa43 | Evaporator low pressure alarm delay | conflict_review_required | rejected | over_merge |

No KO or evidence rows were physically deleted.

## Defensive Assertions

Added `assert_valid_ko_identity` in `packages/compiler/cross_source_merger.py` and used it at:

- canonical-key normalization output
- `merge_candidates` merged KO construction
- `merge_with_existing` upsert path before DB write
- `scripts/retag_consensus_state.py` before retag decisions

New test coverage: `tests/test_cleanup_batch1_structural_guards.py` verifies empty equipment scope, double-colon canonical keys, and retag invalid identity are rejected.

## Verification

- SQL: `ontology_class_id=''` count = 0.
- SQL: `canonical_key LIKE 'hvac::%'` count = 0.
- SQL: `over_merge` total = 31; active/non-rejected = 29.
- Idempotency dry-run after cleanup: structural_total = 0.
- Oracle: PASS (`scripts/verify_cross_publisher_merge.py --skip-precheck`).
- Pytest: PASS (`436 passed`).
- Gates: PASS (`bash scripts/check-all`).
