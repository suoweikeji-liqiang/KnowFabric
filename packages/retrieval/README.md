# Retrieval Package

Search and retrieval module for querying chunks.

## Responsibility

- Build and maintain full-text indexes
- Build and maintain vector indexes (optional in P0)
- Provide hybrid search capabilities
- Support filtering by domain, brand, equipment type

## Phase 1 P0 Status

✅ Implemented in P0-6 (Retrieval Baseline) - Full-text search only.

## Components

- `service.py` - RetrievalService for chunk search
- `semantic_service.py` - Rebuild-track ontology metadata read helpers

## Usage

Via API:
```bash
curl "http://localhost:8000/api/v1/chunks/search?query=temperature&domain=hvac"
```

## Module Boundaries

**May Depend On:**
- core, db

**Must NOT Depend On:**
- extraction, review, exporter

**Forbidden Behaviors:**
- ❌ Modifying chunks or facts (read-only access)
- ❌ Treating indexes as truth source (chunks are truth source)
- ❌ Returning results without traceability fields

See [System Boundaries](../../docs/01_system-boundaries.md) for details.
