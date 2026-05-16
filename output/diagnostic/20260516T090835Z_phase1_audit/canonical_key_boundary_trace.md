# Canonical Key Boundary Trace

Scope: read-only DB + review-pack source inspection. No phase1 `grouping_trace.jsonl` file was present under `output/diagnostic/20260515T173143Z_phase1_keep_text/`, so cluster-level trace is unavailable for this run. Source lookup includes phase1 accepted packs plus the earlier visual accepted packs because some layers predate phase1.

## ko_0d07e38beb2cde12

| field | value |
|---|---|
| ontology_class_id | centrifugal_chiller |
| knowledge_object_type | performance_spec |
| canonical_key | `hvac:ahu:performance_spec:key_bc82deec2d` |
| title | 制冷量 |
| consensus_state | material_conflict |
| conflict_summary | Significant value disagreement across 7 sources |
| prefix_check | expected `hvac:centrifugal_chiller`, actual `hvac:ahu` |

### Authority layers and source candidates

| layer | publisher | source_name | layer doc/chunk | layer payload equipment_class_id | source pack equipment_class_candidate | source canonical_key_candidate | source pack |
|---:|---|---|---|---|---|---|---|
| 1 | McQuay | 制冷量 | `doc_fa41ab46ea8d4bd7` / `chunk_40b14f2fb3a6489f` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 2 | McQuay | 制冷量 | `doc_fa41ab46ea8d4bd7` / `chunk_fcbd31b949284aad` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 3 | McQuay | 制冷量 | `doc_fa41ab46ea8d4bd7` / `chunk_793314253e174227` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 4 | McQuay | 压缩机输入功率(制冷) | `doc_fa41ab46ea8d4bd7` / `chunk_671355f0ee3d4476` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 5 | McQuay | 每台制冷量 | `doc_fa41ab46ea8d4bd7` / `chunk_13860dd5ed314adc` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 6 | 特灵 | 制冷量 | `doc_2380c51ffae04bff` / `chunk_eb342529e1ea4c8b` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'maintenance_procedure', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:cvhe_g` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0060_hvac__doc_2380c51ffae04bff__centrifugal_chiller.json` |
| 7 | 特灵 | 制冷量 | `doc_2380c51ffae04bff` / `chunk_15408d60091e4eed` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'maintenance_procedure', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:cdhg` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0060_hvac__doc_2380c51ffae04bff__centrifugal_chiller.json` |

### Evidence snippets

- `doc_2380c51ffae04bff` p.1 `chunk_eb342529e1ea4c8b` unknown `CTV三级压缩离心机2012样本.pdf`: August 2011 CTV-PRC009-ZHCVHE/G &CDHG 三级压缩离心式冷水机组 (蓄冰/大温差/热回收) CenTraVac® Water-Cooled Liquid Chillers 400~1400&1200~2600Tons
- `doc_2380c51ffae04bff` p.4 `chunk_15408d60091e4eed` unknown `CTV三级压缩离心机2012样本.pdf`: 12345引言 从二十世纪三十年代开发生产第一台封 闭式离心冷水机组开始，特灵公司便一直以先进的技术和可靠的产品称雄于世界中央空调市场。1959年 ，特灵 公司开 始生产世 界上第一 台直接驱动的两级压缩 冷水机组， 使其一 跃成为世界空调业的巨 人。 1981 年，特灵 公司开发出世界 上第 一台直接驱动的三级压缩冷水机组， 该机 组将三级压缩、直接传动和二级经济器等 先进的节能技术集于一体，成为 世界上效 率最 高、振动最小、噪音最低、制冷剂 泄漏 量最少的机组。 自问世以来，该机组 以其性能优越、质量 可靠和投资回报率高 而赢得了用户的青 睐，在美国及全球的销 量远远超过其它 品牌的机组，成为世界空 调行业的首选。产品特性 图3 购买机组总投资图2 著名的“硬币试验” 图1 权威AHRI认证高效节能的典范...
- `doc_fa41ab46ea8d4bd7` p.20 `chunk_13860dd5ed314adc` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: 每台制冷量 冷吨 800
- `doc_fa41ab46ea8d4bd7` p.55 `chunk_fcbd31b949284aad` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: 制冷量 kW 1028.2
- `doc_fa41ab46ea8d4bd7` p.56 `chunk_793314253e174227` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: 制冷量 kW 1196.2
- `doc_fa41ab46ea8d4bd7` p.57 `chunk_40b14f2fb3a6489f` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: 制冷量 kW 1385.5
- `doc_fa41ab46ea8d4bd7` p.76 `chunk_671355f0ee3d4476` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: 压缩机输入功率(制热) kW 100.4

