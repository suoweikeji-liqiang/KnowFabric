# HVAC Starter Batch Plan

This is a curated first-pass plan generated from `source_inventory.csv`. It avoids split ASHRAE `_partNNN` duplicates, excludes product catalogs/samples from the first OEM batch, and separates text-ready manuals from OCR/multimodal holds.

## Batch Groups

- A_standard_authority_first: 8
- B_oem_manual_text_first: 80
- C_ocr_multimodal_hold: 60

## Recommended Modes

- section_context_or_chapter_batch: 6
- doc_level_or_section_context: 2
- doc_level_single_call: 85
- ocr_or_multimodal_first: 55

## OEM First-Pass Brand Mix

- McQuay/Daikin: 15
- Midea: 11
- Gree: 9
- York/JCI: 8
- Haier: 7
- Carrier: 7
- Trane: 7
- TICA: 4
- Mitsubishi Heavy Industries: 3
- Dunham-Bush: 3
- Hitachi: 3
- Daikin: 2
- Kingair: 1

## Operational Recommendation

1. Run `A_standard_authority_first` first, one document or one chapter group at a time. These define high-authority baseline knowledge.
2. Run `B_oem_manual_text_first` as the first overnight batch. Start with doc-level for <=180 page manuals and chapter/section mode for larger manuals.
3. Keep `C_ocr_multimodal_hold` out of the text-only batch. Use OCR or multimodal extraction before LLM knowledge extraction.
4. Do not import product catalogs/samples in the same first batch; use them later for performance/application metadata only.

## First 30 Text-Ready OEM Manuals

