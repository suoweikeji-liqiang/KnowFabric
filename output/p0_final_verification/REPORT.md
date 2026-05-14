# P0 Final Verification Report

## 1) Oracle output

Command:

```bash
cd /Users/asteroida/work/KnowFabric
rm -rf /tmp/knowfabric_embedding_cache
set -a && source .env && source .env.llm.local && set +a
OMLX_API_KEY=<redacted> venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
```

Result:

```text
RESULT: PASS ✓ — Cross-publisher merge plumbing verified end-to-end.
```

Key facts from the passing run:
- total KOs created: `3`
- oil pressure merged: `hvac:e2e_test_chiller:parameter:key_a300dd0250`
- chilled water merged: `hvac:e2e_test_chiller:parameter:chilled_water_leaving_temperature`

## 2) Main DB restore + regroup verification

### Safety backup

Before touching `knowfabric`, I created:

```text
/tmp/pre_h3_restore_20260511T160623Z.sql
```

Before regrouping the restored main DB, I created:

```text
/tmp/h3_main_before_regroup_20260511T161223Z.sql
```

### Restore target requested by operator

Restored file:

```text
/tmp/h3_pre_rerun_20260511T.sql
```

### Actual baseline SQL after restoring `/tmp/h3_pre_rerun_20260511T.sql`

Operator-expected SQL:

```sql
SELECT COUNT(*)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller';
```

Actual result on this machine:

```text
6
```

Additional validation:

```sql
SELECT COUNT(*)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller'
  AND knowledge_object_type='parameter_spec';
```

Result:

```text
6
```

So the restored `/tmp/h3_pre_rerun_20260511T.sql` file is **not** the 56-KO baseline described in the operator prompt, even though it does contain many Carrier-related source references in raw dump text.

### Regroup on restored main DB

Command:

```bash
set -a && source .env && source .env.llm.local && set +a
OMLX_API_KEY=<redacted> venv/bin/python scripts/regroup_chiller_domain.py
```

Result:

```text
stats: {new_merged: 0, updated_existing: 6, merged_existing: 0, material_conflicts: 0}
```

Cross-publisher SQL:

```sql
SELECT canonical_key,
       jsonb_array_length((authority_summary_json::jsonb)->'layers') AS n_layers,
       (SELECT array_agg(DISTINCT layer->>'publisher' ORDER BY layer->>'publisher')
          FROM jsonb_array_elements((authority_summary_json::jsonb)->'layers') layer) AS pubs
FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
  AND knowledge_object_type='parameter_spec'
  AND (SELECT COUNT(DISTINCT layer->>'publisher')
         FROM jsonb_array_elements((authority_summary_json::jsonb)->'layers') layer) >= 2
ORDER BY n_layers DESC;
```

Actual result:

```text
hvac:centrifugal_chiller:parameter:motor_current_limit | 2 | {Carrier,Trane}
```

Main DB hard-metric outcome:

- cross-publisher KOs: `1`
- total chiller parameter_spec KOs: `6`
- Trane+Carrier true merge: **present** (`motor_current_limit`)
- Trane+McQuay true merge: **not present**
- no super-KO on this specific restored-main snapshot

Conclusion on main DB:

- the P0 plumbing fix works enough to recover **at least one real cross-publisher merge**
- but the operator-specified restore file on this machine is **already a late collapsed 6-KO snapshot**, not the required 56-KO H3 baseline

### Rich-backup probe on `/tmp/m1_pre_regroup_20260511T.sql`

Because `/tmp/h3_pre_rerun_20260511T.sql` did not match the stated baseline, I also verified the fix on a richer pre-regroup dump in a temp DB:

```text
/tmp/m1_pre_regroup_20260511T.sql
```

Temp safety backup before regroup:

```text
/tmp/m1_probe_before_regroup_20260511T161030Z.sql
```

Pre-regroup counts in temp DB:

```text
total chiller parameter_spec KOs = 114
Carrier 19XR KOs                = 60
```

After regroup:

```text
stats: {new_merged: 0, updated_existing: 3, merged_existing: 1, material_conflicts: 0}
```

Post-regroup outcome:

