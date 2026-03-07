# System Boundaries

**Status:** Boundary Contract - Enforced by CI
**Last Updated:** 2026-03-07

This document defines hard boundaries between modules. Violations result in automatic PR rejection.

## Module Boundary Principles

1. **High cohesion, low coupling** - Each module has clear responsibility
2. **Explicit dependencies** - No circular dependencies between modules
3. **Interface-based contracts** - Modules communicate through defined interfaces
4. **Domain isolation** - Domain-specific logic stays in domain packages
5. **Enforcement** - Boundaries validated by `scripts/check-boundaries`

## Core Module

**Responsibility:**
- Define domain models and interfaces
- Provide type definitions for all entities
- Define contracts between modules

**Owns:**
- Entity type definitions (Document, Page, Chunk, Fact)
- Interface contracts (IParser, IChunker, IExtractor)
- Shared constants and enums

**Inputs:**
- None (foundation layer)

**Outputs:**
- Type definitions for other modules
- Interface contracts

**May Depend On:**
- Standard library only

**Must Not Depend On:**
- ANY other package in this repository

**Forbidden Behaviors:**
- ❌ Importing from db, storage, or any domain package
- ❌ Containing business logic or processing code
- ❌ Containing domain-specific logic (belongs in domain packages)
- ❌ Direct database access or file I/O

## Ingest Module

**Responsibility:**
- Scan directories for raw documents
- Generate unique document IDs and calculate file hashes
- Record import metadata and batch information
- Apply initial domain/brand tagging based on path/filename

**Owns:**
- Document import logic
- File deduplication
- Initial metadata extraction

**Inputs:**
- Local directory paths
- Supported file format list
- Import batch metadata

**Outputs:**
- `document` records in database
- Deduplication results
- Initial tag assignments

**May Depend On:**
- core (domain models)
- db (database access)
- storage (file operations)

**Must Not Depend On:**
- parser, chunking, extraction, retrieval, review, exporter