### Boundary judgement

落库/merge canonical_key 继承 bug。可找到的 source candidates 和 persisted KO ontology 都是 `centrifugal_chiller`; `hvac:ahu` 只出现在最终 canonical_key prefix。另有一个错误合并层：`压缩机输入功率(制冷)` 被并入 `制冷量`。

## ko_43f6959cb535869f

| field | value |
|---|---|
| ontology_class_id | centrifugal_chiller |
| knowledge_object_type | performance_spec |
| canonical_key | `hvac:screw_chiller:performance_spec:cop` |
| title | COP |
| consensus_state | material_conflict |
| conflict_summary | Significant value disagreement across 5 sources |
| prefix_check | expected `hvac:centrifugal_chiller`, actual `hvac:screw_chiller` |

### Authority layers and source candidates

| layer | publisher | source_name | layer doc/chunk | layer payload equipment_class_id | source pack equipment_class_candidate | source canonical_key_candidate | source pack |
|---:|---|---|---|---|---|---|---|
| 1 | McQuay | COP | `doc_fa41ab46ea8d4bd7` / `chunk_a9bca3459a674947` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 2 | McQuay | COP | `doc_fa41ab46ea8d4bd7` / `chunk_64b9dd94c04f401b` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 3 | McQuay | COP | `doc_fa41ab46ea8d4bd7` / `chunk_ad8fc94853de44e4` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:candidate` | `output/diagnostic/20260514T124900Z_visual_apply/accepted_review_packs/05_mcquay/hvac__doc_fa41ab46ea8d4bd7__centrifugal_chiller.json` |
| 4 | 特灵 | COP | `doc_2380c51ffae04bff` / `chunk_6c39bd9075a64149` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'maintenance_procedure', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:cdhg_cop` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0060_hvac__doc_2380c51ffae04bff__centrifugal_chiller.json` |
| 5 | 特灵 | capacity_range | `doc_e8575c350d45402d` / `chunk_2c37369711584242` |  | {'equipment_class_id': 'centrifugal_chiller', 'equipment_class_key': 'hvac:centrifugal_chiller', 'label': 'Centrifugal Chiller', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['fault_code', 'parameter_spec', 'maintenance_procedure', 'performance_spec']} | `hvac:centrifugal_chiller:performance_spec:cdhf_g` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0032_hvac__doc_e8575c350d45402d__centrifugal_chiller.json` |

### Evidence snippets

- `doc_e8575c350d45402d` p.14 `chunk_2c37369711584242` unknown `特灵离心式水冷冷水机.pdf`: A -S A ir -C ondit ioning S y s t em ( T ianjin ) Lt d A -S A ir -C ondit ioning S y s t em ( T ianjin ) Lt d C us t omer T r aining C V H E C us t omer T r aining C V H E 特灵大型离心式水冷冷水机 L H C V L H C V L H C V L H C V 两级离心式机组 用于 6 0 6 0 6 0 6 0 H z H z H z H z 供电系统 1 3 0 0 ~ 3 0 0 0 1 3 0 0 ~ 3 0 0 0 1 3 0 0 ~ 3 0 0 0 1 3 0 0 ~ 3 0 0 0 冷吨 电机转速 3 6 0 0 3 6 0 0...
- `doc_2380c51ffae04bff` p.19 `chunk_6c39bd9075a64149` unknown `CTV三级压缩离心机2012样本.pdf`: 压缩机型号 换热器规格 冷量范围 外形尺寸长 宽(远程启动柜) 高 接管Tons mmmmmm mm2250 210D/210M/250D ~2600 7619 34723542 DN4002.单回程设计，减小壳管的水压降1.独有串联逆流设计，AHRI工况下COP可达7.0 3.最低卸载到 5% 4.双机头设计，启动电流小5.高/中/低压供电 注：冷凝器和蒸发器的进/ 出水方向相反。抽 气 装 置压缩机 蒸发器 经济器冷凝器CDHG机组 19CDHG 技术参数表接管示意图 机组特点
- `doc_fa41ab46ea8d4bd7` p.44 `chunk_ad8fc94853de44e4` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: COP 5.32
- `doc_fa41ab46ea8d4bd7` p.45 `chunk_a9bca3459a674947` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: COP 5.89
- `doc_fa41ab46ea8d4bd7` p.46 `chunk_64b9dd94c04f401b` 麦克维尔 `【麦克维尔】离心机技术资料合成本（95页）-制冷百家网.pdf`: COP 5.98

