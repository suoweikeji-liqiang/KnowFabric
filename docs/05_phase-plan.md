# Phase Plan

**Status:** Delivery Contract - Binding Acceptance Criteria
**Last Updated:** 2026-03-13

This document defines phase delivery contracts with hard acceptance criteria.

---

## Phase 1: Foundation Layer + Integrable API

### Goal
Establish document/page/chunk/retrieval foundation with full traceability, exposed via integration APIs and MCP Server, deployable via Docker.

### In Scope

1. Document ingestion with deduplication
2. Page generation with traceability
3. Chunk generation with semantic typing
4. Basic retrieval (full-text + vector)
5. Minimal job tracking and logging
6. Two domain packages: hvac, drive
7. Integration API baseline (4 endpoints)
8. MCP Server baseline (3 tools)
9. Docker deployment baseline

### Out of Scope

- ❌ Heavy fact extraction engine
- ❌ Full review workflow platform
- ❌ Graph reasoning capabilities
- ❌ Fine-tuning factory
- ❌ Rich admin web interface
- ❌ Multi-tenant features
- ❌ AI-optimized knowledge delivery (context assembly, token budgets)
- ❌ Python SDK or AI prompt templates

### Deliverables

**Data Layer:**
- document table with deduplication
- document_page table with traceability
- content_chunk table with semantic typing
- Traceability chain: chunk → page → document

**Processing:**
- Document import pipeline
- Page parsing pipeline
- Chunk generation pipeline

**Retrieval:**
- Full-text search on chunks
- Vector search on chunks
- Hybrid search with domain/brand filtering

**Integration API (New):**
- `POST /api/v1/documents/upload` — Async document upload (returns 202 + job_id)
- `GET /api/v1/jobs/{job_id}` — Processing status polling
- `GET /api/v1/chunks/{chunk_id}/trace` — Traceability chain (chunk → page → document)
- `POST /api/v1/chunks/search` — Chunk search with traceability fields
- OpenAPI documentation auto-generated

**MCP Server (New):**
- `search_knowledge` — Search chunks by query with domain filtering
- `trace_evidence` — Retrieve full evidence chain for a chunk
- `list_domains` — List available domain packages and their coverage
- MCP transport: stdio (for local AI agent integration)

**Deployment (New):**
- `docker-compose.yml` for API + PostgreSQL + worker
- Environment variable configuration
- Health check endpoints

**Infrastructure:**
- Database schema baseline
- File storage for documents and page assets
- Job tracking table
- Stage-level logging

### Acceptance Criteria

Phase 1 is complete ONLY when ALL criteria are met:

1. ✅ Can import 100+ documents successfully
2. ✅ Document/page/chunk structure is stable (no data loss)
3. ✅ Chunks are searchable via full-text and vector search
4. ✅ Search results include: doc_id, page_no, chunk_id, evidence_text
5. ✅ Supports incremental import (new documents only)
6. ✅ Supports partial re-processing (by doc_id)
7. ✅ Processing failures are logged with stage information
8. ✅ All quality gates pass (check-docs, check-boundaries, check-forbidden-deps)
9. ✅ hvac and drive domain packages have complete manifest/schema
10. ✅ All packages have README files
11. ✅ Integration API: can upload document and poll status from external client
12. ✅ Integration API: can search chunks and receive traceability fields
13. ✅ MCP Server: AI agent can call search_knowledge and receive structured results
14. ✅ Docker: `docker-compose up` starts a working system

### Exit Criteria

Cannot proceed to Phase 2 until:

1. All acceptance criteria met
2. Sample document set (100+ docs) processed successfully
3. Traceability chain validated end-to-end
4. Quality gates passing consistently
5. Documentation complete
6. External client can call API and MCP endpoints successfully
7. Docker deployment validated

---

## Phase 2: Fact Extraction + AI-Optimized Knowledge Delivery

### Goal
Extract structured facts from chunks with human review workflow, and optimize knowledge delivery for AI agent consumption.

### In Scope

1. Fact extraction from chunks
2. Entity normalization
3. Review workflow (approve/reject/modify)
4. Structured fact query API
5. Context assembly API (token-budget-aware)
6. AI-friendly query endpoints
7. Confidence/trust level semantics in all responses
8. Enhanced MCP tools

### Out of Scope

- ❌ Advanced graph reasoning
- ❌ Fine-tuning sample export
- ❌ Complex multimodal processing
- ❌ Python SDK
- ❌ AI prompt templates
- ❌ Domain package distribution

### Deliverables

**Data Layer:**
- extracted_fact table
- review_record table
- Entity normalization mappings

**Processing:**
- Fact extraction pipeline
- Confidence scoring
- Trust level assignment (L1-L4)

**Review Workflow:**
- Review queue management
- Approve/reject/modify operations
- Review audit trail

**Query:**
- Structured fact query API
- Filter by trust level, review status
- Fact results include evidence and traceability

**AI-Optimized Delivery (New):**
- `POST /api/v1/knowledge/assemble` — Context assembly with token budget control
  - Strategies: greedy (max relevance), diverse (topic spread), deep (single-topic depth)
  - Response includes: content blocks, token counts, confidence scores
