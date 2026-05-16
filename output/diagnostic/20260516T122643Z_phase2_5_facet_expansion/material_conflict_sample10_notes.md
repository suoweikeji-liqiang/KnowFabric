# Phase 2.5 material_conflict sample10 notes

## 1. ko_0d07e38beb2cde12 centrifugal_chiller/performance_spec
- title: 制冷量
- key: `hvac:centrifugal_chiller:performance_spec:制冷量`
- layers: 6
- codex_initial_note: likely_true_conflict: Same nominal cooling capacity concept; values differ by model/range.

- McQuay: 制冷量 | value=1385.5kW | unit=kW | summary=制冷量 kW 1385.5
- McQuay: 制冷量 | value=1028.2kW | unit=kW | summary=制冷量 kW 1028.2
- McQuay: 制冷量 | value=1196.2kW | unit=kW | summary=制冷量 kW 1196.2
- McQuay: 每台制冷量 | value=800冷吨 | unit=冷吨 | summary=每台制冷量 冷吨 800
- 特灵: 制冷量 | value=制冷量 | unit=None | summary=CVHE/G冷水机组常规工况制冷量范围400~1400冷吨。
- 特灵: 制冷量 | value=制冷量 | unit=None | summary=CDHG机组冷量范围2250~2600冷吨。

Human verdict: 

## 2. ko_17f0b96529e22232 ahu/maintenance_procedure
- title: 防冻措施
- key: `hvac:ahu:maintenance:防冻措施`
- layers: 5
- codex_initial_note: true_merge: Same AHU winter coil freeze-protection maintenance procedure.

- 特灵: 防冻措施 | value=防冻措施 | unit=None | summary=机组不使用的季节，必须及时将盘管内余水排尽，以防止冬季换热器铜管冻裂。
- 美的: 冬季防冻措施 | value=冬季防冻措施 | unit=None | summary=若需停机，必须保持盘管内供水连续流动并注入防冻液，且关闭新风阀。若长时间停运，应将盘管内的水放空。
- 格力: 冬季防冻操作 | value=冬季防冻操作 | unit=None | summary=冬季不运行时应放空表冷器内水并用压缩空气吹出存水，防止冻坏。
- unknown: 冬季表冷器防冻 | value=冬季表冷器防冻 | unit=None | summary=冬季表冷器须排尽管内水，所有残留水都应吹去
- 美的: Winter Coil Protection | value=Winter Coil Protection | unit=None | summary=If unit not in operation during winter, release all water from system to prevent coil cracking.

Human verdict: 

## 3. ko_40e8b515811dcc91 screw_chiller/parameter_spec
- title: 冷媒名称
- key: `hvac:screw_chiller:parameter:冷媒名称`
- layers: 5
- codex_initial_note: true_merge: Same refrigerant-name parameter; all layers identify R134a.

- 麦克维尔: 冷媒名称 | value=冷媒名称 | unit=None | summary=冷媒为R134a。
- 麦克维尔: 冷媒名称 | value=冷媒名称 | unit=None | summary=冷媒为R134a
- 约克: 制冷剂 | value=制冷剂 | unit=None | summary=机组使用制冷剂R-134a。
- 麦克维尔: 制冷剂 | value=制冷剂 | unit=None | summary=机组使用环保制冷剂R134a
- 麦克维尔: 制冷剂 | value=制冷剂 | unit=None | summary=机组使用R134a制冷剂。

Human verdict: 

## 4. ko_43f6959cb535869f centrifugal_chiller/performance_spec
- title: COP
- key: `hvac:centrifugal_chiller:performance_spec:cop`
- layers: 4
- codex_initial_note: likely_true_conflict: Same COP metric; values differ by model/rating point.

- McQuay: COP | value=5.89 | unit=None | summary=COP 5.89
- McQuay: COP | value=5.96 | unit=None | summary=COP 5.96
- McQuay: COP | value=5.32 | unit=None | summary=COP 5.32
- 特灵: COP | value=COP | unit=None | summary=CDHG机组在AHRI工况下COP可达7.0。

Human verdict: 

## 5. ko_0a2c2eebadb6cf7a screw_chiller/parameter_spec
- title: 主电源电压波动
- key: `hvac:screw_chiller:parameter:主电源电压波动`
- layers: 4
- codex_initial_note: true_merge: Same power-supply voltage fluctuation/range concept.

