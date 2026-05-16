# Handoff: Rich-State Regroup Over-Grouping

## Current Task

Fix rich-state regroup over-grouping in KnowFabric chiller regroup.

Original symptom:

- 114-KO M1 chiller state regroup collapsed into 4 KOs.
- One super-KO had 111 layers:
  `hvac:centrifugal_chiller:parameter:chilled_water_entering_temperature_maximum`
- Super-KO contained unrelated names such as shuttle clearance and motor load demand limit.

## User Constraints

- Do not touch `scripts/verify_cross_publisher_merge.py`.
- Do not revert P0 plumbing fix in `packages/compiler/cross_source_merger.py`.
- Do not use YAML alias hacks.
- Must `pg_dump` before DB restore or bulk DB writes.
- Do not diagnose as data problem.
- If root cause is not A/B/C, report trace and hypothesis instead of random edits.

## Current State

P0 plumbing fix remains present and was not modified during this task:

- `packages/compiler/cross_source_merger.py` still has prior P0 changes:
  - `_ko_to_candidates`
  - `_source_name_from_evidence`
  - `_looks_like_parameter_name`
  - `merge_with_existing` expands existing KOs per evidence/source.

New rich-state fix is implemented in:

- `packages/compiler/canonical_key.py`
- `tests/test_canonical_key_embedding.py`

## Root Cause Determined

Root cause is A+B:

- A: raw embedding single-link clustering can produce a mega-cluster on rich 105/114-name data.
- B: N3 trust-embedding path bypassed E2 `_sanity_check_groups`, so the mega-cluster was directly trusted.

Evidence:

- Existing trace: `output/diagnostic/20260511T142653Z/n3_llm_refinement_trace.jsonl`
- It contains `cluster_size = 105` with unrelated names.
- Local replay against that trace:
  - raw clustering: `raw 1 [105]`
  - new refined clustering: `refined 44`, max cluster size `7`

## Implemented Fix

In `packages/compiler/canonical_key.py`:

- Added `EMBEDDING_RECLUSTER_MAX_SIZE = 8`.
- Added `_tighten_oversize_embedding_clusters(...)`.
- Added `_dump_embedding_cluster_trace(...)`.

`_group_via_embedding(...)` now:

1. Calls `cluster_by_cosine(...)` to get `raw_clusters`.
2. Tightens only clusters with size `> MAX_GROUP_SIZE`.
3. Leaves normal small clusters unchanged.
4. Dumps raw and refined clusters when `KNOWFABRIC_DUMP_CLUSTER_TRACE=1`.

Important behavior:

- Small P0 oracle clusters are unaffected.
- Oversized rich-state clusters are recursively reclustered with stricter thresholds.
- If recursive clustering still returns a group `> MAX_GROUP_SIZE`, it is split into singletons as a final guard.

## Tests Added

In `tests/test_canonical_key_embedding.py`:

- Added `test_oversize_embedding_cluster_is_tightened`.
- Confirms oversized embedding clusters call recursive tightening with:
  - threshold raised from `0.78` to about `0.83`
  - max size `8`

## Verification Completed

P0 oracle:

```bash
rm -rf /tmp/knowfabric_embedding_cache
set -a && source .env && source .env.llm.local && set +a
OMLX_API_KEY=4496 venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
```

Result:

- `RESULT: PASS`
- 3 KOs created
- Oil pressure cross-brand merged
- Chilled water Trane+McQuay cross-brand merged

Targeted tests:

```bash
venv/bin/pytest tests/test_canonical_key_embedding.py tests/test_canonical_key_batching.py tests/test_clustering.py tests/test_cross_source_merger.py
```

Result:

- `30 passed`

Full tests:

```bash
venv/bin/pytest tests/
```

Result:

- `315 passed, 46 warnings`

Quality gates:

```bash
PATH=/opt/homebrew/Cellar/postgresql@17/17.9/bin:$PATH bash scripts/check-all
```

Result:

- all quality gates passed

## Database And Backup State

