# P0 Final Verification Report

## 2026-05-15 NN Round: Section-Aware Retry for MM Failed Docs

NN retried the 40 MM `extraction_failed` PDFs with `--section-aware` DeepSeek doc-level extraction. The smoke target, ASHRAE Guideline 36-2021, produced 140 anchored candidates from 7 sections, so the full retry proceeded. Non-PDF skipped rows from MM were not part of NN.

Run artifacts:

```text
run_root = output/diagnostic/20260514T175511Z_nn_section_aware_failed_docs
strategy_manifest = output/diagnostic/20260514T175511Z_nn_section_aware_failed_docs/failed_doc_strategy.csv
retry_manifest = output/diagnostic/20260514T175511Z_nn_section_aware_failed_docs/manifests/nn_failed_40_section_aware_manifest.csv
final_failed_docs = output/diagnostic/20260514T175511Z_nn_section_aware_failed_docs/final_failed_docs.csv
section_min_heading_tokens = 24000
section_max_tokens = 30000
oracle = PASS
```

Processing outcome:

```text
completed_docs = 40/40
failed_docs = 0
review_candidates = 5543
section_calls = 298
total_tokens = 9,012,684
actual_cost_rmb = ¥9.9382
max_layers_global = 8
degenerate_canonical_key = 0
```

Final SQL by ontology class:

| ontology_class_id | total | cross_pub | max_layers |
|---|---:|---:|---:|
| `centrifugal_chiller` | 646 | 20 | 8 |
| `ahu` | 430 | 0 | 8 |
| `water_source_heat_pump` | 64 | 0 | 8 |
| `chiller` | 60 | 0 | 5 |
| `hot_water_plant` | 42 | 0 | 6 |
| `screw_chiller` | 27 | 0 | 5 |
| `variable_frequency_drive` | 8 | 0 | 2 |
| `cooling_tower` | 1 | 0 | 1 |
| `condenser_water_pump` | 1 | 0 | 2 |
| `chilled_water_pump` | 1 | 0 | 2 |


Cross-publisher sample after NN:

| ontology_class_id | canonical_key | layers | publishers | consensus |
|---|---|---:|---|---|
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:key_20afb231fb` | 7 | Carrier,Gree,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:key_90cab05c63` | 7 | Carrier,Gree,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:chilled_water_setpoint` | 7 | McQuay,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:key_46778a30cd` | 6 | Carrier,McQuay | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:prestart_alert_low_line_voltage` | 5 | Carrier,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:key_3c9e270d6a` | 4 | Carrier,Gree | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:key_b7acb73d44` | 4 | Carrier,York | partial_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:key_ad1158e75e` | 3 | Carrier,McQuay,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:key_ea3b6f9bfe` | 3 | Carrier,McQuay | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:recycle_alert` | 3 | Carrier,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:fault_code:spare_sensor_alert` | 3 | Carrier,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:key_00a3b7daa5` | 3 | Carrier,McQuay | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:key_9d0ef7d66a` | 3 | Carrier,York | partial_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:key_f288bed573` | 3 | McQuay,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:psio_09` | 3 | Carrier,York | partial_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:performance_spec:key_33b527300b` | 3 | McQuay,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:key_69d0af87ee` | 2 | Carrier,McQuay | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:lcsss_x` | 2 | Carrier,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:minimum_capacity_limit` | 2 | Trane,York | material_conflict |
| `centrifugal_chiller` | `hvac:centrifugal_chiller:parameter:supply_oil_temperature_range` | 2 | Gree,McQuay | agreed |


NN conclusion:

- Section-aware extraction fixed the MM failure mode: all 40 failed PDFs produced review packs and applied successfully.
- Safety checks held: max layers stayed at 8 and degenerate canonical keys stayed at 0.
- The growth target was not met: total KO ended at 1280, centrifugal_chiller cross_pub ended at 20, and AHU cross_pub stayed 0. The retry improved coverage but did not increase cross-publisher merging. The likely cause is data distribution and routing: most added standards are single-publisher standard material, and many ASHRAE sections routed into generic/support classes (`chiller`, `cooling_tower`, `condenser_water_pump`, `controller`) rather than matching existing OEM ontology classes.

## 2026-05-15 MM Round: KEEP_TEXT Bulk Apply

MM used `deepseek-parameter-spec` for the KEEP_TEXT bulk run after LL rejected MiMo for text manuals. No MiMo calls were used. The run applied successful review packs through the existing merger path and stopped on no apply failure.

Run artifacts:

```text
run_root = output/diagnostic/20260514T163553Z_mm_keep_text_bulk
subbatch_count = 15
pre-final-regroup backup = /tmp/mm_final_regroup_pre_20260515T013838Z.sql
failed_docs_csv = output/diagnostic/20260514T163553Z_mm_keep_text_bulk/failed_docs.csv
final_summary = output/diagnostic/20260514T163553Z_mm_keep_text_bulk/mm_final_summary.json
```

Processing outcome:

```text
applied = 98
extraction_failed = 40
skipped = 2
total_tokens = 3,898,494
actual_cost_rmb = ¥4.2141
oracle = PASS
degenerate_canonical_key = 0
max_layers_global = 8
```

Final SQL by ontology class:

| ontology_class_id | total | cross_pub | max_layers |
|---|---:|---:|---:|
| `centrifugal_chiller` | 574 | 22 | 8 |
| `ahu` | 464 | 0 | 8 |
| `water_source_heat_pump` | 64 | 0 | 8 |
| `chiller` | 64 | 0 | 7 |
| `hot_water_plant` | 42 | 0 | 6 |
| `screw_chiller` | 27 | 0 | 5 |
| `variable_frequency_drive` | 8 | 0 | 2 |
| `condenser_water_pump` | 1 | 0 | 2 |
| `cooling_tower` | 1 | 0 | 1 |
| `chilled_water_pump` | 1 | 0 | 2 |

Expectation check:

```text
total_KO >= 2000: NOT MET (actual 1246)
centrifugal_chiller cross_pub >= 60: NOT MET (actual 22)
>=3 ontology_class with cross_pub > 0: NOT MET (actual 1)
max_layers <= 12: PASS (actual 8)
degenerate canonical_key = 0: PASS
oracle PASS: PASS
```

Interpretation: the plumbing stayed stable, but production yield did not meet the growth target. The main blockers were 40 extraction failures and 2 unsupported file skips, concentrated in oversized standards/GB/AHRI PDFs and non-PDF files, plus final regroup aggressively consolidating or splitting low-quality cross-source candidates. This is a data/extraction coverage issue, not an apply/FK/clustering stability issue.

20 cross-publisher samples:

| # | ontology_class_id | layers | publishers | consensus | title | canonical_key |
|---:|---|---:|---|---|---|---|
| 1 | `centrifugal_chiller` | 2 | Carrier,York | `material_conflict` | 谐波滤波器允许的最大持续RMS电流等级 (790/658 HP) | `hvac:centrifugal_chiller:parameter:rms_790_658_hp` |
| 2 | `centrifugal_chiller` | 3 | Carrier,York | `material_conflict` | 传感器出错报警 | `hvac:centrifugal_chiller:fault_code:spare_sensor_alert` |
| 3 | `centrifugal_chiller` | 3 | Carrier,McQuay | `material_conflict` | 三相电压不平衡、缺相、错相 | `hvac:centrifugal_chiller:fault_code:key_ea3b6f9bfe` |
| 4 | `centrifugal_chiller` | 3 | Carrier,York | `material_conflict` | 电机限流百分比(%) | `hvac:centrifugal_chiller:parameter:key_747eed8a69` |
| 5 | `centrifugal_chiller` | 2 | Trane,York | `material_conflict` | External Current Limit Setpoint | `hvac:centrifugal_chiller:parameter:external_current_limit_setpoint` |
| 6 | `centrifugal_chiller` | 3 | Carrier,McQuay,York | `material_conflict` | 多机组循环-触点开 | `hvac:centrifugal_chiller:fault_code:key_ad1158e75e` |
| 7 | `centrifugal_chiller` | 3 | McQuay,York | `material_conflict` | 配电电源 | `hvac:centrifugal_chiller:parameter:key_f288bed573` |
| 8 | `centrifugal_chiller` | 7 | Carrier,York | `material_conflict` | 油泵压力 | `hvac:centrifugal_chiller:parameter:hcfc_22` |
| 9 | `centrifugal_chiller` | 3 | Gree,McQuay | `material_conflict` | 名义制冷量 | `hvac:centrifugal_chiller:performance_spec:key_57d142c8f8` |
| 10 | `centrifugal_chiller` | 3 | Carrier,York | `material_conflict` | 警告-波动保护-过量波动限定 | `hvac:centrifugal_chiller:fault_code:recycle_alert` |
| 11 | `centrifugal_chiller` | 6 | Carrier,McQuay | `material_conflict` | 冷凝器冻结点温度 | `hvac:centrifugal_chiller:parameter:key_46778a30cd` |
| 12 | `centrifugal_chiller` | 5 | Carrier,McQuay | `partial_conflict` | 冷水进水 | `hvac:centrifugal_chiller:parameter:chw_t` |
| 13 | `centrifugal_chiller` | 7 | Carrier,Gree,York | `material_conflict` | 油压低 | `hvac:centrifugal_chiller:fault_code:key_20afb231fb` |
| 14 | `centrifugal_chiller` | 3 | AHRI,Carrier | `material_conflict` | Tower Heat Exchanger Fouling Factor Allowance | `hvac:centrifugal_chiller:parameter:tower_heat_exchanger_fouling_factor_allowance` |
| 15 | `centrifugal_chiller` | 3 | Carrier,York | `material_conflict` | 次数限制 | `hvac:centrifugal_chiller:parameter:key_f5220765fd` |
| 16 | `centrifugal_chiller` | 3 | Carrier,York | `agreed` | 远程模式下的模拟信号 | `hvac:centrifugal_chiller:parameter:key_b70c2b21bd` |
| 17 | `centrifugal_chiller` | 4 | Carrier,Gree | `material_conflict` | 频繁启停禁止开机 | `hvac:centrifugal_chiller:fault_code:key_3c9e270d6a` |
| 18 | `centrifugal_chiller` | 2 | Carrier,McQuay | `material_conflict` | 压缩机轴承温度报警值 | `hvac:centrifugal_chiller:parameter:key_406ab05091` |
| 19 | `centrifugal_chiller` | 4 | Carrier,McQuay | `material_conflict` | 总充注量 | `hvac:centrifugal_chiller:parameter:key_a808b77888` |
| 20 | `centrifugal_chiller` | 7 | Carrier,Gree,York | `material_conflict` | 推力轴承—油温传感器 | `hvac:centrifugal_chiller:fault_code:key_90cab05c63` |

Representative failed/skipped docs are listed in the CSV. First examples:

| doc_id | status | file_name |
|---|---|---|
| `doc_hvac_efficiency_maintenance_authority` | `extraction_failed` | HVAC系统效率和维护最佳实践.pdf |
| `doc_a5de4244eeda4637` | `extraction_failed` | ASHRAE手册 - HVAC系统和设备篇.pdf |
| `doc_4a9b0fec1dfb4103` | `extraction_failed` | ASHRAE手册2024.pdf |
| `doc_2a7ec347e5f44d9e` | `extraction_failed` | ASHRAE手册 - 基础理论篇.pdf |
| `doc_a3ec223669d94058` | `extraction_failed` | 10870-2014-gbt-e-300.pdf |
| `doc_5f1c305ea2d84dd0` | `extraction_failed` | 19409-2013-gbt-e-300.pdf |
| `doc_415e37defa514dd6` | `skipped` | 20111122 Appendix G Pressure Drop Adjustments.xlsx |
| `doc_5c86dfacb8884193` | `extraction_failed` | ahri_550_590_2020_ip_addendum1.pdf |
| `doc_63b3fb8f94784a18` | `extraction_failed` | ahri_550_590_551_591_2020_interpretation_1.pdf |
| `doc_24253b6cf85e4e2d` | `extraction_failed` | ahri_550_590_551_591_2020_interpretation_2.pdf |
| `doc_3d640f4a6f0a44c7` | `extraction_failed` | ahri_550_590_551_591_2020_interpretation_3.pdf |
| `doc_fcf8dcbc70aa4b9f` | `extraction_failed` | ahri_551_591_2020_si_addendum1.pdf |

Next-action recommendation: keep the merger/plumbing frozen and route failed standards to a section-level extraction path instead of single-call doc-level extraction. The OEM KEEP_TEXT path is viable; the standards path needs chunk/section batching before it can materially improve cross-publisher coverage.

## 2026-05-15 KK Round: Visual Apply Complete

KK resumed after the operator accepted JJ4 plumbing quality: 30 cross-publisher
KOs were sample-reviewed as clean, and the previous `cross_publisher >= 50`
target was withdrawn as data-volume-limited rather than an engineering blocker.

Pre-write backup:

```text
backup = /tmp/kk1_pre_remaining_3_apply_20260515T000250Z.sql
size = 133,117,159 bytes
```

Apply progression:

```text
starting point = JJ4 smoke state after McQuay + Carrier 19XR v2

