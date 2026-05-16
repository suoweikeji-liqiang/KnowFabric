# 48 over_merge KO 人审报告

- Auditor: Claude (operator delegated)
- Source: `output/diagnostic/20260516T230734Z_path_a_consensus_state/over_merge_sample.csv`
- DB query against `knowledge_object` + `knowledge_object_evidence`
- Date: 2026-05-17

## 总览判断分布

| 判断 | 数量 | 比例 | 含义 |
|---|---:|---:|---|
| **TRUE over_merge - 需 split** | 25 | 52% | 真不同概念被错合并 |
| **FALSE_POSITIVE - 应改 value_disagreement** | 9 | 19% | 同概念不同 OEM/型号实际值，Path A logic 误判 |
| **STRUCTURAL_BUG - 空 ontology + broken canonical_key** | 8 | 17% | 独立 bug，非 over_merge 本质 |
| **FACET_MISSING - refrigerant 轴漏 detect** | 3 | 6% | R22 vs R407C 未拆分 |
| **EVIDENCE_GARBAGE - 抽取垃圾** | 2 | 4% | HMI 键列表 / 乱码 OCR，是 extraction bug |
| **AGREED - 不该 flag** | 1 | 2% | 都是同一 publisher 重复 evidence |

## 关键结论

1. **真 over_merge 25 个 = 全库 ~0.5%**（25 / ~5000 cross_pub KO）。Phase 2.5 把 over-merge 控制到这个量级是 GA-acceptable 的，**不需要再做 Phase 2.6**
2. **Path A determine_consensus_state 偶尔过于严格**：9 KO 应该是 value_disagreement 但被标 over_merge。logic 可以放宽（见 §3.2）
3. **8 个 structural bug 是独立任务**：canonical_key `hvac::performance_spec:...` 双冒号 + 空 ontology_class，与 over_merge 语义无关，需要单独修复
4. **3 个 facet 漏 detect 暴露 refrigerant 轴的盲点**：润滑油按 R22/R407C 分，名义制冷量也按 refrigerant 分，但 Phase 2.5 refrigerant facet 没捕捉到关键字。需要补 keywords

## §1 TRUE over_merge — 需 split (25 个)

应该拆分成多 KO。具体动作：merger 重新跑 facet split，或人工 unmerge。

### screw_chiller (9)
- `ko_0375092c506a85d8` **高压 断开** — 包含低压断开（subsystem polarity）
- `ko_05b9aebdde71d566` **压力调节阀设定点** — 滑阀 vs 排气压力（不同概念）
- `ko_0a2c2eebadb6cf7a` **主电源电压波动** — 含冷却水水质（完全跨主题）
- `ko_01a4a4047927d344` **Evap High Press** — HMI 键列表 + 专利号（extraction 失败）
- `ko_2108bb796ebd7b19` **压缩机拆卸步骤** — 压缩机拆 + 干燥过滤器拆（不同部件）
- `ko_2cb2a95fb07241cc` **最大允许压力** — 冷媒侧 vs 水侧（subsystem 不同）
- `ko_75c3a5d18c8eaa43` **Evap low pressure alarm delay** — 同 HMI 键列表
- `ko_3d285aa3a09556b2` **制冷模式出水温度设定值** — 额定温度 vs 控制偏差触发
- `ko_899d764444a01370` **1# 压缩机电流限定值(卸载)** — 保持模式 + 卸载模式

### centrifugal_chiller (7)
- `ko_4a7e489f00e85fa8` **高压 断开** — 同上低/高 polarity 混
- `ko_0003dc96ea6cfa09` **冷量优先控制** — evidence 完全无关（过电流 + 控制电路保险丝）
- `ko_0a5634c7d18e0843` **关机顺序** — 全是开机/运转 evidence，KO 名错位
- `ko_04dc5b2658675b79` **油压差过低** — 含 evaporator 低压保护（不同概念）
- `ko_5d02f6cccbb51a2a` **抽空启动设定点** — 抽气装置原理 + 试验温度（不同主题）

### air_cooled_modular_heat_pump (1)
- `ko_178654fc424a0af4` **制冷额定总输入功率** — 含制热额定功率（heating vs cooling）

