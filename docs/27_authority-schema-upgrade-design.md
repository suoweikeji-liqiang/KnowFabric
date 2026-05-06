# Authority Schema Upgrade — Design Document

> **Status**: DRAFT — proposed schema upgrade for authority-layer modeling
> **Date**: 2026-05-01
> **Scope**: KnowFabric internal architecture; companion contract change in [docs/28_contract-v0.2-proposal.md](28_contract-v0.2-proposal.md)
> **Authoritative target version**: contract v0.2

---

## 0. Why now

The parameter_spec vertical (Round-2, Trane CVGF, 23/25 accepted at 92% precision) proved the doc-level extraction pipeline works for a single OEM manual. But the verified KOs are stamped with only:

- `doc_id` (foreign key)
- `evidence_text` (verbatim quote)
- `trust_level` (L1-L4 signal strength)

There is **no structured way** to answer:

- Is this knowledge from an OEM manual or an industry standard?
- If both ASHRAE 90.1 and Trane manual describe the same parameter, do they agree?
- When agent control plane queries a parameter, can it tell which source authority backs the value?

This gap means KnowFabric is currently a "PDF-to-KO converter," not an "industrial knowledge authority engine." The vNext direction (doc 23) explicitly requires authority modeling. This design closes that gap.

---

## 1. Authority hierarchy (the model we are committing to)

Four authority layers, ranked by formal authority strength:

| Level | Slug | Examples | Scope |
|-------|------|----------|-------|
| Industry standard | `industry_standard` | ASHRAE 90.1, ASHRAE Guideline 36, IEC 61800, ISO 7730, Brick Schema | Cross-vendor, cross-site |
| Regulatory code | `regulatory_code` | Local building codes, GB-T (China national standards) | Geographic / regulatory |
| OEM manual | `oem_manual` | Trane CVGF manual, York YK manual, ABB ACS880 manual | Single vendor + model family |
| Vendor application note | `vendor_application_note` | Trane Engineering Bulletin, ABB Application Note | Single vendor, weaker than primary manual |
| Internal SOP | `internal_sop` | Your company's commissioning playbook, internal training material | Internal use only |
| Field observation | `field_observation` | Your operating fleet's runtime measurements + engineer-confirmed deviations | Your fleet specifically |
| Academic reference | `academic_reference` | ASHRAE Handbook chapters, textbooks, papers | Wider context, weaker formal authority |
| Unspecified | `unspecified` | Legacy ingested documents | Fallback only |

Two **orthogonal axes** must be tracked separately:

- **Authority strength** — the formal weight of the source (industry_standard > oem_manual > academic_reference)
- **Practical relevance** — the operator's field truth from real deployments (highest practical weight, regardless of formal authority)

In the operator's specific case, `field_observation` from their hundreds of projects is **practically the strongest signal** even though formally it ranks below industry_standard. This is the moat. Conflict resolution must explicitly accommodate "field observation overrides standard, with documented justification" rather than treating field data as second-class.

---

## 2. Document table — schema additions

### 2.1 Authority typing fields

Add the following columns to the existing `document` table:

```sql
ALTER TABLE document ADD COLUMN authority_level VARCHAR(32);
ALTER TABLE document ADD COLUMN publisher VARCHAR(128);
ALTER TABLE document ADD COLUMN standard_id VARCHAR(128);
ALTER TABLE document ADD COLUMN publication_year INTEGER;
ALTER TABLE document ADD COLUMN revision VARCHAR(64);
ALTER TABLE document ADD COLUMN regulatory_scope VARCHAR(32);
ALTER TABLE document ADD COLUMN vendor_brand VARCHAR(128);
ALTER TABLE document ADD COLUMN vendor_model_family VARCHAR(128);
ALTER TABLE document ADD COLUMN applies_to_equipment_classes_json JSON;
ALTER TABLE document ADD COLUMN language VARCHAR(16);
ALTER TABLE document ADD COLUMN authority_metadata_json JSON;
```

Field semantics:

| Field | Type | Meaning | Example |
|-------|------|---------|---------|
| `authority_level` | enum | Authority layer slug from §1 | `oem_manual` |
| `publisher` | string | Publishing organization | `Trane`, `ASHRAE`, `IEC`, `your_company` |
| `standard_id` | string \| null | Formal identifier (null for OEM) | `ASHRAE 90.1-2022`, `IEC 61800-3:2017` |
| `publication_year` | int \| null | Year of publication / revision |
| `revision` | string \| null | Edition / revision marker | `Rev 3`, `2022 edition` |
| `regulatory_scope` | string \| null | Geographic / regulatory scope | `US`, `CN`, `EU`, `global`, `internal_only` |
| `vendor_brand` | string \| null | OEM brand (null for non-OEM) | `Trane`, `York`, `ABB` |
| `vendor_model_family` | string \| null | OEM model series | `CVGF`, `YK`, `ACS880` |
| `applies_to_equipment_classes_json` | JSON list | Brick equipment_class IDs this doc applies to | `["brick:Centrifugal_Chiller"]` |
| `language` | string | Original language | `zh`, `en`, `de` |
| `authority_metadata_json` | JSON | Free-form additional metadata | `{"section_count": 14, "iso_compliance": "section 6"}` |

Defaults for legacy documents on migration:
- `authority_level = "unspecified"`
- All other fields = null

Operator must run a one-time backfill pass to assign correct authority_level to existing documents (Trane CVGF → `oem_manual`, etc.). A helper script will be provided.

### 2.2 Full-text ingestion + redistribution control (operator decision 2026-05-01)

Standard documents are ingested **in full** through the same Document → Page → Chunk pipeline as OEM manuals. Clause-based chunking (§5) replaces page-based chunking when `authority_level ∈ {industry_standard, regulatory_code}`, but every clause of every standard is stored verbatim in `content_chunk.cleaned_text`.

To control external redistribution of copyrighted content (ASHRAE etc. prohibit verbatim redistribution but allow internal use):

```sql
ALTER TABLE document ADD COLUMN is_redistributable BOOLEAN DEFAULT FALSE;
```

- `is_redistributable = TRUE` → API may return `evidence_text` verbatim
- `is_redistributable = FALSE` (default for `industry_standard` / `regulatory_code` / unspecified) → API substitutes `evidence_text` with `citation + 200-char paraphrased summary` and sets a `redistribution_restricted: true` flag in the response

This flag is enforced at the API serialization boundary (`packages/retrieval/semantic_service.py`), not at the storage boundary — internal MCP tool callers (sw_base_model agent control plane in trusted environment) MAY receive verbatim text by passing an explicit `include_restricted_evidence: true` parameter; external surfaces must NEVER set this flag.

Storage budget note: ~1000 standard docs × 500 pages × 2KB/page ≈ 1GB additional in `content_chunk` table. Acceptable for current scale; revisit if standard corpus grows past 10K documents.

---

## 3. KO + Evidence tables — schema additions

### 3.1 `knowledge_object` table additions

```sql
ALTER TABLE knowledge_object ADD COLUMN authority_summary_json JSON;
ALTER TABLE knowledge_object ADD COLUMN consensus_state VARCHAR(32);
ALTER TABLE knowledge_object ADD COLUMN conflict_summary TEXT;
ALTER TABLE knowledge_object ADD COLUMN highest_authority_level VARCHAR(32);
```

Field semantics:

- `authority_summary_json` — denormalized aggregation of all backing authority sources, computed at apply-time from evidence rows. Each entry:

```json
{
  "level": "industry_standard",
  "doc_id": "doc_ashrae_901_2022",
  "publisher": "ASHRAE",
  "standard_id": "ASHRAE 90.1-2022",
  "citation": "ASHRAE 90.1-2022 §6.5.3.2",
  "value_summary": "10°F",
  "evidence_count": 1
}
```

- `consensus_state` — enum:
  - `single_source` — only one doc backs this KO
  - `agreed` — multiple sources, values consistent
  - `partial_conflict` — sources mostly agree but with some divergence (e.g., default vs range disagreement)
  - `material_conflict` — sources fundamentally disagree on the parameter value

