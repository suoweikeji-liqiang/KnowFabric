# KnowFabric Side: Contract Implementation Plan

> **For Codex:** Execute this plan task-by-task in the KnowFabric repo.
>
> **Authoritative contract:** [`docs/24_knowfabric-sw-base-model-contract.md`](24_knowfabric-sw-base-model-contract.md)
>
> **Companion plan (sw_base_model side):** `sw_base_model/docs/plans/2026-04-27-knowfabric-contract-implementation-plan.md`
>
> **Date:** 2026-04-27
>
> **Sequencing:** Tasks 1-3 must execute in order. Tasks 4-7 can parallelize after Task 3. Task 8 is the final cutover and depends on sw_base_model side completing its Tasks 1-3.

---

**Goal:** Migrate KnowFabric to align with the integration contract: drop ontology authority for structural classes, add ontology_version stamping on all KOs, expose feedback endpoints, downgrade external-product framing, and add CI enforcement.

**Tech Stack:** Python 3.11, SQLAlchemy 2.0, Alembic, FastAPI, Pydantic v2

---

## Task 1: Mirror the contract document

**Files:**
- Verify exists: `docs/24_knowfabric-sw-base-model-contract.md`
- Verify exists: `../sw_base_model/design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`

**Step 1: Confirm contract is in place**

Both files should exist with identical §1-10 content. If they differ, escalate to operator before proceeding.

**Step 2: Compute contract section SHA for CI baseline**

Extract §1 through §10 of `docs/24_knowfabric-sw-base-model-contract.md` (excluding the front matter and CHANGELOG) and compute SHA-256. Save the hash to `scripts/contract_sha_baseline.txt`.

```bash
python3 -c "
import hashlib, re
text = open('docs/24_knowfabric-sw-base-model-contract.md').read()
# Extract sections 1-10 inclusive
m = re.search(r'## 1\..*?(?=## CHANGELOG)', text, re.DOTALL)
content = m.group(0).strip().encode('utf-8')
print(hashlib.sha256(content).hexdigest())
" > scripts/contract_sha_baseline.txt
```

**Verify:** `scripts/contract_sha_baseline.txt` contains a 64-char hex string.

---

## Task 2: Add `curated_against_ontology_version` field to KnowledgeObjectV2

**Files:**
- Modify: `packages/db/models_v2.py`
- Create: `migrations/versions/0xx_add_curated_against_ontology_version.py`

**Step 1: Add the field to the model**

In `packages/db/models_v2.py`, add a new column to `KnowledgeObjectV2`:

```python
curated_against_ontology_version: Mapped[str | None] = mapped_column(
    String(64),
    nullable=True,
    doc="The sw_base_model ontology_version this KO was curated against (semver, e.g., 1.3.0+brick1.3). Null for KOs predating the contract."
)
```

**Step 2: Create Alembic migration**

```bash
alembic revision -m "add curated_against_ontology_version to knowledge_object_v2"
```

In the migration:
- `op.add_column('knowledge_object_v2', sa.Column('curated_against_ontology_version', sa.String(64), nullable=True))`
- Downgrade: `op.drop_column('knowledge_object_v2', 'curated_against_ontology_version')`

**Step 3: Apply migration**

```bash
alembic upgrade head
```

**Step 4: Update affected code**

Search for any code that constructs `KnowledgeObjectV2` instances:

```bash
grep -rn 'KnowledgeObjectV2(' packages/ scripts/ apps/
```

For each, leave `curated_against_ontology_version` as None for now. Task 5 will populate it during compilation.

**Verify:**
- `alembic current` shows the new revision
- All existing tests in `tests/test_*.py` still pass: `python3 -m pytest tests/ -x`

---

## Task 3: Export OntologyClassV2 as seed YAML for sw_base_model

**Files:**
- Create: `scripts/export_ontology_seed_for_sw_base_model.py`
- Create: `output/ontology_export/ontology_seed.yaml` (output)