- `POST /api/v1/knowledge/query` — AI-friendly query endpoint
  - Structured context blocks (content + citation + confidence + token_count)
  - Respects max_tokens parameter
- All API responses include confidence/trust level fields

**Enhanced MCP Tools (New):**
- `query_knowledge` — Token-budget-aware knowledge query
- `get_facts` — Query structured facts with evidence
- `review_fact` — Submit fact review (for AI-assisted review workflows)

### Acceptance Criteria

1. ✅ Can extract facts from chunks with evidence
2. ✅ Facts include subject-relation-object structure
3. ✅ Facts link to source chunk/page/document
4. ✅ Can query facts by entity, relation, domain
5. ✅ Can review and approve/reject facts
6. ✅ Review operations are audited
7. ✅ Approved facts have higher trust level
8. ✅ Context assembly API respects token budget within 5% margin
9. ✅ All knowledge responses include confidence scores
10. ✅ AI agent can assemble context via MCP with token budget control

### Exit Criteria

Cannot proceed to Phase 3 until:

1. All acceptance criteria met
2. At least 1000 facts reviewed and approved
3. Fact quality validated (sample 100 facts)
4. Review workflow tested with real users
5. Context assembly validated with at least 2 AI agent integrations

---

## Phase 3: Domain Deepening + SDK + Distribution

### Goal
Strengthen domain package mechanism, provide Python SDK, AI prompt templates, terminology mappings, and domain package distribution.

### In Scope

1. Complete HVAC and drive domain packages
2. Fine-tuning sample export (JSONL)
3. Export API
4. Python SDK (`knowfabric` package)
5. AI prompt templates per domain
6. Terminology mapping per domain
7. Domain package distribution mechanism

### Out of Scope

- ❌ Advanced graph inference
- ❌ Automatic model training
- ❌ Real-time device control

### Deliverables

**Domain Packages:**
- HVAC domain package complete (including AI prompt templates, terminology)
- Drive domain package complete (including AI prompt templates, terminology)
- Domain package validation tools

**Export:**
- Fine-tuning sample export (JSONL)
- Topic knowledge package export
- RAG snapshot export

**Python SDK (New):**
- `knowfabric` Python package
- Document upload, search, trace, fact query methods
- Context assembly with token budget
- Async support
- Published to PyPI (or internal registry)

**AI Prompt Templates (New):**
- Per-domain prompt templates (`ai_prompt_templates.yaml`)
- Templates for: fault diagnosis, parameter lookup, maintenance guidance
- Template variables mapped to knowledge fields

**Terminology (New):**
- Per-domain terminology mapping (`terminology.yaml`)
- Chinese-English term pairs for industrial vocabulary
- Synonym normalization rules

**Distribution (New):**
- Domain package versioning and packaging
- Domain package registry (local or remote)
- Domain package install/update mechanism

**Infrastructure:**
- Export file storage

### Acceptance Criteria

1. ✅ HVAC and drive domain packages complete and validated
2. ✅ Can export fine-tuning samples filtered by domain/trust level
3. ✅ Can export topic-specific knowledge packages
4. ✅ Python SDK can perform full workflow (upload → search → trace)
5. ✅ AI prompt templates produce usable prompts for each domain
6. ✅ Terminology mapping covers 90%+ of domain-specific terms
7. ✅ Domain packages can be versioned and distributed independently

### Exit Criteria

Cannot proceed to Phase 4 until:

1. All acceptance criteria met
2. SDK tested by at least 2 integration partners
3. Export formats validated
4. Domain packages complete, documented, and distributable
5. AI prompt templates validated with real AI agent workflows

---

## Phase 4: Advanced Capabilities + Cross-Domain

### Goal
Add graph reasoning, fine-tuning sample factory, additional domains, and cross-domain knowledge linking.

### In Scope

1. Graph candidate generation
2. Sample generation templates
3. Energy storage domain package
4. Photovoltaics domain package
5. Cross-domain knowledge linking

### Out of Scope

- TBD based on Phase 3 learnings

### Deliverables

**Graph:**
- Graph candidate generation
- Entity resolution and merging
- Graph query API

**Fine-tuning:**
- Sample generation templates
- Sample quality scoring

**Domain Expansion:**
- Energy storage domain package
- Photovoltaics domain package

**Cross-Domain (New):**
- Cross-domain entity linking (e.g., HVAC ↔ drive shared entities)
- Cross-domain knowledge graph connections
- Unified cross-domain search

### Acceptance Criteria

1. ✅ Can generate graph candidates from facts
2. ✅ Can query graph relationships
3. ✅ Can generate diverse fine-tuning samples
4. ✅ Energy storage and PV domain packages operational
5. ✅ Cross-domain queries return results spanning multiple domains

### Exit Criteria

TBD based on Phase 3 completion.

---

## Phase Transition Rules

### Moving Between Phases

**General Rule:** Cannot start Phase N+1 until Phase N exit criteria are met.

**Validation Required:**
- All acceptance criteria met
- Exit criteria validated
- Quality gates passing
- Documentation complete

**No Exceptions:** Phase boundaries are hard gates.