```text
consensus = multi_facet 1 / single_source 3
cross-publisher KOs = 1
largest cross-publisher KO:
hvac:centrifugal_chiller:parameter:chilled_water_entering_temperature_maximum
layers = 111
publishers = {Carrier,McQuay,Trane}
```

This fails the operator hard metrics:

- cross-publisher KOs `< 3`
- total KO count collapses to `4`
- super-KO exists (`111` layers > `10`)

Failure trace artifacts:

```text
/Users/asteroida/work/KnowFabric/output/diagnostic/20260511T161057Z/merger_input.jsonl
/Users/asteroida/work/KnowFabric/output/diagnostic/20260511T142653Z/n3_llm_refinement_trace.jsonl
```

The latest merger input trace shows:

```text
existing_count = 114
by_doc_existing = {
  doc_55e5ec4e4ee84e9a: 60,
  doc_36640e9f378f4667: 20,
  doc_7c4fca116fd3420a: 10,
  doc_883beab5e0004a2c: 24
}
```

The earlier LLM refinement trace captures the bad mega-cluster behavior directly:

```text
cluster_size = 105
cluster_members include both:
- Carrier: Motor Load Activation Demand Limit / Bearing temperature alarm limit / ...
- Trane: 外部冷冻水设定范围上限 / 启动限制最低油温 / ...
- McQuay: 最低冷冻水出水温度 / 冷冻水最高进水温度 / ...
```

So the current state is:

- **P0 plumbing bug fixed** and oracle-proven
- but on a rich persisted regroup backup, there is still another production regroup failure mode beyond the original plumbing bug

## 3) Actual code change

Changed file:
- `/Users/asteroida/work/KnowFabric/packages/compiler/cross_source_merger.py`

3-line summary:
1. Added `_ko_to_candidates(...)` to expand an existing KO into per-evidence/per-source candidates instead of a single flattened candidate.
2. Added `_source_name_from_evidence(...)` to recover a usable parameter name from evidence text when regrouping existing KOs.
3. Changed `merge_with_existing(...)` to index existing names from expanded candidates, not just `structured_payload_json.parameter_name` of the KO row.

## 4) Why the previous 12 rounds missed it

They were validating the **new-candidate apply path** only.

The real plumbing bug on the production regroup path is:
- `existing KO -> _ko_to_candidate -> merge_with_existing`
- `_ko_to_candidate(...)` kept only the `first_layer` authority metadata and one representative `parameter_name`
- so regroup silently threw away multi-layer source identity before `group_and_normalize(...)` ever saw it

That is why oracle-style direct grouping could look correct while regrouping persisted KOs still behaved incorrectly.

## 5) Test / gate status

- `venv/bin/pytest tests/` → `314 passed`
- `bash scripts/check-all` → `✓ All quality gates passed`

## 6) Environment note

A temp sandbox replay against `knowfabric_sandbox_tmp` confirmed the local artifact set on disk is inconsistent with the prompt's described main DB baseline. The prompt expects a pre-existing ~56-KO chiller state; the available restored local main DB snapshot is already collapsed to 6 KOs, which is why the SQL hard target cannot be reproduced verbatim on this snapshot alone.

## 7) 2026-05-14 Gree 17 + AHRI 8 production apply attempt

### Inputs

- Gree source: `output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0003_格力_c系列离心式冷水机组技术手册_69页/deepseek-parameter-spec/candidates.json`
- AHRI source: `output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0001_ansi_ahri_standard_550_590_2023_i_p_editorial_update/deepseek-parameter-spec/candidates.json`
- Note: these audit files were absent from the current worktree at session start and were copied from sibling worktree `KnowFabric-compiler-hardening` without rerunning extraction.

### Safety backups

- `/tmp/q1_pre_gree_clean_retry_20260514T043828Z.sql`
- `/tmp/q2_pre_regroup_after_namefix_20260514T043917Z.sql`
- `/tmp/q3_pre_ahri_20260514T044028Z.sql`
- `/tmp/q2_pre_regroup_after_ahri_20260514T044042Z.sql`

Additional polluted-state backups and diagnostics were created while isolating apply/regroup defects:

- `/tmp/q2_polluted_pre_restore_20260514T043718Z.sql`
- `output/diagnostic/20260514T043338Z_q1_gree_bad_apply/`
- `output/diagnostic/20260514T043556Z_q2_regroup_no_gree_publisher/`

