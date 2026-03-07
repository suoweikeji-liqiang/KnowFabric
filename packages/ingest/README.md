# Ingest Package

Document ingestion and import pipeline.

## Responsibility

- Scan directories for documents
- Generate document IDs and hashes
- Detect duplicates
- Apply initial tagging
- Record import metadata

## Constraints

- ❌ MUST NOT parse document content
- ❌ MUST NOT generate chunks
- ✅ Import and metadata only