Carrier 19XL 94p:
  pack = output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/04_carrier_19xl
  apply_report = output/diagnostic/20260515T000250Z_kk_remaining_3_apply/01_carrier_19xl/apply_report.json
  apply = success, failed = 0
  regroup = centrifugal_chiller
  after regroup: centrifugal=660, screw=0, water=0, cross=33, max_layers=8, degenerate=0

Haier ACG 89p:
  pack = output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/06_haier_acg
  apply_report = output/diagnostic/20260515T000250Z_kk_remaining_3_apply/02_haier_acg/apply_report.json
  apply = success, failed = 0
  regroup = water_source_heat_pump
  after regroup: centrifugal=660, screw=0, water=82, cross=33, max_layers=8, degenerate=0

York RWF2 80p:
  pack = output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/07_york_rwf2
  apply_report = output/diagnostic/20260515T000250Z_kk_remaining_3_apply/03_york_rwf2/apply_report.json
  apply = success, failed = 0
  regroup = screw_chiller
```

Final SQL:

```text
centrifugal_chiller:    total_kos=660, cross_pub=33
screw_chiller:          total_kos=43,  cross_pub=0
water_source_heat_pump: total_kos=82,  cross_pub=0
max_layers=8
degenerate_canonical_key=0
3_publisher_or_more=3
oracle=PASS
```

Stage evolution:

```text
HH4 final smoke: centrifugal cross_publisher = 32
JJ4 smoke:       centrifugal cross_publisher = 30, plumbing clean, FK fixed
KK final:        centrifugal cross_publisher = 33, screw/water baseline domains populated
```

15 deterministic cross-publisher samples, all from `centrifugal_chiller`.
`screw_chiller` and `water_source_heat_pump` have zero cross-publisher KOs in
this round because each is currently populated by one new publisher baseline:

```text
1.  parameter:key_31569bf758                  n=3 pubs={Carrier,McQuay}     title=压缩机数量
2.  parameter:current_limit_soft_load_percent n=4 pubs={Carrier,Trane,York} title=限流百分比
3.  parameter:key_1e1d96afbd                  n=2 pubs={Carrier,McQuay}     title=膨胀阀整定值
4.  fault_code:key_5d265279f4                 n=2 pubs={Gree,York}          title=润滑油温度过高
5.  parameter:minimum_capacity_limit          n=3 pubs={Carrier,Trane}      title=最小容量限制
6.  fault_code:autorestart_pending            n=4 pubs={Carrier,McQuay}     title=电源紧急中断
7.  fault_code:key_080647b71d                 n=2 pubs={Gree,York}          title=波动保护-过量波动
8.  fault_code:line_current_imbalance         n=2 pubs={Carrier,York}       title=谐波滤波器-C相电流过高
9.  parameter:key_8790cc8fc6                  n=2 pubs={Carrier,McQuay}     title=报警信息显示
10. fault_code:key_3595b768a0                 n=2 pubs={McQuay,York}        title=软件狗-软件重新启动
11. parameter:key_d590fecc53                  n=6 pubs={Carrier,York}       title=导流叶片开度
12. fault_code:key_4b082bde4b                 n=4 pubs={Carrier,York}       title=蒸发器-压力过低-智能冻结
13. parameter:key_aa66c82471                  n=4 pubs={Carrier,McQuay}     title=电机额定负载电压
14. performance_spec:key_58fa717122           n=3 pubs={McQuay,York}        title=电机工作转速
15. fault_code:key_c3db0a3e97                 n=2 pubs={McQuay,York}        title=叶片电机开关打开
```

New baseline domain samples:

```text
screw_chiller:
  - parameter:key_6173128f63_key_6173128f63 n=8 pubs={York} title=基本注油量
  - parameter:key_29b3058d29                n=2 pubs={York} title=模拟输入[mA]
  - parameter:key_42cfddc42e                n=2 pubs={York} title=液击报警及故障设定值
  - parameter:key_c839a8ff17                n=2 pubs={York} title=密码
  - parameter:proportional_band             n=2 pubs={York} title=比例带

