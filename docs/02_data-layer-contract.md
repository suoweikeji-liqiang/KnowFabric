# Data Layer Contract

**Status:** Data Contract - Enforced by Schema and Code Review
**Last Updated:** 2026-03-07

This document defines the mandatory six-layer data architecture. All data flows MUST follow this contract.

## Six-Layer Data Model

KnowFabric uses a six-layer data architecture where each layer has a specific purpose and truth source status.

---

## Layer 1: Raw Document Layer

### Purpose
Store original files as the ultimate truth source for all knowledge in the system.

### Truth Source Status
**PRIMARY TRUTH SOURCE** - All knowledge must trace back to this layer.

### Required Fields
```
doc_id              # Unique document identifier (REQUIRED)
file_hash           # SHA-256 hash (REQUIRED)
storage_path        # Storage location (REQUIRED)
file_name           # Original filename
file_ext            # File extension
mime_type           # MIME type
original_path       # Original file path
file_size           # File size in bytes
import_time         # Import timestamp
source_domain       # Domain tag (hvac, drive)
source_batch_id     # Import batch identifier
doc_version         # Document version
is_active           # Active status flag
```

### Source of Truth Status
PRIMARY - This is the root truth source. All other layers derive from this.

### Rebuildability
NOT rebuildable - This is the source. All other layers rebuild from this.

### Allowed Producers
- ingest module ONLY

### Allowed Consumers
- parser module (reads for page generation)
- storage module (manages file storage)

### Forbidden Shortcuts
- ❌ NEVER delete original files without explicit approval
- ❌ NEVER modify original files in place
- ❌ NEVER skip this layer to generate pages directly
- ❌ NEVER treat derived assets as replacement for originals

---

## Layer 2: Page Layer

### Purpose
Split documents into page-level objects for traceability and multimodal processing.

### Truth Source Status
**TRACEABILITY ANCHOR** - Critical for evidence linking and page-level citations.

### Required Fields
```
page_id             # Unique page identifier (REQUIRED)
doc_id              # Parent document ID (REQUIRED)
page_no             # Page number in document (REQUIRED)
cleaned_text        # Cleaned text (REQUIRED)
page_image_path     # Path to page image
raw_text            # Raw extracted text
page_type           # Page type (text, table, diagram, mixed)
has_table           # Contains table flag
has_diagram         # Contains diagram flag
ocr_status          # OCR processing status
```

### Source of Truth Status
DERIVED - Rebuildable from Layer 1 (Raw Document).

### Rebuildability
MUST be rebuildable from raw documents using parser module.

### Allowed Producers
- parser module ONLY

### Allowed Consumers
- chunking module (reads for chunk generation)
- retrieval module (reads for context)
- review module (reads for display)

### Forbidden Shortcuts
- ❌ NEVER skip page layer to go directly from document to chunks
- ❌ NEVER create chunks without page linkage
- ❌ NEVER modify pages after creation (regenerate instead)
- ❌ NEVER delete pages while chunks reference them

---

## Layer 3: Chunk Layer (Block-Level Semantic Layer)

### Purpose
Split pages into retrieval-optimized, extraction-ready knowledge units.

### Truth Source Status
**RETRIEVAL TRUTH SOURCE** - Primary unit for search and knowledge extraction.

### Required Fields
```
chunk_id            # Unique chunk identifier (REQUIRED)
doc_id              # Source document ID (REQUIRED)
page_id             # Source page ID (REQUIRED)
page_no             # Source page number (REQUIRED)
cleaned_text        # Cleaned chunk text (REQUIRED)
chunk_type          # Chunk type (REQUIRED)
chunk_index         # Chunk order within page
raw_text            # Raw chunk text
text_excerpt        # Short excerpt for display
evidence_anchor     # Evidence location data
```

### Source of Truth Status
DERIVED - Rebuildable from Layer 2 (Page).

### Rebuildability
MUST be rebuildable from pages using chunking module.

### Allowed Producers
- chunking module ONLY

### Allowed Consumers
- extraction module (reads for fact extraction)
- retrieval module (reads for indexing)
- exporter module (reads for export)

