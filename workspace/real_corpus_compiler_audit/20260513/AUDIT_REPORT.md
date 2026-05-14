# Real Corpus Compiler Audit Report

- Date: 2026-05-13
- Run ID: `20260513T121944Z_hvac_doclevel_extraction_batch`
- Batch report: `output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/REPORT.md`
- Manifest: `workspace/real_corpus_compiler_audit/20260513/manifest.csv`

## Result Summary

| Document | Backend Status | Raw | Anchored | Final | Main Signal |
| --- | ---: | ---: | ---: | ---: | --- |
| AHRI 550/590-2023 I-P | ok | 20 | 20 | 8 | Good authority source, but some rejected items had overly broad evidence anchors. |
| ASHRAE Guideline 36-2021 | ok | 20 | 20 | 0 | Doc-level extraction misrouted the full guideline to `condenser_water_pump`; judge correctly rejected non-matching AHU/VAV sequence parameters. |
| Gree C-series centrifugal chiller manual | ok | 20 | 19 | 17 | Best first-pass result; Chinese OEM technical manual produced reviewable fault, parameter, performance, operation, and maintenance candidates. |

## Traceability Check

- Batch `summary.json` contains one `compiler_run` and three source manifest entries.
- Each backend `candidates.json` now carries:
  - `compiler_run.compiler_run_id`
  - per-source `source_manifest`
  - `candidate_entries`
- Each review pack manifest now carries:
  - `upstream_compiler_run`
  - `upstream_source_manifest`
  - per-pack `upstream_compiler_run_id`

This closes the provenance gap found during the run: earlier candidates had the run ID but not the source file hash. The script now writes source manifests into per-backend candidate payloads.

## Quality Findings

1. AHRI 550/590 is a strong source, but the current anchoring can over-accept broad page ranges. Judge rejected examples where the evidence was only the standard title/page list rather than the exact table row.
2. Full-book G36 should not be run as one doc-level extraction target. It needs section-aware routing because one guideline spans AHU, VAV, fan coil, plant, and diagnostic logic.
3. The Gree manual is a good Chinese corpus seed. It produced high anchor and judge acceptance rates, and the accepted candidates are directly review-pack ready.
4. The current review-pack readiness correctly blocks all packs as `blocked_pending` until human review decisions are made. That is the expected state before apply.
5. GB 19577-2024 remains a real corpus gap. Do not use the obsolete GB 19577-2004 copy as current authority evidence.

## Recommendation

Proceed with manual review on two packs first:

1. `AHRI 550/590-2023 I-P`: review 8 accepted parameter specs and check table-level evidence precision.
2. `Gree C-series centrifugal chiller manual`: review 17 accepted Chinese OEM candidates and use it as the first domestic-language quality benchmark.

Do not apply G36 from this run. Re-run G36 later through section-aware extraction with explicit AHU/VAV section targets.
