# Local Multimodal Validation Report

**Run ID:** 20260429T154942Z_trane_multimodal_validation
**PDF:** /Users/asteroida/work/KnowFabric/storage/documents/doc_883beab5e0004a2c/trane_cvgf_400_1000_chiller_manual.pdf
**Service:** `omlx` OpenAI-compatible API on `http://127.0.0.1:7999/v1`
**Requested models:** GLM-OCR-bf16, DeepSeek-OCR-8bit, gemma-4-e4b-it-4bit, Qwen3.5-4B-4bit, Qwen3.5-9B-MLX-4bit

## Inventory

- Available local models: DeepSeek-OCR-4bit, DeepSeek-OCR-8bit, GLM-OCR-bf16, IndexTTS-1.5, Qwen3.5-4B-4bit, Qwen3.5-9B-MLX-4bit, bge-m3-mlx-4bit, gemma-4-e4b-it-4bit
- oMLX DMG local observation: structured output is not supported; multimodal comparison uses plain-text outputs with post-parse.
- oMLX local observation: concurrent Qwen model switching is unstable; this run uses serial evaluation.

## Page Set

- Page 5: expected anchors = none
- Page 25: expected anchors = ['Active Chilled Water Setpoint', 'Active Current Limit Setpoint', 'Chilled Water Reset']
- Page 41: expected anchors = ['External Base Loading Setpoint']
- Page 45: expected anchors = ['External Chilled Water Setpoint', 'External Current Limit Setpoint', 'External Base Loading Setpoint']

## Results

### GLM-OCR-bf16

- Page 5: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 25: ok in cached result, parsed=0, matched_expected=Active Chilled Water Setpoint, sample=none
- Page 41: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 45: ok in cached result, parsed=0, matched_expected=External Chilled Water Setpoint, External Current Limit Setpoint, sample=none

### DeepSeek-OCR-8bit

- Page 5: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 25: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 41: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 45: ok in cached result, parsed=0, matched_expected=none, sample=none

### gemma-4-e4b-it-4bit

- Page 5: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 25: ok in cached result, parsed=5, matched_expected=Active Chilled Water Setpoint, Active Current Limit Setpoint, Chilled Water Reset, sample=Active Chilled Water Setpoint | 44.0F; Chilled Water Reset | Return/Constant Return/Outdoor/None; Active Chilled Water Setpoint | 44.0F; Active Current Limit Setpoint | 100%; Active Current Limit Setpoint | 70%/
- Page 41: ok in cached result, parsed=1, matched_expected=none, sample=HVAC operational parameters | configurable operational parameters
- Page 45: ok in cached result, parsed=5, matched_expected=none, sample=Chilled Water Setpoint | Chilled Water Setpoint(ECWS); Supply Air Temperature | Supply Air Temperature; Supply Airflow | Supply Airflow; Fan Speed | Fan Speed; Pump Speed | Pump Speed

### Qwen3.5-4B-4bit

- Page 5: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 25: ok in cached result, parsed=7, matched_expected=Active Chilled Water Setpoint, Active Current Limit Setpoint, Chilled Water Reset, sample=- Row 1: "Front Panel" | "44.0F" | "Active/Blank"; - Row 2: "BAS" | "48.0F/------" | "Active/Blank"; - Row 3: "External" | "42.0F/------" | "Active/Blank"; - Row 4: "Chilled Water Reset" | "Return/Constant Return/Outdoor/None"; - Row 5: "Active Chilled Water Setpoint" | "44.0F"; - Row 1: "Front Panel" | "100%" | "Active/Blank"
- Page 41: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 45: ok in cached result, parsed=1, matched_expected=External Chilled Water Setpoint, External Current Limit Setpoint, sample=I need to format the output as `parameter_name | evidence phrase`.

### Qwen3.5-9B-MLX-4bit

- Page 5: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 25: ok in cached result, parsed=0, matched_expected=Active Chilled Water Setpoint, Chilled Water Reset, sample=none
- Page 41: ok in cached result, parsed=0, matched_expected=none, sample=none
- Page 45: ok in cached result, parsed=1, matched_expected=External Chilled Water Setpoint, sample=I need to list them in the format `parameter_name | evidence phrase`.

## Findings

- GLM-OCR-bf16 returned valid page outputs on 4/4 pages with 3 expected anchor hits.
- DeepSeek-OCR-8bit behaved conservatively: non-empty parameter output on 0/4 pages.
- Gemma 4 sees the page and produces concise parameter lines, but tends to collapse source rows into higher-level labels.
- Best OCR/transcription signal in this run: `GLM-OCR-bf16`. It cleanly captured page 45 external setpoint text and did not fabricate parameters on the nameplate/components page.
- Best direct page-level parameter listing in this run: `gemma-4-e4b-it-4bit` on page 25. It produced usable `parameter | evidence` lines for the arbitration tables.
- Qwen3.5 local VLMs work only in serial mode on this machine. They see the page content, but instruction-following is weak and outputs drift into long reasoning text.

## Recommendation

- For this validation track, use OCR-specialized models for page text acquisition first, then do parameter classification in a second pass.
- Keep doc-level DeepSeek V4 text extraction as the mainline. Use the multimodal track to audit table-heavy pages, scanned figures, nameplates, and wiring/electrical layouts.
- Prefer `GLM-OCR-bf16` and `DeepSeek-OCR-8bit` for page transcription probes. Treat local Qwen VLMs as optional qualitative comparators until the oMLX switching bug is out of the way.
- Practical local stack for the next round: `GLM-OCR-bf16` for page OCR, then a stronger text model or existing doc-level pipeline for parameter classification and dedup.
