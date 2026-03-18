# Domain Package V2 Migration Checklist

**Status:** Rebuild Working Checklist
**Last Updated:** 2026-03-17

Use this checklist when moving a legacy domain package into the ontology-first
`v2` layout. Keep the legacy files in place until the v2 package has a stable
consumer.

---

## Preconditions

1. Confirm the package only models canonical equipment ontology, knowledge objects, evidence contracts, and semantic delivery placeholders.
2. Confirm no project-instance topology, point binding, runtime control, or site graph data is being introduced.
3. Confirm the six-layer evidence chain remains `Document -> Page -> Chunk -> Knowledge Object -> Delivery`.

---

## File Mapping

### Legacy `manifest.yaml` -> `v2/package.yaml`

- Move domain metadata into `domain_id`, `domain_name`, `package_version`, and `ontology_version`.
- Replace legacy coverage prose with `supported_knowledge_objects` and `supported_languages`.
- Keep maintainers explicit.

### Legacy `label_schema.yaml` -> `v2/ontology/classes.yaml` and `v2/ontology/aliases.yaml`

- Convert equipment labels into canonical `classes.yaml` identifiers.
- Preserve synonyms and multilingual terms in `aliases.yaml`.
- Do not convert site-specific labels into canonical ids.

### Legacy `entity_schema.yaml` -> `v2/ontology/knowledge_anchors.yaml` and `v2/extraction/entities.yaml`

- Promote durable knowledge object types into `knowledge_anchors.yaml`.
- Keep extraction-facing hints in `extraction/entities.yaml`.
- Avoid mixing extraction roles with canonical ontology identifiers.

### Legacy `relation_schema.yaml` -> `v2/ontology/relations.yaml` and `v2/extraction/relations.yaml`

- Move canonical relation vocabulary into `ontology/relations.yaml`.
- Keep extraction heuristics or relation hints in `extraction/relations.yaml`.
- Exclude project-topology relation instances from KnowFabric.

### Legacy `retrieval_profile.yaml` -> `v2/delivery/query_contracts.yaml` and `v2/delivery/response_profiles.yaml`

- Reframe retrieval behavior around semantic query contracts.
- Keep evidence, trust, and ontology ids explicit in response profiles.
- Preserve search compatibility outside the package contract if needed.

### Legacy `extraction_templates/` -> `v2/extraction/prompts/`

- Carry over only prompts that support ontology-anchored knowledge extraction.
- Defer prompt work if ontology identifiers are still unstable.

---

## Review Checklist

1. `package.yaml` validates against `domain_packages/_schemas/v2/package.schema.json`.
2. `ontology/classes.yaml` validates against `domain_packages/_schemas/v2/ontology.classes.schema.json`.
3. Every class id is stable snake_case and deployment-agnostic.
4. Every equipment class maps back to at least one legacy label or package term.
5. Every `supported_knowledge_object` has a matching `kind: concept` metadata class.
6. Every semantic delivery placeholder still preserves chunk-level evidence fields.
7. Legacy package files remain untouched until storage and API consumers are ready.
