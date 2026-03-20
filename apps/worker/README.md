# Worker Service

Background processing workers for document ingestion, parsing, chunking, and extraction.

## Phase 1 P0 Status

Worker service baseline is established. Processing pipelines will be implemented in subsequent issues:
- P0-3: Document ingest worker
- P0-4: Page generation worker
- P0-5: Chunk generation worker

The worker is not required for the current read-only demo evaluation path.

## Running Locally

```bash
# From repository root
cd apps/worker
python main.py
```

## Configuration

Configuration is loaded from environment variables or `.env` file:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/knowfabric
STORAGE_ROOT=./storage/documents
LOG_LEVEL=INFO
```

See [Phase Plan](../../docs/05_phase-plan.md) for processing pipeline details.
