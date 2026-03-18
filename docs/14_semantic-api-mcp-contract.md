# Semantic API And MCP Contract

**Status:** Rebuild Design Contract
**Last Updated:** 2026-03-17

This document defines the minimum semantic delivery contract for the
ontology-first rebuild track.

It is additive and reversible. The first minimal read-only class explanation
route and the first fault knowledge route may be wired into the API app, but
the broader semantic knowledge-object route set and MCP implementation remain
incomplete in this repository.

---

## Current State

Current repository reality:

- REST currently exposes only legacy search at `GET /api/v1/chunks/search`.
- REST now also exposes a first ontology metadata route at `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}`.
- REST may also expose a first semantic knowledge route at `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/fault-knowledge`.
- Search returns chunk-level traceability, but not ontology-anchored semantic knowledge objects.
- There is no `apps/mcp/` implementation directory in the current workspace.
- The AI consumer contract defines generic MCP and context-block expectations, but not rebuild-track semantic endpoints.

This means the rebuild still lacks a stable semantic contract even after
ontology package and storage contracts were drafted.

---

## Gap To Rebuild Target

The rebuild architecture requires semantics-first delivery that lets consumers
query by canonical equipment class id instead of reconstructing meaning from raw
chunks.

Minimum rebuild query set from `docs/10_rebuild-plan.md`:

1. fault knowledge by equipment class and code
2. parameter profile by equipment class and category
3. maintenance guidance by equipment class and task type

The delivery contract must preserve:

- ontology identifiers
- evidence citations
- confidence and trust metadata
- applicability filters such as brand and model family
- domain-scoped identity for ontology classes
- compatibility with legacy search and trace surfaces

---

## Minimal Reversible Path

The recommended path is:

1. Keep legacy `v1` chunk search and trace routes as compatibility surfaces.
2. Add new semantic read-only endpoints under `v2` instead of changing `v1` payloads.
3. Mirror the same query vocabulary in MCP tool schemas.
4. Reuse the storage contract in `docs/13_rebuild-storage-contract.md`; do not create a second semantic-only data path.
5. Keep all semantic interfaces read-only and scoped to ontology classes and knowledge objects.

This avoids breaking legacy clients while giving rebuild-track consumers a clean
contract.

---

## Versioning Decision

### Why `v2`

The semantic interface should be introduced under `/api/v2/` because:

- `v1` is already associated with chunk search compatibility
- semantic responses introduce ontology ids and structured knowledge payloads
- rebuild-track consumers need an explicit contract boundary

### Compatibility Promise

The following legacy surfaces remain supported during migration:

- `GET /api/v1/chunks/search`
- legacy trace-evidence behavior when implemented
- legacy MCP tools such as `search_knowledge` and `trace_evidence`

---

## Identity Scope

Canonical ontology ids are unique only inside a domain package.

Because of that, semantic delivery must treat:

- `domain_id` as the required scope
- `equipment_class_id` as the canonical id within that scope

Examples:

- `hvac + centrifugal_chiller`
- `drive + variable_frequency_drive`

This avoids collisions for shared concept ids such as `fault_code` and
`parameter_spec`.

---

## Shared Response Contract

Every semantic endpoint returns the standard envelope:

```json
{
  "success": true,
  "data": {
    "equipment_class": {
      "equipment_class_id": "centrifugal_chiller",
      "label": "Centrifugal Chiller",
      "domain_id": "hvac"
    },
    "items": [
      {
        "knowledge_object_id": "ko_001",
        "knowledge_object_type": "fault_code",
        "canonical_key": "E01",
        "equipment_class": {
          "equipment_class_id": "centrifugal_chiller",
          "label": "Centrifugal Chiller",
          "domain_id": "hvac"
        },
        "title": "Fault Code E01",
        "summary": "Overcurrent during acceleration.",
        "structured_payload": {
          "fault_code": "E01",
          "severity": "high",
          "recommended_actions": ["Inspect compressor current", "Check startup ramp"]
        },
        "applicability": {
          "brand": "Carrier",
          "model_family": "19XR"
        },
        "confidence": 0.91,
        "trust_level": "L2",
        "review_status": "pending",
        "evidence": [
          {
            "doc_id": "doc_001",
            "doc_name": "Carrier 19XR Service Manual",
            "page_no": 12,
            "chunk_id": "chunk_001",
            "evidence_text": "E01: Overcurrent during acceleration",
            "evidence_role": "primary"
          }
        ]
      }
    ]
  },
  "metadata": {
    "contract_version": "2026-03-17",
    "query_type": "fault_knowledge",
    "filters_applied": {
      "equipment_class_id": "centrifugal_chiller",
      "fault_code": "E01",
      "domain_id": "hvac",
      "brand": "Carrier"
    },
    "total": 1,
    "limit": 20,
    "compatibility_surfaces": [
      "/api/v1/chunks/search",
      "trace_evidence",
      "search_knowledge"
    ]
  }
}
```

### Invariants

1. Every `item` must include `equipment_class.equipment_class_id`.
2. Every `item` must include at least one evidence citation.
3. Every evidence citation must include `doc_id`, `page_no`, `chunk_id`, and `evidence_text`.
4. `structured_payload` contains semantic fields; it never replaces the evidence chain.
5. No semantic response may include site-instance ids, point ids, runtime topology, or live telemetry.

