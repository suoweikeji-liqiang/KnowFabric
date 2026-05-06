# Trane CVGF 参数候选中文预审表

说明：这是 Codex 预审草稿，尚未回写入 review pack。建议分布：23 accepted / 2 rejected / 0 borderline。

需要人工重点看：第 16-25 条原始 canonical_key 为空后缀；第 19、20 条 candidate_id 重复，但语义不是重复参数，回写时需要补唯一 canonical_key 和 KO ID。

| # | candidate_id | 原参数名 | 中文名 | 页码 | 证据摘录 | 建议 decision | 中文理由 |
|---:|---|---|---|---:|---|---|---|
| 1 | `cand_30bfed1339a3f37b` | Date | 当前日期 | 27 | Date | `rejected` | 这是界面时间/日期显示或时钟设置，不是离心式冷水机组的运行、保护或控制参数。 |
| 2 | `cand_68d3f836b4ca13c0` | Differential to Start | 启动温差 | 29 | Differential to Start | `accepted` | 控制冷水机组启动条件的温差设定，属于可配置运行控制参数。 |
| 3 | `cand_7e50207e43355c43` | Differential to Stop | 停机温差 | 29 | Differential to Stop | `accepted` | 控制冷水机组停机条件的温差设定，属于可配置运行控制参数。 |
| 4 | `cand_b30317bad703ec98` | External Base Loading Setpoint | 外部基本负荷设定 | 29 | External Base Loading Setpoint | `accepted` | 基本负荷控制相关设定，影响机组负荷控制方式，属于运行参数。 |
| 5 | `cand_341a810876df29d2` | External Chilled Water Setpoint | 外部冷冻水设定值 | 29 | External Chilled Water Setpoint | `accepted` | 外部来源的冷冻水设定值，属于核心控制设定参数。 |
| 6 | `cand_9e493f44221239ef` | External Current Limit Setpoint | 外部电流限制设定值 | 29 | External Current Limit Setpoint | `accepted` | 外部来源的电流限制设定值，用于需求限制/电流保护控制，属于运行参数。 |
| 7 | `cand_fe8d59f843c1d361` | Front Panel Base Load Setpoint | 前面板基本负荷设定值 | 29 | Front Panel Base Load Setpoint | `accepted` | 通过前面板配置的基本负荷设定，影响容量/负荷控制，属于运行参数。 |
| 8 | `cand_9fbf6c61f4f225c5` | Front Panel Chilled Water Setpoint | 前面板冷冻水设定值 | 29 | Front Panel Chilled Water Setpoint | `accepted` | 通过前面板配置的冷冻水设定值，是冷水机组核心控制参数。 |
| 9 | `cand_a6a27a8c7dea73f0` | Front Panel Current Limit Setpoint | 前面板电流限制设定值 | 29 | Front Panel Current Limit Setpoint | `accepted` | 通过前面板配置的电流限制设定，影响电流限制控制，属于运行参数。 |
| 10 | `cand_7244bdd357718b62` | Outdoor Maximum Reset | 室外最大重置 | 29 | Outdoor Maximum Reset | `accepted` | 冷冻水重置策略中的最大重置量，属于控制策略参数。 |
| 11 | `cand_23bcf5ca50ab38c2` | Outdoor Reset Ratio | 室外重置率 | 29 | Outdoor Reset Ratio | `accepted` | 冷冻水重置策略中的室外温度重置比例，属于控制策略参数。 |
| 12 | `cand_ba811bf939ec274d` | Return Maximum Reset | 回水最大重置 | 29 | Return Maximum Reset | `accepted` | 回水重置策略中的最大重置量，属于控制策略参数。 |
| 13 | `cand_1629db375cefe089` | Return Reset Ratio | 回水重置率 | 29 | Return Reset Ratio | `accepted` | 回水重置策略中的比例设定，属于控制策略参数。 |
| 14 | `cand_fd1f4e2c03568016` | Setpoint Source | 设定值来源 | 29 | Setpoint Source | `accepted` | 决定设定值来自前面板、BAS 或其他来源，属于控制配置参数。 |
| 15 | `cand_d86a27272a0dcce1` | Time Format | 时间格式 | 30 | Time Format | `rejected` | 这是显示/时钟格式设置，不是设备运行、保护或控制参数。 |
| 16 | `cand_5132b597706f4f1e` | 最大压差设定值 | 最大压差设定值 | 43 | 最大压差  标准设为30 psi | `accepted` | 有默认值和可调范围，压力差设定影响机组保护/控制逻辑，属于参数。 |
| 17 | `cand_16f611a491ce0b3a` | 最小压差设定值 | 最小压差设定值 | 43 | 最小压差  标准设定为 0 psi | `accepted` | 有默认值和可调范围，压力差设定影响机组保护/控制逻辑，属于参数。 |
| 18 | `cand_5f8db2b23acaa860` | 容量控制软载时间 | 容量控制软载时间 | 51 | 容量控制软载时间(0-120分钟，默认值为10分钟) | `accepted` | 有 0-120 分钟范围和默认值，控制软载过滤时间常数，属于可配置控制参数。 |
| 19 | `cand_20a759005f0e53c0` | 最大容量限制 | 最大容量限制 | 51 | 最小（默认为0％）和最大容量（默认为100%）的设置可以通过维修工具软件来修改 | `accepted` | 通过维修工具修改，限制机组最大容量并影响 BAS 联动，属于运行控制参数。 |
| 20 | `cand_20a759005f0e53c0` | 最小容量限制 | 最小容量限制 | 51 | 最小（默认为0％）和最大容量（默认为100%）的设置可以通过维修工具软件来修改 | `accepted` | 通过维修工具修改，限制压缩机卸载能力，属于运行控制参数。 |
| 21 | `cand_e2c2beaeb21208af` | 最小电流限制设定 | 最小电流限制设定 | 51 | 最小电流限制设定的默认设置为 40% RLA (可设为 20-100 %) | `accepted` | 有 20-100% RLA 范围和 40% RLA 默认值，属于电流限制保护/需求控制参数。 |
| 22 | `cand_6db23ecf26219bfb` | 滤波器时间 | 滤波器时间 | 51 | 滤波器时间默认为 10分钟 (可设为 0-120分钟 ) | `accepted` | 有 0-120 分钟范围和 10 分钟默认值，用于电流限制设定调整后的稳定控制，属于控制参数。 |
| 23 | `cand_f3ed7a56a454750b` | 电流限制控制软载时间 | 电流限制控制软载时间 | 51 | 电流限制控制软载时间(0-120分钟，默认值为10分钟) | `accepted` | 有 0-120 分钟范围和默认值，控制电流限制设定过滤时间常数，属于控制参数。 |
| 24 | `cand_d0ec82e3c9c84be0` | 电流限制软载起动百分数 | 电流限制软载起动百分数 | 51 | 电流限制软载起动百分数(20-100%，默认值为40%) | `accepted` | 有 20-100% 范围和 40% 默认值，决定电流限制软载起点，属于控制参数。 |
| 25 | `cand_8ed25c80f3e446e5` | 重启抑制时间设定 | 重启抑制时间设定 | 53 | 默认设定是 20分钟 | `accepted` | 默认 20 分钟且可由 TechView 修改，影响机组重启抑制逻辑，属于保护/运行参数。 |

## Codex 建议的最终数字

- accepted: 23
- rejected: 2
- borderline/pending: 0

## 拒绝项

- #1 Date：日期/时钟显示，不是设备运行参数。
- #15 Time Format：时间显示格式，不是设备运行参数。

## 回写 pack 前需要修正

- 给 #16-25 补完整 canonical_key。
- 给 #19 和 #20 补不同的 knowledge_object_id / knowledge_evidence_id，避免重复 candidate_id 导致 KO ID 冲突。
- 给所有 accepted 项补 curation.title 和 curation.summary。
