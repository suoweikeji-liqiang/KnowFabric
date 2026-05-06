# ASHRAE Guideline 36 中文人工评审草稿

- 来源 run: `20260506T101446Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36`
- 标准: ASHRAE Guideline 36-2021
- 覆盖章节: 5.1.14, 5.20, 5.21
- 已验证候选数: 22
- 类型分布: `application_guidance: 1`, `operational_sequence: 15`, `commissioning_procedure: 1`, `fault_diagnostic_rule: 4`, `parameter_spec: 1`
- 人工审核结果: accepted 21 / rejected 1
- 审核口径: 内容真实性、KO 类型正确性、证据是否足以支撑入库分开判断；证据弱但内容正确的条目标为 accepted，并在备注中要求重锚。

## 评审方式

请逐条把 `评审决定` 标为 `accepted` 或 `rejected`。建议按四个维度判断：是否有运维价值、KO 类型是否正确、章节引用是否准确、是否适合作为 `sw_base_model` 可消费的权威知识。

## 1. [application_guidance] VAV 静压控制的 T&R 逻辑应用

- 评审决定: accepted
- 评审备注: 接受。内容属于 T&R 示例应用知识；证据已从跳转句重锚到 §5.1.14.4 示例变量表和操作描述所在 chunk。
- 引用: ASHRAE Guideline 36-2021 §5.1.14.4
- 页码: [48]
- 信任等级: L3
- 摘要: 示例序列为 Td=5 min, T=2 min, I=2, SPtrim=-10 Pa, SPres=15 Pa, SPres-max=37 Pa。当请求数 R≤2 时设定值下调；当 R>2 时设定值上调，单步上调量上限为 37 Pa。
- 触发条件: 风机状态为 ON，且经过 5 min 延时。
- 必要行为: 每 2 min 判断一次：若 R≤2，设定值降低 10 Pa；若 R>2，设定值增加 `(R-2)*15 Pa`，但最大增加 37 Pa。
- 可配置值: SP0 = 120 Pa; SPmin = 37 Pa; SPmax = 370 Pa; Td = 5 min; T = 2 min; I = 2; SPtrim = -10 Pa; SPres = 15 Pa; SPres-max = 37 Pa
- 证据原文: `If R≤I, c hange Setpoint by SPtrim If R > I, change setpoint by (R – I)*SPres but no large r than SPres -max The following is an example of a sequence that uses T&R to control the static pressure setpoint of a VAV AHU serving multiple downstream zones. This sequence defines the T&R variables as shown in Informative Table 5.1.14.4. Informative Tab le 5.1.14.4 Example Sequence T&R Variables Variable Definition Device Supply fan SP0 120 Pa (0.5 in. of water) SPmin 37 Pa (0.15 in. of water) SPmax 370 Pa (1.50 in. of water) Td 5 T 2 I 2 SPtrim –10 Pa (–0.04 in. of water) SPres 15 Pa (0.06 in. of water) SPres -max 37 Pa (0.15 in. of water) Description of General Operation Starting 5 minutes after the fan status indicates the supply fan is ON, the sequence will slowly reduce the AHUs static pressure setpoint by 10 Pa (0.04 in. of water) every 2 minutes if R≤I .`
- 判官理由: 直接捕捉了 Guideline 36 第 5.1.14.4 节中的控制序列示例及其可配置参数。

## 2. [operational_sequence] Trim & Respond 设定值重置逻辑

- 评审决定: accepted
- 评审备注: 接受。内容属于通用 T&R 运行序列；证据已从章节标题重锚到 §5.1.14.4 的 reset logic 正文。
- 引用: ASHRAE Guideline 36-2021 §5.1.14
- 页码: [47]
- 信任等级: L3
- 摘要: T&R 逻辑按固定速率重置设定值，直到下游区域不再满足并产生请求；当请求足够多时提高设定值，请求消退后继续降低设定值。
- 触发条件: 关联设备被证明处于 ON；初始设备启动命令后开始 Td 延时。
- 必要行为: 每个时间步 T：若 R≤I，则按 SPtrim 修剪设定值；若 R>I，则按 `(R-I)*SPres` 响应调整，但不超过 SPres-max。
- 可配置值: SP0 初始设定值; SPmin 最小设定值; SPmax 最大设定值; Td 延时; T 时间步; I 忽略请求数; SPtrim 修剪量; SPres 响应量，符号与 SPtrim 相反; SPres-max 每个时间间隔最大响应量
- 证据原文: `5.1.14.4. Trim & Respond logic shall reset the setpoint within the range SPmin to SPmax. When the associated device is OFF, the setpoint shall be SP0. The reset logic shall be active while the associated device is proven ON, starting Td after initial device start command. When active, every time step T, if R≤I, trim the setpoint by SPtrim. If there are more than I requests , respond by chan ging the setpoint by SPres *(R – I), (i.e., the number of requests minus the number of ignored requests) but no more than SPres -max.`
- 判官理由: 该项描述了 Guideline 36 第 5.1.14 节中的真实运行控制序列。

