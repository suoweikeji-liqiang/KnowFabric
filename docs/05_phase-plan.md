# Phase Plan

**Status:** Delivery Contract - Binding Acceptance Criteria
**Last Updated:** 2026-03-07

This document defines phase delivery contracts with hard acceptance criteria.

---

## Phase 1: Foundation Layer

### Goal
Establish document/page/chunk/retrieval foundation with full traceability.

### In Scope

1. Document ingestion with deduplication
2. Page generation with traceability
3. Chunk generation with semantic typing
4. Basic retrieval (full-text + vector)
5. Minimal job tracking and logging
6. Two domain packages: hvac, drive

### Out of Scope

- ❌ Heavy fact extraction engine
- ❌ Full review workflow platform
- ❌ Graph reasoning capabilities
- ❌ Fine-tuning factory
- ❌ Rich admin web interface
- ❌ Multi-tenant features

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

### Exit Criteria

Cannot proceed to Phase 2 until:

1. All acceptance criteria met
2. Sample document set (100+ docs) processed successfully
3. Traceability chain validated end-to-end
4. Quality gates passing consistently
5. Documentation complete

---

## Phase 2: Fact Extraction and Review

### Goal
Extract structured facts from chunks with human review workflow.

### In Scope

1. Fact extraction from chunks
2. Entity normalization
3. Review workflow (approve/reject/modify)
4. Structured fact query API

### Out of Scope

- ❌ Advanced graph reasoning
- ❌ Fine-tuning sample export
- ❌ Complex multimodal processing

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

### Acceptance Criteria

1. ✅ Can extract facts from chunks with evidence
2. ✅ Facts include subject-relation-object structure
3. ✅ Facts link to source chunk/page/document
4. ✅ Can query facts by entity, relation, domain
5. ✅ Can review and approve/reject facts
6. ✅ Review operations are audited
7. ✅ Approved facts have higher trust level

### Exit Criteria

Cannot proceed to Phase 3 until:

1. All acceptance criteria met
2. At least 1000 facts reviewed and approved
3. Fact quality validated (sample 100 facts)
4. Review workflow tested with real users

---

## Phase 3: Domain Packages and External API

### Goal
Strengthen domain package mechanism and provide complete external APIs.

### In Scope

1. Complete HVAC and drive domain packages
2. Fine-tuning sample export (JSONL)
3. External APIs (document, chunk, fact query)
4. Export API

### Out of Scope

- ❌ Advanced graph inference
- ❌ Automatic model training
- ❌ Real-time device control

### Deliverables

**Domain Packages:**
- HVAC domain package complete
- Drive domain package complete
- Domain package validation tools

**Export:**
- Fine-tuning sample export (JSONL)
- Topic knowledge package export
- RAG snapshot export

**External API:**
- Document query API
- Chunk search API
- Fact query API
- Export API

**Infrastructure:**
- API gateway and rate limiting
- API documentation (OpenAPI)
- Export file storage

### Acceptance Criteria

1. ✅ HVAC and drive domain packages complete and validated
2. ✅ Can export fine-tuning samples filtered by domain/trust level
3. ✅ Can export topic-specific knowledge packages
4. ✅ External APIs return consistent response format
5. ✅ All API responses include traceability fields
6. ✅ API documentation is complete
7. ✅ Rate limiting prevents abuse

### Exit Criteria

Cannot proceed to Phase 4 until:

1. All acceptance criteria met
2. External APIs tested by integration partners
3. Export formats validated
4. Domain packages complete and documented

---

## Phase 4: Advanced Capabilities

### Goal
Add graph reasoning, fine-tuning sample factory, and additional domains.

### In Scope

1. Graph candidate generation
2. Sample generation templates
3. Energy storage domain package
4. Photovoltaics domain package

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

### Acceptance Criteria

1. ✅ Can generate graph candidates from facts
2. ✅ Can query graph relationships
3. ✅ Can generate diverse fine-tuning samples
4. ✅ Energy storage and PV domain packages operational

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
