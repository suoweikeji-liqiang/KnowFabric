# Worker Service

Background processing workers for document ingestion, parsing, chunking, and extraction.

## Workers

- **Ingest Worker** - Document import and deduplication
- **Parse Worker** - Page parsing and asset generation
- **Chunk Worker** - Chunk generation
- **Extract Worker** - Fact extraction
- **Index Worker** - Search index building

## Running

```bash
npm run dev
```

See [Phase Plan](../../docs/05_phase-plan.md) for processing pipeline details.