### Boundary judgement

落库/merge canonical_key 继承 bug。source candidates 和 KO ontology 是 `centrifugal_chiller`; `hvac:screw_chiller` prefix 只在最终 canonical_key 中出现。另有语义误合并层：`capacity_range` 被并入 COP。

## ko_05cadbc5549457f3

| field | value |
|---|---|
| ontology_class_id | standard_reference |
| knowledge_object_type | application_guidance |
| canonical_key | `hvac:standard_reference:application:method_of_testing_thermal_storage_devices` |
| title | Method of Testing Thermal Storage Devices |
| consensus_state | material_conflict |
| conflict_summary | Significant value disagreement across 5 sources |
| prefix_check | expected `hvac:standard_reference`, actual `hvac:standard_reference` |

### Authority layers and source candidates

| layer | publisher | source_name | layer doc/chunk | layer payload equipment_class_id | source pack equipment_class_candidate | source canonical_key_candidate | source pack |
|---:|---|---|---|---|---|---|---|
| 1 | ASHRAE | Method of Testing Thermal Storage Devices | `doc_472265f3b7f141f8` / `chunk_20560b2727174a8d` | standard_reference | {'equipment_class_id': 'standard_reference', 'equipment_class_key': 'hvac:standard_reference', 'label': 'Standard Reference', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['application_guidance', 'performance_spec', 'operational_sequence', 'parameter_spec']} | `hvac:standard_reference:application_guidance:method_of_testing_thermal_storage_devices` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0125_hvac__doc_472265f3b7f141f8__standard_reference.json` |
| 2 | ASHRAE | Double-Effect Absorption Chiller COP Requirement | `doc_38a89d59e8394e2d` / `chunk_a01e5643f5f448bf` | standard_reference | {'equipment_class_id': 'standard_reference', 'equipment_class_key': 'hvac:standard_reference', 'label': 'Standard Reference', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['application_guidance', 'performance_spec', 'operational_sequence', 'parameter_spec']} | `hvac:standard_reference:application_guidance:double_effect_absorption_chiller_cop_requirement` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0128_hvac__doc_38a89d59e8394e2d__standard_reference.json` |
| 3 | 特灵 | 热回收使用条件（ASHRAE 90.1-2001） | `doc_eb6bc699034c4ba5` / `chunk_e9bc7bcfacdb4a7f` |  | {'equipment_class_id': 'standard_reference', 'equipment_class_key': 'hvac:standard_reference', 'label': 'Standard Reference', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['application_guidance', 'performance_spec', 'operational_sequence', 'parameter_spec']} | `hvac:standard_reference:application_guidance:ashrae_90_1_2001` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0074_hvac__doc_eb6bc699034c4ba5__standard_reference.json` |
| 4 | ASHRAE | Method of Testing for Rating Seasonal Efficiency of Unitary Air-Conditioners and... | `doc_472265f3b7f141f8` / `chunk_0e8a7ffecc464a7d` | standard_reference | {'equipment_class_id': 'standard_reference', 'equipment_class_key': 'hvac:standard_reference', 'label': 'Standard Reference', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['application_guidance', 'performance_spec', 'operational_sequence', 'parameter_spec']} | `hvac:standard_reference:application_guidance:method_of_testing_for_rating_seasonal_efficiency_of_unitary_air_conditioners_and_heat_pumps` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0125_hvac__doc_472265f3b7f141f8__standard_reference.json` |
| 5 | ASHRAE | Method of Testing for Rating Commercial Gas, Electric, and Oil Service Water Hea... | `doc_472265f3b7f141f8` / `chunk_1a1dcbfd77124c18` | standard_reference | {'equipment_class_id': 'standard_reference', 'equipment_class_key': 'hvac:standard_reference', 'label': 'Standard Reference', 'confidence': 1.0, 'matched_aliases': [], 'supported_knowledge_anchors': ['application_guidance', 'performance_spec', 'operational_sequence', 'parameter_spec']} | `hvac:standard_reference:application_guidance:method_of_testing_for_rating_commercial_gas_electric_and_oil_service_water_heating_equipment` | `output/diagnostic/20260515T173143Z_phase1_keep_text/model_accepted_review_packs_with_publisher/0125_hvac__doc_472265f3b7f141f8__standard_reference.json` |

