# ADR-0003: Promote KnowFabric to Domain Knowledge Authority and Ontology Owner

**Status:** Accepted
**Date:** 2026-03-17
**Deciders:** Project leadership

## Context

KnowFabric's current positioning as an embeddable knowledge engineering engine was a meaningful improvement over its original "platform" framing, but it still leaves the product too close to generic document processing and RAG infrastructure.

Three forces now make a larger reboot both possible and desirable:

1. **Both internal products are early enough to reset**. KnowFabric and its primary downstream consumer (`sw_base_model`) are both still malleable. We can redraw boundaries before compatibility debt hardens.
2. **The defensible value is not the pipeline alone**. Document ingestion, chunking, indexing, and extraction are necessary, but they are not sufficient differentiation. The durable moat is canonical industrial ontology, curated equipment knowledge, evidence traceability, and domain-specific delivery contracts.
3. **KnowFabric has value beyond a single downstream system**. Equipment vendors, service organizations, AI copilots, design tools, and maintenance platforms all need structured, traceable equipment knowledge. A product defined too narrowly around one runtime system leaves market value on the table.

At the same time, we must preserve a critical boundary:

- KnowFabric SHOULD own **what a class of equipment is and what knowledge attaches to it**.
- KnowFabric MUST NOT own **how a specific project instance is wired, monitored, or controlled at runtime**.

Without this boundary, KnowFabric would collapse into a project digital twin or controls application, which is outside its product scope.

## Decision

KnowFabric is promoted from an embeddable knowledge engineering engine to an **ontology-first domain knowledge authority and publishing engine for industrial equipment knowledge**.

This decision introduces five binding changes for the rebuild track.

### 1. KnowFabric owns canonical domain ontology packages

For each supported domain, KnowFabric becomes the source of truth for:

- equipment class identifiers
- ontology mappings to external standards such as Brick
- aliases and term normalization
- relation vocabularies relevant to knowledge delivery
- knowledge anchor types attached to equipment classes

The ontology package becomes a product artifact, not just an internal config folder.

### 2. Domain packages become ontology-first

Current manifest-centric domain packages are superseded in the rebuild track by a richer package model that separates:

- ontology definition
- extraction contracts
- delivery/query contracts
- evidence and coverage metadata

The package format is described in `docs/09_ontology-authority-architecture.md`.

### 3. Semantic knowledge delivery becomes a first-class interface

KnowFabric will continue to support search and trace APIs, but its differentiating interfaces move up one level to semantic queries such as:

- fault knowledge by equipment class and code
- parameter knowledge by equipment class, brand, and category
- diagnostic paths by symptom and equipment class
- maintenance or commissioning guidance by equipment class

These interfaces are defined around ontology identifiers and evidence-backed knowledge objects, not just free-text retrieval.

### 4. Runtime/project-instance modeling stays outside KnowFabric

KnowFabric does not own:

- site topology
- point bindings for a specific building or project
- live telemetry models
- control sequences for a specific installation
- runtime actuation or supervisory control

Those concerns belong to downstream systems such as `sw_base_model` or other customer applications.

### 5. KnowFabric is designed as an independent product, not only an internal dependency

KnowFabric must be productizable for third parties through:

- embeddable APIs and MCP tools
- curated domain knowledge packs
- private deployment options
- customer-specific document ingestion and evidence grounding

`sw_base_model` is treated as the first major consumer, not the defining boundary of the product.

## Consequences

### Positive

- **Stronger differentiation**: KnowFabric competes as a knowledge authority, not as a generic ingestion stack.
- **Clearer product boundary**: ontology and knowledge authority live here; project runtime intelligence lives elsewhere.
- **Third-party viability**: the product can be sold to customers who do not use `sw_base_model`.
- **Cleaner integration with downstream systems**: consumers query stable equipment-class identifiers instead of inventing their own taxonomies.
- **Better reuse across domains**: new domains can be added through ontology packages and knowledge anchors rather than ad hoc extraction schemas.

### Negative

- **Broader rebuild scope**: package format, schemas, APIs, and parts of the storage model must change.
- **Legacy docs become partially obsolete**: current phase and package contracts describe the baseline architecture, not the rebuild target.
- **Migration work increases**: existing hvac and drive packages need to be rewritten against the new ontology-first format.

### Mitigations

- Preserve the six-layer evidence pipeline as a non-negotiable invariant.
- Rebuild in explicit workstreams instead of performing piecemeal edits.
- Keep search and trace APIs operational as compatibility surfaces while semantic APIs are added.
- Document the rebuild separately and explicitly so contributors do not mix old and new assumptions.

## Scope Boundary Clarification

KnowFabric owns:

- equipment class ontology
- evidence-grounded knowledge objects
- semantic delivery contracts
- terminology normalization
- curated domain knowledge packs

KnowFabric does not own:

- project instance graphs
- site-specific topology templates
- BMS point mapping for individual jobs
- runtime optimization or control
- field execution workflows

## Documents Introduced or Updated

1. `docs/09_ontology-authority-architecture.md` — target architecture for the rebuild track
2. `docs/10_rebuild-plan.md` — phased execution plan for the rebuild track
3. `README.md` — product direction and rebuild entry points
4. `docs/README.md` — documentation navigation for rebuild work
5. `docs/00_repo-charter.md` — note clarifying current baseline vs rebuild track
6. `docs/05_phase-plan.md` — note clarifying legacy phase plan vs rebuild track

## Follow-Up

The next implementation work must start with:

1. ontology package format definition
2. hvac package rewrite against the new format
3. storage contract for ontology anchors and knowledge objects
4. semantic API contract drafts