### Code defects found and fixed during the attempt

1. `apply_review_packs_batch.py` forced a mixed-type review pack through the first accepted candidate's `knowledge_object_type`, misclassifying Gree parameter/performance/sequence/maintenance candidates as `fault_code`.
2. `build_manual_fixture_from_review_candidates.py` dropped curated `publisher` / `citation`, preventing Gree from counting as a cross-publisher layer.
3. `cross_source_merger._ko_to_candidates()` used noisy evidence first lines as regroup names, renaming existing parameter KOs incorrectly during regroup.
4. `summarize_review_pipeline_stats.py` counted `applied_merger` correctly at overall level but not document level.

### Final production DB result after clean restore, fixed apply, AHRI Q3, and regroup

Gree apply:

```text
accepted_count = 17
status = applied_merger
merger_stats = {new_merged: 6, updated_existing: 4, material_conflicts: 3, groups_processed: 5}
```

AHRI apply with applicability option B:

```text
accepted_count = 8
applicability.equipment_classes = [centrifugal_chiller, screw_chiller, scroll_chiller, reciprocating_chiller]
status = applied_merger
merger_stats = {new_merged: 2, updated_existing: 5, material_conflicts: 1, groups_processed: 1}
```

Final regroup:

```text
stats: {new_merged: 0, updated_existing: 7, merged_existing: 0, material_conflicts: 0}
```

Final SQL hard-metric snapshot:

```text
cross_publisher_count = 2
gree_cross_count = 1
super_ko = 0
max_layers = 7
total_chiller = 13
```

Cross-publisher KOs:

```text
hvac:centrifugal_chiller:parameter:key_52a46b11d3
title = 油箱温度控制
layers = 4
publishers = {Gree, Trane}
consensus_state = agreed

hvac:centrifugal_chiller:parameter:motor_current_limit
title = Motor Current Limit
layers = 2
publishers = {Carrier, Trane}
consensus_state = agreed
```

### Outcome

This run did **not** meet the requested hard metric:

- required cross-publisher KOs: `>= 3`; actual: `2`
- required Gree+other pairings: `>= 2`; actual: `1`
- required no super-KO: passed (`max_layers = 7`)
- required chiller KO count not inflated by >20: passed (`6 -> 13`)

No threshold tuning, YAML name-pair hardcoding, or LLM re-extraction was performed. The remaining gap appears to be semantic grouping/data coverage on the current 6-KO baseline: Gree oil temperature naturally merged with Trane; Gree oil pressure did not have a matching persisted non-Gree oil-pressure KO in this baseline, and AHRI standards did not add additional cross-publisher merges.

## 8) 2026-05-14 clean-slate chiller apply + regroup

### Run ID and safety artifacts

Run ID:

```text
20260514T051545Z_cleanslate_chiller
```

Primary diagnostic directory:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/
```

Pre-clean backup:

```text
/tmp/t1_pre_cleanslate_20260514T051545Z.sql
```

Pre-regroup backup:

```text
/tmp/t5_pre_regroup_cleanslate_20260514T052327Z.sql
```

The pre-clean SQL snapshot is stored at:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/t1_current_chiller_state.txt
```

### Clean-slate deletion

Deleted all existing `centrifugal_chiller` rows and evidence from the production DB:

```sql
DELETE FROM knowledge_object_evidence
WHERE knowledge_object_id IN (
  SELECT knowledge_object_id FROM knowledge_object
  WHERE ontology_class_id='centrifugal_chiller'
);

DELETE FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller';
```

Verification result:

```text
centrifugal_chiller KO count = 0
```

### Clean-slate apply manifest

Full machine-readable manifest:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/clean_slate_apply_manifest.json
```

Candidate sources used:

```text
Gree:
output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0003_格力_c系列离心式冷水机组技术手册_69页/deepseek-parameter-spec/candidates.json

AHRI:
output/real_corpus_audit/doclevel/20260513T121944Z_hvac_doclevel_extraction_batch/0001_ansi_ahri_standard_550_590_2023_i_p_editorial_update/deepseek-parameter-spec/candidates.json

Trane CVGF:
output/parameter_spec_vertical/20260506T085338Z_trane_cvgf_400_1000_chiller_manual_parameter_spec/candidates_llm_verified.jsonl

