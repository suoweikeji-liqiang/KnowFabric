# Phase1 KEEP_TEXT Batch Report

Generated: 2026-05-16T04:23:17.884257+00:00

## Scope
- Input: `/Users/asteroida/work/KnowFabric/storage/authority_sources/hvac/_phase1_batch/_phase1_batch_manifest.csv`
- Filter: `text_quality IN ('text','mixed')`, 136 PDFs (`text=121`, `mixed=15`).
- Backend: `deepseek-parameter-spec`; OpenRouter was not used for this run.
- Extraction: 125 doc-level PDFs + 11 section-aware large standards.
- Review packs applied: 131 packs, 4184 candidates. Publisher was backfilled from `document.publisher/vendor_brand` or manifest before final apply.

## Backups
- `/tmp/phase1_text_pre_import_extract_20260515T173203Z.sql`
- `/tmp/phase1_text_pre_apply_bitset_20260515T204539Z.sql`
- `/tmp/phase1_text_pre_apply_publisher_20260516T001108Z.sql`
- `/tmp/phase1_text_pre_final_regroup_20260516T041645Z.sql`

## Extraction / Review
- Candidate entries: `4184`
- Candidate type mix from packs: parameter_spec 2783, performance_spec 442, application_guidance 403, fault_code 222, maintenance_procedure 136, operational_sequence 136, fault_diagnostic_rule 45, symptom 11, diagnostic_step 6.
- Apply report: `apply_publisher_report.json` => applied 131, skipped 0, failed 0.

## KO Results
- Total KO: `3232` (baseline `1280`, net `+1952`).
- Degenerate canonical_key (`:[0-9]+$`): `0`.
- KOs with layers > 8: `0`.

| ontology_class_id | total | cross_pub | baseline_cross_pub | delta | max_layers |
|---|---:|---:|---:|---:|---:|
| centrifugal_chiller | 1611 | 37 | 20 | 17 | 8 |
| ahu | 559 | 31 | 0 | 31 | 8 |
| standard_reference | 493 | 2 | 0 | 2 | 8 |
| screw_chiller | 255 | 37 | 0 | 37 | 6 |
| water_source_heat_pump | 93 | 9 | 0 | 9 | 8 |
| chiller | 80 | 0 | 0 | 0 | 5 |
| air_cooled_modular_heat_pump | 77 | 7 | 0 | 7 | 8 |
| hot_water_plant | 42 | 0 | 0 | 0 | 6 |
| magnetic_bearing_chiller | 11 | 0 | 0 | 0 | 2 |
| variable_frequency_drive | 8 | 0 | 0 | 0 | 2 |
| chilled_water_pump | 1 | 0 | 0 | 0 | 2 |
| condenser_water_pump | 1 | 0 | 0 | 0 | 2 |
| cooling_tower | 1 | 0 | 0 | 0 | 1 |

## Cross-Language Merge Cases
Examples with both Chinese and English publisher labels in one KO:

| KO ID | class | canonical_key | title | publishers | consensus | layers |
|---|---|---|---|---|---|---:|
| ko_0d07e38beb2cde12 | centrifugal_chiller | `hvac:ahu:performance_spec:key_bc82deec2d` | 制冷量 | McQuay, 特灵 | material_conflict | 7 |
| ko_049900646e2b1794 | ahu | `hvac:ahu:parameter:water_temperature_limits` | Water Temperature Limits | unknown, 格力, 美的, 麦克维尔 | material_conflict | 7 |
| ko_43f6959cb535869f | centrifugal_chiller | `hvac:screw_chiller:performance_spec:cop` | COP | McQuay, 特灵 | material_conflict | 5 |
| ko_14b2f0c258dccd4c | centrifugal_chiller | `hvac:centrifugal_chiller:parameter:chilled_water_setpoint` | 冷冻水出水温度设定 | McQuay, 格力 | agreed | 5 |
| ko_05cadbc5549457f3 | standard_reference | `hvac:standard_reference:application:method_of_testing_thermal_storage_devices` | Method of Testing Thermal Storage Devices | ASHRAE, 特灵 | material_conflict | 5 |
| ko_04dc5b2658675b79 | centrifugal_chiller | `hvac:centrifugal_chiller:fault_code:key_9594a80439` | 油压差报警/保护 | Carrier, 格力 | partial_conflict | 5 |
| ko_02e2749573080a28 | centrifugal_chiller | `hvac:centrifugal_chiller:fault_code:key_90cab05c63` | 推力轴承—油温传感器 | Carrier, York, 格力 | material_conflict | 5 |
| ko_ac1ec4ada2e33a7b | ahu | `hvac:ahu:performance_spec:air_flow_range` | air_flow_range | Carrier, Holtop, 特灵, 麦克维尔 | material_conflict | 4 |

