# Parser Package

Document parsing module for splitting documents into pages and extracting text.

## Responsibility

- Split documents into page-level objects
- Extract raw and cleaned text from pages
- Generate page images for traceability
- Identify page types (table, diagram, text, mixed)

## Phase 1 P0 Status

✅ Implemented in P0-4 (Minimal Page Generation).

## Components

- `service.py` - ParserService for page generation

## Usage

```bash
# Parse a document by doc_id
python scripts/parse_document.py doc_abc123
```

## Module Boundaries

**May Depend On:**
- core, db, storage

**Must NOT Depend On:**
- chunking, extraction, retrieval, review, exporter

**Forbidden Behaviors:**
- ❌ Creating chunks (chunking's responsibility)
- ❌ Extracting facts (extraction's responsibility)
- ❌ Semantic analysis beyond page type classification

See [System Boundaries](../../docs/01_system-boundaries.md) for details.
