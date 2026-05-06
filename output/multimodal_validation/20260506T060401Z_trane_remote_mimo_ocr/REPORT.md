# Remote MiMo OCR Validation Report

**Run ID:** 20260506T060401Z_trane_remote_mimo_ocr
**PDF:** /Users/asteroida/work/KnowFabric/storage/documents/doc_883beab5e0004a2c/trane_cvgf_400_1000_chiller_manual.pdf
**API Base:** `https://token-plan-sgp.xiaomimimo.com/v1`
**Models:** mimo-v2.5
**Pages:** [25, 29, 41, 45]
**Parameters:** temperature=0.2, top_p=0.95, max_completion_tokens=4096

## Results

### mimo-v2.5

- Page 25: ok in 12.2s, matched_expected=Active Chilled Water Setpoint, Active Current Limit Setpoint, Chilled Water Reset, sample=TRANE  机组控制面板(UCP)  Back Active Chilled Water Setpoint Arbitration Front Panel 44.0F Active/Blank BAS 48.0F/----- Active/Blank External 42.0F/----- Active/Blank Chilled Water Reset Return/Constant Return/Outdoor/None Act
- Page 29: ok in 14.0s, matched_expected=Front Panel Chilled Water Setpoint, Front Panel Current Limit Setpoint, Front Panel Base Load Setpoint, Differential to Start, Differential to Stop, Setpoint Source, Chilled Water Reset, sample=TRANE  机组控制面板(UCP)  Chiller(冷水机组) Description 说明 | Units(机组) | notes 备注 --- | --- | --- 1. Front Panel Control Type 前端面板控制类型 | (Chilled Water, Hot Water), Chilled Water default (冷冻水, 热水), 冷冻水为默认类型 |  2. Front Panel Chill
- Page 41: ok in 16.1s, matched_expected=none, sample=TRANE  控制系统组件  OPST 运行状态选项 继电器输出模块1A8和1A9提供如下的继电器输出: 1A8选项四位继电器输出状态 | OPST | 继电器#1 | MAR警告继电器 (自锁) | J2-1 NO, J2-2 NC, J2-3 COMMON 1A8选项四位继电器输出状态 | OPST | 继电器#2 | 限制警告继电器 | J2-4 NO, J2-5 NC, J2-6 COMMON 1A8选项四位继电器输出状态 | 
- Page 45: ok in 37.1s, matched_expected=External Chilled Water Setpoint, sample=控制系统组件  外部冷冻水设定External Chilled Water Setpoint(ECWS) 外部冷冻水设定可对冷冻水的设定在远程进行修改。 外部冷冻水设定建立在1A16 J2-2至J2-6(接地)的输入基础上。

## Notes

- This run uses Xiaomi MiMo's OpenAI-compatible API with image input via `image_url`.
- Outputs are raw OCR/transcription text intended for later parameter extraction comparison.
- Page-level expectation hits are only a coarse proxy for OCR usefulness.