| Brand | Kind | Equipment | Pages | Mode | Path |
|---|---|---|---:|---|---|
| McQuay/Daikin | fault_code_reference | controller,fault_code | 31 | doc_level_single_call | /Volumes/TSD302/pan/a00238/06、麦克维尔/技术手册/【麦克维尔】MACD模块机组故障分析与排除技术手册（31页）-.pdf |
| Haier | fault_code_reference | vrf_vrv,fault_code | 111 | doc_level_single_call | /Volumes/TSD302/pan/a00238/08、海尔中央空调/海尔技术手册/（制冷百家）海尔商用故障代码手册-制冷百家网.pdf |
| Gree | technical_manual | air_cooled_chiller_heat_pump | 15 | doc_level_single_call | /Volumes/TSD302/pan/a00238/02、格力/技术手册/【格力】中央空调 MB 系列模块式风冷冷（热）水机组手册-.pdf |
| Kingair | controller_manual | air_cooled_chiller_heat_pump,controller | 17 | doc_level_single_call | /Volumes/TSD302/pan/a00238/21、国祥/【国祥】模块机控制器规格书.pdf |
| Gree | technical_manual | air_cooled_chiller_heat_pump | 18 | doc_level_single_call | /Volumes/TSD302/pan/a00238/02、格力/技术手册/【格力】模块风冷冷水机组控制系统手册-.pdf |
| Mitsubishi Heavy Industries | controller_manual | controller | 20 | doc_level_single_call | /Volumes/TSD302/pan/a00238/07、三菱重工/技术手册/【三菱重工】线控器用户使用说明手册（20页）.pdf |
| TICA | operation_installation_manual | air_cooled_chiller_heat_pump,ahu,controller | 21 | doc_level_single_call | /Volumes/TSD302/pan/a00238/13、天加中央空调/【天加 】风冷净化空调机组安装操作手册.pdf |
| York/JCI | controller_manual | air_cooled_chiller_heat_pump,controller | 23 | doc_level_single_call | /Volumes/TSD302/pan/a00238/04、约克中央空调/约克技术手册/【约克】风冷冷水机组YCAC，YMAC，YSAC通用控制器使用手册3.0.pdf |
| Carrier | operation_installation_manual | air_cooled_chiller_heat_pump | 28 | doc_level_single_call | /Volumes/TSD302/pan/a00238/03、开利中央空调/技术手册/【开利】30AQ开利风冷式热泵机组（28页）-制冷百家网.pdf |
| Carrier | service_manual | air_cooled_chiller_heat_pump | 28 | doc_level_single_call | /Volumes/TSD302/pan/a00238/03、开利中央空调/技术手册/【开利】中央空调30AQ风冷式热泵机组安装维修手册（28页）-制冷百家网.pdf |
| Haier | service_manual | air_cooled_chiller_heat_pump | 28 | doc_level_single_call | /Volumes/TSD302/pan/a00238/08、海尔中央空调/海尔技术手册/【海尔】LSQWRF130C-318C风冷涡旋机组维修手册（28页）-制冷百家网.pdf |
| Haier | service_manual | air_cooled_chiller_heat_pump | 28 | doc_level_single_call | /Volumes/TSD302/pan/a00238/08、海尔中央空调/海尔技术手册/【海尔】LSQ系列风冷涡旋机组维修手册（32页）-制冷百家网.pdf |
| Haier | service_manual | fault_code | 29 | doc_level_single_call | /Volumes/TSD302/pan/a00238/08、海尔中央空调/海尔技术手册/【海尔】商用柜机KFR(d)-120LW】维修手册（29页）-制冷百家网.pdf |
| Midea | service_manual | fault_code | 30 | doc_level_single_call | /Volumes/TSD302/pan/a00238/09、美的/美的技术手册/【美的】高温直热循环式热水机 RSJ 系列 技术手册（30页）-制冷百家网.pdf |
| TICA | operation_installation_manual | screw_chiller | 32 | doc_level_single_call | /Volumes/TSD302/pan/a00238/13、天加中央空调/【天加】水冷螺杆式冷水机组操作使用说明书.3.pdf |
| Trane | operation_installation_manual | controller,fault_code | 32 | doc_level_single_call | /Volumes/TSD302/pan/a00238/05、特灵中央空调/特灵/【特灵】WPWE040-100热泵空调安装维护手册（32页）-制冷百家网.pdf |
| Trane | operation_installation_manual | water_source_heat_pump,controller,fault_code | 32 | doc_level_single_call | /Volumes/TSD302/pan/a00238/05、特灵中央空调/特灵/【特灵】水源热泵空调wpwe技术手册-制冷百家网.pdf |
| York/JCI | technical_manual | air_cooled_chiller_heat_pump | 33 | doc_level_single_call | /Volumes/TSD302/pan/a00238/04、约克中央空调/约克技术手册/【约克】YHAC-B风冷空气源热泵机安装调试与维护手册（33页）-制冷百家网.pdf |
| TICA | operation_installation_manual | air_cooled_chiller_heat_pump | 35 | doc_level_single_call | /Volumes/TSD302/pan/a00238/13、天加中央空调/【天加 】空调模块机组安装操作手册（22页）.pdf |
| Dunham-Bush | operation_installation_manual | screw_chiller,air_cooled_chiller_heat_pump | 35 | doc_level_single_call | /Volumes/TSD302/pan/a00238/18、顿汉布什/【顿汉布什】风冷螺杆安装操作说明书.pdf |
| McQuay/Daikin | operation_installation_manual | water_source_heat_pump | 36 | doc_level_single_call | /Volumes/TSD302/pan/a00238/06、麦克维尔/技术手册/【麦克维尔】MWH008～350C(R)水源热泵安装使用说明书（36页）-制冷百家网.pdf |
| Dunham-Bush | operation_installation_manual | screw_chiller,air_cooled_chiller_heat_pump | 38 | doc_level_single_call | /Volumes/TSD302/pan/a00238/18、顿汉布什/【顿汉布什】风冷螺杆冷水机组安装操作维修说明书.pdf |
| Dunham-Bush | operation_installation_manual | screw_chiller,air_cooled_chiller_heat_pump | 38 | doc_level_single_call | /Volumes/TSD302/pan/a00238/25、其他品牌/顿汉布什风冷螺杆冷水机组安装操作维修说明书.pdf |
| Trane | operation_installation_manual | controller | 39 | doc_level_single_call | /Volumes/TSD302/pan/a00238/05、特灵中央空调/特灵/【特灵】奥迪斯风管机空调安装操作维护手册（39页）.pdf |
| Trane | operation_installation_manual | air_cooled_chiller_heat_pump | 42 | doc_level_single_call | /Volumes/TSD302/pan/a00238/05、特灵中央空调/特灵/【特灵】Aquastream风冷式冷水（热泵）机组技术手册（42页）-制冷百家网.pdf |
| Carrier | technical_manual | air_cooled_chiller_heat_pump | 43 | doc_level_single_call | /Volumes/TSD302/pan/a00238/03、开利中央空调/技术手册/【开利】30RB192-802涡旋式风冷冷水机组开机运行维护手册43页-制冷百家网.pdf |
| Midea | technical_manual | screw_chiller | 44 | doc_level_single_call | /Volumes/TSD302/pan/a00238/09、美的/美的技术手册/【美的】C系列干式螺杆冷水机组技术手册（44页）-制冷百家网.pdf |
| Midea | service_manual | fault_code | 44 | doc_level_single_call | /Volumes/TSD302/pan/a00238/09、美的/美的技术手册/【美的】空气能热泵热水机安装使用维修手册(一)（44页）-制冷百家网.pdf |
| TICA | operation_installation_manual | screw_chiller,water_source_heat_pump | 46 | doc_level_single_call | /Volumes/TSD302/pan/a00238/13、天加中央空调/【天加 】满液式水源螺杆热泵机组(用户手册)（46页）.pdf |
| York/JCI | service_manual | air_cooled_chiller_heat_pump | 46 | doc_level_single_call | /Volumes/TSD302/pan/a00238/04、约克中央空调/约克技术手册/【约克】YMAC风冷冷水热泵机组维修手册（46页）-制冷百家网.pdf |

## Standard Authority Set

| Kind | Pages | Mode | Path |
|---|---:|---|---|
| standard_guideline_control_sequences | 292 | section_context_or_chapter_batch | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/HVAC系统高性能运行序列指南.pdf |
| standard_handbook |  | doc_level_or_section_context | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE手册2019.pdf |
| standard_handbook | 19 | doc_level_or_section_context | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE 211能源审计最佳实践.pdf |
| standard_handbook | 401 | section_context_or_chapter_batch | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/空调 系统 设计 手册 Ashrae 特别 出版物.pdf |
| standard_handbook | 494 | section_context_or_chapter_batch | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE绿色建筑指南.pdf |
| standard_handbook | 986 | section_context_or_chapter_batch | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE手册 - HVAC系统和设备篇.pdf |
| standard_handbook | 1006 | section_context_or_chapter_batch | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE手册2024.pdf |
| standard_handbook | 1014 | section_context_or_chapter_batch | /Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE手册 - 基础理论篇.pdf |
