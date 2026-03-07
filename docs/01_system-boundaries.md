# System Boundaries

## Module Boundary Principles

1. **High cohesion, low coupling** - Each module has clear responsibility
2. **Explicit dependencies** - No circular dependencies between modules
3. **Interface-based contracts** - Modules communicate through defined interfaces
4. **Domain isolation** - Domain-specific logic stays in domain packages

## Core Modules

### Ingest Module

**Responsibility:**
- Scan local directories for raw documents
- Generate unique document IDs
- Calculate file hashes for deduplication
- Record import metadata and batch information
- Apply initial domain/brand tagging based on path/filename

**Inputs:**
- Local directory paths
- Supported file format list
- Import batch metadata
- Initial domain mapping rules

**Outputs:**
- `document` records in database
- Deduplication results
- Initial tag assignments
- Import logs

**Forbidden:**
- ❌ Must NOT parse document content (parser's job)
- ❌ Must NOT generate chunks (chunking's job)
- ❌ Must NOT perform extraction (extraction's job)
- ❌ Must NOT build indexes (retrieval's job)

**Dependencies:**
- `core` - Domain models
- `db` - Database access
- `storage` - File storage operations

---

### Parser Module

**Responsibility:**
- Split documents into page-level objects
- Extract raw text and cleaned text from pages
- Generate page images for traceability
- Identify page types (table, diagram, fault code, procedure)
- Record OCR and multimodal processing status

**Inputs:**
- `document` records with file paths
- Parsing configuration

**Outputs:**
- `document_page` records
- `page_asset` records (images, extracted tables)
- Page-level text and metadata

**Forbidden:**
- ❌ Must NOT create chunks (chunking's job)
- ❌ Must NOT extract facts (extraction's job)
- ❌ Must NOT build search indexes (retrieval's job)

**Dependencies:**
- `core` - Domain models
- `db` - Database access
- `storage` - Page asset storage

---

### Chunking Module

**Responsibility:**
- Split pages into semantic knowledge units
- Identify chunk types (title, paragraph, table, procedure, fault code)
- Generate chunk summaries and keywords
- Maintain traceability to source pages
- Prepare chunks for retrieval and extraction

**Inputs:**
- `document_page` records with text
- Chunking strategy configuration
- Domain-specific chunking rules

**Outputs:**
- `content_chunk` records
- Text excerpts and summaries
- Entity and keyword lists
- Evidence anchors (bbox, text offsets)

**Forbidden:**
- ❌ Must NOT extract structured facts (extraction's job)
- ❌ Must NOT build vector indexes (retrieval's job)
- ❌ Must NOT perform review (review's job)

**Dependencies:**
- `core` - Domain models
- `db` - Database access
- `domain-kit` - Domain-specific chunking rules

---

### Extraction Module

**Responsibility:**
- Extract structured facts from chunks
- Identify entities, relations, and conditions
- Normalize subjects and objects
- Maintain evidence text and source traceability
- Calculate confidence scores

**Inputs:**
- `content_chunk` records
- Domain package extraction templates
- Entity and relation schemas

**Outputs:**
- `extracted_fact` records
- Normalized entity mappings
- Relation candidates
- Confidence scores and trust levels

**Forbidden:**
- ❌ Must NOT modify source chunks (read-only)
- ❌ Must NOT build indexes (retrieval's job)
- ❌ Must NOT approve facts (review's job)

**Dependencies:**
- `core` - Domain models
- `db` - Database access
- `domain-kit` - Extraction templates and schemas

---

### Retrieval Module

**Responsibility:**
- Build and maintain full-text indexes
- Build and maintain vector indexes
- Provide hybrid search capabilities
- Support filtering by domain, brand, equipment type, trust level
- Return results with traceability fields

**Inputs:**
- `content_chunk` records
- Search queries with filters
- Retrieval configuration

**Outputs:**
- Search results with chunk IDs
- Relevance scores
- Traceability metadata (doc_id, page_no, evidence_text)

**Forbidden:**
- ❌ Must NOT modify chunks or facts (read-only)
- ❌ Must NOT extract new facts (extraction's job)
- ❌ Indexes are NOT truth source (chunks are truth source)

**Dependencies:**
- `core` - Domain models
- `db` - Database access
- Search engine / vector database

---

### Review Module

**Responsibility:**
- Provide review workflow for facts and chunks
- Support approve, reject, modify, merge, split operations
- Record review history and audit trail
- Manage review status transitions
- Track reviewer identity and timestamps

**Inputs:**
- `extracted_fact` records pending review
- Review operations (approve/reject/modify)
- Reviewer identity

**Outputs:**
- Updated review_status on facts
- `review_record` audit entries
- Modified fact versions

**Forbidden:**
- ❌ Must NOT extract new facts (extraction's job)
- ❌ Must NOT rebuild indexes automatically (retrieval's job)
- ❌ Must NOT export assets (exporter's job)

**Dependencies:**
- `core` - Domain models
- `db` - Database access

---

### Exporter Module

**Responsibility:**
- Export knowledge assets in various formats
- Generate fine-tuning samples (JSONL)
- Create topic-specific knowledge packages
- Export graph candidate packages
- Apply filtering by domain, trust level, review status

**Inputs:**
- `content_chunk` and `extracted_fact` records
- Export configuration and filters
- Output format specifications

**Outputs:**
- Fine-tuning sample files (JSONL)
- Topic knowledge packages (JSON/Parquet)
- Graph candidate exports
- RAG snapshots

**Forbidden:**
- ❌ Must NOT modify source data (read-only)
- ❌ Must NOT perform extraction (extraction's job)
- ❌ Must NOT approve facts (review's job)

**Dependencies:**
- `core` - Domain models
- `db` - Database access
- `storage` - Export file storage

---

### Domain-Package Module

**Responsibility:**
- Define domain-specific schemas (entities, relations, labels)
- Provide extraction templates
- Configure retrieval profiles
- Define export profiles
- Maintain domain manifest

**Inputs:**
- Domain package configuration files (YAML/JSON)

**Outputs:**
- Domain schemas loaded into system
- Extraction templates for extraction module
- Retrieval profiles for retrieval module
- Export profiles for exporter module

**Forbidden:**
- ❌ Must NOT contain business logic (only configuration)
- ❌ Must NOT directly access database (provides config only)
- ❌ Must NOT hardcode domain logic into core modules

**Dependencies:**
- `core` - Domain model interfaces
- Configuration files only (no runtime dependencies)

---

## Dependency Rules

### Allowed Dependencies

```
apps/* → packages/*
packages/ingest → core, db, storage
packages/parser → core, db, storage
packages/chunking → core, db, domain-kit
packages/extraction → core, db, domain-kit
packages/retrieval → core, db
packages/review → core, db
packages/exporter → core, db, storage
packages/domain-kit → core
```

### Forbidden Dependencies

```
❌ core → any other package (core is foundation)
❌ db → domain-kit (db is domain-agnostic)
❌ ingest → parser, chunking, extraction, retrieval
❌ parser → chunking, extraction, retrieval
❌ chunking → extraction, retrieval
❌ extraction → retrieval, review, exporter
❌ retrieval → extraction, review, exporter
❌ Circular dependencies between any modules
```

## Boundary Validation

Run `npm run check:boundaries` to validate:
- No forbidden imports between modules
- No circular dependencies
- All modules respect interface contracts