**Step 1: Write the export script**

The script reads all rows from `OntologyClassV2`, `OntologyAliasV2` (only structural aliases), and `OntologyMappingV2` (only structural mappings — see Step 2 for split criteria), and produces a YAML file matching the structure in sw_base_model `DESIGN-01-PROJECT-UNDERSTANDING.md` §2.5:

```yaml
namespace:
  brick: "https://brickschema.org/schema/Brick#"
  ext: "https://sw-platform.example.com/ontology/ext#"

ontology_version: "0.1.0"  # initial seed version, sw_base_model will own bumps

equipment_classes:
  - class: <name>
    parent: <parent>
    namespace: brick | ext
    typical_points: [...]
    typical_relations: [...]

point_classes:
  - class: <name>
    parent: <parent>
    namespace: brick | ext
    tags: { medium, direction, measurement, point_type }

relation_types:
  - type: <name>
    namespace: brick | ext
    inverse: <inverse_or_null>
    description: <description>
```

**Step 2: Identify structural vs domain mappings in OntologyMappingV2**

`OntologyMappingV2` rows must be split:
- **Structural mappings** (Brick ↔ 223P, 223P ↔ Open223, brick ID → standard external IRI): export to seed YAML
- **OEM naming variants** (canonical_term ↔ vendor product name, e.g., "centrifugal_chiller" ↔ "York YK"): keep in KnowFabric (will be processed in Task 4)

Use `mapping_type` field if it exists, or inspect rows manually. Add a `--include-mapping-types <list>` flag to the export script for explicit control.

**Step 3: Run the export**

```bash
python3 scripts/export_ontology_seed_for_sw_base_model.py \
  --output output/ontology_export/ontology_seed.yaml \
  --include-mapping-types brick_to_223p,brick_to_open223
```

**Step 4: Operator approval gate**

PAUSE here. The seed YAML must be reviewed by the operator before being handed off to sw_base_model. Print a summary on stdout:

```
Exported N equipment_classes, M point_classes, P relation_types
Output: output/ontology_export/ontology_seed.yaml
Next: hand this file to sw_base_model side Task 1, then resume KnowFabric Task 4.
```

**Verify:**
- `output/ontology_export/ontology_seed.yaml` exists and parses as valid YAML
- Equipment class count matches `SELECT COUNT(*) FROM ontology_class_v2`

---

## Task 4: Split OntologyMappingV2 — keep OEM naming, drop structural mappings

**Files:**
- Modify: `packages/db/models_v2.py`
- Create: `migrations/versions/0xx_drop_structural_mappings.py`

**Step 1: Identify rows to delete**

Same `mapping_type` filter as Task 3 Step 2. Structural mapping rows (brick_to_223p, etc.) are now owned by sw_base_model and must be deleted from KnowFabric to prevent dual-source-of-truth drift.

**Step 2: Create migration**

```bash
alembic revision -m "drop structural mappings from ontology_mapping_v2"
```

The migration deletes rows by `mapping_type`:

```python
def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM ontology_mapping_v2
        WHERE mapping_type IN ('brick_to_223p', 'brick_to_open223', 'brick_to_external_standard')
    """))

def downgrade():
    # Cannot restore deleted data automatically; this is a one-way migration
    pass
```

Document the irreversibility in the migration docstring.

**Step 3: Apply migration**

```bash
alembic upgrade head
```

**Verify:**
- Remaining rows are only OEM naming variants (`SELECT DISTINCT mapping_type FROM ontology_mapping_v2`)
- All tests pass: `python3 -m pytest tests/ -x`

---

## Task 5: Add feedback API endpoints

**Files:**
- Create: `packages/retrieval/feedback_service.py`
- Modify: `apps/api/main.py` (register new routes)
- Create: `tests/test_feedback_endpoints.py`

**Step 1: Define feedback schemas**

