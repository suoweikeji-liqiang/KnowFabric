# Ontology Authority Architecture

**Status:** Rebuild Architecture Contract
**Last Updated:** 2026-03-17

This document defines the target architecture for the KnowFabric rebuild track.

For the rebuild track, this document supersedes the legacy domain-package assumptions in `docs/03_domain-package-spec.md`. The six-layer evidence pipeline remains mandatory.

---

## Product Identity

KnowFabric is an ontology-first domain knowledge authority and publishing engine for industrial equipment knowledge.

Its purpose is to turn technical documentation into:

- canonical domain ontology packages
- evidence-grounded knowledge objects
- semantic delivery APIs for AI agents and software systems
- curated knowledge packs that can be consumed independently of any single downstream application

KnowFabric is not a project digital twin, controls runtime, or site modeling application.

---

## Core Boundary

### KnowFabric Owns

- canonical equipment class identifiers
- mappings to external standards such as Brick
- domain relation vocabularies used for knowledge representation
- aliases, terminology normalization, and multilingual labels
- evidence-grounded knowledge objects attached to equipment classes
- semantic query and publishing interfaces

### KnowFabric Does Not Own

- individual site or project instances
- physical topology of a specific installation
- point binding for a specific BMS deployment
- runtime control logic for a specific building
- telemetry processing and operational optimization

This boundary is non-negotiable. If a model requires a concrete site instance, it belongs downstream.

---

## Target Architecture

KnowFabric is rebuilt around four layers.

### 1. Ontology Layer

The ontology layer defines what exists in a supported domain.

It includes:

- equipment class hierarchy
- external standard mappings
- aliases and labels
- relation vocabulary
- knowledge anchor types

Example concepts:

- `centrifugal_chiller`
- `condenser_water_pump`
- `frequency_converter`
- `fault_code`
- `maintenance_procedure`

### 2. Evidence Pipeline Layer

The evidence pipeline remains the mandatory ingestion backbone:

`Raw Document -> Page -> Chunk -> Knowledge Object -> Delivery Surface`

Additional rules:

- each chunk may be anchored to one or more ontology classes
- each extracted knowledge object must reference the ontology anchor it belongs to
- every delivery surface must preserve document, page, and chunk traceability

### 3. Knowledge Object Layer

Knowledge is no longer treated as an undifferentiated fact stream. It is organized into typed knowledge objects attached to ontology nodes.

Core knowledge object types for the rebuild track:

- `fault_code`
- `parameter_spec`
- `symptom`
- `diagnostic_step`
- `maintenance_procedure`
- `commissioning_step`
- `selection_criterion`
- `performance_spec`

Each knowledge object must contain:

- stable identifier
- ontology anchor (`equipment_class_id` or another canonical class)
- source evidence references
- trust metadata
- optional brand/model applicability

### 4. Delivery Layer

The delivery layer exposes knowledge through semantics-first interfaces.

Baseline delivery surfaces:

- REST API
- MCP tools
- exportable knowledge packs
- later SDKs

The delivery layer must support both:

- generic search and evidence trace
- semantic knowledge retrieval by ontology identifier

---

## Domain Package v2

The rebuild track replaces the current manifest-centric domain package with an ontology-first package layout.

```text
domain_packages/{domain_id}/
├── package.yaml
├── ontology/
│   ├── classes.yaml
│   ├── relations.yaml
│   ├── aliases.yaml
│   ├── mappings.yaml
│   └── knowledge_anchors.yaml
├── extraction/
│   ├── entities.yaml
│   ├── relations.yaml
│   ├── confidence_rules.yaml
│   └── prompts/
├── delivery/
│   ├── query_contracts.yaml
│   ├── response_profiles.yaml
│   └── terminology.yaml
├── coverage/
│   ├── brands.yaml
│   ├── document_profiles.yaml
│   └── exclusions.yaml
└── examples/
    └── example_queries.yaml
```

### `package.yaml`

Owns package metadata and release policy:

- `domain_id`
- `domain_name`
- `package_version`
- `ontology_version`
- `supported_languages`
- `supported_knowledge_objects`
- `maintainers`

### `ontology/classes.yaml`

Defines canonical classes and identifiers.

Minimum fields per class:

- `id`
- `label`
- `parent_id`
- `kind` (`equipment`, `component`, `concept`)
- `external_mappings`
- `aliases`
- `knowledge_anchors`

Example:

```yaml
classes:
  - id: centrifugal_chiller
    label:
      en: Centrifugal Chiller
      zh: 离心式冷水机组
    parent_id: chiller
    kind: equipment
    external_mappings:
      brick: brick:Centrifugal_Chiller
    aliases:
      - centrifugal chiller
      - turbo chiller
    knowledge_anchors:
      - fault_code
      - parameter_spec
      - maintenance_procedure
      - performance_spec
```