### Forbidden Shortcuts
- ❌ NEVER create chunks without page linkage (doc_id, page_id, page_no required)
- ❌ NEVER create chunks directly from documents (must go through pages)
- ❌ NEVER create facts directly from pages (must go through chunks)
- ❌ NEVER treat embeddings as replacement for chunk text

---

## Layer 4: Fact Layer

### Purpose
Extract structured business knowledge from chunks for structured queries and export.

### Truth Source Status
**STRUCTURED KNOWLEDGE TRUTH SOURCE** - Primary source for structured queries and exports.

### Required Fields
```
fact_id                 # Unique fact identifier (REQUIRED)
source_doc_id           # Source document ID (REQUIRED)
source_page_no          # Source page number (REQUIRED)
source_chunk_id         # Source chunk ID (REQUIRED)
evidence_text           # Evidence text snippet (REQUIRED)
subject                 # Subject entity (REQUIRED)
relation                # Relation type (REQUIRED)
object                  # Object entity (REQUIRED)
fact_type               # Fact type category
confidence_score        # Extraction confidence
trust_level             # Trust level (L1-L4)
```

### Source of Truth Status
DERIVED - Rebuildable from Layer 3 (Chunk).

### Rebuildability
MUST be rebuildable from chunks using extraction module.

### Allowed Producers
- extraction module ONLY

### Allowed Consumers
- review module (reads for review workflow)
- exporter module (reads for export)
- retrieval module (reads for fact queries)

### Forbidden Shortcuts
- ❌ NEVER create facts without evidence_text
- ❌ NEVER create facts without source traceability (doc_id, page_no, chunk_id)
- ❌ NEVER skip chunk layer to extract directly from pages
- ❌ NEVER create facts directly from documents

---

## Layer 5: Index Layer

### Purpose
Accelerate queries through full-text and vector indexes.

### Truth Source Status
**NOT A TRUTH SOURCE** - Indexes are derived and rebuildable from chunks.

### Required Fields
```
# Indexes reference chunk_id only
# No independent truth stored here
```

### Source of Truth Status
DERIVED - Rebuildable from Layer 3 (Chunk).

### Rebuildability
MUST be rebuildable from chunks at any time.

### Allowed Producers
- retrieval module ONLY

### Allowed Consumers
- retrieval module (uses for search)

### Forbidden Shortcuts
- ❌ NEVER use index as primary data storage
- ❌ NEVER assume index is always in sync with chunks
- ❌ NEVER return indexed data without fetching source chunk
- ❌ NEVER store chunk text only in index (must exist in chunk table)

---

## Layer 6: Derived Assets Layer

### Purpose
Generate application-specific knowledge products for export and external use.

### Truth Source Status
**NOT A TRUTH SOURCE** - All assets are derived and regenerable from previous layers.

### Required Fields
```
# Assets must include source traceability metadata
asset_id            # Unique asset identifier
source_layer        # Source layer (chunk/fact)
generation_time     # When asset was generated
```

### Source of Truth Status
DERIVED - Rebuildable from Layers 3 and 4 (Chunk and Fact).

### Rebuildability
MUST be regenerable from chunks and facts at any time.

### Allowed Producers
- exporter module ONLY

### Allowed Consumers
- External systems (via export files)

### Forbidden Shortcuts
- ❌ NEVER treat as primary truth source
- ❌ NEVER modify without regenerating from source
- ❌ NEVER export without source traceability metadata
- ❌ NEVER use as input for fact extraction

---

## Traceability Contract

Every external output MUST include these mandatory fields:

### Mandatory Traceability Fields
```
source_doc_id       # Source document (REQUIRED)
source_page_no      # Page number (REQUIRED)
evidence_text       # Evidence snippet (REQUIRED)
source_chunk_id     # Chunk identifier (if from chunk/fact)
confidence_score    # Confidence level
```

### Four-Level Traceability Chain

**Level 1: Result → Knowledge Unit**
```
Any output → chunk_id or fact_id
```

**Level 2: Knowledge Unit → Page**
```
chunk/fact → doc_id, page_id, page_no, evidence_text
```

**Level 3: Page → Raw Document**
```
page → doc_id, file_path, file_hash
```