In `packages/retrieval/feedback_service.py`, add Pydantic models matching contract §4.3:

```python
class KOFeedbackBase(BaseModel):
    project_id: str
    finding_id: str
    reviewer_id: str
    knowledge_object_id: str

class KOConfirmation(KOFeedbackBase): pass
class KORejection(KOFeedbackBase):
    reason: str | None = None
class CoverageGapSignal(BaseModel):
    project_id: str
    equipment_class_id: str
    expected_ko_type: str  # one of fault_code/parameter_spec/...
    expected_pattern: str  # human-readable description
    triggered_by_finding_id: str | None = None
class ConflictEvidence(BaseModel):
    project_id: str
    knowledge_object_id: str
    field_observation: dict  # actual field reading that conflicts
    observation_window: str  # ISO 8601 interval
    reviewer_id: str
```

**Step 2: Add idempotency**

Use `(project_id, finding_id, knowledge_object_id, event_type)` as a uniqueness key. Persist to a new table `ko_feedback_event` (create another migration). Repeat submissions return 200 with `{"status": "duplicate"}` rather than re-applying trust changes.

**Step 3: Wire to API**

In `apps/api/main.py`, register four POST routes:
- `POST /api/v2/feedback/ko-confirmation`
- `POST /api/v2/feedback/ko-rejection`
- `POST /api/v2/feedback/coverage-gap`
- `POST /api/v2/feedback/conflict-evidence`

Each accepts the corresponding Pydantic model, validates, persists the event, and returns:

```json
{ "success": true, "data": { "event_id": "...", "status": "accepted" } }
```

**Step 4: Trust score updates (skeleton only)**

For v0.1 of the contract, do NOT yet adjust trust scores from feedback. Just persist the events. Trust adjustment is deferred to a later phase. Document this in code comments.

**Step 5: Add tests**

In `tests/test_feedback_endpoints.py`, write tests covering:
- happy path for each endpoint
- idempotency (same event submitted twice returns duplicate)
- missing required field returns 422

**Verify:**
- `python3 -m pytest tests/test_feedback_endpoints.py -v`
- Manual: `curl -X POST http://localhost:8000/api/v2/feedback/ko-confirmation -d '{...}'` returns 200

---

## Task 6: Add CI checks for contract enforcement

**Files:**
- Create: `scripts/check-contract-mirror`
- Modify: `scripts/check-forbidden-deps`
- Modify: `scripts/check-all`

**Step 1: Implement check-contract-mirror**

Bash script that:
1. Computes SHA-256 of `docs/24_knowfabric-sw-base-model-contract.md` §1-10
2. Computes SHA-256 of `../sw_base_model/design/DESIGN-10-KNOWFABRIC-INTEGRATION.md` §1-10 (if path exists)
3. Compares to `scripts/contract_sha_baseline.txt`
4. Fails if local SHA differs from baseline OR if both repos accessible and SHAs differ

If sw_base_model path is not available locally (CI runs in isolated repo checkout), only check against baseline. Document this fallback behavior.

```bash
#!/usr/bin/env bash
set -euo pipefail

contract_path="docs/24_knowfabric-sw-base-model-contract.md"
baseline_path="scripts/contract_sha_baseline.txt"

current_sha=$(python3 -c "
import hashlib, re
text = open('$contract_path').read()
m = re.search(r'## 1\..*?(?=## CHANGELOG)', text, re.DOTALL)
print(hashlib.sha256(m.group(0).strip().encode('utf-8')).hexdigest())
")

baseline_sha=$(cat "$baseline_path")

if [ "$current_sha" != "$baseline_sha" ]; then
  echo "ERROR: Contract section SHA changed."
  echo "  Expected: $baseline_sha"
  echo "  Got:      $current_sha"
  echo "  If this is intentional, update $baseline_path AND coordinate paired PR in sw_base_model."
  exit 1
fi

# Cross-repo check (only when sw_base_model is co-located)
sw_base_path="../sw_base_model/design/DESIGN-10-KNOWFABRIC-INTEGRATION.md"
if [ -f "$sw_base_path" ]; then
  cross_sha=$(python3 -c "
import hashlib, re
text = open('$sw_base_path').read()
m = re.search(r'## 1\..*?(?=## CHANGELOG)', text, re.DOTALL)
print(hashlib.sha256(m.group(0).strip().encode('utf-8')).hexdigest())
")
  if [ "$current_sha" != "$cross_sha" ]; then
    echo "ERROR: Contract differs between KnowFabric and sw_base_model."
    exit 1
  fi
fi

echo "OK: contract SHA matches baseline."
```