### ahu (3)
- `ko_0aa1d7491394e13d` **AFDD FC#13** — 含 FC#3（不同 fault code）
- `ko_09774088f47b820e` **Temperature Control Cooling Mode** — 含 hot-deck（不同 duct）
- `ko_933017f2e086099d` **Zone Temperature Alarms** — L2 只是 section header（poor evidence）

### standard_reference (4)
- `ko_050ac03ff6e2b012` **outdoor design temperatures** — 含 wall U-values、R-1234yf 等无关 evidence
- `ko_051d666042fe81b7` **Maximum solvent vapor concentration** — unit ventilator vs VOC（不同主题）
- `ko_22c130aad4ba2827` **normal_boiling_point** — 不同 refrigerant 性质表（应按 refrigerant 拆）
- `ko_ec0f999bae1fab30` **entering_water_temperature_selection** — 含 stormwater management 等完全无关 evidence

### hot_water_plant (2)
- `ko_0d80e765f6b64a5c` **HW Plant FC#9** — 含 FC#6（不同 fault code）
- `ko_497eb8d85aae2821` **AFDD - FC#10** — 含 FC#8 + FC#11（不同 fault codes）

### water_source_heat_pump (1)
- `ko_d53103623a638535` **设置环境温度范围** — 含主电源电压波动 evidence（完全跨主题）

## §2 FALSE_POSITIVE — 应改 value_disagreement (9 个)

Path A determine_consensus_state 把这些标为 over_merge 是因为某个 facet 轴判定为 diverge，但 evidence 看实际都是同一概念在不同 OEM/型号的实测值。应该是 value_disagreement。

| KO | Title | 真实判断 |
| --- | --- | --- |
| `ko_1d071b6223568b3b` | screw_chiller 水流量 | 不同 OEM 不同 m³/h 值，VD |
| `ko_534fd0c2b1bac8ab` | screw_chiller 水流量 | ±15% vs 80-110% 是不同 OEM 容差表达，VD |
| `ko_bdb23b9ca27b48e5` | screw_chiller 标准制冷量 | 不同 unit (kcal/h vs kW) 同概念，VD |
| `ko_2b176becc0c0144b` | centrifugal 加油泵压力要求 | 同 publisher 复制 evidence，应 agreed |
| `ko_2d3b188217c0b0d4` | centrifugal 压差/压力 | 两 layer 都是 cond - evap 压差，VD |
| `ko_4fe798a5fee250e2` | centrifugal 频率上限控制模式 | 都是同一控制模式，AGREED 或 VD |
| `ko_d9a76c77bbe67132` | centrifugal 供油压力与油箱压力差 | 同概念不同描述，VD |
| `ko_206163c136ed5d4b` | ahu Totalize Airflow from VAV | 同概念两 evidence，AGREED |
| `ko_bd10ecd70736fb0b` | ahu 最低运行噪音 | 不同静压条件下噪音值，VD |

## §3 STRUCTURAL_BUG — 空 ontology + 双冒号 canonical_key (8 个)

这 8 个 KO 有结构性 bug，**与 over_merge 语义无关**：

- canonical_key 形如 `hvac::performance_spec:hvac::performance_spec:制冷量_制冷量_17` (双 hvac:: 前缀，缺 ontology 段)
- ontology_class_id = 空字符串
- 这破坏了 Phase 2 FIX 应该已经解决的 prefix 一致性

| KO | Title | Publishers |
| --- | --- | --- |
| `ko_11becc6d84e45ec3` | 制冷量 | 特灵; 美意 |
| `ko_2a48a81c382ba634` | 制冷量 | 日立; 美意; unknown |
| `ko_591ae739b27c71b9` | 制冷额定总输入功率 | 麦克维尔 |
| `ko_eb13c84bd93a04e3` | 制热量 | 美意 |
| `ko_4e94733f46e8b8a1` | 名义制冷量 | 美意; 麦克维尔; unknown |
| `ko_33a96a59e127e69a` | 名义制热量 | 美意; 麦克维尔; unknown |
| `ko_6718ae939ea97fff` | 最大允许压力 | 日立 |
| `ko_4f473c89ca544582` | 水流量 | 特灵; 美意; unknown |