## 3. [commissioning_procedure] Request-Hours 累加器复位

- 评审决定: rejected
- 评审备注: 拒绝。内容来自标准且有证据，但 KO 类型不应是 commissioning_procedure；它描述的是运行计数器/请求小时复位逻辑，更适合 operational_sequence 或维护/运行规则，不能按调试规程入库。
- 引用: ASHRAE Guideline 36-2021 §5.1.14.2
- 页码: [47]
- 信任等级: L3
- 摘要: 当 System Run-Hours Total 超过 400 h 时，Request-Hours Accumulator 和 System Run-Hours Total 自动复位为零；也可由全局操作员命令手动复位。
- 触发条件: System Run-Hours Total 超过 400 h，或收到手动复位命令。
- 必要行为: 将 Request-Hours Accumulator 和 System Run-Hours Total 复位为零。
- 可配置值: 自动复位阈值 400 h
- 证据原文: `The Request-Hours Accumulator and System Run-Hours Total are reset to zero as follows: i. Reset automatically for an individual zone/system when the System Run-Hours Total exceeds 400 hours. ii. Reset manually by a global operator command.`
- 判官理由: 捕捉了请求小时累加器的自动/手动复位规程，属于可执行的调试和运维知识。

## 4. [fault_diagnostic_rule] 基于累计请求小时百分比的 Rogue Zone 检测

- 评审决定: accepted
- 评审备注: 接受。该条是明确的 Level 4 告警条件，阈值、运行小时条件和告警行为都由证据直接支撑，KO 类型 fault_diagnostic_rule 正确。
- 引用: ASHRAE Guideline 36-2021 §5.1.14.2
- 页码: [47]
- 信任等级: L3
- 摘要: 当 zone Importance-Multiplier > 0、Cumulative% Request-Hours > 70%、且总运行小时数 > 40 h 时，生成 Level 4 告警。
- 触发条件: Importance-Multiplier > 0，Cumulative% Request-Hours > 70%，总运行小时数 > 40 h。
- 必要行为: 生成 Level 4 告警。
- 可配置值: Importance-Multiplier 默认 1; Cumulative% Request-Hours 阈值 70%; 运行小时阈值 40 h
- 故障条件: 某个 Rogue Zone 正在驱动重置逻辑
- 证据原文: `A Level 4 alarm is generated if the zone Importance-Multiplier is greater than zero, the zone/system Cumulative% Request Hours exceeds 70%, and the total number of zone/system run hours exceeds 40.`
- 判官理由: 该项有明确触发条件和告警行为，是来自标准的真实故障诊断规则。

## 5. [parameter_spec] T&R 变量及默认/调试要求

- 评审决定: accepted
- 评审备注: 接受。T&R 变量、范围角色和调试要求属于可配置参数规格；建议后续标题从 “Defaults” 改为 “Variables and Tuning Parameters”，因为证据主要是变量定义和调试要求。
- 引用: ASHRAE Guideline 36-2021 §5.1.14.3
- 页码: [47]
- 信任等级: L3
- 摘要: 定义 Device、SP0、SPmin、SPmax、Td、T、I、SPtrim、SPres、SPres-max 等变量。初始值由系统/机房序列定义，trim、respond、time step 等应被调试到稳定控制。
- 可配置值: Device; SP0; SPmin; SPmax; Td; T; I; SPtrim; SPres; SPres-max
- 证据原文: `For each upstream system or plant setpoint being controlled by a T&R loop, define the following variables. Initial values are defined in system/plant sequences below. Values for trim, respond, time step, etc. shall be tuned to provide stable control. See Table 5.1.14.3.`
- 判官理由: 捕捉了 T&R 回路的可配置控制参数及调试要求，适合作为参数规格知识。