### Evidence snippets

- `doc_eb6bc699034c4ba5` p.6 `chunk_e9bc7bcfacdb4a7f` unknown `特灵暖通空调系统设计指南.pdf`: 3 54水泵压头、 速度重置 制冷剂每冷 吨充注量将泵的运行压力重置可以保 证自控阀对压力需求最大时的开度为 90%左右。 泵节能 (11)没有相关的文献讲述优 化泵压，但可参阅风机控制的相关原理： (10) 6热回收 水冷式制冷机组冷凝器的热 量回收，可以用来提供: 加热冷空气 (用于湿度控制） 预热室外空气加热进入建筑物的补水制冷剂越少则系统泄漏对环境的影响也越小，特别是中高压系统可参照 ASHRAE 技术指南第 三部 进一步减少制冷剂的耗 散减少系统中的制冷剂量 ASHRAE 90.1-2001 要 求在下列情况下使用热回收加热生活用水：设备每天 24小时运行 系统总散热量超过6,000,000 Btu/h ( 约相当 于450冷吨的冷水机组 ) 生活用水的设计加热负荷超过 1,000,000 Btu/h...
- `doc_38a89d59e8394e2d` p.138 `chunk_a01e5643f5f448bf` ASHRAE `ASHRAE绿色建筑指南.pdf`: A S H R AE G R E E N G U I D E   1 2 1 grams are c o nc e rne d no t o nl y wi th the b ui l di ng he at gai n b ut al s o wi th the c o ntri b u- ti o n o f the b ui l di ng s truc ture and as s o c i ate d hards c ap e wi th the he at i s l and e f f e c t. T he he at i s l and e f f e c t i s a s i te s i s s ue , rathe r than s tri c tl y a b ui l di ...
- `doc_472265f3b7f141f8` p.1041 `chunk_0e8a7ffecc464a7d` unknown `ASHRAE_Handbook_-_Fundamentals_2021_-_IP_(NXPowerLite_Copy).pdf`: Codes and Standards 41.15 Single Package Vertical Air-Conditioner and Heat Humps AHRI ANSI/AHRI 390-2003 Direct Geoexchange Heat Pumps AHRI ANSI/AHRI 870-2005 Variable Refrigerant Flow (VRF) Multi-Split Air-Conditioning and Heat Pump EquipmentAHRI ANSI/AHRI 1230-2010 Methods of Testing for Rating Electrically Driven Unitary Air-Conditioning and Heat Pump Equ...
- `doc_472265f3b7f141f8` p.1051 `chunk_20560b2727174a8d` unknown `ASHRAE_Handbook_-_Fundamentals_2021_-_IP_(NXPowerLite_Copy).pdf`: SMACNA SMACNA 2002 Thermal StorageThermal Energy Storage: A Guide for Commercial HVAC Contractors ACCA ACCA 2005 Method of Testing Thermal Storage Devices wi th Electrical Input and Thermal Output Based on Thermal PerformanceASHRAE ANSI/ASHRAE 94.2-2010 Measurement, Testing, Adjusting, and Balancing of Building HVAC Systems ASH RAE ANSI/ASHRAE 111-2008 Metho...
- `doc_472265f3b7f141f8` p.1053 `chunk_1a1dcbfd77124c18` unknown `ASHRAE_Handbook_-_Fundamentals_2021_-_IP_(NXPowerLite_Copy).pdf`: SMACNA SMACNA 2013 Water Heaters Desuperheater/Water Heaters AHRI ANSI/AHRI 470-2006 Safety for Electrically Heated Live stock Waterers ASABE ASAE EP342.3-2010 Methods of Testing to Determine the Thermal Performance of Solar Domestic Water Heating SystemsASHRAE ANSI/ASHRAE 95-1981 (RA87) Method of Testing for Rating Commercial Gas, Electric, and Oil Service ...

### Boundary judgement

不是 canonical_key/ontology prefix 越界：KO ontology 与 key prefix 都是 `standard_reference`。问题是 semantic over-merge：Trane 设计指南中的 ASHRAE 90.1 热回收条件与 ASHRAE 标准测试方法列表聚到同一 KO。