Current DB:

```sql
SELECT COUNT(*) FROM knowledge_object WHERE ontology_class_id='centrifugal_chiller';
-- 6

SELECT COALESCE(MAX(jsonb_array_length(authority_summary_json::jsonb->'layers')),0)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller';
-- 2
```

Safety backup created:

- `/tmp/pre_overgroup_current_20260512T142226Z.sql`
- Size: about 125 MB

Earlier safety backup also exists:

- `/private/tmp/pre_overgroup_restore_20260512T140520Z.sql`
- Size: about 125 MB

PostgreSQL client note:

- `psql` is not in default PATH.
- Use `/opt/homebrew/Cellar/postgresql@17/17.9/bin`.
- Server is PostgreSQL 17.9, so use `pg_dump` from `postgresql@17`.
- Using `pg_dump` from `postgresql@16` fails with server version mismatch.

## Blocker

M1 restore/regroup validation could not be completed because expected dump is missing:

- `/tmp/m1_pre_regroup_20260511T.sql` does not exist.
- `/private/tmp/m1_pre_regroup_20260511T.sql` does not exist.

Searches performed:

- `/private/tmp`
- `/tmp`
- `/Users/asteroida`
- Desktop / Downloads / Documents
- Trash
- large `.sql`, `.dump`, `.backup` files

Only relevant SQL found:

- `/private/tmp/pre_overgroup_restore_20260512T140520Z.sql`
- `/tmp/pre_overgroup_current_20260512T142226Z.sql`

## Still To Do When M1 Dump Is Restored

Once `/tmp/m1_pre_regroup_20260511T.sql` is available:

1. Back up current DB again:

```bash
PATH=/opt/homebrew/Cellar/postgresql@17/17.9/bin:$PATH \
pg_dump knowfabric > /tmp/pre_m1_regroup_$(date -u +%Y%m%dT%H%M%SZ).sql
```

2. Restore M1:

```bash
PATH=/opt/homebrew/Cellar/postgresql@17/17.9/bin:$PATH dropdb knowfabric
PATH=/opt/homebrew/Cellar/postgresql@17/17.9/bin:$PATH createdb knowfabric
PATH=/opt/homebrew/Cellar/postgresql@17/17.9/bin:$PATH psql knowfabric < /tmp/m1_pre_regroup_20260511T.sql
```

3. Run regroup with trace:

```bash
set -a && source .env && source .env.llm.local && set +a
KNOWFABRIC_DUMP_CLUSTER_TRACE=1 \
OMLX_API_KEY=4496 \
venv/bin/python scripts/regroup_chiller_domain.py
```

4. Validate SQL:

```sql
SELECT COUNT(*)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller';

SELECT COALESCE(MAX(jsonb_array_length(authority_summary_json::jsonb->'layers')),0)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller';

SELECT canonical_key,
       jsonb_array_length(authority_summary_json::jsonb->'layers') AS n_layers,
       (SELECT array_agg(DISTINCT layer->>'publisher')
        FROM jsonb_array_elements(authority_summary_json::jsonb->'layers') layer) AS pubs
FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
  AND (SELECT COUNT(DISTINCT layer->>'publisher')
       FROM jsonb_array_elements(authority_summary_json::jsonb->'layers') layer) >= 2
ORDER BY n_layers DESC;
```

Expected acceptance:

- total chiller KO count 40-80
- max layers per KO <= 8
- cross-publisher KO >= 3
- includes Trane+Carrier oil pressure merge
- includes Trane+McQuay chilled water merge
- no super-KO

5. Update `output/p0_final_verification/REPORT.md`.

## Current Git State

Modified tracked files:

- `packages/compiler/canonical_key.py`
- `packages/compiler/cross_source_merger.py`
- `tests/test_canonical_key_embedding.py`

Notes:

- `cross_source_merger.py` changes are prior P0 plumbing fix, not part of this rich-state fix.
- Many untracked `output/diagnostic/...` directories exist from previous debugging sessions.