## 6. [operational_sequence] 冷水机房启用逻辑

- 评审决定: accepted
- 评审备注: 接受。冷水机房启用逻辑准确，条件包括停用时间、请求数、OAT lockout 和 schedule；证据已重锚到跨相邻 chunk 的完整启用条件。
- 引用: ASHRAE Guideline 36-2021 §5.20.2.2
- 页码: [172]
- 信任等级: L3
- 摘要: 当机房已停用至少 15 min、Chiller Plant Requests 数量大于 I 默认 0、OAT > CH-LOT、且日程有效时，以最低 stage 启用机房。
- 触发条件: 机房停用 ≥15 min，Chiller Plant Requests > I，OAT > CH-LOT，且启用日程有效。
- 必要行为: 以最低 stage 启用冷水机房。
- 可配置值: I 默认 0; CH-LOT
- 证据原文: `5.20.2.2. Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and: a. Number of Chiller Plant Requests > I (I = Ignores shall default to 0, adjustable), and b. OAT>CH -LOT, and c. The chiller plant enable schedule is active.`
- 判官理由: 第 5.20.2.2 节中的真实机房启用控制序列，包含可配置阈值。

## 7. [operational_sequence] 冷水机房停用逻辑

- 评审决定: accepted
- 评审备注: 接受。冷水机房停用逻辑准确，三类停用条件和 3 min 条件均由证据直接支撑。
- 引用: ASHRAE Guideline 36-2021 §5.20.2.3
- 页码: [172]
- 信任等级: L3
- 摘要: 当机房已启用至少 15 min，且请求数 ≤ I 持续 3 min、或 OAT < CH-LOT - 1°F、或日程无效时，停用机房。
- 触发条件: 机房启用 ≥15 min，且满足上述任一停用条件。
- 必要行为: 停用冷水机房。
- 可配置值: I 默认 0; CH-LOT
- 证据原文: `Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Chiller Plant Requests ≤ I for 3 minutes, or b. OAT<CH-LOT – 1°F, or c. The chiller plant enable schedule is inactive.`
- 判官理由: 捕捉了第 5.20.2.3 节中的真实停用控制逻辑。

## 8. [operational_sequence] 水侧节能器启用逻辑

- 评审决定: accepted
- 评审备注: 接受。水侧节能器启用逻辑准确，20 min 条件、PHXLWT 关系和温差阈值均清楚，KO 类型正确。
- 引用: ASHRAE Guideline 36-2021 §5.20.3.1
- 页码: [175]
- 信任等级: L3
- 摘要: 若 WSE 已停用至少 20 min，且换热器上游 CHWRT > PHXLWT + 2°F，则启用水侧节能器。PHXLWT 由湿球温度、设计 approach 和部分负荷比计算得到。
- 触发条件: WSE 停用 ≥20 min，且 CHWRT upstream of HX > PHXLWT + 2°F。
- 必要行为: 启用水侧节能器。
- 可配置值: DA HX; DA CT; DT WB; m 可调参数
- 证据原文: `Enable waterside economizer (WSE) if it has been disabled for at least 20 minutes and CHWRT upstream of HX is greater than the predicted heat exchanger leaving water temperature (PHXLWT) plus 2°F.`
- 判官理由: 来自 Guideline 36 的真实 WSE 启用序列，包含时间和温差条件。

## 9. [operational_sequence] 水侧节能器停用逻辑

- 评审决定: accepted
- 评审备注: 接受。水侧节能器停用逻辑准确，运行时间、温差和持续 2 min 条件均由证据支撑。
- 引用: ASHRAE Guideline 36-2021 §5.20.3.2
- 页码: [176]
- 信任等级: L3
- 摘要: WSE 运行至少 20 min 后，若换热器下游冷冻水温度 > 上游 CHWRT - 1°F 持续 2 min，则停用 WSE。
- 触发条件: WSE 启用 ≥20 min，且下游 CHW 温度 > 上游 CHWRT - 1°F 持续 2 min。
- 必要行为: 停用水侧节能器。
- 证据原文: `Disable WSE when it has run for at least 20 minutes and CHW temp downstream of HX is greater than CHWRT upstream of HX less 1ºF for 2 minutes`
- 判官理由: 捕捉了水侧节能器基于运行时间和温度条件的停用序列。

