# Phase 1 Implementation Contract

**Status:** Binding Delivery Contract
**Last Updated:** 2026-03-13

This document defines the hard boundaries and acceptance criteria for Phase 1 implementation.

---

## Phase 1 Unique Goal

**Build the minimal viable knowledge main chain with integrable API:**

```
Raw Document → Page → Chunk → Retrieval → Integration API / MCP
```

Phase 1 establishes the foundation data pipeline with full traceability AND exposes it via integration APIs so external consumers (AI agents, developers, applications) can use it immediately.

---

## Must Deliver

Phase 1 MUST deliver these capabilities:

### 1. Repository Skeleton Ready

- ✅ Monorepo structure established
- ✅ Core governance docs complete (00-08 series)
- ✅ Quality gates operational
- ✅ All packages have README files

### 2. Database Migration Baseline

- ✅ Migration framework in place
- ✅ Baseline schema: document, document_page, content_chunk tables
- ✅ Traceability fields present in all tables
- ✅ Version tracking fields present

### 3. Document Ingest Entry

- ✅ Can scan directory for documents
- ✅ Can generate unique doc_id
- ✅ Can calculate file hash for deduplication
- ✅ Can store documents with metadata
- ✅ Can detect duplicate imports

### 4. Page Generation Pipeline

- ✅ Can split documents into pages
- ✅ Can extract text from pages
- ✅ Can generate page images
- ✅ Can link pages to source documents (doc_id)
- ✅ Can preserve page order (page_no)

### 5. Chunk Pipeline

- ✅ Can split pages into semantic chunks
- ✅ Can classify chunk types (paragraph, table, etc.)
- ✅ Can link chunks to source pages (page_id, page_no)
- ✅ Can maintain chunk order (chunk_index)
- ✅ Can store evidence anchors

### 6. Retrieval API Baseline

- ✅ Can search chunks by full-text
- ✅ Can search chunks by vector similarity
- ✅ Can filter by domain/brand
- ✅ Returns results with traceability (doc_id, page_no, chunk_id, evidence_text)

### 7. Jobs/Status/Log Baseline

- ✅ Can track processing jobs
- ✅ Can log stage-level progress
- ✅ Can identify failed jobs
- ✅ Can resume from failure

### 8. Test Fixtures Baseline

- ✅ Sample document set (10+ docs minimum)
- ✅ Test data for each pipeline stage
- ✅ Traceability validation tests

### 9. Integration API Baseline (New)

- ✅ `POST /api/v1/documents/upload` — Async document upload (returns 202 Accepted + job_id)
- ✅ `GET /api/v1/jobs/{job_id}` — Processing status with stage progress
- ✅ `GET /api/v1/chunks/{chunk_id}/trace` — Full traceability chain
- ✅ `POST /api/v1/chunks/search` — Chunk search with traceability in results
- ✅ OpenAPI documentation auto-generated and accessible at `/docs`
- ✅ Standard response envelope on all endpoints

### 10. MCP Server Baseline (New)

- ✅ `search_knowledge` tool — Search chunks by query, returns structured results with traceability
- ✅ `trace_evidence` tool — Given chunk_id, returns full evidence chain (chunk → page → document)
- ✅ `list_domains` tool — Returns available domains with coverage summary
- ✅ MCP transport: stdio
- ✅ MCP server entry point at `apps/mcp/`

### 11. Deployment Baseline (New)

- ✅ `docker-compose.yml` with API, PostgreSQL, and worker services
- ✅ Environment variable configuration via `.env`
- ✅ Health check endpoints for all services
- ✅ Can start full system with `docker-compose up`

---

## Must NOT Deliver

Phase 1 explicitly does NOT include:

### 1. Full Fact Extraction Engine

- ❌ Heavy fact extraction (minimal extraction acceptable)
- ❌ Entity normalization
- ❌ Relation extraction
- ❌ Graph candidate generation

### 2. Review Platform

- ❌ Review workflow UI
- ❌ Approve/reject operations
- ❌ Review audit trail
- ❌ Batch review operations

### 3. Graph Package

- ❌ Graph storage
- ❌ Graph query API
- ❌ Entity resolution
- ❌ Relation validation

### 4. Finetune Export System

- ❌ Fine-tuning sample generation
- ❌ Sample quality scoring
- ❌ Export templates
- ❌ Evaluation dataset generation

### 5. Complex Front-End Shell

- ❌ Rich admin web interface
- ❌ Interactive dashboards
- ❌ Visual query builder
- ❌ Document viewer (basic acceptable)

### 6. AI-Optimized Knowledge Delivery (Phase 2)

- ❌ Context assembly API with token budget control
- ❌ AI-friendly query endpoints with confidence aggregation
- ❌ Token-budget-aware MCP tools
- ❌ Confidence/trust level semantics beyond basic fields

### 7. SDK and Distribution (Phase 3)

- ❌ Python SDK package
- ❌ AI prompt templates
- ❌ Terminology mappings
- ❌ Domain package distribution mechanism