**Forbidden Behaviors:**
- ❌ Parsing document content (parser's responsibility)
- ❌ Generating chunks (chunking's responsibility)
- ❌ Extracting facts (extraction's responsibility)
- ❌ Building indexes (retrieval's responsibility)
- ❌ Reading document text content beyond metadata

---

### Parser Module

## Parser Module

**Responsibility:**
- Split documents into page-level objects
- Extract raw and cleaned text from pages
- Generate page images for traceability
- Identify page types (table, diagram, fault code, procedure)

**Owns:**
- Page generation logic
- Text extraction
- Page asset generation

**Inputs:**
- `document` records with file paths
- Parsing configuration

**Outputs:**
- `document_page` records
- `page_asset` records (images, tables)
- Page-level text and metadata

**May Depend On:**
- core, db, storage

**Must Not Depend On:**
- chunking, extraction, retrieval, review, exporter

**Forbidden Behaviors:**
- ❌ Creating chunks (chunking's responsibility)
- ❌ Extracting facts (extraction's responsibility)
- ❌ Building search indexes (retrieval's responsibility)
- ❌ Semantic analysis beyond page type classification

---

### Chunking Module

## Chunking Module

**Responsibility:**
- Split pages into semantic knowledge units
- Identify chunk types (title, paragraph, table, procedure, fault code)
- Generate chunk summaries and keywords
- Maintain traceability to source pages

**Owns:**
- Chunk generation logic
- Semantic segmentation
- Chunk metadata extraction

**Inputs:**
- `document_page` records with text
- Chunking strategy configuration
- Domain-specific chunking rules

**Outputs:**
- `content_chunk` records
- Text excerpts and summaries
- Entity and keyword lists
- Evidence anchors (bbox, text offsets)

**May Depend On:**
- core, db, domain-kit

**Must Not Depend On:**
- extraction, retrieval, review, exporter

**Forbidden Behaviors:**
- ❌ Extracting structured facts (extraction's responsibility)
- ❌ Building vector indexes (retrieval's responsibility)
- ❌ Performing review operations (review's responsibility)
- ❌ Modifying source pages

---

### Extraction Module

## Extraction Module

**Responsibility:**
- Extract structured facts from chunks
- Identify entities, relations, and conditions
- Normalize subjects and objects
- Maintain evidence text and source traceability

**Owns:**
- Fact extraction logic
- Entity normalization
- Confidence scoring

**Inputs:**
- `content_chunk` records
- Domain package extraction templates
- Entity and relation schemas

**Outputs:**
- `extracted_fact` records
- Normalized entity mappings
- Confidence scores and trust levels

**May Depend On:**
- core, db, domain-kit

**Must Not Depend On:**
- retrieval, review, exporter

**Forbidden Behaviors:**
- ❌ Modifying source chunks (read-only access)
- ❌ Building indexes (retrieval's responsibility)
- ❌ Approving facts (review's responsibility)
- ❌ Exporting assets (exporter's responsibility)

---

### Retrieval Module

## Retrieval Module

**Responsibility:**
- Build and maintain full-text indexes
- Build and maintain vector indexes
- Provide hybrid search capabilities
- Support filtering by domain, brand, equipment type

**Owns:**
- Index construction and maintenance
- Search query execution
- Result ranking

**Inputs:**
- `content_chunk` records
- Search queries with filters
- Retrieval configuration

**Outputs:**
- Search results with chunk IDs
- Relevance scores
- Traceability metadata (doc_id, page_no, evidence_text)

**May Depend On:**
- core, db, search engine/vector database

**Must Not Depend On:**
- extraction, review, exporter

**Forbidden Behaviors:**
- ❌ Modifying chunks or facts (read-only access)
- ❌ Extracting new facts (extraction's responsibility)
- ❌ Treating indexes as truth source (chunks are truth source)
- ❌ Returning results without traceability fields

---

### Review Module

## Review Module

**Responsibility:**
- Provide review workflow for facts and chunks
- Support approve, reject, modify operations
- Record review history and audit trail
- Manage review status transitions

**Owns:**
- Review workflow logic
- Audit trail management
- Review status tracking

**Inputs:**
- `extracted_fact` records pending review
- Review operations (approve/reject/modify)
- Reviewer identity

**Outputs:**
- Updated review_status on facts
- `review_record` audit entries
- Modified fact versions

**May Depend On:**
- core, db

**Must Not Depend On:**
- extraction, retrieval, exporter

**Forbidden Behaviors:**
- ❌ Extracting new facts (extraction's responsibility)
- ❌ Rebuilding indexes automatically (retrieval's responsibility)
- ❌ Exporting assets (exporter's responsibility)
- ❌ Modifying source chunks

---

### Exporter Module

## Exporter Module

**Responsibility:**
- Export knowledge assets in various formats
- Generate fine-tuning samples (JSONL)
- Create topic-specific knowledge packages
- Apply filtering by domain, trust level, review status

**Owns:**
- Export logic and formatting
- Asset packaging
- Filter application

**Inputs:**
- `content_chunk` and `extracted_fact` records
- Export configuration and filters
- Output format specifications

**Outputs:**
- Fine-tuning sample files (JSONL)
- Topic knowledge packages (JSON/Parquet)
- Graph candidate exports
- RAG snapshots

**May Depend On:**
- core, db, storage

**Must Not Depend On:**
- extraction, retrieval, review

**Forbidden Behaviors:**
- ❌ Modifying source data (read-only access)
- ❌ Performing extraction (extraction's responsibility)
- ❌ Approving facts (review's responsibility)
- ❌ Building indexes (retrieval's responsibility)

---

### Domain-Package Module

## Domain-Package Module

**Responsibility:**
- Define domain-specific schemas (entities, relations, labels)
- Provide extraction templates
- Configure retrieval profiles
- Define export profiles

**Owns:**
- Domain schema definitions
- Extraction templates
- Configuration files only

**Inputs:**
- Domain package configuration files (YAML/JSON)

**Outputs:**
- Domain schemas loaded into system
- Extraction templates for extraction module
- Retrieval profiles for retrieval module

**May Depend On:**
- core (domain model interfaces only)

**Must Not Depend On:**
- db, storage, or any processing modules

**Forbidden Behaviors:**
- ❌ Containing runtime business logic (configuration only)
- ❌ Direct database access
- ❌ Hardcoding domain logic into core modules
- ❌ Importing from processing modules

---

## Module Dependency Matrix

| Module | May Depend On | Must NOT Depend On |
|--------|---------------|-------------------|
| core | stdlib only | ALL other packages |
| db | core | domain-kit, processing modules |
| storage | core | domain-kit, processing modules |
| domain-kit | core | db, storage, processing modules |
| ingest | core, db, storage | parser, chunking, extraction, retrieval, review, exporter |
| parser | core, db, storage | chunking, extraction, retrieval, review, exporter |
| chunking | core, db, domain-kit | extraction, retrieval, review, exporter |
| extraction | core, db, domain-kit | retrieval, review, exporter |
| retrieval | core, db | extraction, review, exporter |
| review | core, db | extraction, retrieval, exporter |
| exporter | core, db, storage | extraction, retrieval, review |

---

## Forbidden Dependency Rules

These dependencies are explicitly forbidden and will cause CI failure:

1. **No Reverse Pipeline Flow**
   - ❌ ingest → parser
   - ❌ parser → chunking
   - ❌ chunking → extraction
   - ❌ extraction → retrieval

2. **No Core Contamination**
   - ❌ core → ANY other package

3. **No Domain Package Runtime Dependencies**
   - ❌ domain_packages → ANY runtime code imports

4. **No Circular Dependencies**
   - ❌ ANY module → module that depends on it

5. **No Layer Skipping**
   - ❌ ingest → chunking (must go through parser)
   - ❌ parser → extraction (must go through chunking)

---

## Forbidden Behavior Rules

These behaviors are explicitly forbidden:

### Ingest Module
- ❌ Reading document text content beyond metadata
- ❌ Parsing semantic content
- ❌ Generating chunks or facts

### Parser Module
- ❌ Semantic analysis beyond page type classification
- ❌ Creating chunks
- ❌ Extracting structured facts

### Chunking Module
- ❌ Extracting structured facts (only keywords/entities allowed)
- ❌ Building vector indexes
- ❌ Modifying source pages

### Extraction Module
- ❌ Modifying source chunks
- ❌ Building indexes
- ❌ Approving or reviewing facts

### Retrieval Module
- ❌ Treating indexes as truth source
- ❌ Modifying chunks or facts
- ❌ Returning results without traceability

### Review Module
- ❌ Extracting new facts
- ❌ Modifying source chunks
- ❌ Automatically rebuilding indexes

### Exporter Module
- ❌ Modifying source data
- ❌ Performing extraction
- ❌ Approving facts

### Domain Packages
- ❌ Containing runtime business logic
- ❌ Direct database access
- ❌ Importing from processing modules

---

## Boundary Validation

Run boundary checks:
```bash
scripts/check-boundaries
```

This validates:
- No forbidden imports between modules
- No circular dependencies
- Module dependency matrix compliance