## 10. [operational_sequence] 冷机 staging 降级条件

- 评审决定: accepted
- 评审备注: 接受。冷机 stage down 条件准确，包含 OPLR 阈值、15 min 持续时间、2.5%/min 斜率约束和 failsafe 排除条件。
- 引用: ASHRAE Guideline 36-2021 §5.20.4.15
- 页码: [182, 183, 184]
- 信任等级: L4
- 摘要: 若下一较低 stage 的 OPLR < SPLR_DN 持续 15 min，且该 OPLR 在 5 min 平均下没有以超过 2.5%/min 的速率上升，并且 failsafe stage up 条件不成立，则降级。
- 触发条件: 下一可用较低 stage OPLR < SPLR_DN 持续 15 min；且 OPLR 上升速率不超过 2.5%/min；且 failsafe stage up 不成立。
- 必要行为: 发起 stage down。
- 可配置值: SPLR_DN，按冷机类型和 lift 计算
- 证据原文: `Stage down if both of the following are true: 1. Next available lower stage OPLR < SPLR DN for 15 minutes and next lower stage OPLR is not increasing at a rate greater than 2.5% per minute averaged over 5 minutes; and 2. The failsafe stage up condition is not true.`
- 判官理由: 真实冷机 staging 控制规则，有明确阈值、时间和 failsafe 条件。

## 11. [operational_sequence] 冷机 staging 升级效率条件

- 评审决定: accepted
- 评审备注: 接受。该条是 stage up 的 efficiency condition，不是完整 stage-up 全部逻辑；标题已体现这一点，可作为 operational_sequence 入库。
- 引用: ASHRAE Guideline 36-2021 §5.20.4.15
- 页码: [182, 183, 184, 185]
- 信任等级: L4
- 摘要: 若当前 stage 的 OPLR > SPLR_UP 持续 15 min，且 OPLR 在 5 min 平均下没有以超过 2.5%/min 的速率下降，则升级。
- 触发条件: 当前 stage OPLR > SPLR_UP 持续 15 min，且 OPLR 下降速率不超过 2.5%/min。
- 必要行为: 发起 stage up。
- 可配置值: SPLR_UP，按冷机类型和 lift 计算
- 证据原文: `Efficiency Condition : Current stage OPLR > SPLR UP for 15 minutes and current stage OPLR is not decreasing at a rate greater than 2.5% per minute averaged over 5 minutes`
- 判官理由: 捕捉了标准中的具体冷机 staging 控制规则。

## 12. [operational_sequence] 压差控制回路下的冷冻水供水温度重置

- 评审决定: accepted
- 评审备注: 接受。内容正确并有运维价值；证据已从 §5.20.5.2 标题重锚到下一页正文和 T&R 参数表。
- 引用: ASHRAE Guideline 36-2021 §5.20.5.2
- 页码: [200]
- 信任等级: L3
- 摘要: 先按 loop output 0-50% 将 DP 设定值从 CHW-DPmin 重置到 CHW-DPmax，再按 loop output 50-100% 将 CHWST 设定值从 CHWSTmax 重置到 CHWSTmin，并使用 T&R 参数。
- 触发条件: 冷水机房启用。
- 必要行为: 使用给定 T&R 逻辑重置 CHW Plant Reset 变量。
- 可配置值: CHW-DPmin; CHW-DPmax; CHWSTmin; CHWSTmax; Td=15 min; T=5 min; I=2; SPtrim=-2%; SPres=+3%; SPres-max=+7%
- 证据原文: `From 0% loop output to 50% loop output, reset DP setpoint from CHW -DPmin to CHWP - DPmax. b. From 50% loop output to 100% loop output, reset CHWST setpoint from CHWSTmax to CHWSTmin. c. CHW Plant Reset variable shall be reset using Trim & Respond logic with the following parameters: Variable Value Device Any CHW Pump Distribution Loop SP0 100% SPmin 0% SPmax 100% Td 15 minutes T 5 minutes I 2 R Cooling CHWST Reset Requests SPtrim -2% SPres +3% SPres-max +7%`
- 判官理由: 捕捉了压差控制冷冻水供水温度重置的真实运行序列。