---

## Phase 1 Data Contract

### Document Table (Minimum Fields)

```
doc_id              # REQUIRED
file_hash           # REQUIRED
storage_path        # REQUIRED
file_name
import_time
source_domain
is_active
```

### Page Table (Minimum Fields)

```
page_id             # REQUIRED
doc_id              # REQUIRED (FK to document)
page_no             # REQUIRED
cleaned_text        # REQUIRED
page_image_path
raw_text
```

### Chunk Table (Minimum Fields)

```
chunk_id            # REQUIRED
doc_id              # REQUIRED (FK to document)
page_id             # REQUIRED (FK to page)
page_no             # REQUIRED
cleaned_text        # REQUIRED
chunk_type          # REQUIRED
chunk_index
evidence_anchor
```

### Retrieval Response (Minimum Fields)

```
chunk_id            # REQUIRED
doc_id              # REQUIRED
page_no             # REQUIRED
evidence_text       # REQUIRED
relevance_score
```

---

## Definition of Done

Phase 1 is complete ONLY when ALL criteria are met:

### 1. Can Run

- ✅ Can import 100+ documents without crashes
- ✅ Can generate pages for all imported documents
- ✅ Can generate chunks for all pages
- ✅ Can search chunks and get results

### 2. Can Query

- ✅ Full-text search returns results <2s
- ✅ Vector search returns results <2s
- ✅ Can filter by domain
- ✅ Can filter by document

### 3. Can Trace

- ✅ Every search result includes: doc_id, page_no, chunk_id, evidence_text
- ✅ Can navigate from chunk → page → document
- ✅ Can retrieve original document from chunk result

### 4. Can Rerun

- ✅ Can add new documents without reprocessing existing ones
- ✅ Can reprocess specific doc_id without affecting others
- ✅ Can resume failed jobs

### 5. Can Test

- ✅ All quality gates pass (check-docs, check-boundaries, check-forbidden-deps)
- ✅ Sample document set processes successfully
- ✅ Traceability chain validated end-to-end

### 6. Can Integrate (New)

- ✅ External HTTP client can upload a document via API and poll until processing completes
- ✅ External HTTP client can search chunks and receive results with traceability
- ✅ AI agent can call MCP search_knowledge and receive structured knowledge results
- ✅ AI agent can call MCP trace_evidence and navigate the full evidence chain
- ✅ OpenAPI spec is generated and accessible

### 7. Can Deploy (New)

- ✅ `docker-compose up` starts API, database, and worker
- ✅ Health check endpoints respond correctly
- ✅ System processes documents end-to-end in Docker environment

---

## Acceptance Test Procedure

Run these commands to validate Phase 1 completion:

```bash
# 1. Quality gates must pass
scripts/check-all

# 2. Import sample documents
python scripts/import_documents.py <directory> --domain hvac

# 3. Process documents
python scripts/parse_document.py <doc_id>
python scripts/chunk_document.py <doc_id>

# 4. Test search via API
curl -X POST http://localhost:8000/api/v1/chunks/search \
  -H "Content-Type: application/json" \
  -d '{"query": "chiller fault code", "domain": "hvac"}'

# 5. Validate traceability via API
curl http://localhost:8000/api/v1/chunks/{chunk_id}/trace

# 6. Test MCP tools (via MCP client or stdio)
# Verify search_knowledge, trace_evidence, list_domains

# 7. Docker deployment
docker-compose up -d
curl http://localhost:8000/health
```

All commands must return exit code 0 or expected HTTP status codes.

---

## Non-Negotiable Constraints

These constraints apply to Phase 1 implementation:

1. **No Layer Skipping** - Must go through: Document → Page → Chunk
2. **Traceability Mandatory** - Every output includes: doc_id, page_no, evidence_text
3. **Quality Gates Must Pass** - No merge without passing all gates
4. **Migration-First Schema** - All schema changes via migration scripts
5. **No Bypass Flags** - No --skip-checks or --force flags
6. **API Response Envelope** - All API responses use standard envelope format
7. **MCP Reuses Existing Packages** - MCP tools call existing retrieval/db packages, no separate data path

---

## Success Metrics

Phase 1 is successful when:

- ✅ 100+ documents imported and processed
- ✅ Document/page/chunk records stable (no data loss)
- ✅ Search latency <2s for typical queries
- ✅ Traceability chain validated
- ✅ Quality gates passing consistently
- ✅ Zero forbidden boundary violations
- ✅ External client can call API endpoints successfully
- ✅ AI agent can use MCP tools to search and trace
- ✅ Docker deployment works end-to-end

---

## What Comes After Phase 1

Phase 2 will add:
- Fact extraction from chunks
- Review workflow
- Structured fact query API
- AI-optimized knowledge delivery (context assembly, token budgets)
- Enhanced MCP tools

But Phase 2 cannot start until Phase 1 exit criteria are met.
