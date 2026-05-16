# Operator 10-min review: 12 most likely over-merge KOs

Each KO below is `material_conflict` cross-publisher. The question for each:

> **是否同一个概念被多个 publisher 描述？** 还是不同概念被错误合并了？

评判简单：看下面每个 publisher 的 evidence quote 第一句话，问"它们说的是同一参数吗？"

---

## #1  `Water Temperature Limits` (ahu)

- KO id: `ko_049900646e2b1794`
- canonical_key: `hvac:ahu:parameter:water_temperature_limits`
- publishers: unknown, 格力, 美的, 麦克维尔  (7 layers, 6 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| unknown | 热水进出水温 |  |  | .26 .注：1.热水进出水温60℃/50℃，盘管迎面风速2.5m/s。            2.进风干温度7℃。 3.表中数据为盘管性能参数，整机性能参数以选型报告为准。注：1.热水进出水温60℃/50℃，盘管迎面风速2.5m/s。           2.进风干温度15℃。    3.表中数据为盘管性能参数，整机性能参数以选型报告为准。箱体规格额定风量 （m3/h）2排 4排 6排 汇管管径 |
| 格力 | 热水供热进水温度 |  |  | 12 13 GREE Central Air Conditioning Units格力 GZK 系列组合式空调机组 ◆ 新风工况 说明： 1、机组迎面风速：2.5m/s。 2、上表为单用热水盘管，进水温度 90℃。 3、回风工况：进风干球温度：15℃。 4、新风工况：进风干球温度：- 4℃。4、机组供热量 ( 蒸汽供热 ) ◆ 回风工况 ቆJOEE  |
| 格力 | 热水加热器设计温度 |  |  | 智能控制系统 安装注意事项： ◆ 风机电机应有可靠保护，如过流保护、 过热保护、 缺相保护。当电 机功率较大时， 采用 Y-△起动装置或其他降低起动电流的装置。 ◆ 换热器的工作压力不应超过 1.6MPa，如工作压力过高请与我 公司联系，可按非标设计。 ◆ 机组安装完毕后检查机组内不应留有杂物， 并对内部清理干净。 ◆ 检查各手动、电动阀门是否开启灵活，处于工作状态。 ◆ 检查风机各部件螺栓是否松 |
| 美的 | Water Temperature Limits |  |  | 1703-7C1612 Commercial Air Conditioners  2017/2018 Air Handling Unit & Modular Air Handling Unit iOS Version Android VersionMidea CAC After-service Application iOS VersionMidea CAC News Application Co |
| 美的 | 额定热量测试工况（回风） |  |  | 高冷 标冷 高冷 标冷 高冷 标冷 高冷 标冷 高冷 标冷 高冷 标冷 高冷 标冷 高冷 标冷 高冷 标冷 高冷 标冷 高冷3000 4000 5000 6000 7000 8000 9000 10000 12000 1500003D 04D 05D 06D 07D 08D 09D 10D 12D 15D 型号 排数风量 m3/h机外余压(Pa) 电机功率(kW) 02D 750 870 555  |
| 麦克维尔 | 热水进水温度及温差 |  |  | 6麦克维尔MDM系列组合式空气处理机组 MDM 7麦克维尔MDM系列组合式空气处理机组 MDM 注： ■ 冷冻水进水温度7℃，温差5℃； ■ 标准新风供冷工况为进风干球温度34℃，湿球温度28℃；■ 盘管为铜管铝翅片，标准片距为12片/英寸，片距有9~14片/英寸可选；■ 具体机型的参数请参考麦克维尔Integrated-AHU选型软件的选型结果。常用机组性能参数表——供冷新风工况 注： ■ 热水 |

**判断（你填 ✅/❌/?）**: 

---

## #2  `Method of Testing Thermal Storage Devices` (standard_reference)

- KO id: `ko_05cadbc5549457f3`
- canonical_key: `hvac:standard_reference:application:method_of_testing_thermal_storage_devices`
- publishers: ASHRAE, 特灵  (5 layers, 5 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| ASHRAE | Method of Testing Thermal Storage Devices |  |  | SMACNA SMACNA 2002 Thermal StorageThermal Energy Storage: A Guide for Commercial HVAC Contractors ACCA ACCA 2005 Method of Testing Thermal Storage Devices wi th Electrical Input and Thermal Output Bas |
| ASHRAE | Double-Effect Absorption Chiller COP Requirement |  |  | A S H R AE  G R E E N G U I D E   1 2 1 grams  are  c o nc e rne d no t o nl y wi th the  b ui l di ng he at gai n b ut al s o  wi th the  c o ntri b u- ti o n o f  the  b ui l di ng s truc ture  a |
| 特灵 | 热回收使用条件（ASHRAE 90.1-2001） |  |  | 3 54水泵压头、 速度重置 制冷剂每冷 吨充注量将泵的运行压力重置可以保 证自控阀对压力需求最大时的开度为 90%左右。 泵节能 (11)没有相关的文献讲述优 化泵压，但可参阅风机控制的相关原理： (10) 6热回收 水冷式制冷机组冷凝器的热 量回收，可以用来提供: 加热冷空气 (用于湿度控制） 预热室外空气加热进入建筑物的补水制冷剂越少则系统泄漏对环境的影响也越小，特别是中高压系统可参照 AS |

**判断（你填 ✅/❌/?）**: 

---

## #3  `推力轴承—油温传感器` (centrifugal_chiller)

- KO id: `ko_02e2749573080a28`
- canonical_key: `hvac:centrifugal_chiller:fault_code:key_90cab05c63`
- publishers: Carrier, York, 格力  (5 layers, 4 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| Carrier | 预启动报警 | 105 |  | 105 预启动报警 PRESTART ALERT 油温低 LOW OIL TEMPERATURE |
| York | 推力轴承—油温传感器 |  | °F | 接近探针探测出在高速排油线内的油温已升到 >250.0°F。 |
| York | 润滑油温度过高 | >180.0 | °F | 润滑油温度传感器感应到的润滑油温度已升高到>180.0°F。 |
| 格力 | 供油温度高温报警/保护 |  |  | 39 维修篇 1 机组故障一览表 故障显示  故障名称  故障信号来源  保护说明 油压差报 警/保护 压缩机油 压差报警/ 保护 供油压力 油箱压力 如果供油不足，轴承有烧掉的危险，为保证机组主 电动机、压缩机各轴承处润滑充分，即保证充分供 油，需要足够的油压差，运行时当压差过低时机组 报警或者保护停机，在机组起动时，压差低于设定 值主机将不起动 供油温度 报警/保 护 供油温度 高温报警 /  |
| 格力 | 供油温度高温报警/保护 |  |  | 39 维修篇 1 机组故障一览表 故障显示  故障名称  故障信号来源  保护说明 油压差报 警/保护 压缩机油 压差报警/ 保护 供油压力 油箱压力 如果供油不足，轴承有烧掉的危险，为保证机组主 电动机、压缩机各轴承处润滑充分，即保证充分供 油，需要足够的油压差，运行时当压差过低时机组 报警或者保护停机，在机组起动时，压差低于设定 值主机将不起动 供油温度 报警/保 护 供油温度 高温报警 /  |

**判断（你填 ✅/❌/?）**: 

---

## #4  `能量调节范围` (water_source_heat_pump)

- KO id: `ko_1c30a6cbb8f911c0`
- canonical_key: `hvac:centrifugal_chiller:parameter:key_2b0d5b413b`
- publishers: Haier, 三菱重工, 格力  (4 layers, 4 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| Haier | 能量调节范围 | 25-100 | % | 能量调节范围 25~100 调节 |
| Haier | 压缩机转换能量 | 50 | % | 压缩机25%能量运行30秒 |
| 三菱重工 | 热水流量变化下限 |  |  | 热泵  E T W   技术资料  42 控制柜构成 9 999...555      可可可变变变流流流量量量规规规格格格的的的对对对应应应（（（选选选购购购件件件））） 为了实现空调设备的节能，可能会设置多台热源水与热水泵，并根据负荷进行某 些台数的起停或利用变频器进行流量控制。此时的注意事项如下所示。 999...555...111      注注注意意意事事事项项项 (1) 流量变化下限值 |
| 格力 | 最大负荷设定 |  |  | 17 格力高效水源热泵螺杆机组 安装、运行、维护说明书 图 3.24 彩屏显示板——用户设置 图 3.25 触摸屏——用户设置 各控制区功能如下： 序号 控制项目 范围 备注 1冷冻水出水温度 设定4.0 ～ 15.0℃① 若蒸发器出水温度超出表中范围值，请联系格力公司。 ② 若蒸发器出水温度低于表中最低值，循环水系统中需添加 防冻液，并联系格力公司订购低温机组。 2最大负荷设定 40~100%通 |

**判断（你填 ✅/❌/?）**: 

---

## #5  `Room temperature and humidity limits` (centrifugal_chiller)

- KO id: `ko_0aa4c474998d9d3b`
- canonical_key: `hvac:centrifugal_chiller:application:room_temperature_and_humidity_limits`
- publishers: 格力, 盾安  (10 layers, 4 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| 格力 | 安装环境要求 |  |  | 12 7 机组安装空间要求 7.1 安装基础与环境 ◆安装环境 1) 制冷机应避免接近火源和易燃物。若与锅炉等发热体 安装在一起时，应充分注意热辐射 的影响。 2) 最好选用室温在40℃以下，通风通畅的场所，（因高温是故障的原因并加快腐蚀）,在40 ℃时的环境相对湿度应在90％以下，不允许室外或露天安装、存放。 3) 应选取灰尘少的场所（灰尘是电故障的原因）。 4) 现场应采光良好，以便于维护、检 |
| 格力 | 安装环境要求 |  |  | 12 7 机组安装空间要求 7.1 安装基础与环境 ◆安装环境 1) 制冷机应避免接近火源和易燃物。若与锅炉等发热体 安装在一起时，应充分注意热辐射 的影响。 2) 最好选用室温在40℃以下，通风通畅的场所，（因高温是故障的原因并加快腐蚀）,在40 ℃时的环境相对湿度应在90％以下，不允许室外或露天安装、存放。 3) 应选取灰尘少的场所（灰尘是电故障的原因）。 4) 现场应采光良好，以便于维护、检 |
| 盾安 | Room temperature and humidity limits |  |  | 机组外形尺寸、基础图 机组安装、使用、维护 1. 机组起吊示意图 利用钢索和方形梁进行吊装作业，在机组管板吊装孔处安装卸扣起吊（如下起吊图所示）；在吊装之前 请检查吊索的强度和方形梁的平衡性，吊装用的钢索每根都要能单独承受机组的重量；方形梁的刚度要满足 需求，起吊过程中钢索和横梁都必须与机组保持足够的间距，以免损坏机组。 2. 安装环境 1) 机组应安装在通风通畅、灰尘少的专用机房（灰尘易造成电气 |
| 盾安 | Room temperature and humidity limits |  |  | 机组外形尺寸、基础图 机组安装、使用、维护 1. 机组起吊示意图 利用钢索和方形梁进行吊装作业，在机组管板吊装孔处安装卸扣起吊（如下起吊图所示）；在吊装之前 请检查吊索的强度和方形梁的平衡性，吊装用的钢索每根都要能单独承受机组的重量；方形梁的刚度要满足 需求，起吊过程中钢索和横梁都必须与机组保持足够的间距，以免损坏机组。 2. 安装环境 1) 机组应安装在通风通畅、灰尘少的专用机房（灰尘易造成电气 |