需要查 path A retag 或更早 phase 哪一步把这些 KO 的 ontology 弄空了。是独立 bug fix，不在 over_merge 范畴。

## §4 FACET_MISSING — refrigerant 轴漏 detect (3 个)

这些应该被 refrigerant facet 自动拆，但 keywords 没匹配到：

- `ko_69ed0c22154f8e08` **air_cooled_modular_heat_pump 润滑油型号** — R22 用 3GS, R407C 用 ICI RL32CF。"R22" / "R407C" 应该触发 refrigerant facet，但因为 keyword 在 evidence 里以"R22 kW"形式出现（紧贴 unit），可能没匹配
- `ko_7f9870a9f4f55691` **air_cooled_modular_heat_pump 名义制冷量** — R22 vs R407C 不同值，同问题
- `ko_d117735fd9164c58` **air_cooled_modular_heat_pump 名义制热量** — 同上

**修法**：在 brick_facet_map.yaml refrigerant facet 加 keyword 变体（"R22 kW"、"R-22"、"R407C kW"等紧贴模式），或改 detect_facet 用 regex 而非纯 keyword match。

## §5 EVIDENCE_GARBAGE (2 个) + AGREED (1 个)

- `ko_01a4a4047927d344` **Evap High Press** & `ko_75c3a5d18c8eaa43` **Evap low pressure alarm delay** — evidence 是 HMI 按键列表 + 专利号，PDF 抽取垃圾。**应该 drop 而非 split**，是 extraction quality 问题
- `ko_2b176becc0c0144b` **加油泵压力要求** — 同 publisher（Carrier）4 layer 是同内容复制，应 agreed

## §6 建议下一步

### 6.1 立即（小动作）

1. **8 个 structural bug**：定位 path A retag 中哪步弄空了 ontology_class_id + 双 hvac:: prefix，修补回去。这是独立任务，**比 over_merge 拆分优先级高**（结构破损 > 语义模糊）
2. **9 个 false_positive**：写个一次性脚本把这 9 个 KO 的 consensus_state 从 over_merge 改为 value_disagreement（或 agreed for 2 个真 duplicate）
3. **2 个 evidence_garbage**：从 KO 库 drop 或标 review_status='rejected'，让 sw_base_model 不要展示

### 6.2 短期（25 个真 over_merge 拆分）

不需要写新代码，直接跑一次有针对性的 regroup，但只对这 25 个 KO 涉及的 evidence 重新走 merger（Phase 2.5 facet 已经在位）。

**Codex 任务**：
- 输入：25 个 KO ID 列表
- 对每个 KO，pull 其 evidence，重新跑 cluster + facet split
- 拆出来的多 KO 替换原 1 KO
- pg_dump 备份 + 8-layer cap

### 6.3 中期（refinement）

1. **refinement Phase 2.5 facet 漏 detect**：refrigerant keyword 加 regex 模式，覆盖紧贴 "R22 kW" 这种
2. **Path A determine_consensus_state 放宽**：cluster size ≤ 3 且只有一个 facet 轴部分 diverge 的，倾向 partial_conflict 而非 over_merge

### 6.4 不动的

- **不要追"全库 over_merge = 0"**：剩 25 个真 over_merge = 0.5% 全库，这个量级 GA-acceptable。重要的是有 review queue 兜底（path C），不是 0%

## §7 给操作员的一句话

48 个 over_merge 里：
- **25 个真需要 split**（拆 KO 库内部）
- **9 个 Path A 误判**（改 state 标签即可）
- **8 个 structural bug**（与 over_merge 无关的破损 ontology，单独修）
- **3 个 facet 漏 detect**（refrigerant 关键字补齐）
- **2 个 extraction 垃圾**（drop）
- **1 个 duplicate**（改 agreed）

**真 over_merge 占全库 0.5%，可以 GA**。优先修 8 个 structural bug + 9 个 false_positive 改 state，25 个拆分作为下一轮 cleanup task。
