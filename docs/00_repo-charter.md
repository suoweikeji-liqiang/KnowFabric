# Repository Charter

**Status:** Governance Document - Binding Contract
**Last Updated:** 2026-04-28

> Contract note: the active cross-repository boundary with sw_base_model is
> defined in [24_knowfabric-sw-base-model-contract.md](24_knowfabric-sw-base-model-contract.md).
> If this charter conflicts with that contract, the integration contract wins.

## What KnowFabric Is

KnowFabric is the domain knowledge compilation and authority engine for
sw_base_model. It transforms raw industrial technical documentation into
structured, traceable knowledge objects through a mandatory six-layer data
pipeline, and delivers them to sw_base_model through REST, MCP, and review
feedback surfaces.

**Core Identity:**
- Domain knowledge content engine for sw_base_model
- Evidence-grounded KO compilation from OEM manuals, service guides, and parameter tables
- Six-layer data architecture with mandatory traceability
- Integration-first: REST API, MCP Server, and feedback endpoints as primary interfaces
- Content authority for KOs, evidence chains, trust scoring, and health checks

## Relationship to sw_base_model

sw_base_model owns the structural ontology: equipment classes, point classes,
relation types, location classes, and `ontology_version` publication.
KnowFabric references those IDs read-only and stamps compiled KOs with
`curated_against_ontology_version`.

KnowFabric owns the content layer: KO instances, evidence chains, OEM naming
variants, feedback ingestion, trust signals, and compile/check/publish health
outputs. The binding integration contract is
[24_knowfabric-sw-base-model-contract.md](24_knowfabric-sw-base-model-contract.md).

## What KnowFabric Is NOT

- ❌ NOT a device control or real-time automation system
- ❌ NOT the owner of project-instance or site runtime models
- ❌ NOT the owner of structural ontology definitions now governed by sw_base_model
- ❌ NOT a UI-first product shell

## Mandatory Data Pipeline

**The Only Valid Path:**
```
Raw Document → Page → Chunk → Fact → Retrieval/Export
```

Every knowledge output MUST trace through this pipeline. No shortcuts permitted.

## First Phase Scope - Hard Boundaries

### Phase 1 ONLY Does

1. Document ingestion with deduplication
2. Page generation with traceability
3. Chunk generation with semantic typing
4. Basic retrieval (full-text + vector)
5. Minimal job tracking and logging
6. Two domain packages: hvac, drive
7. Integration API baseline for sw_base_model consumption
8. MCP Server baseline for sw_base_model tool catalog registration
9. Docker deployment baseline (docker-compose)

### Phase 1 Explicitly Does NOT Do

1. ❌ Heavy fact extraction engine
2. ❌ Full review workflow platform
3. ❌ Graph reasoning capabilities
4. ❌ Fine-tuning factory
5. ❌ Rich admin web interface
6. ❌ Project-instance or tenant runtime modeling
7. ❌ Real-time device control
8. ❌ AI-optimized knowledge delivery (context assembly, token budgets — Phase 2)
9. ❌ Python SDK or AI prompt templates (Phase 3)

## Non-Negotiable Constraints (Hard Rules)

These constraints are binding and cannot be bypassed:

### Data Pipeline Constraints

1. **No Layer Skipping** - Every output MUST flow through: Raw Document → Page → Chunk → (Fact) → Output
2. **No Direct Shortcuts** - Cannot generate facts directly from documents without intermediate chunk layer
3. **Traceability Mandatory** - Every output MUST include: source_doc_id, source_page_no, evidence_text
4. **Raw Document Immutability** - Original files are never modified in place
5. **Chunk as Truth Source** - Indexes and derived assets are NOT truth sources; chunks are

### Module Boundary Constraints

6. **No Reverse Dependencies** - ingest cannot depend on parser; parser cannot depend on chunking; chunking cannot depend on extraction
7. **Core Isolation** - core package cannot import from any other package
8. **Domain Package Purity** - domain packages contain only configuration, no runtime business logic
9. **No Circular Dependencies** - Zero tolerance for circular imports between packages

### Quality Gate Constraints

10. **All Gates Must Pass** - No merge without passing: docs check, boundary check, forbidden deps check
11. **Migration-First Schema** - All database schema changes go through migration scripts
12. **No Bypass Flags** - No --skip-checks, --force, or --no-verify flags in CI/CD

## Phase 1 Success Criteria (Acceptance Contract)

Phase 1 is complete ONLY when ALL criteria are met:

### Functional Criteria

1. **Import Capability** - Can import 100+ documents with deduplication working
2. **Data Chain Stability** - document/page/chunk records generated without data loss
3. **sw_base_model Consumption Working** - v2 semantic routes return KO and equipment-class data for sw_base_model
4. **Traceability Present** - Every search result includes: doc_id, page_no, chunk_id, evidence_text
5. **Ontology Version Stamping** - KOs can record the sw_base_model ontology version they were curated against
6. **Feedback Ingestion** - sw_base_model can submit confirmation, rejection, coverage-gap, and conflict events idempotently
7. **Failure Recovery** - Failed jobs logged with stage information; can resume

### Quality Criteria

8. **All Quality Gates Pass** - check-docs, check-boundaries, check-forbidden-deps all return exit code 0
9. **Domain Packages Valid** - hvac and drive packages have complete manifest/schema/profile
10. **Documentation Complete** - All packages have README; all core docs exist
11. **Contract Mirror Enforced** - KnowFabric and sw_base_model contract §1-10 SHA checks pass

### Non-Criteria (Explicitly NOT Required for Phase 1)

- ❌ Heavy fact extraction (minimal extraction acceptable)
- ❌ Full review workflow (basic status tracking acceptable)
- ❌ Rich admin interface (API-only acceptable)
- ❌ Graph reasoning
- ❌ Fine-tuning export

## Evolution Principles (Development Priorities)

These principles govern all development decisions:

1. **API Before Implementation** - Define and expose integration APIs before building internal features
2. **AI-Consumable Before Human-Only** - Ensure outputs are structured for AI consumption, not just human reading
3. **Platform Before Shell** - Build data pipeline and APIs before building UI layers
4. **Traceability Before Performance** - Ensure evidence chains work before optimizing speed
5. **Boundaries Before Implementation** - Define module contracts before writing code
6. **Domain Packages Before Hardcoding** - Use pluggable domain configs, not hardcoded logic
7. **Migration Before Schema Change** - All DB changes go through versioned migration scripts
8. **Gates Before Merge** - All quality gates must pass; no bypass permitted

## Governance Model

This repository operates under strict governance:

- **Charter Status**: Binding contract, not aspirational document
- **Boundary Violations**: Automatic PR rejection via CI checks
- **Quality Gates**: Mandatory for all merges, no exceptions
- **Documentation**: Required for all packages and domain packages
- **Review Authority**: Tech lead has final authority on boundary disputes