**Level 4: Version Lineage**
```
Any entity → doc_version, parse_version, extraction_version
```

---

## Version Lineage Contract

All entities MUST track version lineage:

### Version Types
```
doc_version         # Document version (file changes)
parse_version       # Parser version (parsing logic changes)
extraction_version  # Extraction version (extraction rules change)
embedding_version   # Embedding model version
```

### Version Change Scenarios

1. **Original unchanged, parser upgraded** → parse_version increments, regenerate pages
2. **Original updated** → doc_version increments, regenerate all downstream
3. **Extraction rules changed** → extraction_version increments, regenerate facts
4. **Embedding model changed** → embedding_version increments, rebuild indexes

---

## Forbidden Shortcuts (Hard Rules)

These shortcuts are explicitly forbidden and will cause code review rejection:

### Layer Skipping Shortcuts

1. **Document → Chunk (skipping Page)**
   - ❌ FORBIDDEN: Generating chunks directly from documents
   - ✅ REQUIRED: Document → Page → Chunk

2. **Document → Fact (skipping Page and Chunk)**
   - ❌ FORBIDDEN: Extracting facts directly from documents
   - ✅ REQUIRED: Document → Page → Chunk → Fact

3. **Page → Fact (skipping Chunk)**
   - ❌ FORBIDDEN: Extracting facts directly from pages
   - ✅ REQUIRED: Page → Chunk → Fact

4. **Document → Output (skipping all intermediate layers)**
   - ❌ FORBIDDEN: Generating outputs directly from raw documents
   - ✅ REQUIRED: Document → Page → Chunk → (Fact) → Output

### Truth Source Shortcuts

5. **Index as Truth Source**
   - ❌ FORBIDDEN: Treating index as primary data storage
   - ❌ FORBIDDEN: Returning indexed data without fetching source chunk
   - ✅ REQUIRED: Index references chunks; chunks are truth source

6. **Derived Assets as Truth Source**
   - ❌ FORBIDDEN: Using export packages as input for extraction
   - ❌ FORBIDDEN: Modifying derived assets without regenerating from source
   - ✅ REQUIRED: Derived assets are read-only outputs

### Traceability Shortcuts

7. **Output without Evidence**
   - ❌ FORBIDDEN: Returning facts without evidence_text
   - ❌ FORBIDDEN: Returning results without source_doc_id, source_page_no
   - ✅ REQUIRED: All outputs include traceability fields

8. **Embedding-Only Storage**
   - ❌ FORBIDDEN: Storing only embeddings without chunk text
   - ❌ FORBIDDEN: Deleting chunk text after embedding generation
   - ✅ REQUIRED: Chunk text must always be preserved

### Data Flow Shortcuts

9. **Reverse Flow**
   - ❌ FORBIDDEN: Modifying source layers from downstream layers
   - ❌ FORBIDDEN: Facts modifying chunks
   - ❌ FORBIDDEN: Chunks modifying pages
   - ✅ REQUIRED: Data flows forward only (Document → Page → Chunk → Fact)

10. **Cross-Layer Modification**
    - ❌ FORBIDDEN: Extraction module modifying chunks
    - ❌ FORBIDDEN: Retrieval module modifying facts
    - ❌ FORBIDDEN: Review module modifying source chunks
    - ✅ REQUIRED: Each layer is read-only to downstream consumers

---

## Mandatory Data Flow

The ONLY valid data flow path:

```
Raw Document (Layer 1)
    ↓ parser
Page (Layer 2)
    ↓ chunking
Chunk (Layer 3)
    ↓ extraction
Fact (Layer 4)
    ↓ retrieval/exporter
Index/Derived Assets (Layers 5-6)
```

**No shortcuts. No exceptions.**

---

## Rebuild Requirements

All derived layers MUST be rebuildable:

- **Pages** MUST be rebuildable from raw documents
- **Chunks** MUST be rebuildable from pages
- **Facts** MUST be rebuildable from chunks
- **Indexes** MUST be rebuildable from chunks
- **Derived Assets** MUST be rebuildable from chunks and facts

If any layer cannot be rebuilt from its source layer, the architecture is violated.