Make executable: `chmod +x scripts/check-contract-mirror`

**Step 2: Extend check-forbidden-deps**

Add a rule that fails if any Python file under `packages/`, `apps/`, or `scripts/` imports from a path containing `sw_base_model`. Update the existing forbidden-deps check script accordingly.

**Step 3: Wire into check-all**

In `scripts/check-all`, add:

```bash
bash scripts/check-contract-mirror || exit 1
```

**Verify:**
- `bash scripts/check-all` passes
- Modify §1 of the contract by one character; `bash scripts/check-contract-mirror` fails as expected
- Revert the change

---

## Task 7: Rewrite charter and README to downgrade external-product framing

**Files:**
- Modify: `README.md`
- Modify: `docs/00_repo-charter.md`
- Modify: `docs/22_external-evaluation-guide.md`

**Step 1: Rewrite README intro**

Replace the existing "rebuilding into an ontology-first domain knowledge authority and publishing engine" framing. New intro:

```markdown
# KnowFabric

KnowFabric is the domain knowledge compilation and authority engine for the
intelligent O&M platform at `sw_base_model`. It ingests raw industrial documents
(OEM manuals, service guides, parameter tables) and compiles them into
evidence-grounded knowledge objects (fault codes, parameter specs, diagnostic
chains, etc.) that sw_base_model consumes via REST and MCP.

KnowFabric does not own structural ontology (equipment classes, point classes,
relation types) — those live in sw_base_model. KnowFabric owns the content
layer: the knowledge objects, evidence chains, trust scoring, and health checks.

For the integration contract between the two repos, see
[`docs/24_knowfabric-sw-base-model-contract.md`](docs/24_knowfabric-sw-base-model-contract.md).
```

**Step 2: Update charter**

In `docs/00_repo-charter.md`:
- Remove the "Three Consumer Classes" section (AI Agents / Developers / Upstream Applications)
- Remove the "What KnowFabric Is NOT" external-product NOT list (chatbot, document management, etc.) — keep only the layer-internal NOT list (no project-instance modeling, no runtime control)
- Add a new section "Relationship to sw_base_model" pointing to the contract
- Update "Phase 1 Success Criteria" to remove externally-oriented criteria; success is measured by sw_base_model consumption

**Step 3: Mark external evaluation guide as historical**

At the top of `docs/22_external-evaluation-guide.md`, prepend:

```markdown
> **Status note (2026-04-27):** With the v0.1 integration contract in place,
> KnowFabric's primary consumer is sw_base_model. The external evaluation
> flow described below remains functional and is preserved as an optional
> standalone demo, but it is not the main delivery path. New work should
> target sw_base_model consumption first.
```

**Step 4: Verify**

```bash
bash scripts/check-docs
bash scripts/check-all
```

Both must pass.

---

## Task 8: Drop OntologyClassV2 (cutover — depends on sw_base_model Task 3 completion)

**Files:**
- Modify: `packages/db/models_v2.py`
- Modify: `packages/retrieval/semantic_service.py`
- Create: `migrations/versions/0xx_drop_ontology_class_v2.py`

