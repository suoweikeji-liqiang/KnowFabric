# Chunking Package

Chunk generation module for splitting pages into semantic knowledge units.

## Responsibility

- Split pages into semantic knowledge units
- Identify chunk types (title, paragraph, table, procedure)
- Generate chunk summaries and keywords
- Maintain traceability to source pages

## Phase 1 P0 Status

✅ Implemented in P0-5 (Minimal Chunk Generation).

## Components

- `service.py` - ChunkingService for chunk generation

## Usage

```bash
# Generate chunks for a document
python scripts/chunk_document.py doc_abc123
```

## Module Boundaries

**May Depend On:**
- core, db, domain-kit

**Must NOT Depend On:**
- extraction, retrieval, review, exporter

**Forbidden Behaviors:**
- ❌ Extracting structured facts (extraction's responsibility)
- ❌ Building vector indexes (retrieval's responsibility)
- ❌ Modifying source pages

See [System Boundaries](../../docs/01_system-boundaries.md) for details.
