# Ingest Package

Document ingestion module for scanning, importing, and deduplicating documents.

## Responsibility

- Scan directories for raw documents
- Generate unique document IDs and calculate file hashes
- Record import metadata and batch information
- Apply initial domain/brand tagging based on path/filename

## Phase 1 P0 Status

✅ Implemented in P0-3 (Minimal Document Ingest).

## Components

- `service.py` - IngestService for document import
- `manager.py` - Storage operations (in storage package)

## Usage

```bash
# Import documents from directory
python scripts/import_documents.py /path/to/documents --domain hvac
```

## Module Boundaries

**May Depend On:**
- core, db, storage

**Must NOT Depend On:**
- parser, chunking, extraction, retrieval, review, exporter

**Forbidden Behaviors:**
- ❌ Parsing document content (parser's responsibility)
- ❌ Generating chunks (chunking's responsibility)
- ❌ Reading document text content beyond metadata

See [System Boundaries](../../docs/01_system-boundaries.md) for details.