- `conflict_summary` — when consensus_state is partial/material_conflict, a human-readable summary of the disagreement

- `highest_authority_level` — the strongest level among all backing sources, denormalized for fast filtering

### 3.2 `knowledge_object_evidence` table additions

```sql
ALTER TABLE knowledge_object_evidence ADD COLUMN authority_role VARCHAR(64);
ALTER TABLE knowledge_object_evidence ADD COLUMN evidence_citation VARCHAR(256);
```

Field semantics:

- `authority_role` enum extension (existing field `evidence_role` keeps current values; this adds finer authority-aware classification):
  - `primary_oem` — the principal OEM source for this KO
  - `primary_standard` — the principal industry-standard source
  - `corroborating_oem` — additional OEM confirmation (cross-vendor)
  - `corroborating_standard` — additional standard confirmation
  - `field_validation` — your fleet's field observation supporting this KO
  - `contradicting_oem` / `contradicting_standard` / `contradicting_field` — sources that disagree, surfaced as part of conflict tracking
  - `historical_revision` — superseded by a newer revision but retained for audit

- `evidence_citation` — formal citation string for the chunk. For standards: `"ASHRAE 90.1-2022 §6.5.3.2"`. For OEM: `"Trane CVGF 400-1000 Operation Manual p.29"`. For field: `"project_id=PRJ-AAA, observation_period=2025-Q1"`.

---

## 4. Trust level vs consensus state — orthogonal axes

These are now distinct concepts:

| Trust level | Meaning | Calculation |
|-------------|---------|-------------|
| L1 | LLM inference, no verbatim anchor | Should be rare/dropped |
| L2 | Paraphrased evidence | Verbatim quote check failed but evidence is loosely supported |
| L3 | Verbatim quote in single chunk | Anchor-passed, single source |
| L4 | Verbatim quote in ≥ 2 chunks | Anchor-passed, multi-chunk corroboration |

| Consensus state | Meaning |
|-----------------|---------|
| `single_source` | Only one source doc; trust level reflects per-source quality |
| `agreed` | Multiple sources back it, no conflict on values |
| `partial_conflict` | Multiple sources back it, minor value disagreement |
| `material_conflict` | Multiple sources back it, significant value disagreement requiring human review |

A KO can be **L4 + material_conflict**: high signal strength from each source individually, but they disagree. The agent consuming this should NOT pick a winner silently; it should surface the conflict.

---

## 5. Parser changes — clause-based chunking for standards

Current parser (`packages/parser/service.py`) does page-level + paragraph-level chunking, which fits OEM manuals.

Industry-standard documents need **clause-based chunking**:

- Recognize section/clause numbering patterns: `§6.5.3.2`, `Section 6.5.3.2`, `6.5.3.2`, `第 6.5.3.2 条`, `6.5.3.2节`
- Each clause becomes one chunk, regardless of its physical page boundary
- Add `standard_clause` column to `content_chunk`:

```sql
ALTER TABLE content_chunk ADD COLUMN standard_clause VARCHAR(64);
ALTER TABLE content_chunk ADD COLUMN clause_path JSON;
```

- `standard_clause` — flat clause string: `"6.5.3.2"`
- `clause_path` — hierarchy: `["6", "6.5", "6.5.3", "6.5.3.2"]` for navigation

Routing: parser dispatches based on `Document.authority_level`:

```python
def parse_document(doc):
    if doc.authority_level in ("industry_standard", "regulatory_code"):
        return _parse_clause_based(doc)
    else:
        return _parse_page_based(doc)  # current path
```

Parser changes are scoped — current OEM manual flow is unchanged.

---

## 6. LLM compiler changes — authority extraction

When compiling KOs from a document, the compiler must:

1. Read source `Document.authority_level` and pass it into the LLM prompt as context: "this document is an industry standard ASHRAE 90.1-2022; treat citations as standard references."
2. For standard documents: require citation in clause format (`ASHRAE 90.1-2022 §6.5.3.2`), NOT page number.
3. For OEM documents: continue page-based citations.
4. The verbatim anchor system extends to clause-level for standards; for OEM, page-level is unchanged.
5. After extraction, compiler populates the per-evidence `authority_role` field based on authority_level:

```python
def _resolve_authority_role(doc: Document, is_primary: bool) -> str:
    if doc.authority_level == "industry_standard":
        return "primary_standard" if is_primary else "corroborating_standard"
    if doc.authority_level == "oem_manual":
        return "primary_oem" if is_primary else "corroborating_oem"
    if doc.authority_level == "field_observation":
        return "field_validation"
    return "unspecified"
```

Cross-source dedup is enhanced:

- When KO has evidence from multiple authority levels (e.g., one from `industry_standard`, one from `oem_manual`):
  - If values agree → `consensus_state = "agreed"`
  - If values disagree → `consensus_state = "material_conflict"`, populate `conflict_summary`
- When KO has evidence from same authority level only:
  - Existing L3/L4 logic applies, `consensus_state = "single_source"` or `"agreed"` based on value consistency

The `highest_authority_level` field is computed as the max of all evidence rows' source authority levels.

---

## 7. API response changes

Existing semantic API (`/api/v2/domains/{domain}/equipment-classes/{class}/parameter-profiles` and siblings) extends each item with:

```json
{
  "knowledge_object_id": "ko_abc123",
  "title": "Active Chilled Water Setpoint",
  "trust_level": "L4",
  "consensus_state": "agreed",
  "highest_authority_level": "industry_standard",
  "authority_layers": [
    {
      "level": "industry_standard",
      "publisher": "ASHRAE",
      "standard_id": "ASHRAE 90.1-2022",
      "citation": "ASHRAE 90.1-2022 §6.5.3.2",
      "value_summary": "10°F",
      "evidence_count": 1
    },
    {
      "level": "oem_manual",
      "publisher": "Trane",
      "standard_id": null,
      "citation": "Trane CVGF Operation Manual p.29",
      "value_summary": "44.0F",
      "evidence_count": 1
    }
  ],
  "conflict_summary": null,
  "evidence": [...]
}
```

For agent control plane (sw_base_model) consumption:

- Agent can filter by `min_authority_level=industry_standard` to get only standards-backed knowledge
- Agent sees `consensus_state` to decide if it should use the value directly or escalate to human
- Agent sees `authority_layers` to cite sources back to operator in chat/copilot responses

---

## 8. Migration plan

### 8.1 Schema migrations

```
migration 008: add authority columns to document table
migration 009: add authority columns to knowledge_object + knowledge_object_evidence
migration 010: add clause columns to content_chunk
```

All three migrations are additive; no data loss, no downtime concern for self-use deployment.

### 8.2 Backfill scripts

Required:

- `scripts/classify_existing_documents.py` — interactive helper that prompts operator for authority_level + publisher per existing doc, OR uses LLM to suggest classification + human confirms
- `scripts/recompute_ko_authority_summaries.py` — rebuilds `authority_summary_json` and `consensus_state` for existing KOs based on linked evidence rows

Order:
1. Apply migrations
2. Run document classifier on the 1 existing doc (Trane CVGF) → mark as `oem_manual`, `Trane`, `null` standard_id
3. Run KO summary recompute → 23 existing parameter_specs get authority_summary populated (single source each, consensus=single_source)
4. Verify API responses include new fields
5. Verify check-all and tests pass

### 8.3 Validation experiment after migration