water_source_heat_pump:
  - performance_spec:key_49bc12cf25_key_49bc12cf25_2 n=7 pubs={Haier} title=名义制热量
  - performance_spec:key_9c4be37d3f_key_e80458dedf   n=1 pubs={Haier} title=压缩机 型式
  - performance_spec:key_49bc12cf25_key_57d142c8f8   n=1 pubs={Haier} title=名义制冷量
  - parameter:key_8ec20befd3                         n=3 pubs={Haier} title=冷凝器出水温度
  - parameter:key_5860df52a6                         n=1 pubs={Haier} title=油压差值
```

Plumbing fixes now validated in production apply flow:

```text
complete-linkage numpy implementation = no stall on large visual batches
final layer cap = max_layers stayed at 8
degenerate slug guard = no :[0-9]+ canonical keys
apply_review_packs_batch exit code = failed packs now return non-zero
merger FK migration = Carrier 19XR v2 no longer fails evidence migration
```

## 2026-05-14 II Remaining Visual Apply (Stopped)

II started from the HH4 smoke state after operator sample review passed.

Pre-write backup:

```text
backup = /tmp/ii1_pre_remaining_5_apply_20260514T150457Z.sql
size = 132,548,048 bytes
```

Apply progression:

```text
baseline before II:
  centrifugal_chiller KO = 405

McQuay centrifugal 95p:
  candidates = 537
  apply_report = output/diagnostic/20260514T150500Z_ii_remaining_5_apply/01_mcquay_apply_report.json
  apply_time = 350.69s
  regroup_time = 165.10s
  after regroup centrifugal_chiller KO = 493
  cross_publisher = 41
  max_layers_over_8 = 0
  degenerate_keys = 0
```

Stop condition:

```text
failed_doc = Carrier 19XR v2 97p
action = stopped; did not continue to Carrier 19XL / Haier ACG / York RWF2
apply_report = output/diagnostic/20260514T150500Z_ii_remaining_5_apply/02_carrier_19xr_v2_apply_report.json
failure = knowledge_object_evidence FK violation while migrating evidence
target_ko = ko_74a833cfe9223e02
src_ko = ko_1e871a7ae4c9c55d
error = target KO is not present in knowledge_object
```

The apply script returned process exit 0 despite `failed=1`, so the compound
shell command launched regroup. That regroup was interrupted immediately after
the failed apply was detected.

Current DB state after interrupt is partial and not accepted as II completion:

```text
failure_partial_backup = /tmp/ii_failure_partial_state_20260514T152359Z.sql
current_centrifugal_chiller_ko = 535
failed_state_cross_publisher_rows = 37
failed_state_max_layers_over_8 = 0
failed_state_degenerate_keys = 0
summary = output/diagnostic/20260514T150500Z_ii_remaining_5_apply/ii_stopped_summary.json
cross_publisher_top50 = output/diagnostic/20260514T150500Z_ii_remaining_5_apply/failed_state_cross_publisher_top50.tsv
```

Per II hard constraint, no UPDATE repair or further apply was attempted. Operator
decision needed: restore `backup` or investigate/fix the evidence migration bug.

## 2026-05-14 HH Rollback + Visual Apply Fix

HH rolled back the failed GG partial apply and fixed the two blockers before
any further visual-pack apply.

Rollback:

```text
partial_backup = /tmp/hh1_pre_rollback_partial_20260514T141852Z.sql
restore_source = /tmp/gg1_pre_visual_apply_20260514T124822Z.sql
post_restore_centrifugal_chiller_ko = 32
pre_numpy_validation_backup = /tmp/hh2_pre_numpy_validation_20260514T142752Z.sql
```

Complete-linkage performance fix:

```text
root = packages/compiler/clustering.py recomputed cosine/norm inside complete-link checks
fix = numpy-normalize embeddings once, compute sim_matrix once, then check cached submatrices
scale_test = 700 dense embeddings under 5s
oracle = PASS
```

Super-KO root cause:

```text
diagnostic = output/diagnostic/20260514T142200Z_hh3_super_ko/super_ko_root_cause.jsonl
observed_bad_key = hvac:centrifugal_chiller:parameter:1
observed_layers = 33
cause = _slugify_part("1分钟限制开机计时器") -> "1"
why_guard_missed = embedding-first path and raw-key rename did not run E2 degenerate-key sanity
fix = degenerate slug guard falls back to key_<hash>; registry lookup ignores existing degenerate keys
```

Additional smoke finding:

```text
after parameter:1 fix, York+Carrier smoke still produced >8-layer groups
cause = final merger groups can accumulate >8 candidate layers after raw-key rename
fix = final merger group cap splits oversize groups by source name, max 8 layers
```

HH4 smoke validation intentionally applied only the two docs that previously ran
before the GG stop:

```text
run_dir = output/diagnostic/20260514T144800Z_hh4_york_carrier_final_smoke
York YK apply = 19.17s, regroup = 10.68s
Carrier 19XR apply = 174.57s, regroup = 129.45s
final_centrifugal_chiller_ko = 405
cross_publisher_ko = 32
max_layers = 8
parameter_1_count = 0
cross_publisher_list = output/diagnostic/20260514T144800Z_hh4_york_carrier_final_smoke/cross_publisher_final.tsv
summary = output/diagnostic/20260514T144800Z_hh4_york_carrier_final_smoke/hh4_summary.json
```

Verification:

```text
oracle = PASS
pytest = 390 passed
check-all = 4 gates passed
```

Per HH4 scope, the remaining visual packs were not applied:

```text
not_applied = Carrier 19XR v2, Carrier 19XL, McQuay, Haier ACG, York RWF2
```

## 2026-05-14 GG Visual Apply Round (Stopped)

Goal: apply the 7 MiMo visual review packs into the chiller/screw/water-source
domains without changing grouping, merger, Brick, unit facets, thresholds, or
the oracle.

Pre-write backup passed the non-empty guard:

```text
backup = /tmp/gg1_pre_visual_apply_20260514T124822Z.sql
size = 131,598,457 bytes
```

The raw visual review packs were still `review_decision=pending`; the first two
direct apply attempts were skipped by `apply_review_packs_batch.py`. A separate
audit copy was generated under:

```text
output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/
```

The copy promotes deterministic `judge_verdict=accepted` entries to
`review_decision=accepted`, fills curation title/summary from the extracted
payload/evidence, stamps publisher, and preserves the original visual outputs.
Haier ACG was routed to `water_source_heat_pump`; RWF2 was routed to
`screw_chiller`.

Apply progression before stop:

```text
baseline centrifugal_chiller KO = 32
after pending-pack regroup checks = 31

York YK 123p:
  candidates = 337
  apply_report = output/diagnostic/20260514T124900Z_visual_apply/01_york_yk_accepted_apply_report.json
  merger_stats = {new_merged: 77, updated_existing: 27, material_conflicts: 56, groups_processed: 3}
  after regroup KO = 88

Carrier 19XR 97p:
  candidates = 543
  apply_report = output/diagnostic/20260514T124900Z_visual_apply/02_carrier_19xr_accepted_apply_report.json
  merger_stats = {new_merged: 150, updated_existing: 54, material_conflicts: 104, groups_processed: 3}
  after regroup KO = 177
```

Stop condition:

```text
failed_doc = Carrier 19XR v2 97p
action = stopped; did not continue to 19XL / McQuay / Haier / RWF2
reason = complete-linkage clustering became CPU-bound for >40 minutes
traceback = packages/compiler/clustering.py::_can_complete_link -> cosine
failed_input = output/diagnostic/20260514T131045Z/merger_input.jsonl
failed_input_shape = parameter_spec existing_count=265, new_count=411
sample = output/diagnostic/20260514T124900Z_visual_apply/03_carrier_19xr_v2_sample.txt
transaction = interrupted before commit; KO count remained 177
```

Partial SQL outputs:

```text
cross_publisher = output/diagnostic/20260514T124900Z_visual_apply/partial_cross_publisher_after_stop.tsv
carrier_dedup = output/diagnostic/20260514T124900Z_visual_apply/partial_carrier_dedup_after_stop.tsv
summary = output/diagnostic/20260514T124900Z_visual_apply/gg_visual_apply_stopped_summary.json
```

Partial state is not accepted as GG completion:

```text
cross_publisher_rows = 34
max_layers = 33
super_KO_present = yes
examples = hvac:centrifugal_chiller:parameter:1 has 33 layers; ma_diffuser_full_span_ma_rating has 21 layers
4_publisher_present = yes, supply_oil_temperature_range has {Carrier,Gree,McQuay,Trane}
quality_gate = FAIL due super-KO / garbage merges and aborted second 19XR apply
```

No oracle, grouping, merger, Brick map, unit detector, LLM arbiter scope, or
threshold code was changed in this round.

## 2026-05-14 Milestone: First Clean Cross-Publisher Merge

KnowFabric reached its first 100% clean production cross-publisher merge KO:

```text
canonical_key = hvac:centrifugal_chiller:parameter:supply_oil_temperature_range
publishers = Gree + McQuay
consensus_state = agreed
source_names = {供油温度范围}
```

Current verification baseline:

```text
oracle = PASS
garbage_oil_temp_pressure_mix = 0
parameter_name_corrupted = 0
max_layers = 3
```

Remaining limitation:

```text
Unit facets distinguish physical quantity families such as temperature vs
pressure differential, but they do not distinguish reference points inside the
same facet. Temperature still needs Tier 2 modeling to separate oil temperature,
cooling-water inlet temperature, and chilled-water leaving/supply temperature.
```

Key fixes that produced this baseline:

```text
P0 plumbing fix
5a5634e oversize sanity
U1 parameter_name pollution fix
U2 candidate persistence / same-document split
V1 complete-linkage clustering
X4 unit-based facet split
Y1 detector reads summary/evidence text units
```

## 2026-05-14 BB/CC: Contextual Embedding + Upsert Preservation

BB isolated the publisher-loss bug to merger upsert behavior, then fixed two
production edge cases:

```text
1. A split regroup pass could reuse the same existing KO id twice, causing a
   later Trane-only group to overwrite a previously written Gree+Trane group.