**PRECONDITION:** sw_base_model side has completed its Task 3 (ontology.yaml seeded with KnowFabric export, version 0.1.0 published). Do NOT execute Task 8 before this is confirmed by the operator.

**Step 1: Replace direct OntologyClassV2 joins with reference-only access**

Search for usages:

```bash
grep -rn 'OntologyClassV2' packages/ apps/ scripts/
```

For each occurrence in `packages/retrieval/semantic_service.py` and elsewhere:
- Replace SQLAlchemy join queries with `equipment_class_id` string lookup
- Where typical_points or typical_relations are needed, fetch from sw_base_model ontology API (defer to a thin client; for v0.1 it can read a locally cached YAML if sw_base_model API is not yet reachable)

Add a thin client `packages/core/sw_base_model_ontology_client.py`:

```python
class SwBaseModelOntologyClient:
    """Read-only client for sw_base_model ontology.yaml.

    Phase 1 (this contract version): reads from a locally cached YAML file
    pulled from sw_base_model. Phase 2: switches to live HTTP API.
    """
    def __init__(self, cached_yaml_path: Path):
        with open(cached_yaml_path) as f:
            self._data = yaml.safe_load(f)

    def get_equipment_class(self, class_id: str) -> dict | None: ...
    def get_typical_points(self, class_id: str) -> list[str]: ...
    def get_typical_relations(self, class_id: str) -> list[dict]: ...
    def ontology_version(self) -> str: ...
```

**Step 2: Drop the table**

```bash
alembic revision -m "drop ontology_class_v2 (migrated to sw_base_model)"
```

In the migration:
- `op.drop_table('ontology_class_v2')`
- Downgrade: re-create the empty table schema (data is gone, just structural rollback)

**Step 3: Apply migration**

```bash
alembic upgrade head
```

**Step 4: Update tests**

Tests under `tests/test_ontology_projection_v2.py` and `tests/test_sync_ontology_package_v2.py` likely reference `OntologyClassV2`. Either:
- Update them to use the new client pattern with a fixture YAML, OR
- Mark them as `pytest.mark.skip(reason="OntologyClassV2 migrated to sw_base_model in contract v0.1")` and create new test cases against the client

**Step 5: Final verify**

```bash
python3 -m pytest tests/ -x
bash scripts/check-all
```

All must pass.

---

## Post-cutover: 60-day follow-up tasks (out of scope for this plan)

These are tracked separately and should NOT be executed as part of the contract migration:

- **Task A:** Add `packages/extraction/extractor.py` with DeepSeek-based parameter_spec compilation MVP (separate plan)
- **Task B:** Add OCR routing layer with GLM-OCR primary (separate plan)
- **Task C:** Coverage Gap check v0 driven by sw_base_model SP2 query misses (separate plan)
- **Task D:** Trust score auto-adjustment from feedback events (separate plan, requires Task 5 stable)

---

## Rollback strategy

If cutover (Task 8) goes wrong:
1. `alembic downgrade -1` reverts the drop_table migration (table re-created empty)
2. Re-import OntologyClassV2 data from `output/ontology_export/ontology_seed.yaml` via a one-shot import script
3. Revert `packages/retrieval/semantic_service.py` and `packages/core/sw_base_model_ontology_client.py` changes via git
4. Operator decides whether to re-attempt cutover after fixing the issue, or hold the contract at "Tasks 1-7 done, Task 8 deferred"

Tasks 1-7 are independently committable and do not require cutover to be valuable.

---

## Definition of Done

- All 8 tasks merged
- `bash scripts/check-all` passes
- `python3 -m pytest tests/` passes
- README and charter reflect new identity
- `output/ontology_export/ontology_seed.yaml` handed to sw_base_model and merged into their `ontology.yaml`
- Both repos' contract files have identical SHA on §1-10
- Operator confirms by running `python3 scripts/run_live_demo_evaluation.py --output-dir output/demo` — should still work as a standalone demo (downgraded from primary path but functional)