## 13. [operational_sequence] 一次冷冻水泵转速控制（变一次-变二次，带解耦流量计）

- 评审决定: accepted
- 评审备注: 接受。一次冷冻水泵转速控制逻辑清楚，PID 目标 5% PCHWFdesign 和可配置值均合理，KO 类型正确。
- 引用: ASHRAE Guideline 36-2021 §5.20.6.17
- 页码: [204]
- 信任等级: L3
- 摘要: 通过反作用 PID 回路维持解耦器流量为 PCHWFdesign 的 5%，并将 loop output 映射到 CH-MinPriPumpSpdStage 至 100% 转速。
- 触发条件: 冷水机房启用，且一次泵已证明运行。
- 必要行为: 通过 PID 回路维持解耦器流量为 PCHWFdesign 的 5%。
- 可配置值: CH-MinPriPumpSpdStage; PCHWFdesign
- 证据原文: `Primary pump speed shall be reset by a reverse acting PID loop maintaining flow through the decoupler flow meter at 5% of PCHWFdesign`
- 判官理由: 直接来自第 5.20.6.17 节的一次泵转速重置控制序列。

## 14. [fault_diagnostic_rule] AFDD - 冷冻水供水温度过高

- 评审决定: accepted
- 评审备注: 接受。AFDD FC#6 条件、适用 OS 和故障描述明确，属于 fault_diagnostic_rule。
- 引用: ASHRAE Guideline 36-2021 §5.20.18.6
- 页码: [230]
- 信任等级: L3
- 摘要: 故障条件 FC#6：`CHWST_AVG - ƐCHWT ≥ CHWSTSP`，适用于 OS #2-#5。
- 触发条件: CHWST_AVG - ƐCHWT ≥ CHWSTSP
- 必要行为: 上报告警，并给出可能诊断：冷机机械问题或一次流量过高。
- 可配置值: ƐCHWT 默认 2°F
- 故障条件: 冷冻水供水温度过高
- 证据原文: `FC#6 Equation CHWST AVG - ƐCHWT ≥ CHWSTSP Applies to OS #2 – #5 Description Chilled water supply temperature is too high`
- 判官理由: 有明确公式和适用运行状态，是有效的故障诊断规则。

## 15. [fault_diagnostic_rule] AFDD - 冷凝器 approach 过高

- 评审决定: accepted
- 评审备注: 接受。AFDD FC#8 条件、适用 OS 和诊断方向明确，属于 fault_diagnostic_rule。
- 引用: ASHRAE Guideline 36-2021 §5.20.18.6
- 页码: [230]
- 信任等级: L3
- 摘要: 故障条件 FC#8：`Approach_COND ≥ RefrigCondTemp_CH-x,AVG - CWRT_CH-x,AVG`，适用于 OS #2、#3、#5。
- 触发条件: Approach_COND ≥ RefrigCondTemp_CH-x,AVG - CWRT_CH-x,AVG
- 必要行为: 上报告警，并给出可能诊断：冷凝器结垢、冷却水温度过低或流量过低。
- 可配置值: Approach_COND 默认 4°F
- 故障条件: 冷凝器 approach 过高
- 证据原文: `FC#8 Equation Approach COND ≥ RefrigCondTemp CH-x, AVG - CWRT CH-x, AVG Applies to OS #2, #3, #5 Description Condenser approach is too high`
- 判官理由: 标准中的具体故障诊断规则，有公式和适用范围。

## 16. [fault_diagnostic_rule] AFDD - 蒸发器 approach 过高

- 评审决定: accepted
- 评审备注: 接受。AFDD FC#9 条件、适用 OS 和诊断方向明确，属于 fault_diagnostic_rule。
- 引用: ASHRAE Guideline 36-2021 §5.20.18.6
- 页码: [230]
- 信任等级: L3
- 摘要: 故障条件 FC#9：`Approach_EVAP ≥ CHWST_CH-x,AVG - RefrigEvapTemp_CH-x,AVG`，适用于 OS #2、#3、#5。
- 触发条件: Approach_EVAP ≥ CHWST_CH-x,AVG - RefrigEvapTemp_CH-x,AVG
- 必要行为: 上报告警，并给出可能诊断：蒸发器结垢、制冷剂充注量低或制冷剂被污染。
- 可配置值: Approach_EVAP 默认 3°F
- 故障条件: 蒸发器 approach 过高
- 证据原文: `FC#9 Equation Approach EVAP ≥ CHWST CH-x, AVG - RefrigEvapTemp CH-x, AVG Applies to OS #2, #3, #5 Description Evaporator approach is too high`
- 判官理由: 捕捉了具体故障诊断公式和适用范围，来源于标准。