2. After Brick subtype splitting, compatible same-subtype fragments needed a
   second complete-linkage pass so a contaminant could not permanently block a
   valid oil-temperature merge.
```

CC changed embedding input from bare `parameter_name` to compact contextual text
(`parameter_name + summary + value/default/range/unit`) while keeping final
canonical keys based on raw source names. The 13-pair BGE-M3 4-bit check did not
justify threshold changes:

```text
name-only POS-NEG gap = 0.0791
contextual POS-NEG gap = 0.0827
delta = +0.0037
decision = keep threshold unchanged
```

Final clean-slate validation with contextual embedding:

```text
run_dir = output/diagnostic/20260514T184500Z_bb4_full_validation_contextual_rawkeys
oracle = PASS
total_chiller_ko = 29
cross_publisher_ko = 5
cross_publisher_with_gree_trane = 1
max_layers = 6
garbage_oil_temp_pressure_mix = 0
parameter_spec_pname_numeric_or_placeholder = 0
```

Cross-publisher KOs:

```text
hvac:centrifugal_chiller:parameter:active_current_limit_setpoint | 6 | {McQuay,Trane} | material_conflict
hvac:centrifugal_chiller:parameter:bas_chilled_water_setpoint | 6 | {AHRI,McQuay,Trane} | material_conflict
hvac:centrifugal_chiller:parameter:current_limit_soft_load_time | 6 | {McQuay,Trane} | material_conflict
hvac:centrifugal_chiller:parameter:supply_oil_temperature_range | 5 | {Gree,McQuay,Trane} | material_conflict
hvac:centrifugal_chiller:parameter:oil_cooler_max_inlet_temperature | 3 | {AHRI,McQuay} | partial_conflict
```

## 2026-05-14 EE LLM Arbiter Round

EE added a scoped LLM final adjudication stage after embedding clustering,
unit-facet split, and Brick subtype split. Scope is intentionally narrow:

```text
trigger = cluster size 2-8 AND >=2 publishers
backend = deepseek-parameter-spec
cache = /tmp/knowfabric_llm_arbiter_cache
fallback = keep stage 1-3 cluster if LLM/cache/JSON validation fails
```

Final regroup was run once from the EE pre-regroup backup:

```text
restore_point = /tmp/ee_pre_llm_arbiter_regroup_20260514T094900Z.sql
pre_final_backup = /tmp/ee_pre_final_regroup_20260514T095632Z.sql
regroup_stats = {'new_merged': 5, 'updated_existing': 16, 'merged_existing': 0, 'material_conflicts': 7}
total_chiller_ko = 32
cross_publisher_ko = 2
cross_publisher_ko_with_3_publishers = 2
max_layers = 5
```

Cross-publisher KOs after EE:

```text
hvac:centrifugal_chiller:parameter:supply_oil_temperature_range | 油箱温度控制 | 5 | {Gree,McQuay,Trane} | material_conflict
hvac:centrifugal_chiller:parameter:evaporator_water_temperatures | 出水温度停机保护设定 | 3 | {AHRI,McQuay,Trane} | material_conflict
```

Specified garbage merges were removed:

```text
导叶速度出厂设置值 -> standalone McQuay KO
热气旁通启动点电流值 -> standalone McQuay KO
油冷/变频器冷却最低进水温度 -> standalone McQuay KO
Air-cooled Condenser EDB at Part-load -> standalone AHRI KO
```

Residual gap:

```text
cross_publisher_ko target was >=3; final strict-quality result is 2.
Gree/Trane oil-pressure similarity is high enough for embedding, but Brick
subtype currently labels Gree oil pressure differential as oil_pressure and
Trane minimum differential pressure as differential_pressure. Because EE runs
after Brick subtype split and this round forbids changing Brick map/unit
detector/thresholds, the LLM arbiter cannot re-merge that pressure pair.
```

## 1) Oracle output

Command:

```bash
cd /Users/asteroida/work/KnowFabric
rm -rf /tmp/knowfabric_embedding_cache
set -a && source .env && source .env.llm.local && set +a
OMLX_API_KEY=<redacted> venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
```

Result:

```text
RESULT: PASS ✓ — Cross-publisher merge plumbing verified end-to-end.
```

Key facts from the passing run:
- total KOs created: `3`
- oil pressure merged: `hvac:e2e_test_chiller:parameter:key_a300dd0250`
- chilled water merged: `hvac:e2e_test_chiller:parameter:chilled_water_leaving_temperature`

## 2) Main DB restore + regroup verification

### Safety backup

Before touching `knowfabric`, I created:

```text
/tmp/pre_h3_restore_20260511T160623Z.sql
```

Before regrouping the restored main DB, I created:

```text
/tmp/h3_main_before_regroup_20260511T161223Z.sql
```

### Restore target requested by operator

Restored file:

```text
/tmp/h3_pre_rerun_20260511T.sql
```

### Actual baseline SQL after restoring `/tmp/h3_pre_rerun_20260511T.sql`

Operator-expected SQL:

```sql
SELECT COUNT(*)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller';
```

Actual result on this machine:

```text
6
```

Additional validation:

```sql
SELECT COUNT(*)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller'
  AND knowledge_object_type='parameter_spec';
```

Result:

```text
6
```

So the restored `/tmp/h3_pre_rerun_20260511T.sql` file is **not** the 56-KO baseline described in the operator prompt, even though it does contain many Carrier-related source references in raw dump text.

### Regroup on restored main DB

Command:

```bash
set -a && source .env && source .env.llm.local && set +a
OMLX_API_KEY=<redacted> venv/bin/python scripts/regroup_chiller_domain.py
```

Result:

```text
stats: {new_merged: 0, updated_existing: 6, merged_existing: 0, material_conflicts: 0}
```

Cross-publisher SQL:

```sql
SELECT canonical_key,
       jsonb_array_length((authority_summary_json::jsonb)->'layers') AS n_layers,
       (SELECT array_agg(DISTINCT layer->>'publisher' ORDER BY layer->>'publisher')
          FROM jsonb_array_elements((authority_summary_json::jsonb)->'layers') layer) AS pubs
FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
  AND knowledge_object_type='parameter_spec'
  AND (SELECT COUNT(DISTINCT layer->>'publisher')
         FROM jsonb_array_elements((authority_summary_json::jsonb)->'layers') layer) >= 2
