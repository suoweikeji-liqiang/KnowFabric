# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KnowFabric is an embeddable knowledge engineering engine for industrial domains. It transforms raw technical documentation into structured, traceable knowledge assets and delivers them via integration APIs (REST, MCP, SDK) to AI agents, developers, and applications. It is NOT a chatbot, document management system, end-user application, or general-purpose RAG demo. It is a knowledge engineering engine for industrial/energy domains (currently HVAC and drive/converter).

The project is in early Phase 1, focused on: the minimal traceable "main chain" (Document → Page → Chunk → Retrieval), integration API baseline, MCP Server baseline, and Docker deployment. Fact extraction, review workflows, graph reasoning, AI-optimized delivery, SDK, and admin UI are explicitly out of scope for Phase 1.

## Rebuild Track Note

The repository also has an approved ontology-first rebuild track. If the task is about the rebuild, read these first and treat them as the active direction:

- `docs/adr/0003-promote-knowfabric-to-domain-knowledge-authority.md`
- `docs/09_ontology-authority-architecture.md`
- `docs/10_rebuild-plan.md`
- `docs/11_rebuild-session-kickoff.md`

On the rebuild track:

- preserve the six-layer evidence discipline
- keep project-instance/runtime modeling out of KnowFabric
- prefer `v2` package structures beside legacy files before deleting legacy files
- use legacy Phase 1 docs as baseline context, not as the target end-state

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
createdb knowfabric
alembic upgrade head

# Run services
cd apps/api && python main.py      # API at http://localhost:8000
cd apps/worker && python main.py   # Worker (placeholder)
cd apps/mcp && python main.py      # MCP Server for AI agents

# Docker deployment
docker-compose up                  # Full stack (API + DB + worker)

# Quality gates (must all pass before merge)
bash scripts/check-all             # Run all gates
bash scripts/check-docs            # Documentation completeness
bash scripts/check-boundaries      # Module boundary compliance
bash scripts/check-forbidden-deps  # Forbidden dependency patterns

# Database migrations
alembic upgrade head               # Apply migrations
alembic revision -m "description"  # Create new migration

# Processing scripts (run from repo root)
python scripts/import_documents.py <directory> --domain hvac
python scripts/parse_document.py <doc_id>
python scripts/chunk_document.py <doc_id>
python scripts/check_job.py <job_id>
python scripts/rerun_document.py <doc_id>

# Tests
python tests/test_main_chain.py
```

## Architecture

### Mandatory Data Pipeline

Every knowledge output must flow through this exact path — no layer skipping:

```
Raw Document (Layer 1) → Page (Layer 2) → Chunk (Layer 3) → Fact (Layer 4) → Index/Export (Layers 5-6)
```

Chunks are the retrieval truth source. Indexes are NOT truth sources. Every output must include traceability fields: `source_doc_id`, `source_page_no`, `evidence_text`.

### Module Dependency Rules

The dependency graph is strictly one-directional. The key constraint is **no reverse pipeline flow**:

| Module | May Depend On | Must NOT Depend On |
|--------|---------------|-------------------|
| core | stdlib only | ALL other packages |
| db | core | domain-kit, processing modules |
| storage | core | domain-kit, processing modules |
| ingest | core, db, storage | parser, chunking, extraction, retrieval |
| parser | core, db, storage | chunking, extraction, retrieval |
| chunking | core, db, domain-kit | extraction, retrieval |
| extraction | core, db, domain-kit | retrieval, review, exporter |
| retrieval | core, db | extraction, review, exporter |

The `core` package must never import from any other package. Domain packages (`domain_packages/`) contain only YAML configuration — no runtime business logic.

### Key Directories

- `apps/` — Entry points (FastAPI API server, background worker, MCP server)
- `packages/` — Shared packages organized by responsibility (core, db, ingest, parser, chunking, retrieval, etc.)
- `domain_packages/` — Domain-specific YAML configs (entity schemas, label schemas, relation schemas, retrieval profiles, AI prompt templates)
- `migrations/` — Alembic migrations (migration-first for all schema changes)
- `scripts/` — Quality gate scripts and processing utilities
- `docs/` — Binding governance documents (charter, boundaries, data layer contract, engineering standards, AI consumer contract)
- `final_docs/` — Original Chinese-language requirement documents

### Tech Stack

- **Python 3.11+**, FastAPI, Pydantic v2, SQLAlchemy 2.0
- **PostgreSQL 14+** with Alembic migrations
- **pypdf** for PDF parsing, **Whoosh** for full-text search
- Config via `pydantic-settings` and `.env` file

### Database Models (`packages/db/models.py`)

Five tables: `document`, `document_page`, `content_chunk`, `processing_job`, `processing_stage_log`. Tables use singular snake_case names. All IDs are string-based (e.g., `doc_abc123`, `page_xyz`, `chunk_xyz`).

### API Conventions

- Endpoints versioned: `/api/v1/...`
- Resource-oriented nouns, not verbs
- Response envelope: `{"success": true/false, "data": ..., "metadata": {...}}`
- All search results must include traceability fields (`chunk_id`, `doc_id`, `page_no`, `evidence_text`)

## Hard Constraints

- Functions must be <50 lines, files <800 lines, nesting <4 levels
- All processing tasks must be idempotent
- Original documents are never modified in place
- Domain-specific logic goes in `domain_packages/`, never hardcoded in core modules
- Structured JSON logging with required fields: `timestamp`, `level`, `job_id`, `stage`, `doc_id`, `message`
- Governance docs in `docs/` are binding contracts — read `docs/00_repo-charter.md` and `docs/01_system-boundaries.md` before making architectural changes