## 17. [operational_sequence] 热水机房启用逻辑

- 评审决定: accepted
- 评审备注: 接受。热水机房启用逻辑准确；标题已收窄为 Hot Water Plant Enable Logic，证据已重锚到跨相邻 chunk 的完整启用条件。
- 引用: ASHRAE Guideline 36-2021 §5.21.2.2
- 页码: [235]
- 信任等级: L3
- 摘要: 当机房停用至少 15 min、Heating Hot-Water Plant Requests 数量大于 I 默认 0、OAT < HW-LOT、且锅炉机房启用日程有效时，以最低 stage 启用机房。
- 触发条件: 机房停用 ≥15 min；Heating Hot-Water Plant Requests > I；OAT < HW-LOT；Boiler plant enable schedule active。
- 必要行为: 以最低 stage 启用热水机房。
- 可配置值: I 忽略请求数，默认 0; HW-LOT 锁定温度
- 证据原文: `5.21.2.2. Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and: a. Number of Heating Hot -Water Plant Requests > I (I = Ignores shall default to 0, ad justable), and b. OAT<HW -LOT, and c. The Boiler plant enable schedule is active.`
- 判官理由: 带可配置参数的热水机房启用运行序列，来源于第 5.21.2.2 节。

## 18. [operational_sequence] 热水机房停用逻辑

- 评审决定: accepted
- 评审备注: 接受。热水机房停用逻辑准确，条件包括请求数、OAT lockout 和 schedule inactive，KO 类型正确。
- 引用: ASHRAE Guideline 36-2021 §5.21.2.3
- 页码: [235]
- 信任等级: L3
- 摘要: 当机房启用至少 15 min，且 Heating Hot-Water Plant Requests ≤ I 持续 3 min、或 OAT > HW-LOT + 1°F、或锅炉机房启用日程无效时，停用机房。
- 触发条件: 机房启用 ≥15 min，且满足上述任一停用条件。
- 必要行为: 停用热水机房。
- 可配置值: I 忽略请求数; HW-LOT
- 证据原文: `Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Heating Hot-Water Plant Requests ≤ I for 3 minutes, or b. OAT>HW-LOT + 1°F, or c. The Boiler plant enable schedule is inactive.`
- 判官理由: 捕捉了第 5.21.2.3 节的具体停用控制逻辑。

## 19. [operational_sequence] 一次系统冷凝锅炉 staging 降级

- 评审决定: accepted
- 评审备注: 接受。一次系统冷凝锅炉 stage down 条件完整，包含 B-STAGE MIN、旁通阀、failsafe 和下一 stage 容量条件。
- 引用: ASHRAE Guideline 36-2021 §5.21.3.9.g
- 页码: [238]
- 信任等级: L3
- 摘要: 若 Qrequired 低于当前 stage 的 B-STAGE MIN 的 110% 持续 5 min，或旁通阀开度 >0% 持续 5 min；同时 failsafe stage up 不成立；且 Qrequired 低于下一较低 stage 锅炉设计容量的 80% 持续 5 min，则降级。
- 触发条件: 三项同时满足：负荷/旁通条件、failsafe stage up 不成立、下一较低 stage 容量条件。
- 必要行为: 降级到下一可用较低 stage。
- 可配置值: B-STAGE MIN; QbX 设计容量
- 证据原文: `Stage down if all of the following are true: 1. Either: i. Qrequired falls below 110% of B-STAGE MIN of the current stage for 5 minutes; or ii. The minimum flow bypass valve, if provided, is greater than 0% open for 5 minutes. 2. The fail safe stage up condition is not true. 3. Qrequired is less than 80% of the design capacity, QbX, of the boilers in the next available lower stage for 5 minutes.`
- 判官理由: 第 5.21.3.9.g 节中的真实 staging 降级序列，包含参数和计时条件。

## 20. [operational_sequence] 变一次/变二次冷凝锅炉 staging 降级