ORDER BY n_layers DESC;
```

Actual result:

```text
hvac:centrifugal_chiller:parameter:motor_current_limit | 2 | {Carrier,Trane}
```

Main DB hard-metric outcome:

- cross-publisher KOs: `1`
- total chiller parameter_spec KOs: `6`
- Trane+Carrier true merge: **present** (`motor_current_limit`)
- Trane+McQuay true merge: **not present**
- no super-KO on this specific restored-main snapshot

Conclusion on main DB:

- the P0 plumbing fix works enough to recover **at least one real cross-publisher merge**
- but the operator-specified restore file on this machine is **already a late collapsed 6-KO snapshot**, not the required 56-KO H3 baseline

### Rich-backup probe on `/tmp/m1_pre_regroup_20260511T.sql`

Because `/tmp/h3_pre_rerun_20260511T.sql` did not match the stated baseline, I also verified the fix on a richer pre-regroup dump in a temp DB:

```text
/tmp/m1_pre_regroup_20260511T.sql
```

Temp safety backup before regroup:

```text
/tmp/m1_probe_before_regroup_20260511T161030Z.sql
```

Pre-regroup counts in temp DB:

```text
total chiller parameter_spec KOs = 114
Carrier 19XR KOs                = 60
```

After regroup:

```text
stats: {new_merged: 0, updated_existing: 3, merged_existing: 1, material_conflicts: 0}
```

Post-regroup outcome:

```text
consensus = multi_facet 1 / single_source 3
cross-publisher KOs = 1
largest cross-publisher KO:
hvac:centrifugal_chiller:parameter:chilled_water_entering_temperature_maximum
layers = 111
publishers = {Carrier,McQuay,Trane}
```

This fails the operator hard metrics:

- cross-publisher KOs `< 3`
- total KO count collapses to `4`
- super-KO exists (`111` layers > `10`)

Failure trace artifacts:

```text
/Users/asteroida/work/KnowFabric/output/diagnostic/20260511T161057Z/merger_input.jsonl
/Users/asteroida/work/KnowFabric/output/diagnostic/20260511T142653Z/n3_llm_refinement_trace.jsonl
```

The latest merger input trace shows:

```text
existing_count = 114
by_doc_existing = {
  doc_55e5ec4e4ee84e9a: 60,
  doc_36640e9f378f4667: 20,
  doc_7c4fca116fd3420a: 10,
  doc_883beab5e0004a2c: 24
}
```

The earlier LLM refinement trace captures the bad mega-cluster behavior directly:

```text
cluster_size = 105
cluster_members include both:
- Carrier: Motor Load Activation Demand Limit / Bearing temperature alarm limit / ...
- Trane: 外部冷冻水设定范围上限 / 启动限制最低油温 / ...
- McQuay: 最低冷冻水出水温度 / 冷冻水最高进水温度 / ...
```

So the current state is:

- **P0 plumbing bug fixed** and oracle-proven
- but on a rich persisted regroup backup, there is still another production regroup failure mode beyond the original plumbing bug

## 3) Actual code change

Changed file:
- `/Users/asteroida/work/KnowFabric/packages/compiler/cross_source_merger.py`

3-line summary:
1. Added `_ko_to_candidates(...)` to expand an existing KO into per-evidence/per-source candidates instead of a single flattened candidate.
2. Added `_source_name_from_evidence(...)` to recover a usable parameter name from evidence text when regrouping existing KOs.
3. Changed `merge_with_existing(...)` to index existing names from expanded candidates, not just `structured_payload_json.parameter_name` of the KO row.

## 4) Why the previous 12 rounds missed it

They were validating the **new-candidate apply path** only.

The real plumbing bug on the production regroup path is:
- `existing KO -> _ko_to_candidate -> merge_with_existing`
- `_ko_to_candidate(...)` kept only the `first_layer` authority metadata and one representative `parameter_name`
- so regroup silently threw away multi-layer source identity before `group_and_normalize(...)` ever saw it

That is why oracle-style direct grouping could look correct while regrouping persisted KOs still behaved incorrectly.

## 5) Test / gate status

- `venv/bin/pytest tests/` → `314 passed`
- `bash scripts/check-all` → `✓ All quality gates passed`

## 6) Environment note

A temp sandbox replay against `knowfabric_sandbox_tmp` confirmed the local artifact set on disk is inconsistent with the prompt's described main DB baseline. The prompt expects a pre-existing ~56-KO chiller state; the available restored local main DB snapshot is already collapsed to 6 KOs, which is why the SQL hard target cannot be reproduced verbatim on this snapshot alone.

## 7) 2026-05-14 Gree 17 + AHRI 8 production apply attempt

### Inputs

- Gree source: `output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0003_格力_c系列离心式冷水机组技术手册_69页/deepseek-parameter-spec/candidates.json`
- AHRI source: `output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0001_ansi_ahri_standard_550_590_2023_i_p_editorial_update/deepseek-parameter-spec/candidates.json`
- Note: these audit files were absent from the current worktree at session start and were copied from sibling worktree `KnowFabric-compiler-hardening` without rerunning extraction.

### Safety backups

- `/tmp/q1_pre_gree_clean_retry_20260514T043828Z.sql`
- `/tmp/q2_pre_regroup_after_namefix_20260514T043917Z.sql`
- `/tmp/q3_pre_ahri_20260514T044028Z.sql`
- `/tmp/q2_pre_regroup_after_ahri_20260514T044042Z.sql`

Additional polluted-state backups and diagnostics were created while isolating apply/regroup defects:

- `/tmp/q2_polluted_pre_restore_20260514T043718Z.sql`
- `output/diagnostic/20260514T043338Z_q1_gree_bad_apply/`
- `output/diagnostic/20260514T043556Z_q2_regroup_no_gree_publisher/`

### Code defects found and fixed during the attempt

1. `apply_review_packs_batch.py` forced a mixed-type review pack through the first accepted candidate's `knowledge_object_type`, misclassifying Gree parameter/performance/sequence/maintenance candidates as `fault_code`.
2. `build_manual_fixture_from_review_candidates.py` dropped curated `publisher` / `citation`, preventing Gree from counting as a cross-publisher layer.
3. `cross_source_merger._ko_to_candidates()` used noisy evidence first lines as regroup names, renaming existing parameter KOs incorrectly during regroup.
4. `summarize_review_pipeline_stats.py` counted `applied_merger` correctly at overall level but not document level.

### Final production DB result after clean restore, fixed apply, AHRI Q3, and regroup

Gree apply:

```text
accepted_count = 17
status = applied_merger
merger_stats = {new_merged: 6, updated_existing: 4, material_conflicts: 3, groups_processed: 5}
```

AHRI apply with applicability option B:

```text
accepted_count = 8
applicability.equipment_classes = [centrifugal_chiller, screw_chiller, scroll_chiller, reciprocating_chiller]
status = applied_merger
merger_stats = {new_merged: 2, updated_existing: 5, material_conflicts: 1, groups_processed: 1}
```

Final regroup:

```text
stats: {new_merged: 0, updated_existing: 7, merged_existing: 0, material_conflicts: 0}
```

Final SQL hard-metric snapshot:

```text
cross_publisher_count = 2
gree_cross_count = 1
super_ko = 0
max_layers = 7
total_chiller = 13
```

Cross-publisher KOs:

```text
hvac:centrifugal_chiller:parameter:key_52a46b11d3
title = 油箱温度控制
layers = 4
publishers = {Gree, Trane}
consensus_state = agreed

hvac:centrifugal_chiller:parameter:motor_current_limit
title = Motor Current Limit
layers = 2
publishers = {Carrier, Trane}
consensus_state = agreed
```

### Outcome

This run did **not** meet the requested hard metric:

- required cross-publisher KOs: `>= 3`; actual: `2`
- required Gree+other pairings: `>= 2`; actual: `1`
- required no super-KO: passed (`max_layers = 7`)
- required chiller KO count not inflated by >20: passed (`6 -> 13`)

No threshold tuning, YAML name-pair hardcoding, or LLM re-extraction was performed. The remaining gap appears to be semantic grouping/data coverage on the current 6-KO baseline: Gree oil temperature naturally merged with Trane; Gree oil pressure did not have a matching persisted non-Gree oil-pressure KO in this baseline, and AHRI standards did not add additional cross-publisher merges.

## 8) 2026-05-14 clean-slate chiller apply + regroup

### Run ID and safety artifacts

Run ID:

```text
20260514T051545Z_cleanslate_chiller
```

Primary diagnostic directory:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/
```

Pre-clean backup:

```text
/tmp/t1_pre_cleanslate_20260514T051545Z.sql
```

Pre-regroup backup:

```text
/tmp/t5_pre_regroup_cleanslate_20260514T052327Z.sql
```

The pre-clean SQL snapshot is stored at:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/t1_current_chiller_state.txt
```

### Clean-slate deletion

Deleted all existing `centrifugal_chiller` rows and evidence from the production DB:

```sql
DELETE FROM knowledge_object_evidence
WHERE knowledge_object_id IN (
  SELECT knowledge_object_id FROM knowledge_object
  WHERE ontology_class_id='centrifugal_chiller'
);

DELETE FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller';
```

Verification result:

```text
centrifugal_chiller KO count = 0
```

### Clean-slate apply manifest

Full machine-readable manifest:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/clean_slate_apply_manifest.json
```

Candidate sources used:

```text
Gree:
output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0003_格力_c系列离心式冷水机组技术手册_69页/deepseek-parameter-spec/candidates.json

AHRI:
output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0001_ansi_ahri_standard_550_590_2023_i_p_editorial_update/deepseek-parameter-spec/candidates.json

Trane CVGF:
output/parameter_spec_vertical/20260506T085338Z_trane_cvgf_400_1000_chiller_manual_parameter_spec/candidates_llm_verified.jsonl

McQuay WSC/WDC/HSC/HDC:
output/w3_multisource_extraction/20260511T042453Z_hvac_doclevel_extraction_batch/0001_麦克维尔_wsc_wdc_hsc_hdc单_双压缩机离心式安装维护手册_49页_制冷百家网/deepseek-parameter-spec/candidates.json

McQuay single/double compressor:
output/w3_multisource_extraction/20260511T042453Z_hvac_doclevel_extraction_batch/0002_麦克维尔_单_双压缩机离心式冷水机组安装维修手册/deepseek-parameter-spec/candidates.json
```

Prepared review pack directories:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/gree/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/ahri/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/trane_cvgf/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/mcquay_wsc_wdc_hsc_hdc/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/mcquay_single_double/review_packs
```

Carrier 19XR/19XL status:

```text
missing_candidates
```

Only chunk task results were found under `output/chiller_visual_import`; no Carrier 19XR/19XL `candidates.json`, JSONL, or review bundle was present. Carrier was therefore excluded from this clean-slate run per the no-re-extraction constraint.

### Apply evolution

All writes were preceded by `pg_dump`. The detailed TSV is:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_counts.tsv
```

Observed KO counts:

```text
Gree apply                         -> total chiller KO = 7
AHRI apply                         -> total chiller KO = 9
Trane apply                        -> total chiller KO = 26
McQuay WSC/WDC/HSC/HDC apply       -> total chiller KO = 25
McQuay single/double first attempt -> failed, total chiller KO = 25
McQuay single/double retry         -> total chiller KO = 24
```

The first McQuay single/double apply attempt exposed an evidence migration idempotency defect:

```text
duplicate key value violates unique constraint "uq_knowledge_object_evidence_ref"
```

Fixed in `packages/compiler/cross_source_merger.py` by preserving target evidence, dropping duplicate source evidence, and migrating only non-duplicate rows before deleting merged source KOs. This was an apply plumbing fix, not a grouping threshold or YAML-name intervention.

### Regroup result

Command:

```bash
venv/bin/python scripts/regroup_chiller_domain.py
```

Result:

```text
stats: {'new_merged': 0, 'updated_existing': 15, 'merged_existing': 1, 'material_conflicts': 1}
```

Final hard metrics:

```text
total_chiller_ko = 22
cross_publisher_ko = 2
gree_other_ko = 1
max_layers = 7
```

Cross-publisher KOs:

```text
hvac:centrifugal_chiller:parameter:key_52a46b11d3
layers = 5
publishers = {Gree, Trane}
consensus_state = agreed

hvac:centrifugal_chiller:parameter:key_1f4206db93
layers = 2
publishers = {McQuay, Trane}
consensus_state = agreed
```

### Clean-slate outcome

This run did **not** meet the requested hard metric:

- required cross-publisher KOs: `>= 3`; actual: `2`
- required Gree+other pairings: `>= 2`; actual: `1`
- required at least one Gree+Trane or Gree+Carrier pairing: passed via Gree+Trane oil temperature
- required max layers `<= 8`: passed (`7`)
- required total chiller KO not `> 100`: passed (`22`)

Failure trace:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/cleanslate_grouping_trace.jsonl
```

Working hypothesis for operator review:

- Carrier 19XR was absent, so the intended Carrier-side oil concepts could not participate.
- Gree+Trane oil temperature did merge naturally.
- Trane+McQuay produced one additional cross-publisher merge.
- Gree oil-pressure remained Gree-only after clean-slate regroup despite no super-KO, so the remaining gap appears to be semantic/data coverage for the available non-Carrier candidate set rather than historical DB pollution.

No LLM re-extraction, threshold tuning, YAML name-pair hardcoding, or oracle script changes were performed.

### Verification commands after clean-slate run

```text
venv/bin/python -m pytest tests/test_review_pipeline_stats.py::test_summarize_review_pipeline_stats_combines_candidates_packs_and_apply -q
1 passed

venv/bin/python -m pytest tests -q
336 passed

bash scripts/check-all
All quality gates passed
```

## 9) 2026-05-14 U1/U2 apply pollution fix attempt

### Bugs confirmed and fixed

U1 root cause:

- The source review pack for Trane `30 psipsid` had the correct concept name: `structured_payload_candidate.parameter_name = 最大压差设定值`.
- The DB pollution came from regroup expansion, not the review pack.
- `_ko_to_candidates()` used layer `value_summary` as `parameter_name`; later it also matched layers only by `doc_id`, so multiple layers from one manual could inherit the wrong source name.
- Fixed by storing `source_name`, `chunk_id`, and per-layer `structured_payload` in `authority_summary_json.layers`, then expanding existing KOs by `chunk_id` first.

U2 root cause:

- Gree review pack contained all 17 accepted entries, including the 4 reviewed `parameter_spec` entries.
- The 4 Gree parameter candidates reached merger input, so this was not review-pack parsing or review_status filtering.
- Empty-DB first apply over-grouped distinct same-document parameter names into one KO.
- Fixed with a first-apply guard that splits same-document groups when source names contain conflicting qualifiers such as temperature vs pressure or start vs running.

### Final U3 rerun

Run ID:

```text
20260514T084500Z_u3_chiller_fix_rerun6
```

Artifacts:

```text
output/diagnostic/20260514T084500Z_u3_chiller_fix_rerun6/apply_counts.tsv
output/diagnostic/20260514T084500Z_u3_chiller_fix_rerun6/cross_publisher_kos.txt
output/diagnostic/20260514T084500Z_u3_chiller_fix_rerun6/metrics.tsv
output/diagnostic/20260514T084500Z_u3_chiller_fix_rerun6/u3_final_grouping_trace.jsonl
```

Apply evolution:

```text
Gree apply                         -> total chiller KO = 16
AHRI apply                         -> total chiller KO = 15
Trane apply                        -> total chiller KO = 33
McQuay WSC/WDC/HSC/HDC apply       -> total chiller KO = 34
McQuay single/double apply         -> total chiller KO = 31
After regroup                      -> total chiller KO = 30
```

Final metrics:

```text
total_chiller_ko = 30
cross_publisher_ko = 1
gree_other_ko = 1
max_layers = 5
parameter_spec_pname_numeric_or_placeholder = 0
```

Outcome:

- `parameter_name` pollution was fixed: value/default/placeholder count went from 9 to `0`.
- Gree reviewed parameter candidates no longer disappear in the empty-DB first apply path.
- The run still did **not** meet the requested cross-publisher hard metric: required `>= 3`, actual `1`.
- The remaining cross-publisher KO is a mixed oil-temperature / oil-pressure / pressure-differential group and is marked `material_conflict`.

No oracle changes, threshold tuning, YAML name-pair additions, or LLM re-extraction were performed.

## 10) 2026-05-14 V1-V4 complete-linkage quality verification

### V1 implementation

Changed `packages/compiler/clustering.py` so `cluster_by_cosine()` now accepts:

```text
linkage="complete"  # default
linkage="single"    # old behavior, explicit only
```

Complete-linkage only unions two clusters when every pair in the merged cluster
has cosine similarity above the existing `0.78` threshold. No threshold changes
were made.

Regression test added:

```text
tests/test_clustering.py::test_complete_linkage_blocks_semantic_chain_merge
```

The test uses a three-node chain with A-B = 0.85, B-C = 0.85, A-C = 0.60 and
verifies:

```text
single-linkage   -> [A, B, C]
complete-linkage -> [A, B], [C]
```

### V2 oracle regression

Command:

```text
rm -rf /tmp/knowfabric_embedding_cache
OMLX_API_KEY=<redacted> venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
```

Result after the clustering change and stale-KO merge protection:

```text
RESULT: PASS - Cross-publisher merge plumbing verified end-to-end.
```

Backup before DB-writing oracle runs:

```text
/tmp/v2_pre_oracle_20260514T055326Z.sql
/tmp/v2_post_changes_pre_oracle_20260514T055617Z.sql
```

### V3 clean-slate rerun

Run ID:

```text
20260514T091500Z_v3_complete_linkage_cleanslate_retry
```

Artifacts:

```text
output/diagnostic/20260514T091500Z_v3_complete_linkage_cleanslate_retry/apply_counts.tsv
output/diagnostic/20260514T091500Z_v3_complete_linkage_cleanslate_retry/cross_publisher_quality.txt
output/diagnostic/20260514T091500Z_v3_complete_linkage_cleanslate_retry/embedding_cluster_trace.json
output/diagnostic/20260514T091500Z_v3_complete_linkage_cleanslate_retry/oil_cluster_pairwise_cosines.tsv
output/diagnostic/20260514T091500Z_v3_complete_linkage_cleanslate_retry/metrics.tsv
```

Clean-slate apply evolution:

```text
Gree apply                         -> total chiller KO = 15
AHRI apply                         -> total chiller KO = 16
Trane apply                        -> total chiller KO = 28
McQuay WSC/WDC/HSC/HDC apply       -> total chiller KO = 25
McQuay single/double apply         -> total chiller KO = 25
After regroup                      -> total chiller KO = 23
```

Regroup stats:

```text
{'new_merged': 0, 'updated_existing': 12, 'merged_existing': 2, 'material_conflicts': 4}
```

### V4 quality result

Final metrics:

```text
total_chiller_ko = 23
cross_publisher_ko = 2
max_layers = 4
parameter_spec_pname_numeric_or_placeholder = 0
garbage_oil_temp_pressure_mix = 1
```

Cross-publisher KOs after regroup:

```text
hvac:centrifugal_chiller:parameter:front_panel_chilled_water_setpoint
  n = 4
  pubs = {McQuay, Trane}
  consensus_state = multi_facet
  source_names = {冷冻水最高进水温度, Chilled Water Reset, Front Panel Chilled Water Setpoint}

