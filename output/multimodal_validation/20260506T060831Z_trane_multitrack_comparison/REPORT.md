# Trane Parameter Extraction Three-Track Comparison

**Run ID:** 20260506T060831Z_trane_multitrack_comparison
**DeepSeek doc-level:** /Users/asteroida/work/KnowFabric/output/parameter_spec_vertical/20260429T145634Z_trane_cvgf_400_1000_chiller_manual_parameter_spec_v4_pro_judge/candidates_llm_verified.jsonl
**Local GLM-OCR -> gemma:** /Users/asteroida/work/KnowFabric-qwen-vl-validate/output/multimodal_validation/20260506T060537Z_trane_ocr_text_validation/summary.json
**Remote MiMo OCR -> gemma:** /Users/asteroida/work/KnowFabric-qwen-vl-validate/output/multimodal_validation/20260506T060754Z_trane_remote_mimo_ocr_text_validation/summary.json

## Per-page comparison

### Page 25

- DeepSeek doc-level: 0
- Local GLM-OCR -> gemma: 3
- Remote MiMo OCR -> gemma: 2
- Three-way overlap: 0

**DeepSeek only:** none

**Local only:** active chilled water setpoint arbitration, dynamic current limit setpoint

**Remote only:** active current limit setpoint

**Three-way overlap:** none

### Page 29

- DeepSeek doc-level: 13
- Local GLM-OCR -> gemma: 14
- Remote MiMo OCR -> gemma: 17
- Three-way overlap: 7

**DeepSeek only:** none

**Local only:** base load command, base load setpoint, chilled water setpoint temperature, current limit setpoint

**Remote only:** front panel base load command

**Three-way overlap:** differential to start, differential to stop, outdoor maximum reset, outdoor reset ratio, return maximum reset, return reset ratio, setpoint source

### Page 41

- DeepSeek doc-level: 0
- Local GLM-OCR -> gemma: 4
- Remote MiMo OCR -> gemma: 5
- Three-way overlap: 0

**DeepSeek only:** none

**Local only:** analog input/output, digital input

**Remote only:** analog input/output module, analog output, digital switch input module

**Three-way overlap:** none

### Page 45

- DeepSeek doc-level: 2
- Local GLM-OCR -> gemma: 2
- Remote MiMo OCR -> gemma: 1
- Three-way overlap: 1

**DeepSeek only:** none

**Local only:** none

**Remote only:** none

**Three-way overlap:** external chilled water setpoint

## Overall summary

- DeepSeek union: 13
- Local GLM-OCR -> gemma union: 23
- Remote MiMo OCR -> gemma union: 24
- DeepSeek ∩ Local: 9
- DeepSeek ∩ Remote: 13
- Local ∩ Remote: 15

## Quick take

- DeepSeek doc-level remains the highest-recall text-first baseline across the full manual.
- Local GLM-OCR -> gemma reflects what the local image-first stack can recover on selected pages.
- Remote MiMo OCR -> gemma tests whether a remote full-modal OCR source improves page-level parameter recovery.
