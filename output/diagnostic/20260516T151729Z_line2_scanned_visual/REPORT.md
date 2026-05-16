# Line 2 Scanned Visual Extraction Report

Run root: `output/diagnostic/20260516T151729Z_line2_scanned_visual`

## Smoke
- Smoke ran 3 scanned docs: McQuay WSC/WDC/WCC chiller, Midea/Clivet AHU, Mitsubishi ETW high-temperature water-source heat pump.
- Manifest had no `scanned` ASHRAE/Standard rows, so the third smoke used the ETW scanned heat-pump manual instead of ASHRAE.
- Smoke output: 56 + 47 + 16 candidates = 119.
- Schema was compatible after normalization: `parameter_name`, value/range/unit, evidence_quote, publisher/citation all present in review packs.

## Visual Extraction
- Docs processed: 93; docs with candidates: 84; failed docs: 0.
- Pages: 2042 total, 2005 ok, 37 page-level failures.
- Raw verified candidates: 4743; accepted review-pack candidates: 4610 across 80 packs.
- MiMo token usage: 5,081,119 total (4,573,390 input / 507,729 output), cap 150,000,000.
- `visual_unreachable.csv` has no failed-document rows; page-level parse failures are in `visual_page_failures.csv`.

## Apply / KO Growth
| ontology_class_id | pre_total | post_total | net | pre_cross_pub | post_cross_pub | delta_cross_pub | max_layers |
|---|---:|---:|---:|---:|---:|---:|---:|
| ahu | 745 | 920 | 175 | 9 | 43 | 34 | 8 |
| air_cooled_modular_heat_pump | 77 | 201 | 124 | 1 | 5 | 4 | 8 |
| centrifugal_chiller | 4987 | 5853 | 866 | 18 | 64 | 46 | 8 |
| magnetic_bearing_chiller | 12 | 28 | 16 | 0 | 0 | 0 | 2 |
| screw_chiller | 280 | 1003 | 723 | 20 | 128 | 108 | 8 |
| water_source_heat_pump | 100 | 399 | 299 | 2 | 32 | 30 | 8 |

Notes: apply was serial at DB write points. Two pure performance fixes were needed during apply: batch canonical registry writes and large-N complete-linkage without Python bigint bitmasks. Both preserve clustering semantics.

## Consensus State
| ontology_class_id | agreed | partial_conflict | material_conflict |
|---|---:|---:|---:|
| ahu | 5 | 3 | 35 |
| air_cooled_modular_heat_pump | 0 | 1 | 4 |
| centrifugal_chiller | 15 | 15 | 34 |
| screw_chiller | 16 | 13 | 99 |
| water_source_heat_pump | 6 | 4 | 22 |

## Guards
- visual_anchor: 0
- total_ko: 9981
- degenerate: 0
- prefix_mismatch: 0
- Oracle: PASS (`scripts/verify_cross_publisher_merge.py --skip-precheck`).
- pytest: PASS, 427 passed.
- gates: PASS, 4/4 via `bash scripts/check-all`.

## Visual Evidence Anchor
- `visual_evidence_anchor` rows: 0. The anchor chain is not connected for this visual parameter path yet; evidence was persisted through `knowledge_object_evidence` using synthetic visual page chunks (`visual_page_<doc_id>_<page_no>`).

## Cross-Language / Publisher Notes
- Cross-publisher growth is strong in scanned-heavy domains: AHU +34, screw +108, water-source +30, centrifugal +46.
- Some visual packs inherit missing publisher as `unknown` from source metadata; those are retained as-is and should be cleaned at manifest/source metadata level, not by merger rules.
- `material_conflict_sample10_line2.csv` contains 10 high-layer material-conflict KOs for operator audit. I did not overwrite verdicts; `human_audit_verdict` is blank.

## Backups
- `/tmp/line2_pre_apply_accepted_20260516T170917Z.sql`
- `/tmp/line2_pre_centrifugal_parameter_largeN_fix_20260516T182614Z.sql`
- `/tmp/line2_pre_centrifugal_parameter_retry_20260516T181930Z.sql`
- `/tmp/line2_pre_continue_after_sparse_clustering_20260516T180633Z.sql`
- `/tmp/line2_pre_full_visual_extract_20260516T152731Z.sql`
- `/tmp/line2_pre_remaining_apply_after_registry_fix_20260516T173616Z.sql`
- `/tmp/line2_pre_small_remaining_apply_20260516T181619Z.sql`
- `/tmp/line2_pre_smoke_20260516T151718Z.sql`

## Code Diff Summary
- MiMo visual calls now use `RateLimitedClient` with `LLM_MAX_*_MIMO` knobs.
- `run_visual_parameter_batch.py` supports manifest-driven scanned import/extraction and creates synthetic visual chunks for review-pack FK integrity.
- `cluster_by_cosine` keeps complete-linkage semantics but uses sparse eligible-pair iteration and a large-N path without bigint row masks.
- canonical-key registry writes are batched per grouping call to avoid O(N * registry-size) YAML rewrites.

## Review Pipeline Stats
- `scripts/summarize_review_pipeline_stats.py` was exercised against a representative visual review-pack directory and wrote `review_pipeline_stats_sample.json` successfully.
- Aggregate visual pack counts are reported directly from all 80 discovered review packs: 4610 accepted / 0 pending / 0 rejected.

## Over-Merge Spot Check
- The 10 sampled material-conflict KOs are dominated by same-concept, different-model/value conflicts (e.g. 制冷量, 运行重量, 启动电流, 制冷剂), not obvious facet/subsystem mixes.
- Quick engineering spot-check: 0/10 obvious over-merge. Formal `human_audit_verdict` remains blank in CSV for operator review.
