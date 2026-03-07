# Repository Charter

**Status:** Governance Document - Binding Contract
**Last Updated:** 2026-03-07

## What KnowFabric Is

KnowFabric is an industrial knowledge injection platform that transforms raw technical documentation into structured, traceable knowledge assets through a mandatory six-layer data pipeline.

**Core Identity:**
- Knowledge engineering platform for industrial/energy domains
- Domain-agnostic foundation with pluggable domain packages
- Six-layer data architecture with mandatory traceability
- Service-oriented platform providing retrieval and query APIs

## What KnowFabric Is NOT

- ❌ NOT a chatbot or conversational AI shell
- ❌ NOT a document management or file storage system
- ❌ NOT an automatic knowledge graph inference engine
- ❌ NOT a device control or real-time automation system
- ❌ NOT a multi-tenant SaaS platform
- ❌ NOT a general-purpose RAG demo

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

### Phase 1 Explicitly Does NOT Do

1. ❌ Heavy fact extraction engine
2. ❌ Full review workflow platform
3. ❌ Graph reasoning capabilities
4. ❌ Fine-tuning factory
5. ❌ Rich admin web interface
6. ❌ Multi-tenant features
7. ❌ Real-time device control

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
3. **Retrieval Working** - Full-text and vector search return results with <2s latency
4. **Traceability Present** - Every search result includes: doc_id, page_no, chunk_id, evidence_text
5. **Incremental Import** - Can add new documents without reprocessing existing ones
6. **Partial Rerun** - Can reprocess specific doc_id without affecting others
7. **Failure Recovery** - Failed jobs logged with stage information; can resume

### Quality Criteria

8. **All Quality Gates Pass** - check-docs, check-boundaries, check-forbidden-deps all return exit code 0
9. **Domain Packages Valid** - hvac and drive packages have complete manifest/schema/profile
10. **Documentation Complete** - All packages have README; all core docs exist

### Non-Criteria (Explicitly NOT Required for Phase 1)

- ❌ Heavy fact extraction (minimal extraction acceptable)
- ❌ Full review workflow (basic status tracking acceptable)
- ❌ Rich admin interface (API-only acceptable)
- ❌ Graph reasoning
- ❌ Fine-tuning export

## Evolution Principles (Development Priorities)

These principles govern all development decisions:

1. **Platform Before Shell** - Build data pipeline and APIs before building UI layers
2. **Traceability Before Performance** - Ensure evidence chains work before optimizing speed
3. **Boundaries Before Implementation** - Define module contracts before writing code
4. **Domain Packages Before Hardcoding** - Use pluggable domain configs, not hardcoded logic
5. **Migration Before Schema Change** - All DB changes go through versioned migration scripts
6. **Gates Before Merge** - All quality gates must pass; no bypass permitted

## Governance Model

This repository operates under strict governance:

- **Charter Status**: Binding contract, not aspirational document
- **Boundary Violations**: Automatic PR rejection via CI checks
- **Quality Gates**: Mandatory for all merges, no exceptions
- **Documentation**: Required for all packages and domain packages
- **Review Authority**: Tech lead has final authority on boundary disputes
