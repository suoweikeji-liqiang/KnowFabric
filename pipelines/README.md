# Pipelines

Processing pipelines for document ingestion and knowledge extraction.

## Structure

Pipelines orchestrate the flow from raw documents to knowledge assets:

1. **Ingestion Pipeline** - Document import and deduplication
2. **Parsing Pipeline** - Page extraction and asset generation
3. **Chunking Pipeline** - Semantic chunk generation
4. **Extraction Pipeline** - Fact extraction
5. **Indexing Pipeline** - Search index building

## Usage

Each pipeline is independently runnable and supports:
- Incremental processing
- Partial re-runs
- Stage-level recovery
- Job tracking

See [Phase Plan](../docs/05_phase-plan.md) for pipeline details.