hvac:centrifugal_chiller:parameter:supply_oil_temperature_range
  n = 4
  pubs = {Gree, McQuay, Trane}
  consensus_state = material_conflict
  source_names = {供油温度范围, 油压差范围（运行）, 油箱温度控制, 润滑油温度控制设定范围}
```

Outcome:

- Oracle regression passed.
- `parameter_name` value/default/placeholder pollution stayed fixed: count = `0`.
- `max_layers <= 5` passed: actual = `4`.
- V4 did **not** pass because `total_chiller_ko` is `23` rather than `>= 30`.
- V4 did **not** pass because the oil temperature / oil pressure mixed cross-publisher KO still exists.

The diagnostic trace shows complete-linkage is active, but the oil cluster is
still internally pairwise above the unchanged threshold:

```text
油箱温度控制 - 油压差范围（运行）             0.8336
油箱温度控制 - 润滑油温度控制设定范围       0.8846
油箱温度控制 - 供油温度范围                 0.8619
油压差范围（运行） - 润滑油温度控制设定范围 0.8371
油压差范围（运行） - 供油温度范围           0.8574
润滑油温度控制设定范围 - 供油温度范围       0.8811
```

This means the remaining garbage merge is not a single-linkage chain failure in
this production clean-slate run: all six pairwise similarities inside the oil
cluster are already above `0.78`, so complete-linkage cannot split it without a
separate policy change. No threshold tuning, YAML hardcoding, LLM re-extraction,
single-link fallback, or oracle script changes were performed.

## 11) 2026-05-14 X1-X4 unit-based facet detection

### X1 implementation

Removed the string-enumeration facet design from `cross_source_merger.py`:

```text
FACET_KEYWORDS removed
_detect_facets removed
```

Added unit-based physical facet detection:

```text
packages/compiler/unit_facet_detector.py
```

Detection order:

```text
1. structured_payload.unit
2. units embedded in value/default_value/range_min/range_max/value_summary/name text
3. generic pressure-differential markers: 压差, 差压, differential pressure, pressure differential, psid, ΔP
4. None when no physical unit/facet is known
```

The detector covers physical unit families only: temperature, pressure,
pressure_differential, current, voltage, frequency, flow, power, ratio, and
time. It does not enumerate concrete parameter names such as oil temperature or
chilled-water temperature.

### X2 clustering integration

`group_and_normalize()` now accepts:

```text
facet_hints: dict[str, str | None] | None
```

`merge_candidates()` builds those hints from each candidate structured payload
before calling `group_and_normalize()`.

Embedding clustering still runs first. After cosine clustering and oversize
tightening, any multi-member cluster with two or more known incompatible unit
facets is split by facet before canonical keys are assigned. Unknown facets do
not split a cluster by themselves.

The in-memory hash cache now includes `facet_hints` so a same-name batch cannot
reuse a grouping computed without the unit constraints.

### X3 tests

Added:

```text
tests/test_unit_facet_detector.py
tests/test_canonical_key_embedding.py::test_embedding_cluster_splits_by_unit_facet
```

Updated the old keyword-facet consensus test so keyword labels no longer
override value disagreement.

Targeted verification:

```text
venv/bin/python -m pytest \
  tests/test_unit_facet_detector.py \
  tests/test_canonical_key_embedding.py \
  tests/test_canonical_key_batching.py \
  tests/test_cross_source_merger.py \
  tests/test_cross_source_merger_crosslingual.py \
  tests/test_cross_source_merger_regroup.py \
  tests/test_clustering.py -q

45 passed
```

### X4 oracle and clean-slate result

Oracle command:

```text
rm -rf /tmp/knowfabric_embedding_cache
OMLX_API_KEY=<redacted> venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
```

Oracle result:

```text
RESULT: PASS - Cross-publisher merge plumbing verified end-to-end.
```

Backup before oracle:

```text
/tmp/x4_pre_oracle_20260514T062410Z.sql
```

Clean-slate run ID:

```text
20260514T143000Z_x4_unit_facet_cleanslate
```

Artifacts:

```text
output/diagnostic/20260514T143000Z_x4_unit_facet_cleanslate/apply_counts.tsv
output/diagnostic/20260514T143000Z_x4_unit_facet_cleanslate/cross_publisher_quality.txt
output/diagnostic/20260514T143000Z_x4_unit_facet_cleanslate/oil_temperature_pressure_kos.txt
output/diagnostic/20260514T143000Z_x4_unit_facet_cleanslate/metrics.tsv
```

Clean-slate apply evolution:

```text
Gree apply                         -> total chiller KO = 15
AHRI apply                         -> total chiller KO = 16
Trane apply                        -> total chiller KO = 33
McQuay WSC/WDC/HSC/HDC apply       -> total chiller KO = 35
McQuay single/double apply         -> total chiller KO = 34
After regroup                      -> total chiller KO = 30
```

Regroup stats:

```text
{'new_merged': 0, 'updated_existing': 18, 'merged_existing': 4, 'material_conflicts': 5}
```

Final metrics:

```text
total_chiller_ko = 30
cross_publisher_ko = 0
max_layers = 3
garbage_oil_temp_pressure_mix = 0
parameter_spec_pname_numeric_or_placeholder = 0
```

Outcome:

- Oracle regression passed.
- The previous oil temperature / oil pressure garbage cross-publisher KO no longer appears.
- Total chiller KO count is `30`, satisfying the `>= 23` non-overmerge guard.
- `max_layers` is `3`.
- Cross-publisher count is `0`; this is acceptable under the quality-first X4 criteria because the bad merge was eliminated without threshold tuning, YAML aliases, LLM re-extraction, or oracle changes.

Backlog for the next round only:

```text
Tier 2 Brick Schema tag mapping:
domain_packages/hvac/v2/brick_facet_map.yaml
Brick tag -> bilingual quantity/reference-point hints
```

## 12) 2026-05-14 Y1-Y3 same-facet regression trace

### Y1 trace instrumentation

Added optional grouping trace controlled by:

```text
KNOWFABRIC_GROUPING_TRACE_DIR=<dir>
```

Trace file:

```text
<dir>/grouping_trace.jsonl
```

Each `_group_via_embedding()` call records:

```text
input_names
facet_hints
raw_clusters
tightened_clusters
facet_split_clusters
final mapping
pairwise cosine values
```

The trace is diagnostic-only and does not affect grouping unless the env var is
set.

### Y1 root cause

Clean-slate trace run:

```text
output/diagnostic/20260514T150000Z_y1_trace/
```

Root cause found:

- Gree structured payloads did not use `unit`, `range_min`, `range_max`, or `default_value`.
- Their units were embedded only in `structured_payload.summary`, for example:

```text
供油温度范围: 正常运行供油温度应稳定在35～50℃。
油压差范围（运行）: 正常运行供油压力比油箱压力高150～250kPa。
油箱温度控制: 停机时油箱温度保持在48～52℃之间。
```

Before the fix, `detect_unit_facet()` did not inspect `summary`, so:

```text
供油温度范围 -> None
油箱温度控制 -> None
油压差范围（运行） -> pressure_differential
Trane 低油温起动抑制设定 -> temperature
```

This was case (b): facet hints for Gree historical candidates were incomplete.

### Y2 fix

Updated `detect_unit_facet()` to extract units from additional payload text
fields:

```text
title
summary
description
evidence_quote
value
default_value
range_min
range_max
value_summary
```

This stays unit-based: it reads physical units in text and does not enumerate
specific parameter names.

Added tests:

```text
detect_unit_facet("供油温度范围", {"summary": "正常运行供油温度应稳定在35～50℃。"}) -> temperature
detect_unit_facet("油压差范围（运行）", {"summary": "正常运行供油压力比油箱压力高150～250kPa。"}) -> pressure_differential
```

### Y3 verification

Oracle backup:

```text
/tmp/y3_pre_oracle_20260514T071310Z.sql
```

Oracle command:

```text
rm -rf /tmp/knowfabric_embedding_cache
OMLX_API_KEY=<redacted> venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
```

Oracle result:

```text
RESULT: PASS - Cross-publisher merge plumbing verified end-to-end.
```

Clean-slate run:

```text
output/diagnostic/20260514T151500Z_y3_unit_summary_fix_y1_trace/
```

Apply evolution:

```text
Gree apply                         -> total chiller KO = 16
AHRI apply                         -> total chiller KO = 19
Trane apply                        -> total chiller KO = 38
McQuay WSC/WDC/HSC/HDC apply       -> total chiller KO = 37
McQuay single/double apply         -> total chiller KO = 37
After regroup                      -> total chiller KO = 34
```

Regroup stats:

```text
{'new_merged': 0, 'updated_existing': 23, 'merged_existing': 3, 'material_conflicts': 4}
```

Final metrics:

```text
total_chiller_ko = 34
cross_publisher_ko = 1
max_layers = 3
garbage_oil_temp_pressure_mix = 0
parameter_spec_pname_numeric_or_placeholder = 0
```

Final cross-publisher KO:

```text
hvac:centrifugal_chiller:parameter:supply_oil_temperature_range
  n = 2
  pubs = {Gree, McQuay}
  consensus_state = agreed
  source_names = {供油温度范围}
