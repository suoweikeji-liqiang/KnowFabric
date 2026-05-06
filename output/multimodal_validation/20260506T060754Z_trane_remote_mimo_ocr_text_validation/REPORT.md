# Remote MiMo OCR -> Local Text Validation Report

**Run ID:** 20260506T060754Z_trane_remote_mimo_ocr_text_validation
**MiMo OCR source:** /Users/asteroida/work/KnowFabric-qwen-vl-validate/output/multimodal_validation/20260506T060401Z_trane_remote_mimo_ocr
**OCR model:** mimo-v2.5
**Text model:** gemma-4-e4b-it-4bit

## Results

- Page 25: parsed=2, matched_expected=Active Chilled Water Setpoint, Active Current Limit Setpoint, sample=Active Chilled Water Setpoint | Active Chilled Water Setpoint 44.0F; Active Current Limit Setpoint | Active Current Limit Setpoint 100%
- Page 29: parsed=17, matched_expected=Front Panel Chilled Water Setpoint, Front Panel Current Limit Setpoint, Front Panel Base Load Setpoint, Differential to Start, Differential to Stop, Setpoint Source, Chilled Water Reset, sample=Front Panel Chilled Water Setpoint | Front Panel Chilled Water Setpoint; Front Panel Current Limit Setpoint | Front Panel Current Limit Setpoint; Front Panel Base Load Command | Front Panel Base Load Command; Front Panel Base Load Setpoint | Front Panel Base Load Setpoint; Differential to Start | Differential to Start; Differential to Stop | Differential to Stop; Setpoint Source | Setpoint Source; Chilled Water Reset | Chilled Water Reset
- Page 41: parsed=11, matched_expected=none, sample=Relay Output Status | 1A8选项四位继电器输出状态; Relay Output Status | 1A8选项四位继电器输出状态; Relay Output Status | 1A8选项四位继电器输出状态; Relay Output Status | 1A8选项四位继电器输出状态; Analog Input/Output Module | 1A17选项模拟输入/输出模块; Analog Input/Output Module | 1A17选项模拟输入/输出模块; Digital Switch Input Module | 1A18选项双LV开关量输入模块; Digital Switch Input Module | 1A18选项双LV开关量输入模块
- Page 45: parsed=1, matched_expected=External Chilled Water Setpoint, sample=External Chilled Water Setpoint | External Chilled Water Setpoint

## Findings

- This run isolates whether MiMo OCR text is good enough for a second-stage local parameter extractor.
- Compare this report against the local GLM-OCR -> gemma run and the DeepSeek doc-level baseline.