McQuay WSC/WDC/HSC/HDC:
output/w3_multisource_extraction/20260511T042453Z_hvac_doclevel_extraction_batch/0001_麦克维尔_wsc_wdc_hsc_hdc单_双压缩机离心式安装维护手册_49页_制冷百家网/deepseek-parameter-spec/candidates.json

McQuay single/double compressor:
output/w3_multisource_extraction/20260511T042453Z_hvac_doclevel_extraction_batch/0002_麦克维尔_单_双压缩机离心式冷水机组安装维修手册/deepseek-parameter-spec/candidates.json
```

Prepared review pack directories:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/gree/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/ahri/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/trane_cvgf/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/mcquay_wsc_wdc_hsc_hdc/review_packs
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_sources/mcquay_single_double/review_packs
```

Carrier 19XR/19XL status:

```text
missing_candidates
```

Only chunk task results were found under `output/chiller_visual_import`; no Carrier 19XR/19XL `candidates.json`, JSONL, or review bundle was present. Carrier was therefore excluded from this clean-slate run per the no-re-extraction constraint.

### Apply evolution

All writes were preceded by `pg_dump`. The detailed TSV is:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/apply_counts.tsv
```

Observed KO counts:

```text
Gree apply                         -> total chiller KO = 7
AHRI apply                         -> total chiller KO = 9
Trane apply                        -> total chiller KO = 26
McQuay WSC/WDC/HSC/HDC apply       -> total chiller KO = 25
McQuay single/double first attempt -> failed, total chiller KO = 25
McQuay single/double retry         -> total chiller KO = 24
```

The first McQuay single/double apply attempt exposed an evidence migration idempotency defect:

```text
duplicate key value violates unique constraint "uq_knowledge_object_evidence_ref"
```

Fixed in `packages/compiler/cross_source_merger.py` by preserving target evidence, dropping duplicate source evidence, and migrating only non-duplicate rows before deleting merged source KOs. This was an apply plumbing fix, not a grouping threshold or YAML-name intervention.

### Regroup result

Command:

```bash
venv/bin/python scripts/regroup_chiller_domain.py
```

Result:

```text
stats: {'new_merged': 0, 'updated_existing': 15, 'merged_existing': 1, 'material_conflicts': 1}
```

Final hard metrics:

```text
total_chiller_ko = 22
cross_publisher_ko = 2
gree_other_ko = 1
max_layers = 7
```

Cross-publisher KOs:

```text
hvac:centrifugal_chiller:parameter:key_52a46b11d3
layers = 5
publishers = {Gree, Trane}
consensus_state = agreed

hvac:centrifugal_chiller:parameter:key_1f4206db93
layers = 2
publishers = {McQuay, Trane}
consensus_state = agreed
```

### Clean-slate outcome

This run did **not** meet the requested hard metric:

- required cross-publisher KOs: `>= 3`; actual: `2`
- required Gree+other pairings: `>= 2`; actual: `1`
- required at least one Gree+Trane or Gree+Carrier pairing: passed via Gree+Trane oil temperature
- required max layers `<= 8`: passed (`7`)
- required total chiller KO not `> 100`: passed (`22`)

Failure trace:

```text
output/diagnostic/20260514T051545Z_cleanslate_chiller/cleanslate_grouping_trace.jsonl
```

Working hypothesis for operator review:

- Carrier 19XR was absent, so the intended Carrier-side oil concepts could not participate.
- Gree+Trane oil temperature did merge naturally.
- Trane+McQuay produced one additional cross-publisher merge.
- Gree oil-pressure remained Gree-only after clean-slate regroup despite no super-KO, so the remaining gap appears to be semantic/data coverage for the available non-Carrier candidate set rather than historical DB pollution.

No LLM re-extraction, threshold tuning, YAML name-pair hardcoding, or oracle script changes were performed.

### Verification commands after clean-slate run

```text
venv/bin/python -m pytest tests/test_review_pipeline_stats.py::test_summarize_review_pipeline_stats_combines_candidates_packs_and_apply -q
1 passed

venv/bin/python -m pytest tests -q
336 passed

bash scripts/check-all
All quality gates passed
```
