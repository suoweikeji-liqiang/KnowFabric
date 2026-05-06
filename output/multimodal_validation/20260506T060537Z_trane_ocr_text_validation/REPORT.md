# Local OCR->Text Validation Report

**Run ID:** 20260506T060537Z_trane_ocr_text_validation
**OCR model:** GLM-OCR-bf16
**Text models:** gemma-4-e4b-it-4bit
**Pages:** [25, 29, 41, 45]

## Results

### gemma-4-e4b-it-4bit

- Page 25: parsed=3, matched_expected=Active Chilled Water Setpoint, Active Current Limit Setpoint, sample=Active Chilled Water Setpoint Arbitration |动态冷冻水温度设定(Active Chilled Water Setpoint Arbitration); Active Chilled Water Setpoint |冷冻水重置状态(Active Chilled Water Setpoint); dynamic current limit setpoint |动态电流限制设定(active current limit setpoint)
- Page 29: parsed=14, matched_expected=Differential to Start, Differential to Stop, Setpoint Source, Chilled Water Reset, sample=Chilled Water Setpoint Temperature |前端面板冷冻水设定; Current Limit Setpoint |前端面板电流限制设定; Base Load Command |前端面板基本负荷要求; Base Load Setpoint |前端面板基本负荷设定; Differential to Start |前端面板基本负荷要求; Differential to Stop |
- Page 41: parsed=15, matched_expected=none, sample=Relay Output Status | OPST 线手器#1; Relay Output Status | OPST 线手器#2; Relay Output Status | OPST 继电器#3; Relay Output Status | OPST 线手器#4; Analog Input/Output | EXOP 信号#1 外部基本负荷设定输入; Analog Input/Output | EXOP 信号#2 制冷剂监视器输入
- Page 45: parsed=4, matched_expected=External Chilled Water Setpoint, External Current Limit Setpoint, sample=External Chilled Water Setpoint | External Chilled Water Setpoint(ECWS); External Chilled Water Setpoint | 可对冷冻水的设定在远程进行修改。; External Current Limit Setpoint | External Current Limit Setpoint; External Current Limit Setpoint | 选项运行远程调整电流限制设定值。

## Findings

- This run isolates whether local models fail because of image understanding or because of parameter classification/instruction following.
- If a text model succeeds here but failed in the image-first run, the bottleneck was image-side control, not text extraction logic.