- 格力: 主电源电压波动 | value=主电源电压波动 | unit=None | summary=主电源的电压波动应在铭牌标称值的±10%范围之内，且电压不平衡在±2%以内。
- 约克: 电源电压 | value=电源电压 | unit=None | summary=机组电源电压允许波动为额定电压的±10%。
- 麦克维尔: 电源电压范围 | value=电源电压范围 | unit=None | summary=电源电压最大440V，最小342V
- 麦克维尔: 电源 | value=3相380V、50Hz | unit=None | summary=电源为3相380V、50Hz；电压波动±10%，频率波动±5%，电压不平衡度5%以内。

Human verdict: 

## 6. ko_9cc9ac81388f1519 ahu/parameter_spec
- title: 热水进水温度及温差
- key: `hvac:ahu:parameter:热水进水温度及温差`
- layers: 3
- codex_initial_note: likely_true_conflict: Hot-water inlet/design temperature are close but may need operator review.

- 麦克维尔: 热水进水温度及温差 | value=热水进水温度及温差 | unit=None | summary=热水进水温度60℃，温差10℃。
- 格力: 热水供热进水温度 | value=热水供热进水温度 | unit=None | summary=热水供热进水温度默认90℃。
- 格力: 热水加热器设计温度 | value=热水加热器设计温度 | unit=None | summary=热水加热器未注明按90℃设计；冷热盘管共用按60℃设计。

Human verdict: 

## 7. ko_02deaee3cba9f419 centrifugal_chiller/parameter_spec
- title: 冷却水进水温度
- key: `hvac:centrifugal_chiller:parameter:冷却水进水温度`
- layers: 3
- codex_initial_note: needs_human_review: Cooling-water entering temperature contains one suspicious -40..118C Carrier layer.

- Carrier: 冷却水进水温度 | value=[-40, 118] | unit=℃ | summary=冷却水进水温度 -40-118 ℃
- 格力: 冷却水进水温度 | value=冷却水进水温度 | unit=None | summary=冷却水进水温度应在20℃～34℃之间。
- 格力: 冷却水进水温度范围 | value=冷却水进水温度范围 | unit=None | summary=冷却水进水温度在20～34℃

Human verdict: 

## 8. ko_3da062e3080afdd8 centrifugal_chiller/parameter_spec
- title: 润滑油温度控制设定范围
- key: `hvac:centrifugal_chiller:parameter:润滑油温度控制设定范围`
- layers: 3
- codex_initial_note: needs_human_review: Not classified automatically; operator should review evidence rows.

- Trane: 润滑油温度控制设定范围 | value=[100 F, 160 F] | unit=None | summary=润滑油温度控制设定范围是从 100 到 160 F
- Carrier: 油箱温度范围 | value=52~66℃ | unit=℃ | summary=在压缩机运行期间，油箱温度范围为52~66℃。
- Carrier: 油箱温度范围 | value=52~66℃ | unit=℃ | summary=在压缩机运行期间，油箱温度范围为52～66℃。

Human verdict: 

## 9. ko_724b3ec6d034c43e centrifugal_chiller/fault_code
- title: 启动过频报警
- key: `hvac:centrifugal_chiller:fault_code:启动过频报警`
- layers: 3
- codex_initial_note: true_merge: Same frequent-start/start-cycle-limit fault with matching 8 starts / 12 h rule.

- Carrier: 启动过频报警 | value=8次次/12小时 | unit=次/12小时 | summary=如果12小时内启动次数超过8次，会发出启动过频报警
- 格力: 频繁启停保护 | value=频繁启停保护 | unit=None | summary=12小时内开机次数超过8次时报警禁止启动
- 格力: 频繁启停禁止开机 | value=频繁启停禁止开机 | unit=None | summary=12小时内开机次数超过8次时报警，禁止启动。

Human verdict: 

## 10. ko_54faa91286e39dd5 screw_chiller/parameter_spec
- title: 制冷温度设置
- key: `hvac:screw_chiller:parameter:制冷温度设置`
- layers: 3
- codex_initial_note: true_merge: Same chilled-water leaving temperature setpoint range concept.

- 天加: 制冷温度设置 | value=制冷温度设置 | unit=None | summary=冷冻水出水温度设定值，允许设置范围为6~12℃，出厂默认7℃。
- 格力: 冷冻水出水温度设定 | value=冷冻水出水温度设定 | unit=None | summary=制冷或低温模式下可设定冷冻水出水温度
- 约克: 冷冻水出口温度 | value=冷冻水出口温度 | unit=None | summary=标准空调机组冷冻水出口温度设定范围为4.5°C至15°C。

Human verdict: 