- 评审决定: accepted
- 评审备注: 接受。变一次/变二次冷凝锅炉 stage down 条件完整，L4 合理；泵速、HWRT 温差、failsafe 和容量条件均明确。
- 引用: ASHRAE Guideline 36-2021 §5.21.3.9.i
- 页码: [239, 240]
- 信任等级: L4
- 摘要: 若 Qrequired 低于当前 stage 的 B-STAGE MIN 的 110% 持续 5 min，或一次热水泵处于 B-MinPriPumpSpdStage 且一次 HWRT 比二次 HWRT 高 3°F 持续 5 min；同时 failsafe stage up 不成立；且 Qrequired 低于下一较低 stage 设计容量的 80% 持续 5 min，则降级。
- 触发条件: 三项同时满足：负荷/泵速温差条件、failsafe stage up 不成立、下一较低 stage 容量条件。
- 必要行为: 降级到下一可用较低 stage。
- 可配置值: B-STAGE MIN; B-MinPriPumpSpdStage; QbX
- 证据原文: `Stage down if all of the following are true: 1. Either: i. Qrequired falls below 110% of B-STAGE MIN of the current stage for 5 minutes; or ii. For 5 minutes, Primary HW pumps are at B-MinPriPumpSpdStage and primary HWRT exceeds secondary HWRT by 3°F. 2. The failsafe stage up condition is not true. 3. Qrequired is less than 80% of the design capacity, QbX, of the boilers in the next available lower stage for 5 minutes.`
- 判官理由: 捕捉了标准中的真实 staging 降级控制序列，条件和计时明确。

## 21. [operational_sequence] 非冷凝锅炉 staging 降级

- 评审决定: accepted
- 评审备注: 接受。非冷凝锅炉 stage down 条件明确，10 min 持续时间和 80% 设计容量条件由证据支撑。
- 引用: ASHRAE Guideline 36-2021 §5.21.3.9.k
- 页码: [240]
- 信任等级: L3
- 摘要: 若 Qrequired 低于下一可用较低 stage 设计容量的 80% 持续 10 min，且 failsafe stage up 不成立，则降级。
- 触发条件: Qrequired < 下一较低 stage 设计容量的 80% 持续 10 min，且 failsafe stage up 不成立。
- 必要行为: 降级到下一可用较低 stage。
- 可配置值: QbX
- 证据原文: `Stage down if both of the following are true: 1. Qrequired is less than 80% of the design capacity of the next lower available stage for 10 minutes; and 2. The failsafe stage up condition is not true.`
- 判官理由: 第 5.21.3.9.k 节中的真实 staging 降级序列。

## 22. [operational_sequence] 混合锅炉 staging 降级（当前 stage 全为冷凝锅炉）

- 评审决定: accepted
- 评审备注: 接受。混合锅炉在当前 stage 全为冷凝锅炉时的 stage down 条件清楚，引用 §5.21.3.9.i 的逻辑关系合理。
- 引用: ASHRAE Guideline 36-2021 §5.21.3.9.m
- 页码: [240]
- 信任等级: L3
- 摘要: 若当前 stage 中所有已启用锅炉均为冷凝锅炉，则按变一次/变二次冷凝锅炉相同条件降级：Qrequired 低于 B-STAGE MIN 的 110% 持续 5 min，或一次泵在最低转速且一次 HWRT 比二次 HWRT 高 3°F 持续 5 min；failsafe stage up 不成立；且下一较低 stage 容量条件满足。
- 触发条件: 同 §5.21.3.9.i。
- 必要行为: 降级到下一可用较低 stage。
- 可配置值: B-STAGE MIN; B-MinPriPumpSpdStage; QbX
- 证据原文: `If all boilers enabled in the current stage are condensing, stage down if all of the following are true: 1. Either: i. Qrequired falls below 110% of B-STAGE MIN of the current stage for 5 minutes; or ii. For 5 minutes, Primary HW pumps are at B-MinPriPumpSpdStage and primary HWRT exceeds secondary HWRT by 3°F. 2. The failsafe stage up condition is not true. 3. Qrequired is less than 80% of the design capacity, QbX, of the boilers in the next available lower stage for 5 minutes.`
- 判官理由: 捕捉了第 5.21.3.9.m 节中的真实控制序列，包含可配置参数和计时条件。
