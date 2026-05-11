# HVAC Authority Batch Pipeline Report

- Run ID: `20260507T153658Z_hvac_authority_batch_pipeline`
- Mode: `execute`
- Manifest: `workspace/hvac_source_inventory/20260507T083207Z/starter_batch_manifest.csv`
- Output dir: `output/hvac_authority_batch_pipeline/20260507T153658Z_hvac_authority_batch_pipeline`

## Lane Counts

- g36_standard: 1
- standard_reference_hold: 7
- oem_text: 3
- visual_queue: 10

## Executed Commands

| Name | Status | Seconds |
|---|---|---:|
| `g36_0001_hvac系统高性能运行序列指南` | failed | 7166.172 |
| `oem_text_doclevel` | passed | 2368.476 |

## Notes

- `g36_standard` uses the existing ASHRAE G36 section-context extraction runner.
- `oem_text` uses document-level extraction plus model review.
- `standard_reference_hold` is intentionally held until a standard-specific extractor is selected.
- `visual_queue.csv` lists low-text/image-heavy PDFs for visual semantic validation.