#### Knowledge Anchor Authority

`knowledge_anchors` is the authoritative capability list attached to an
equipment or component class.

The corresponding `kind: concept` classes such as `fault_code`,
`parameter_spec`, or `maintenance_procedure` are metadata carriers for those
anchors. They provide:

- multilingual labels
- aliases
- optional standard-facing metadata

They do **not** replace the `knowledge_anchors` list as the source of truth for
"what knowledge can attach to this equipment class".

Every `supported_knowledge_object` in `package.yaml` should therefore have a
matching `kind: concept` class so that semantic delivery can carry labels and
aliases consistently.

### `ontology/relations.yaml`

Defines canonical relation vocabulary.

Relation families:

- composition: `has_component`
- applicability: `applies_to`
- diagnostic causality: `indicates`, `causes`, `may_cause`
- maintenance dependency: `requires`
- standard mapping: `same_as_standard_class`

Physical topology relation definitions may be referenced for interoperability, but site-specific relation instances stay outside KnowFabric.

### `ontology/mappings.yaml`

Defines interoperability mappings to external standards and downstream identifiers.

Initial target:

- Brick mappings for HVAC and related equipment classes

Future targets may include:

- Haystack
- vendor catalogs
- customer-specific adapter maps

When a downstream standard uses a different semantic abstraction than
KnowFabric, the mapping entry should carry metadata that explains the scope of
the mapping.

Example:

- a physical field sensor device in KnowFabric may map to `brick:Sensor` for
  interoperability, but the entry should declare that the mapping is being used
  as a physical-device proxy rather than as a point-level assertion.

---

## Canonical Identifier Rules

Every ontology-owned identifier must follow these rules:

1. stable snake_case identifier
2. globally unique within its domain package
3. never encode deployment-specific context
4. external mappings are attributes, not replacements
5. aliases do not become canonical ids

Canonical examples:

- `chiller`
- `centrifugal_chiller`
- `fault_code`
- `parameter_spec`

Non-canonical examples:

- `project_a_chiller_01`
- `ahu_3f_west`
- `chw_supply_temp_sensor_b1`

Those belong to downstream runtime systems.

---

## Evidence and Storage Implications

The rebuild track requires stronger anchoring between content and ontology.

### Chunk-Level Anchoring

Each chunk may record:

- detected `equipment_class_ids`
- detected brand/model candidates
- document type
- knowledge anchor hints

Chunk anchoring is probabilistic and may be revised during review.

### Knowledge Object Persistence

Knowledge objects require storage fields for:

- `knowledge_object_id`
- `knowledge_type`
- `equipment_class_id`
- `brand_id` or `brand_name`
- `model_family`
- `evidence_refs[]`
- `confidence`
- `trust_level`
- lifecycle status

### Evidence Integrity

No knowledge object may exist without at least one evidence reference back to:

- document id
- page number
- chunk id
- evidence text or excerpt window

---

## Delivery Contract Direction

Search remains necessary, but it is no longer the primary expression of product value.

The rebuild track adds semantic delivery contracts such as:

- `get_fault_knowledge(equipment_class_id, fault_code, brand?)`
- `get_parameter_profile(equipment_class_id, parameter_category, brand?, model_family?)`
- `get_diagnostic_path(equipment_class_id, symptom_id | symptom_text)`
- `get_maintenance_guidance(equipment_class_id, task_type, brand?)`
- `explain_equipment_class(equipment_class_id)`

Each response must include:

- canonical ontology identifiers
- structured knowledge payload
- evidence citations
- confidence and trust metadata
- applicability filters used by the query

---

## Interoperability with Downstream Systems

Downstream systems such as `sw_base_model` consume KnowFabric through ontology and knowledge contracts.

### Expected Integration Pattern

1. downstream system maps its local runtime model to KnowFabric ontology ids
2. downstream system queries KnowFabric by equipment class and symptom/fault context
3. KnowFabric returns evidence-grounded knowledge objects
4. downstream system keeps ownership of runtime reasoning, topology, and action execution

### Anti-Pattern

KnowFabric must not ingest downstream site instance models as its own ontology source of truth. Downstream systems may publish adapters, but canonical class ownership stays in KnowFabric.

---

## Success Criteria for the Rebuild Architecture

The rebuild architecture is considered established when:

1. HVAC package v2 defines canonical classes and Brick mappings
2. Drive package v2 uses the same ontology package conventions
3. chunks can be anchored to ontology ids
4. at least three semantic query contracts are defined and testable
5. evidence-grounded knowledge objects are queryable by ontology id
6. downstream systems can integrate without importing project-instance concepts into KnowFabric