## Top Cross-Publisher KOs

| class | canonical_key | title | publishers | consensus | layers |
|---|---|---|---|---|---:|
| centrifugal_chiller | `hvac:centrifugal_chiller:application:room_temperature_and_humidity_limits` | Room temperature and humidity limits | 格力, 盾安 | material_conflict | 8 |
| centrifugal_chiller | `hvac:centrifugal_chiller:parameter:key_9fc1319bb1` | 启动电流 | Carrier, McQuay | partial_conflict | 8 |
| ahu | `hvac:ahu:parameter:water_temperature_limits` | Water Temperature Limits | 格力, 美的, 麦克维尔, unknown | material_conflict | 7 |
| centrifugal_chiller | `hvac:ahu:performance_spec:key_bc82deec2d` | 制冷量 | 特灵, McQuay | material_conflict | 7 |
| screw_chiller | `hvac:screw_chiller:parameter:power_supply` | 电源 | 顿汉布什, 麦克维尔 | material_conflict | 6 |
| screw_chiller | `hvac:ahu:performance_spec:key_bc82deec2d` | 制冷量 | 特灵, 麦克维尔 | partial_conflict | 6 |
| screw_chiller | `hvac:centrifugal_chiller:parameter:key_2b0d5b413b` | 能量调节范围 | 欧科, 约克, 麦克维尔 | material_conflict | 5 |
| air_cooled_modular_heat_pump | `hvac:air_cooled_modular_heat_pump:parameter:maximum_hot_water_outlet_temperature` | maximum hot water outlet temperature | 特灵, 麦克维尔 | material_conflict | 5 |
| standard_reference | `hvac:standard_reference:application:method_of_testing_thermal_storage_devices` | Method of Testing Thermal Storage Devices | 特灵, ASHRAE | material_conflict | 5 |
| screw_chiller | `hvac:screw_chiller:parameter:key_b45c97cb55` | 制冷剂 | 约克, 麦克维尔 | partial_conflict | 5 |
| centrifugal_chiller | `hvac:centrifugal_chiller:fault_code:key_9594a80439` | 油压差报警/保护 | 格力, Carrier | partial_conflict | 5 |
| screw_chiller | `hvac:screw_chiller:maintenance:key_d4a11fbe9e` | 油加热器预热时间 | 国祥, 天加, 盾安 | material_conflict | 5 |
| centrifugal_chiller | `hvac:centrifugal_chiller:fault_code:key_90cab05c63` | 推力轴承—油温传感器 | 格力, Carrier, York | material_conflict | 5 |
| centrifugal_chiller | `hvac:centrifugal_chiller:parameter:chilled_water_setpoint` | 冷冻水出水温度设定 | 格力, McQuay | agreed | 5 |
| screw_chiller | `hvac:screw_chiller:performance_spec:key_6428129801` | 排气压力 | 天加, 约克 | material_conflict | 5 |
| centrifugal_chiller | `hvac:screw_chiller:performance_spec:cop` | COP | 特灵, McQuay | material_conflict | 5 |
| centrifugal_chiller | `hvac:centrifugal_chiller:parameter:key_42f5d7a8ec` | 重启抑制时间设定值 | Carrier, Trane | material_conflict | 4 |
| screw_chiller | `hvac:centrifugal_chiller:performance_spec:key_47246f135c` | 性能系数 | 欧科, 麦克维尔 | partial_conflict | 4 |
| centrifugal_chiller | `hvac:centrifugal_chiller:operational_sequence:key_deeba31c9b` | 全自动启动顺序 | 格力, 约克 | material_conflict | 4 |
| centrifugal_chiller | `hvac:centrifugal_chiller:performance_spec:key_c001032cf6` | 排水管接口尺寸 | 特灵, York | material_conflict | 4 |

## Verification
- Oracle: PASS (`scripts/verify_cross_publisher_merge.py --skip-precheck`).
- Tests: PASS, `397 passed`.
- Gates: PASS, `bash scripts/check-all` 4/4 gates.

## Notes
- `centrifugal_chiller` cross_pub improved from actual baseline 20 to 37 (`+17`), below the requested >=45 target. AHU reached 31 cross_pub and screw_chiller reached 37 cross_pub.
- Many new cross_pub KOs are `material_conflict`; this run validates throughput and publisher plumbing, but quality sampling should remain a follow-up before GA claims.
- During apply, complete-linkage CPU stalled on repeated NumPy submatrix copies. The fix keeps complete-linkage semantics and replaces repeated submatrix checks with bitset membership masks; clustering tests pass.
