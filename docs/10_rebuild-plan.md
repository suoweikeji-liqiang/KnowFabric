# Rebuild Plan

**Status:** Execution Plan - Rebuild Track
**Last Updated:** 2026-03-17

This document is the execution plan for rebuilding KnowFabric into an ontology-first domain knowledge authority.

For the rebuild track, this plan supersedes the legacy delivery sequencing in `docs/05_phase-plan.md`.

---

## Program Goal

Deliver a version of KnowFabric that can stand as an independent product and that downstream systems can consume through stable ontology ids and evidence-grounded semantic knowledge APIs.

The rebuild keeps the six-layer evidence discipline and replaces the current manifest-centric domain model with ontology-first packages and semantic delivery contracts.

---

## Program Principles

1. Keep the evidence pipeline, replace the weak product boundary.
2. Define ontology contracts before rewriting storage or APIs.
3. Move one domain all the way through first, then generalize.
4. Preserve compatibility surfaces where cheap; do not preserve accidental schema debt.
5. Prefer explicit package versioning and migration scripts over ad hoc rewrites.

---

## Workstream 0: Rebuild Ground Rules

### Goal

Freeze the direction of the rebuild and make contributor expectations explicit.

### Deliverables

- ADR-0003 accepted
- target architecture document
- rebuild execution plan
- README and docs index pointing to rebuild materials

### Exit Criteria

- contributors can identify which documents govern the rebuild track
- no ambiguity remains about KnowFabric vs downstream runtime ownership

---

## Workstream 1: Ontology Package Core

### Goal

Define the package format and canonical identifiers for domain ontology.

### Deliverables

- `domain_packages/*/package.yaml` contract
- v2 ontology folder structure
- canonical identifier rules
- Brick mapping contract for supported HVAC classes
- relation vocabulary baseline
- migration notes from legacy `manifest.yaml` package shape

### First Implementation Targets

- HVAC class hierarchy
- Drive class hierarchy
- alias and multilingual label support

### Exit Criteria

- HVAC package v2 exists and validates
- at least 80 percent of current HVAC equipment labels map to canonical ids
- Drive package v2 follows the same schema

---

## Workstream 2: Evidence Anchoring and Knowledge Objects

### Goal

Attach chunks and extracted knowledge to ontology ids instead of leaving them as free-floating facts.

### Deliverables

- chunk anchor model
- knowledge object schema
- evidence reference contract
- storage migrations for ontology and knowledge objects
- review status model for anchored knowledge

### Design Constraints

- no knowledge object without evidence
- ontology anchor required for semantic delivery
- chunk truth source remains intact

### Exit Criteria

- chunks can store ontology anchors
- at least four knowledge object types persist with evidence
- a reviewer can inspect knowledge attached to an equipment class

---

## Workstream 3: Semantic Delivery APIs and MCP

### Goal

Make KnowFabric valuable as a product without requiring consumers to reconstruct meaning from raw search results.

### Deliverables

- semantic REST endpoints
- semantic MCP tools
- response envelope for ontology ids, trust, confidence, and evidence
- fallback search and trace compatibility endpoints
- consumer examples for AI agents and external systems

### Minimum Query Set

- fault knowledge by equipment class and code
- parameter profile by equipment class and category
- maintenance guidance by equipment class and task type

### Exit Criteria

- at least three semantic endpoints work end to end
- at least three MCP tools expose semantic retrieval
- a downstream consumer can resolve equipment class knowledge without parsing free-text chunks manually

---

## Workstream 4: Domain Rewrite and Curation

### Goal

Prove the architecture with real packages and curated knowledge coverage.

### Deliverables

- HVAC package rewritten to v2
- Drive package rewritten to v2
- initial brand coverage lists
- curated seed knowledge for major equipment families
- review workflow tuned for ontology-attached knowledge

### Recommended Proof Points

- centrifugal chiller
- screw chiller
- chilled water pump
- cooling tower
- common VFD families

### Exit Criteria

- HVAC and Drive packages both produce usable semantic responses
- evidence and trust metadata survive the full pipeline
- at least one downstream integration can consume the new contracts

---

## Workstream 5: Productization

### Goal

Package KnowFabric so third parties can adopt it independently of internal systems.

### Deliverables

- product packaging for API/MCP deployment
- private deployment guidance
- curated knowledge pack packaging strategy
- versioning and release notes for ontology packages
- optional SDK backlog definition

### Exit Criteria

- third-party evaluation path exists without `sw_base_model`
- ontology package versions are publishable artifacts
- curated knowledge packs can be described as a sellable product surface

---

## Immediate Backlog

These are the next concrete tickets to execute after this planning drop:

1. Define `package.yaml` and `ontology/classes.yaml` schemas.
2. Rewrite `domain_packages/hvac` into a v2 skeleton alongside the legacy package.
3. Draft storage changes for ontology classes, aliases, mappings, chunk anchors, and knowledge objects.
4. Draft semantic API contracts and MCP tool schemas.
5. Create a migration checklist from legacy package files to v2 package files.

---

## Sequencing Notes

- Do not start with database migrations before ontology identifiers are stable.
- Do not start with SDK work before semantic API contracts stabilize.
- Do not attempt cross-domain graph reasoning before HVAC and Drive both work under the new ontology model.
- Do not import downstream runtime topology into KnowFabric just to accelerate demos.

---

## Definition of Rebuild Readiness

The rebuild track is ready to move from planning to execution when:

1. ontology package schemas are approved
2. one pilot domain package can be rewritten without unresolved boundary questions
3. storage owners agree on anchor and knowledge object persistence
4. API owners agree on the initial semantic contract set
