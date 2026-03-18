# Scripts

Utility scripts and quality gate checks.

## Quality Gates

- `check-docs` - Verify documentation completeness
- `check-boundaries` - Verify module boundaries
- `check-forbidden-deps` - Check for forbidden dependencies
- `check-all` - Run all quality checks

## Utilities

- Database migration scripts
- Data import/export utilities
- Development helpers
- `validate_domain_package_v2.py` - Validate rebuild-track ontology packages
- `sync_ontology_package_v2.py` - Sync ontology package metadata into additive rebuild tables
- `seed_manual_validation_fixtures.py` - Seed chunk anchors and semantic knowledge objects from manual validation fixtures
- `generate_chunk_backfill_candidates.py` - Generate review JSON candidates from existing chunk rows and synced ontology metadata
- `build_review_scaffold_from_candidates.py` - Turn candidate JSON into a review-ready scaffold with curation placeholders
- `build_review_packs_from_candidates.py` - Split candidate JSON into smaller review packs grouped by doc_id and equipment_class_id
- `build_manual_fixture_from_review_candidates.py` - Convert accepted review candidates into a manual fixture JSON that the existing backfill path can consume
- `bootstrap_review_pack_curation.py` - Fill obvious empty curation fields in a review pack with editable draft values
- `bootstrap_review_packs_batch.py` - Batch-bootstrap a review pack directory into editable draft copies with a report
- `check_review_pack_readiness.py` - Validate review packs before batch apply and report which ones are ready, pending, rejected-only, or invalid
- `apply_review_packs_batch.py` - Batch-apply fully reviewed packs, generate fixture JSON files, and emit a success/skip/failure report
- `summarize_review_pipeline_stats.py` - Summarize candidate hit rate, review decisions, and batch-apply outcomes by doc and review pack
- `export_review_pipeline_artifacts.py` - Export candidates, review packs, stats, and an artifact manifest for one scoped review bundle
- `print_review_pipeline_summary.py` - Render review pipeline stats as a terminal-friendly summary
- `prepare_review_pipeline_bundle.py` - One-shot prepare a full review bundle: export, bootstrap, readiness-check, stats, and summary text
- `apply_ready_review_bundle.py` - Apply only ready packs from a prepared bundle and refresh apply report, stats, and summary text
- `backfill_manual_knowledge_from_chunks.py` - Backfill chunk anchors and semantic knowledge objects from existing chunk rows plus manual fixtures

## Usage

```bash
# Run quality gates
npm run check:all

# Run specific gate
npm run check:boundaries
```

See [Quality Gates](../docs/06_quality-gates.md) for details.

## Chunk Review Flow

```bash
# 1. Generate chunk-backed candidates
python3 scripts/generate_chunk_backfill_candidates.py hvac --doc-id <doc_id> --equipment-class-id <equipment_class_id> --output candidates.json

# Recommended shortcut: prepare a full review bundle in one command
python3 scripts/prepare_review_pipeline_bundle.py hvac review_bundle --doc-id <doc_id> --equipment-class-id <equipment_class_id>

# After editing bootstrapped packs, apply only the packs that are ready
python3 scripts/apply_ready_review_bundle.py review_bundle

# 2. Build review packs from those candidates
python3 scripts/build_review_packs_from_candidates.py candidates.json review_packs

# 3. Review one pack file in review_packs/

# 4. Convert accepted entries into a manual fixture
python3 scripts/build_manual_fixture_from_review_candidates.py review_packs/<pack_file>.json --output reviewed_fixture.json

# 5. Backfill semantic rows from the reviewed fixture
python3 scripts/backfill_manual_knowledge_from_chunks.py reviewed_fixture.json

# Optional: bootstrap empty curation fields in one pack before review/apply
python3 scripts/bootstrap_review_pack_curation.py review_packs/<pack_file>.json --output review_packs/<pack_file>.json

# Optional: bootstrap an entire review pack directory into editable draft copies
python3 scripts/bootstrap_review_packs_batch.py review_packs

# 6. Check which review packs are actually ready for apply
python3 scripts/check_review_pack_readiness.py review_packs

# 7. Or batch-apply all fully reviewed packs in one directory
python3 scripts/apply_review_packs_batch.py review_packs

# 8. Summarize pipeline stats across candidates, review packs, and apply report
python3 scripts/summarize_review_pipeline_stats.py --candidate-file candidates.json --pack-dir review_packs

# Or export a ready-to-review artifact bundle in one command
python3 scripts/export_review_pipeline_artifacts.py hvac review_bundle --doc-id <doc_id> --equipment-class-id <equipment_class_id>

# Print a terminal-friendly summary from exported stats
python3 scripts/print_review_pipeline_summary.py --stats-file review_bundle/review_pipeline_stats.json
```