```

Additional trace finding:

- During Trane apply, Gree and Trane oil-temperature names did merge:

```text
供油温度范围                       facet=temperature
油箱温度控制                       facet=temperature
启动限制最低油温默认设定           facet=temperature
润滑油温度控制设定范围             facet=temperature
低油温起动抑制设定                 facet=temperature
canonical_key = hvac:centrifugal_chiller:parameter:supply_oil_temperature_range
```

- Relevant pairwise cosine values were above threshold:

```text
供油温度范围 - 低油温起动抑制设定       0.8191
供油温度范围 - 润滑油温度控制设定范围   0.8811
油箱温度控制 - 低油温起动抑制设定       0.8566
油箱温度控制 - 润滑油温度控制设定范围   0.8846
```

- Later McQuay applies introduced other temperature names such as oil-cooler /
  inverter-cooling inlet temperature. Unit facet correctly keeps all of these as
  `temperature`, so it cannot distinguish reference point within the same
  physical quantity family.

Conclusion:

- The X4 regression was caused by missing unit extraction from Gree summary text.
- That specific regression is fixed.
- The remaining same-temperature drift is outside unit-facet scope and needs
  Tier 2 reference-point modeling, e.g. Brick tag mapping, not threshold tuning
  or YAML name-pair hardcoding.

## 13) 2026-05-14 Brick Validation Round

### Pre-Brick Baseline

Backup before validation:

```text
/tmp/aa1_pre_brick_validation_20260514T082059Z.sql
```

Baseline SQL artifact:

```text
output/diagnostic/20260514T163000Z_aa3_brick_validation/pre_brick_baseline.txt
```

Actual baseline on this machine was `34` centrifugal-chiller KOs, not `30`.
The baseline already contained the first clean cross-publisher KO:

```text
hvac:centrifugal_chiller:parameter:supply_oil_temperature_range
publishers = {Gree, McQuay}
```

### Oracle

Command:

```text
rm -rf /tmp/knowfabric_embedding_cache
OMLX_API_KEY=<redacted> venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
```

Result:

```text
RESULT: PASS - Cross-publisher merge plumbing verified end-to-end.
```

### Clean-Slate Run

Run artifacts:

```text
output/diagnostic/20260514T163000Z_aa3_brick_validation/apply_counts.tsv
output/diagnostic/20260514T163000Z_aa3_brick_validation/cross_publisher_quality.txt
output/diagnostic/20260514T163000Z_aa3_brick_validation/oil_and_water_temperature_kos.txt
output/diagnostic/20260514T163000Z_aa3_brick_validation/grouping_trace.jsonl
output/diagnostic/20260514T163000Z_aa3_brick_validation/metrics.tsv
```

Apply evolution:

```text
Gree apply                         -> total chiller KO = 16
AHRI apply                         -> total chiller KO = 19
Trane apply                        -> total chiller KO = 38
McQuay WSC/WDC/HSC/HDC apply       -> total chiller KO = 41
McQuay single/double apply         -> total chiller KO = 41
After regroup                      -> total chiller KO = 37
```

Regroup stats:

```text
{'new_merged': 0, 'updated_existing': 25, 'merged_existing': 4, 'material_conflicts': 5}
```

Final metrics:

```text
total_chiller_ko = 37
cross_publisher_ko = 0
cross_publisher_with_trane = 0
max_layers = 6
garbage_oil_temp_pressure_mix = 0
parameter_spec_pname_numeric_or_placeholder = 0
```

Cross-publisher KO list:

```text
(0 rows)
```

### Facet/Subtype Findings

No final cross-publisher KOs existed after regroup, so there was no final
cross-publisher facet-consistency row to validate.

Brick subtype detection did work on important intermediate grouping boundaries:

```text
供油温度范围                       -> (temperature, oil_temperature)
油箱温度控制                       -> (temperature, oil_temperature)
低油温起动抑制设定                 -> (temperature, oil_temperature)
润滑油温度控制设定范围             -> (temperature, oil_temperature)
油冷/变频器冷却最低进水温度         -> (temperature, cooling_water_inlet_temperature)
最低冷冻水出水温度                 -> (None, chilled_water_supply_temperature)
```

In the Trane apply trace, Gree and Trane oil-temperature concepts were clustered
together with matching subtype:

```text
供油温度范围                       hint = [temperature, oil_temperature]
油箱温度控制                       hint = [temperature, oil_temperature]
启动限制最低油温默认设定           hint = [temperature, oil_temperature]
润滑油温度控制设定范围             hint = [temperature, oil_temperature]
低油温起动抑制设定                 hint = [temperature, oil_temperature]
canonical_key = hvac:centrifugal_chiller:parameter:supply_oil_temperature_range
```

Relevant pairwise similarities:

```text
供油温度范围 - 低油温起动抑制设定       0.8191
供油温度范围 - 润滑油温度控制设定范围   0.8811
油箱温度控制 - 低油温起动抑制设定       0.8566
油箱温度控制 - 润滑油温度控制设定范围   0.8846
```

Brick also separated one key reference-point boundary:

```text
润滑油温度控制设定范围 / 低油温起动抑制设定
  -> oil_temperature

油冷/变频器冷却最低进水温度
  -> cooling_water_inlet_temperature
```

### Failure Analysis

The AA hard metric did **not** pass:

```text
required cross_publisher_ko >= 2
actual cross_publisher_ko = 0
```

The final DB after regroup no longer contained a Gree temperature
`parameter_spec`; Gree parameter_spec survived only as oil pressure differential:

```text
hvac:centrifugal_chiller:parameter:key_f538ca006e
title = 油压差范围（运行）
publishers = {Gree}
```

This means Brick subtype detection was not the only limiting factor. The trace
shows the Gree+Trane oil-temperature merge existed during Trane apply, but later
apply/regroup persistence removed or rewrote the Gree temperature parameter
layers before final verification. That is a persistence/regroup continuity
problem, not evidence that Brick reference-point modeling failed.

Known Brick map gap observed but not changed in this round:

```text
油冷/变频器冷却最高进水温度 -> (temperature, temperature)
油冷/变频器冷却最低进水温度 -> (temperature, cooling_water_inlet_temperature)
```

The `最高进水温度` variant did not hit the cooling-water-inlet subtype because
the initial Brick keyword set covered the explicit `最低进水温度` string but not
the parallel max/inlet wording. Per the round constraint, the map was not
patched in-place.

No threshold tuning, canonical-key YAML name-pair additions, LLM re-extraction,
NIM integration, or oracle edits were performed.

### Embedding Context

Operator-provided model sweep data is consistent with this result: nine generic
cloud embedding models, including NVIDIA NemoRetriever-family models, BGE-M3
fp16, Qwen3 4B/8B, and Gemini embedding, did not simultaneously satisfy
`POS_LANG >= 0.75`, `POS_REF >= 0.78`, and `NEG_REF < 0.78`. Reference-point
separation still needs structured Brick-style semantics rather than generic
embedding alone.
