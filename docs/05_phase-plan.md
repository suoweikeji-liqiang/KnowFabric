# Phase Plan

## Phase Delivery Principles

1. **Standards before scale** - Establish contracts before building features
2. **Assets before intelligence** - Build stable data layers before advanced reasoning
3. **Traceability before optimization** - Ensure evidence chains before performance tuning
4. **Incremental delivery** - Each phase must be independently valuable

## Phase 1: Foundation Layer

### Goal
Establish document/page/chunk/retrieval foundation with full traceability.

### Deliverables

**Data Layer:**
- ✅ Document ingestion with deduplication
- ✅ Page-level parsing and asset generation
- ✅ Chunk generation with semantic typing
- ✅ Traceability chain (chunk → page → document)

**Processing:**
- ✅ Document import pipeline
- ✅ Page parsing pipeline
- ✅ Chunk generation pipeline
- ✅ Basic multimodal enhancement (high-value pages only)

**Retrieval:**
- ✅ Full-text search on chunks
- ✅ Vector search on chunks
- ✅ Hybrid search with filtering
- ✅ Domain/brand/equipment filtering

**Infrastructure:**
- ✅ Database schema (document, page, chunk tables)
- ✅ File storage for documents and page assets
- ✅ Processing job tracking
- ✅ Stage-level logging

### Acceptance Criteria

1. Can import 100+ documents successfully
2. Can generate stable document/page/chunk structure
3. Chunks are searchable via full-text and vector search
4. Search results include traceability fields (doc_id, page_no, evidence_text)
5. Supports incremental import (new documents only)
6. Supports partial re-processing (by doc_id)
7. Processing failures are logged and recoverable

### Out of Scope (Phase 1)

- ❌ Structured fact extraction
- ❌ Human review workflow
- ❌ Knowledge export
- ❌ External API (beyond basic search)

---

## Phase 2: Fact Extraction and Review

### Goal
Extract structured facts from chunks with human review workflow.

### Deliverables

**Data Layer:**
- ✅ Fact extraction from chunks
- ✅ Entity normalization
- ✅ Relation candidates
- ✅ Review status tracking

**Processing:**
- ✅ Fact extraction pipeline
- ✅ Confidence scoring
- ✅ Trust level assignment (L1-L4)

**Review Workflow:**
- ✅ Review queue management
- ✅ Approve/reject/modify operations
- ✅ Review audit trail
- ✅ Batch review operations

**Query:**
- ✅ Structured fact query API
- ✅ Filter by trust level, review status
- ✅ Fact results include evidence and traceability

**Infrastructure:**
- ✅ Fact and review tables
- ✅ Review workflow backend
- ✅ Basic admin interface for review

### Acceptance Criteria

1. Can extract facts from chunks with evidence
2. Facts include subject-relation-object structure
3. Facts link to source chunk/page/document
4. Can query facts by entity, relation, domain
5. Can review and approve/reject facts
6. Review operations are audited
7. Approved facts have higher trust level

### Out of Scope (Phase 2)

- ❌ Advanced graph reasoning
- ❌ Fine-tuning sample export
- ❌ Complex multimodal processing

---

## Phase 3: Domain Packages and External API

### Goal
Strengthen domain package mechanism and provide complete external APIs.

### Deliverables

**Domain Packages:**
- ✅ HVAC domain package complete
- ✅ Drive domain package complete
- ✅ Domain package validation tools
- ✅ Cross-domain reference support

**Export:**
- ✅ Fine-tuning sample export (JSONL)
- ✅ Topic knowledge package export
- ✅ RAG snapshot export
- ✅ Graph candidate export

**External API:**
- ✅ Document query API
- ✅ Chunk search API
- ✅ Fact query API
- ✅ Export API
- ✅ Review API (for external systems)

**Infrastructure:**
- ✅ API gateway and rate limiting
- ✅ API documentation (OpenAPI)
- ✅ Export file storage and versioning

### Acceptance Criteria

1. HVAC and drive domain packages are complete and validated
2. Can export fine-tuning samples filtered by domain/trust level
3. Can export topic-specific knowledge packages
4. External APIs return consistent response format
5. All API responses include traceability fields
6. API documentation is complete and accurate
7. Rate limiting prevents abuse

### Out of Scope (Phase 3)

- ❌ Advanced graph inference
- ❌ Automatic model training
- ❌ Real-time device control

---

## Phase 4: Advanced Capabilities

### Goal
Add graph reasoning, fine-tuning sample factory, and additional domains.

### Deliverables

**Graph:**
- ✅ Graph candidate generation
- ✅ Entity resolution and merging
- ✅ Relation validation
- ✅ Graph query API

**Fine-tuning:**
- ✅ Sample generation templates
- ✅ Sample quality scoring
- ✅ Sample diversity optimization
- ✅ Evaluation dataset generation

**Domain Expansion:**
- ✅ Energy storage domain package
- ✅ Photovoltaics domain package
- ✅ Cross-domain knowledge linking

**Advanced Processing:**
- ✅ Enhanced multimodal processing
- ✅ Diagram understanding
- ✅ Table structure extraction

### Acceptance Criteria

1. Can generate graph candidates from facts
2. Can query graph relationships
3. Can generate diverse fine-tuning samples
4. Energy storage and PV domain packages operational
5. Cross-domain queries work correctly

---

## Phase Transition Rules

### Transition from Phase 1 to Phase 2

**Prerequisites:**
- All Phase 1 acceptance criteria met
- Quality gates passing
- Documentation complete
- Sample document set processed successfully

**Validation:**
- Run full regression test suite
- Verify traceability chain integrity
- Confirm incremental processing works

### Transition from Phase 2 to Phase 3

**Prerequisites:**
- All Phase 2 acceptance criteria met
- Fact extraction quality validated
- Review workflow tested with real users
- At least 1000 facts reviewed and approved

**Validation:**
- Fact quality spot check (sample 100 facts)
- Review workflow performance test
- Traceability chain validation

### Transition from Phase 3 to Phase 4

**Prerequisites:**
- All Phase 3 acceptance criteria met
- External APIs tested by integration partners
- Export formats validated
- Domain packages complete and documented

**Validation:**
- API integration tests passing
- Export quality validation
- Domain package coverage check

---

## Delivery Artifacts (Each Phase)

Each phase must deliver:

1. **Runnable Code**
   - All features implemented and tested
   - No critical bugs

2. **Documentation**
   - README updated
   - API documentation (if applicable)
   - Configuration guide

3. **Tests**
   - Unit tests passing
   - Integration tests passing
   - Regression tests passing

4. **Data Schema**
   - Migration scripts
   - Schema documentation
   - Sample data

5. **Known Limitations**
   - Document what's not included
   - Document known issues
   - Document workarounds

---

## Phase Timeline Estimates

**Phase 1:** 6-8 weeks
- Week 1-2: Database schema and ingestion
- Week 3-4: Parsing and chunking
- Week 5-6: Retrieval and search
- Week 7-8: Testing and refinement

**Phase 2:** 4-6 weeks
- Week 1-2: Fact extraction
- Week 3-4: Review workflow
- Week 5-6: Testing and refinement

**Phase 3:** 4-6 weeks
- Week 1-2: Domain packages
- Week 3-4: Export and API
- Week 5-6: Testing and documentation

**Phase 4:** 6-8 weeks
- Week 1-3: Graph and fine-tuning
- Week 4-5: Domain expansion
- Week 6-8: Testing and refinement

**Note:** These are estimates. Actual timeline depends on team size and complexity encountered.
