# Local OCR->Text Validation Report

**Run ID:** 20260430T010658Z_trane_ocr_text_validation
**OCR model:** GLM-OCR-bf16
**Text models:** gemma-4-e4b-it-4bit
**Pages:** [5, 29, 45]

## Results

### gemma-4-e4b-it-4bit

- Page 5: parsed=0, matched_expected=none, sample=none
- Page 29: parsed=14, matched_expected=Differential to Start, Differential to Stop, Setpoint Source, Chilled Water Reset, sample=Chilled Water Setpoint Temperature |前端面板冷冻水设定; Current Limit Setpoint |前端面板电流限制设定; Base Load Command |前端面板基本负荷要求; Base Load Setpoint |前端面板基本负荷设定; Differential to Start |前端面板基本负荷要求; Differential to Stop |
- Page 45: parsed=4, matched_expected=External Chilled Water Setpoint, External Current Limit Setpoint, sample=External Chilled Water Setpoint | External Chilled Water Setpoint(ECWS); External Chilled Water Setpoint | 可对冷冻水的设定在远程进行修改。; External Current Limit Setpoint | External Current Limit Setpoint; External Current Limit Setpoint | 选项运行远程调整电流限制设定值。

## Findings

- This run isolates whether local models fail because of image understanding or because of parameter classification/instruction following.
- If a text model succeeds here but failed in the image-first run, the bottleneck was image-side control, not text extraction logic.