Pick a real ASHRAE document chapter (one that's freely distributable, e.g., from Brick Schema documentation or an open guideline excerpt) and run it through the upgraded pipeline:

1. Ingest with `authority_level = industry_standard`, populate metadata
2. Parser auto-uses clause-based chunking
3. LLM compiler extracts parameter_specs with clause citations
4. Compare extracted KOs against existing Trane KOs:
   - If overlap exists with same parameter and consistent values → KO enters `consensus_state = "agreed"` with two evidence rows
   - If overlap exists but values differ → KO enters `consensus_state = "material_conflict"` with conflict_summary populated
5. API response correctly surfaces the multi-layer authority structure

This experiment is the acceptance gate for declaring the authority schema works.

---

## 9. Open decisions (operator must resolve before implementation)

| # | Decision | Recommendation |
|---|----------|----------------|
| D1 | Should `field_observation` documents be a separate doc_type or just `authority_level=field_observation` on the Document table? | Same Document table. Simpler. Field observations are still ingestable assets with traceable provenance. |
| D2 | When operator's field data contradicts ASHRAE, how is the deviation justified? | Add a `deviation_justification_json` field on KO. Required when consensus_state contradicts an industry_standard with field_observation evidence. |
| D3 | Do we ingest full text of standards (copyright concern) or only citations + summaries? | **CLOSED 2026-05-01: full text in DB.** Operator decision: ingest standards verbatim through the same six-layer pipeline as OEM manuals. Copyright protected via the `is_redistributable` flag (see §3.3) — when false, API substitutes citation + summary for evidence_text in external-facing responses. |
| D4 | Should `highest_authority_level` filtering be a query parameter on the existing API routes? | Yes. Add `?min_authority_level=industry_standard` filter to all `/api/v2/...` query endpoints. |
| D5 | Conflict resolution policy: should the API auto-pick a winner or always surface conflicts? | Always surface. Agent decides. KnowFabric is the authority engine, not the decider. |
| D6 | Vendor catalog (`vendor_brand`, `vendor_model_family`) — does this need its own normalized table or is the string field enough? | String for now. Promote to lookup table only after we hit ~100 vendors with naming variants needing normalization. |

---

## 10. Out of scope (for this design)

- Automated standard-document acquisition (procurement / purchasing workflow)
- Standard revision tracking workflow (when ASHRAE 90.1-2022 → 90.1-2025, how do KOs migrate?)
- Multi-language standard documents (ASHRAE in Chinese vs English translations of the same standard)
- Authority-based access control beyond `is_redistributable` (per-user / per-tenant gating)

These are separate workstreams.

---

## 11. Implementation effort estimate

| Workstream | Effort |
|------------|--------|
| Schema migrations + Document model update | 2 days |
| Backfill helper scripts | 2 days |
| Parser clause-based chunking | 3-4 days |
| LLM compiler authority handling | 2 days |
| API response upgrade + redistribution gating | 3 days |
| ASHRAE validation experiment | 2 days |
| Contract v0.2 paired PR with sw_base_model | 1 day |
| **Backend total** | **~2-2.5 weeks** |
| Admin-web UI workstream (§12) | **~2-3 weeks parallel** |

Backend and UI workstreams can run in parallel after the schema is frozen. The UI workstream depends on backend API surface stability (~end of week 1 backend work).

---

## 12. Admin-web UI requirements (operator priority 2026-05-01)

Operator decision: manual ingestion + review must be UI-friendly, not CLI-only. The current `apps/admin-web/src/pages/ReviewCenterPage.tsx` covers KO review at a basic level but is not authority-aware.

### 12.1 Required new pages / sections

| Page / Component | Purpose | Backend dependency |
|------------------|---------|-------------------|
| **Document Ingest** (new) | Drag-drop file upload + LLM-suggested authority metadata form (level / publisher / standard_id / vendor_brand) → human confirms or corrects | Document table v0.2 schema; LLM authority classifier (separate task) |
| **Document Library** (new) | List view of all ingested docs grouped/filterable by `authority_level`; bulk-edit authority metadata; toggle `is_redistributable` | Document v0.2 schema |
| **Authority Classification Review** (new) | When LLM auto-suggested authority metadata, human reviewer confirms/corrects in queue form. Default queue = "newly ingested, not yet confirmed" | Document.authority_metadata_json + new `authority_review_status` field (enum: `auto_suggested`, `human_confirmed`, `human_corrected`) |
| **Standard Document Navigator** (new) | Tree view of clauses (§6 → §6.5 → §6.5.3 → §6.5.3.2) for industry_standard documents; clicking a clause shows its KOs and bidirectional links | Clause-based chunks (§5); KO ↔ chunk navigation API |
| **KO Review Center** (extend existing `ReviewCenterPage.tsx`) | Show `authority_layers` + `consensus_state` + `conflict_summary` per candidate; side-by-side multi-source view when consensus_state ≠ single_source | KO v0.2 schema + API response shape |
| **Conflict Resolution** (new sub-page of Review Center) | When `material_conflict` detected, present sources side-by-side with values + citations; operator picks: `accept_both_surface_conflict` / `pick_winner_<source_id>` / `mark_deviation_justified` (requires deviation_justification_json) | KO v0.2 schema |

### 12.2 UX principles

These are non-negotiable for the v0.2 UI work:

1. **LLM-assisted, human-final**. Every authority field is auto-suggested by LLM at ingest time; human only confirms or corrects. No 10-field manual entry forms.
2. **Bulk operations first-class**. List views default to multi-select with bulk edit. Single-record edit is a fallback, not the primary flow.
3. **Provenance visible at every layer**. Any KO display surface shows which document(s) back it, with one click to original source clause/page.
4. **Conflict cannot be hidden**. KOs with `material_conflict` get a visual marker in any list view; cannot be silently approved without explicit conflict resolution action.
5. **Bilingual labels**. UI labels in Chinese with English secondary; KO content displays in source language with auto-translate hint.
6. **Read-only mode for outsiders**. A view-only role exists for stakeholders who should not edit authority metadata. Tied to operator's auth scheme.

### 12.3 Data flow back to the backend

UI write operations touch these existing or new backend endpoints (all under `/api/v2/admin/...`):

| UI action | Endpoint | Body |
|-----------|----------|------|
| Upload doc with metadata | `POST /api/v2/admin/documents` | multipart: file + authority metadata |
| Update doc authority metadata | `PATCH /api/v2/admin/documents/{doc_id}` | authority fields |
| Confirm/correct LLM authority suggestion | `POST /api/v2/admin/documents/{doc_id}/authority-review` | reviewer_id + decision |
| Resolve KO conflict | `POST /api/v2/admin/knowledge-objects/{ko_id}/resolve-conflict` | resolution + justification |
| Bulk authority update | `POST /api/v2/admin/documents/bulk-authority` | doc_ids[] + new authority_level |

These are admin-only endpoints. The existing read-only `/api/v2/...` consumer-facing endpoints remain unchanged in shape, except for the response field additions in §7.

### 12.4 Out of scope for v0.2 UI

- Full WYSIWYG editor for clause/KO content
- Inline LaTeX/diagram rendering for ASHRAE figures
- Real-time collaboration (multi-user simultaneous editing)
- Mobile-responsive design (desktop-only acceptable for v0.2)
- Standard document search/full-text-search UI (out of scope; CLI suffices for v0.2)

These are flagged for v0.3+.

### 12.5 Suggested workstream split

UI work is large enough that it should be its own design doc once §12 is approved:

> **Suggestion**: after operator confirms §12 scope, spin out into `docs/29_admin-web-authority-ui-design.md` with detailed page wireframes, component breakdown, and Codex-executable build plan. Treat docs/27 §12 as the requirements document; docs/29 (future) is the implementation document.

---

## 13. Definition of Done

- All three migrations applied, no test breakage
- Trane CVGF document is correctly classified as `oem_manual`, `Trane`, vendor_model_family `CVGF`
- All 23 existing parameter_specs have `authority_summary_json` populated and `consensus_state = single_source`
- Parser correctly distinguishes industry_standard vs oem_manual flow
- API `/api/v2/.../parameter-profiles` returns new authority_layers + consensus_state fields
- `?min_authority_level=industry_standard` query parameter filters correctly
- ASHRAE validation experiment produces at least one KO with `consensus_state != single_source` (proves the multi-source merge logic)
- Contract v0.2 mirror PR is filed and SHA matches between repos

Stop here. Operator confirms before implementation begins.