---

## REST Endpoint Contracts

### `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/fault-knowledge`

Purpose:
Return `fault_code`, `symptom`, and `diagnostic_step` knowledge objects attached
to a canonical equipment class.

Query parameters:

- `fault_code`
- `brand`
- `model_family`
- `include_related_symptoms`
- `min_confidence`
- `min_trust_level`
- `limit`

Notes:

- This endpoint is the semantics-first replacement for “search chunks for fault text.”
- Response items should be ordered by trust level first, then confidence, then evidence quality.

### `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/parameter-profiles`

Purpose:
Return `parameter_spec` and optionally related `performance_spec` knowledge
objects attached to a canonical equipment class.

Query parameters:

- `parameter_category`
- `parameter_name`
- `brand`
- `model_family`
- `min_confidence`
- `min_trust_level`
- `limit`

Notes:

- Intended for settings lookup, ranges, defaults, and operating constraints.

### `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/maintenance-guidance`

Purpose:
Return `maintenance_procedure` and optionally linked `diagnostic_step`
knowledge objects attached to a canonical equipment class.

Query parameters:

- `task_type`
- `brand`
- `model_family`
- `include_diagnostic_steps`
- `min_confidence`
- `min_trust_level`
- `limit`

Notes:

- Intended for preventive and corrective maintenance guidance, not runtime execution.

### `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}`

Purpose:
Explain a canonical equipment class and its ontology metadata.

Response should include:

- primary label
- aliases
- parent class id
- external mappings
- supported knowledge anchors

This is recommended but not required for the minimum rebuild query set.

---

## Error Contract

Semantic endpoints should continue using the standard response envelope.

Recommended error cases:

- `404 EQUIPMENT_CLASS_NOT_FOUND` when the canonical id does not exist
- `422 INVALID_FILTER_COMBINATION` when filters conflict
- `422 INVALID_TRUST_LEVEL` when trust filters are unsupported
- `503 SEMANTIC_INDEX_NOT_READY` when semantic persistence exists but has not been backfilled yet

---

## MCP Tool Schemas

Semantic MCP tools must mirror the REST contract and remain read-only.

### `get_fault_knowledge`

```json
{
  "name": "get_fault_knowledge",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "equipment_class_id": { "type": "string" },
      "domain_id": { "type": "string" },
      "fault_code": { "type": "string" },
      "brand": { "type": "string" },
      "model_family": { "type": "string" },
      "include_related_symptoms": { "type": "boolean", "default": true },
      "min_confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
      "min_trust_level": { "type": "string", "enum": ["L1", "L2", "L3", "L4"], "default": "L4" },
      "limit": { "type": "integer", "minimum": 1, "maximum": 100, "default": 20 }
    },
    "required": ["domain_id", "equipment_class_id"]
  }
}
```

### `get_parameter_profile`

```json
{
  "name": "get_parameter_profile",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "equipment_class_id": { "type": "string" },
      "domain_id": { "type": "string" },
      "parameter_category": { "type": "string" },
      "parameter_name": { "type": "string" },
      "brand": { "type": "string" },
      "model_family": { "type": "string" },
      "min_confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
      "min_trust_level": { "type": "string", "enum": ["L1", "L2", "L3", "L4"], "default": "L4" },
      "limit": { "type": "integer", "minimum": 1, "maximum": 100, "default": 20 }
    },
    "required": ["domain_id", "equipment_class_id"]
  }
}
```

### `get_maintenance_guidance`

```json
{
  "name": "get_maintenance_guidance",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "equipment_class_id": { "type": "string" },
      "domain_id": { "type": "string" },
      "task_type": { "type": "string" },
      "brand": { "type": "string" },
      "model_family": { "type": "string" },
      "include_diagnostic_steps": { "type": "boolean", "default": true },
      "min_confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
      "min_trust_level": { "type": "string", "enum": ["L1", "L2", "L3", "L4"], "default": "L4" },
      "limit": { "type": "integer", "minimum": 1, "maximum": 100, "default": 20 }
    },
    "required": ["domain_id", "equipment_class_id"]
  }
}
```

### `explain_equipment_class`

```json
{
  "name": "explain_equipment_class",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "equipment_class_id": { "type": "string" },
      "domain_id": { "type": "string" },
      "language": { "type": "string", "default": "en" }
    },
    "required": ["domain_id", "equipment_class_id"]
  }
}
```

---

## Mapping Between REST And MCP

The semantic read path should use one contract vocabulary across both surfaces:

- `domain_id` and `equipment_class_id` are mandatory everywhere
- `brand` and `model_family` stay applicability filters, not identity
- `min_confidence` and `min_trust_level` are optional ranking and filtering controls
- evidence citation format is identical across API and MCP

This avoids separate semantics for agent consumers and HTTP consumers.

---

## What This Change Does Not Approve

- no implementation of the full knowledge-object `/api/v2/...` route set yet
- no claim that `apps/mcp/` already exists
- no write-capable MCP tools
- no runtime or project-instance query surface
- no replacement of legacy search and trace endpoints