**判断（你填 ✅/❌/?）**: 

---

## #6  `排气压力` (screw_chiller)

- KO id: `ko_13be08b257cfe5ef`
- canonical_key: `hvac:screw_chiller:performance_spec:key_6428129801`
- publishers: 天加, 约克  (5 layers, 4 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| 天加 | 排气压力 |  |  | 水冷满液式螺杆式水机组 （用户手册）  V1.0 南京天加空调设备有限公司                                      第 11 页 共 33 页 8.机组启动及运行 8.1机组启动前检查项 8.1.1水路部分 检查所有的水系统管路，确认蒸发器和冷凝器水路连接无误而且水流方向正确，检查上述换热器进 出水管是否连接良好，开启所有的水阀，启动相关水泵。冲洗水管，保证水系统 |
| 天加 | 排气压力 |  |  | 第10页， 共43页 表一表一 表一表一:安全装置检查项安全装置检查项安全装置检查项安全装置检查项 检查项目检查项目 检查项目检查项目 项目项目 项目项目 检查方法检查方法 检查方法检查方法 控制要求（R22/ R134a）控制要求（R22/ R134a）控制要求（R22/ R134a）控制要求（R22/ R134a） 1.排气压力 检查高压显示值（排气） 1.1-2.3MPa/ 0.6-1.8M |
| 约克 | 固态启动器冷却水回路工作压力 |  |  | 9供选件、选型表 弹簧减振器 机组楼面安装，建议用弹簧减振器 来代替标准的橡胶减振垫。四个水 平度可调节的弹簧减振器，配有防 滑垫，便于安装在管端板下面。弹 簧减振的设计压缩量为 25.4mm。 船用式水室 船用式水室使得清洗热交换器铜管极 为方便，不需拆掉水管。螺栓连接的 端盖方便了检修。水管采用沟槽式连 接方式，或法兰连接。冷凝器和蒸发 器都可以采用船用式水室。 水室铰链 将水室和筒体通过铰链 |
| 约克 | 水室设计工作压力 |  |  | 7综述 约克YR螺杆式冷水机组完全由工厂组装，包括蒸发 器、冷凝器、压缩机、电机、润滑系统、彩色图象控 制中心和整装机组内所有的接管及敷线，并为每台机 组提供制冷剂和润滑油的首次充注。 驱动装置 选用高效工业用半封闭双螺杆式压缩机，高精度加 工，独特结构，高效可靠。 压缩机采用铸铁壳体，锻钢转子，转子间隙很小，但 不接触，而支撑面确保转子在各种压力比时，保持精 确定位，减少磨损，防止渗漏，延长寿命 |

**判断（你填 ✅/❌/?）**: 

---

## #7  `重启抑制时间设定值` (centrifugal_chiller)

- KO id: `ko_007c216c7e472be1`
- canonical_key: `hvac:centrifugal_chiller:parameter:key_42f5d7a8ec`
- publishers: Carrier, Trane  (4 layers, 4 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| Carrier | 需求限制时间 | 5-60 | MIN | 需求限制时间 5-60 MIN 15 |
| Carrier | 1分钟限制开机计时器 | 1分钟 | 分钟 | 15分钟限制开机计时器开始计时（D之后10秒） |
| Trane | 重启抑制时间设定值 |  |  | 52次启动的间隔时间。 默认设定是 20分钟，可以使用 TechView 更 改 设 置 。 如 果 使 用 TechView 设置重启限制类型为“时 间”，或者检测到电机绕组温度过 高时，将启用基于时间的重启抑制 功能。 注意：当重启抑制功能发挥作 用抑制重启时，将会显示剩余时间 和重启抑制模式。由于重启抑制使 用计时器来根据上次启动的时间来 来判断下次的启动时间，因此，即 使在 MP上按下“启 |

**判断（你填 ✅/❌/?）**: 

---

## #8  `排水管接口尺寸` (centrifugal_chiller)

- KO id: `ko_3fde94ba89d7abd8`
- canonical_key: `hvac:centrifugal_chiller:performance_spec:key_c001032cf6`
- publishers: York, 特灵  (4 layers, 4 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| York | 排水管接口尺寸 | 19.1mm | mm | 设计的工作压力是1034kPa表压，在1551kPa表压时测试。 |
| York | 冷凝器流量过小 - 压差要求 | 8 | 英尺水柱 | VSD系统要求热交换器前后的压差为8英尺水柱，以提供足够的GPM。 |
| 特灵 | 蒸发器管径与效率 |  |  | 蒸发器 z壳管降膜式蒸发器 y筒体是由两个半月形筒组成 ，采用全穿透坡口焊沿着纵向焊接在一 起 z根据ASME锅炉和压力容器规范和 PED 为制冷剂侧 220 psig (15.2 Bars) 工作压力设计 、测试和制造的 。 z个别可替换 ，1” (25.4mm) OD 管用于0.182 kW/kW (0.64 kW/Ton) 设计和 3/4” (19mm) OD 用于0.165 kW/kW ( |
| 特灵 | 冷凝器管径与效率 |  |  | 冷凝器 z壳管式冷凝器 筒体是由两个半月形筒组成 ，采用全穿透坡口焊沿着纵向接 在一起 z根据ASME锅炉和压力容器规范和 PED (Pressure Equipment Directive) 为制冷剂侧 220 psig (15.2 Bars) 工作压力设计 、测试和制造的 。 z个别可替换 ，1” (25.4mm) OD 管用于0.182 kW/kW (0.64 kW/Ton) 设计和 3/4 |

**判断（你填 ✅/❌/?）**: 

---

## #9  `工作压力` (screw_chiller)

- KO id: `ko_80e2ce015328c396`
- canonical_key: `hvac:ahu:parameter:key_a58b0e8cfc`
- publishers: 约克, 麦克维尔  (4 layers, 4 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| 约克 | 蒸发器设计工作压力 |  |  | 1MPa表压。 容量控制：压缩机在最小负荷位置启动，受微处 理器控制的容量调节阀通过一连续作用的滑阀在 100%～25%负荷范围内实现无级调节。容量调节阀的弹簧自动复位到最小负荷位置，以确 保压缩机电机在最小负荷下启动。 内部排气止回阀可以防止转子在停机时逆转。排气截止阀。防水接线盒。吸气冷却、高效可靠的半封闭式电机具有过载保 护：热敏电阻保护。跟直 接启动相比，星三角压缩机电机启动器使启动 电流 |
| 麦克维尔 | 工作压力 |  |  | 您的冷暖我关怀·麦克维尔空调 YourClimate,We’reThere·McQuay 9【麦克维尔空调】中央空调方案书 （二）、风机盘管技术特点 麦克维尔卧式暗装风机盘管机组主要由五个部份组成：换热盘管、风机、电机、钣 金件及包装。产品设计简单灵活，高效换热，运行稳定可靠，宁静低噪，从各个方面 满足并超越用户需求。 先进的设计、优质的选材、先进的加工设备和工艺、再加上100%严格的测试，保 证 |
| 麦克维尔 | 密封性试验压力 |  |  | 您的冷暖我关怀·麦克维尔空调 YourClimate,We’reThere·McQuay 10【麦克维尔空调】中央空调方案书 盘管经100%密封性试验：2.0MPa气压持续1分钟，无渗漏。 运转稳定低噪：McQuay风机盘管机组采用宽大叶轮的 高效低噪离心式风机，其迎风面积要大。整片板材经 冲压卷绕而成的风轮，为盘管提供均匀风速，提高了 机组的送风量和换热效果。符合空气动力学的蜗壳板， 防止在出 |

**判断（你填 ✅/❌/?）**: 

---

## #10  `air_flow_range` (ahu)

- KO id: `ko_ac1ec4ada2e33a7b`
- canonical_key: `hvac:ahu:performance_spec:air_flow_range`
- publishers: Carrier, Holtop, 特灵, 麦克维尔  (4 layers, 3 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| Carrier | air_flow_range |  |  | 39CNE [2,000~100,000 m3/h] A I R  H A N D L I N G  U N I T |
| Holtop | air_leakage_rate | <1% at 1000Pa |  | Pressure endurance up to 2000Pa, suitable for large airflow application. High air tightness - Double inlaid sealing to join the frameworks and panels tightly, minimizing air leakage. Air leakage rate  |
| 特灵 | 加湿量 |  |  | 湿膜加湿器加湿量 LPCQ湿膜加湿器加湿量 型号 标准风量 混风工况 新风工况 LPCQ  CMH (kg/h) (kg/h) 003 2000 4.6 3.6 2500 5.7 4.5 004 3000 6.8 5.4 4000 9.1 7.2 006 5000 11.4 9.0 6000 13.7 10.8 008 7000 16.0  12.6 8000 18.2 14.4 010 9000 |
| 麦克维尔 | air_leakage_rate |  |  | 5 4unctional applications功能应用F 5 4高级净化型空气处理机组 机组特点 高级净化型组合式空气处理机组 MDM-XE系列机组传承了50余年的空气净化处理技术，结构先进， 品质高端，是一款专为洁净场所而打造的新一代高级净化空气处理机 组，可广泛应用于微电子无尘室、医院手术部、生物科技、制药厂 房、卷烟厂、汽车厂房等净化场所。 风量应用范围：2000~200000m3/h， |

**判断（你填 ✅/❌/?）**: 

---

## #11  `Heating capacity YEAS300R 45°C/7°C` (screw_chiller)

- KO id: `ko_0269f9e22638c29b`
- canonical_key: `hvac:screw_chiller:performance_spec:heating_capacity_yeas300r_45_c_7_c`
- publishers: 特灵, 约克, 麦克维尔  (6 layers, 3 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| 特灵 | 制热工况条件 |  |  | 260 926263 261.8 889 247.3 3 4450 18 25050 134 134176 291 291354 125 125132 12080 10625360 1272 362 356.7 1211 341.9 4 61 51 24 25050 176 176134134354354291291132132125125 15800 13627 13337 10397 注：1. |
| 约克 | Heating capacity YEAS300R 45°C/7°C |  |  | 6型号出水温 度℃进入盘管的空气温度 (℃) -10 -5 0 5 7 10 15 20 25 热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW 7530 153 59 188 60 219 62 263 66 291 68 308 70 330 72 348 73  |
| 约克 | Heating capacity YEAS300R 45°C/7°C |  |  | 6型号出水温 度℃进入盘管的空气温度 (℃) -10 -5 0 5 7 10 15 20 25 热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW热量 kW功率 kW 7530 153 59 188 60 219 62 263 66 291 68 308 70 330 72 348 73  |
| 麦克维尔 | 制热设计工况 |  |  | 4 4 6 6 8 8 8 10 10 12 总风量 ×104m3/h 8.8 8.8 13.2 13.2 17.6 17.6 17.6 22.0 22.0 26.4 总输入功率 kW 8.0 8.0 12.0 12.0 16.0 16.0 16.0 20.0 20.0 24.0 水侧换热器类型 壳管式换热器 制冷工况水流量 m3/h 29 35 41 48 62 73 78 90 107 112 |

**判断（你填 ✅/❌/?）**: 

---

## #12  `能量调节范围` (screw_chiller)

- KO id: `ko_6ba078de2eed310a`
- canonical_key: `hvac:centrifugal_chiller:parameter:key_2b0d5b413b`
- publishers: 欧科, 约克, 麦克维尔  (5 layers, 3 个不同 parameter_name/source_name)

| publisher | parameter_name / source_name | value/range | unit | evidence quote (first 200 chars) |
|---|---|---|---|---|
| 欧科 | 能量控制 |  |  | 11www.euroklimat.com.cn 螺杆式风冷冷水(热泵)机组机组规格参数表 机组规格参数表(EKAS065~EKAS165 R22制冷剂) 注: ■ 制冷设计工况为：室外干球温度35℃，出水温度7℃，水流量0.172m3/(h·kW)； ■ 制热设计工况为：室外干球/湿球温度7℃/6℃，出水温度45℃，水流量0.172m3/(h·kW)； ■ ＊此项为热泵型机组的制热量参数，EKAS |
| 欧科 | 能量控制 |  |  | 1www.euroklimat.com.cn 螺杆式风冷冷水(热泵)机组机组规格参数表(EKAS180~EKAS275 R22制冷剂) 注: ■ 制冷设计工况为：室外干球温度35℃，出水温度7℃，水流量0.172m3/(h·kW)； ■ 制热设计工况为：室外干球/湿球温度7℃/6℃，出水温度45℃，水流量0.172m3/(h·kW)； ■ ＊此项为热泵型机组的制热量参数，EKAS单冷型机组无此项 |
| 约克 | 容量调节范围 |  |  | 1MPa表压。 容量控制：压缩机在最小负荷位置启动，受微处 理器控制的容量调节阀通过一连续作用的滑阀在 100%～25%负荷范围内实现无级调节。容量调节阀的弹簧自动复位到最小负荷位置，以确 保压缩机电机在最小负荷下启动。 内部排气止回阀可以防止转子在停机时逆转。排气截止阀。防水接线盒。吸气冷却、高效可靠的半封闭式电机具有过载保 护：热敏电阻保护。跟直 接启动相比，星三角压缩机电机启动器使启动 电流 |
| 麦克维尔 | 能量调节范围 |  |  | 7 6 螺杆式风冷冷水/热泵机组 螺杆式风冷冷水/热泵机组 7 6规格参数 说明：■ *所示表中“/”分别为主机和辅机的参数；其它未标识的与此相同； ■ 制冷名义工况：冷冻水进/出水温度12℃/7℃；环境干球温度35℃； ■ 制热名义工况：热水进/出水温度40℃/45℃；环境干球温度7℃，湿球温度6℃；■ MHS235~450 机组除以上标配附件外，还包括：温度传感器、通讯线； ■ MHS235~ |
| 麦克维尔 | 能量调节范围 |  |  | 机型MHS ST 050.1 060.1 070.1 080.1 090.1 100.1 120.1 135.1 150.1 170.1 名义制冷量kW 164 198 232 270 299 347 388 456 495 607 USR T 47 56 66 77 85 99 110 130 141 173 ×104kcal/h 14 17 20 23 26 30 33 39 43 52 压缩 |

**判断（你填 ✅/❌/?）**: 

---

