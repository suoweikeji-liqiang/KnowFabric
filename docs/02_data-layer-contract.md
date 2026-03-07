# Data Layer Contract

## Six-Layer Data Model

KnowFabric uses a six-layer data architecture where each layer has a specific purpose and truth source status.

## Layer 1: Raw Document Layer

### Purpose
Store original files as the ultimate truth source for all knowledge in the system.

### Storage Objects
- PDF, Word, PPT, images, scanned documents, text files
- Original file metadata and hash

### Truth Source Status
**PRIMARY TRUTH SOURCE** - All knowledge must trace back to this layer.

### Core Requirements
1. Original files are immutable (no in-place modification)
2. Each file gets unique `doc_id`
3. File hash recorded for deduplication
4. Original path and import source preserved
5. Version history maintained

### Key Fields
```
doc_id              # Unique document identifier
file_name           # Original filename
file_ext            # File extension
mime_type           # MIME type
original_path       # Original file path
storage_path        # Storage location
file_hash           # SHA-256 hash
file_size           # File size in bytes
created_time        # File creation time
modified_time       # File modification time
import_time         # Import timestamp
source_domain       # Domain tag (hvac, drive, etc.)
source_batch_id     # Import batch identifier
doc_version         # Document version
is_active           # Active status flag
```

### Constraints
- ❌ NEVER delete original files without explicit approval
- ❌ NEVER modify original files in place
- ✅ ALWAYS maintain file hash for integrity verification
- ✅ ALWAYS support version tracking

---

## Layer 2: Page Layer

### Purpose
Split documents into page-level objects for traceability and multimodal processing.

### Storage Objects
- Page raw text and cleaned text
- Page rendered images
- Page summaries
- Page structure information
- OCR results
- Multimodal enhancement results

### Truth Source Status
**TRACEABILITY ANCHOR** - Critical for evidence linking and page-level citations.

### Key Fields
```
page_id             # Unique page identifier
doc_id              # Parent document ID
page_no             # Page number in document
page_image_path     # Path to page image
page_image_hash     # Page image hash
raw_text            # Raw extracted text
cleaned_text        # Cleaned text
page_type           # Page type (text, table, diagram, mixed)
has_table           # Contains table flag
has_diagram         # Contains diagram flag
has_fault_code      # Contains fault code flag
has_procedure       # Contains procedure flag
ocr_status          # OCR processing status
multimodal_status   # Multimodal processing status
page_summary        # Page summary
page_confidence     # Confidence score
```

### Constraints
- ✅ MUST link to parent document via `doc_id`
- ✅ MUST preserve page order via `page_no`
- ✅ MUST store page images for visual traceability
- ❌ NEVER skip page layer to go directly from document to chunks

---

## Layer 3: Chunk Layer (Block-Level Semantic Layer)

### Purpose
Split pages into retrieval-optimized, extraction-ready knowledge units.

### Storage Objects
- Semantic chunks with type classification
- Text excerpts and summaries
- Keywords and entity lists
- Evidence anchors (bbox, text offsets)

### Truth Source Status
**RETRIEVAL TRUTH SOURCE** - Primary unit for search and knowledge extraction.

### Chunk Types
```
title               # Document/section titles
heading             # Section headings
paragraph           # Text paragraphs
list                # List items
table_block         # Table content
figure_caption      # Figure captions
procedure_block     # Step-by-step procedures
fault_code_block    # Fault code entries
parameter_block     # Parameter descriptions
diagram_description # Diagram descriptions
mixed_block         # Mixed content
```

### Key Fields
```
chunk_id            # Unique chunk identifier
doc_id              # Source document ID
page_id             # Source page ID
page_no             # Source page number
chunk_index         # Chunk order within page
chunk_type          # Chunk type (see above)
chunk_title         # Chunk title/heading
raw_text            # Raw chunk text
cleaned_text        # Cleaned chunk text
text_excerpt        # Short excerpt for display
summary             # Chunk summary
keyword_list        # Extracted keywords
entity_list         # Extracted entities
relation_candidates # Relation candidates
embedding_status    # Embedding generation status
embedding_model     # Embedding model used
confidence_score    # Chunk quality score
evidence_anchor     # Evidence location data
bbox_json           # Bounding box coordinates
review_status       # Review status
```

### Constraints
- ✅ MUST link to source page via `page_id` and `doc_id`
- ✅ MUST maintain chunk order via `chunk_index`
- ✅ MUST include evidence anchors for traceability
- ✅ MUST be semantically complete (not fragmented)
- ❌ NEVER create chunks without page linkage

---

## Layer 4: Fact Layer

### Purpose
Extract structured business knowledge from chunks for structured queries, graph candidates, and sample export.

### Storage Objects
- Structured facts (subject-relation-object triples)
- Evidence text and source traceability
- Normalized entity references
- Confidence and trust scores

### Truth Source Status
**STRUCTURED KNOWLEDGE TRUTH SOURCE** - Primary source for structured queries and exports.

### Fact Types (Examples)
```
Equipment Facts:
- equipment → has_component → component
- component → monitors → parameter
- sensor → measures → variable

Fault Facts:
- fault_code → means → description
- symptom → may_cause → fault
- fault → requires → repair_action
- symptom → check → diagnostic_step

Control Facts:
- strategy → controls → target_variable
- strategy → manipulates → actuator
- strategy → applies_to → scenario
- parameter → affects → behavior

Parameter Facts:
- parameter → belongs_to → parameter_group
- parameter → default_value → value
- parameter → valid_range → range
- parameter → setting_effect → effect
```

### Key Fields
```
fact_id                 # Unique fact identifier
fact_type               # Fact type category
subject                 # Subject entity
relation                # Relation type
object                  # Object entity
condition_text          # Conditional context
normalized_subject_id   # Normalized subject reference
normalized_object_id    # Normalized object reference
source_doc_id           # Source document ID
source_page_id          # Source page ID
source_page_no          # Source page number
source_chunk_id         # Source chunk ID
evidence_text           # Evidence text snippet
evidence_bbox           # Evidence bounding box
extraction_method       # Extraction method used
extraction_model        # Model used for extraction
confidence_score        # Extraction confidence
trust_level             # Trust level (L1-L4)
review_status           # Review status
fact_version            # Fact version
```

### Trust Levels
```
L1: Manufacturer explicit rules (highest trust)
L2: Engineering experience knowledge
L3: Research paper conclusions
L4: Model inference or candidates (lowest trust)
```

### Constraints
- ✅ MUST include evidence text (not just triples)
- ✅ MUST link to source chunk, page, and document
- ✅ MUST include confidence and trust level
- ✅ MUST support version tracking
- ❌ NEVER create facts without evidence
- ❌ NEVER skip chunk layer to extract directly from pages

---

## Layer 5: Index Layer

### Purpose
Accelerate queries through full-text and vector indexes.

### Storage Objects
- Full-text search indexes
- Vector embeddings and indexes
- Tag and filter indexes
- Brand, equipment type, fault code indexes

### Truth Source Status
**NOT A TRUTH SOURCE** - Indexes are derived and rebuildable from chunks.

### Index Types
```
full_text_index     # Full-text search
vector_index        # Vector similarity search
label_index         # Tag-based filtering
brand_index         # Brand filtering
equipment_index     # Equipment type filtering
fault_code_index    # Fault code lookup
domain_index        # Domain filtering
```

### Constraints
- ✅ MUST be rebuildable from chunk layer
- ✅ MUST NOT be treated as truth source
- ❌ NEVER use index as primary data storage
- ❌ NEVER assume index is always in sync with chunks

---

## Layer 6: Derived Assets Layer

### Purpose
Generate application-specific knowledge products for export and external use.

### Storage Objects
- RAG knowledge base snapshots
- Topic-specific knowledge packages
- Graph node and edge sets
- Fine-tuning JSONL samples
- FAQ sample sets
- Diagnostic templates
- External API cache results

### Truth Source Status
**NOT A TRUTH SOURCE** - All assets are derived and regenerable from previous layers.

### Asset Types
```
rag_snapshot            # RAG knowledge base export
topic_package           # Topic-specific knowledge
graph_candidate_package # Graph nodes and edges
finetune_jsonl          # Fine-tuning samples
faq_samples             # FAQ pairs
diagnostic_templates    # Diagnostic workflows
api_cache               # API response cache
```

### Constraints
- ✅ MUST be regenerable from chunks and facts
- ✅ MUST include source traceability metadata
- ❌ NEVER treat as primary truth source
- ❌ NEVER modify without regenerating from source

---

## Traceability Chain Requirements

### Four-Level Traceability

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
page → doc_id, file_path, file_hash, doc_version
```

**Level 4: Version Lineage**
```
Any entity → doc_version, parse_version, extraction_version,
             embedding_version, multimodal_version
```

### Mandatory Traceability Fields

All external outputs MUST include:
```
source_doc_id       # Source document
source_doc_name     # Document name
source_page_no      # Page number
source_chunk_id     # Chunk identifier (if applicable)
evidence_text       # Evidence snippet
confidence_score    # Confidence level
review_status       # Review status
```

---

## Version Chain Requirements

### Version Types

```
doc_version         # Document version (file changes)
parse_version       # Parser version (parsing logic changes)
extraction_version  # Extraction version (extraction rules change)
embedding_version   # Embedding model version
multimodal_version  # Multimodal model version
```

### Version Change Scenarios

1. **Original unchanged, parser upgraded** → parse_version increments
2. **Original updated, page numbers change** → doc_version increments
3. **Extraction rules changed** → extraction_version increments
4. **Multimodal model changed** → multimodal_version increments

---

## Data Flow Constraints

### Mandatory Flow

```
Raw Document → Page → Chunk → Fact → Index/Export
```

### Forbidden Shortcuts

```
❌ Document → Chunk (skipping page layer)
❌ Document → Fact (skipping page and chunk layers)
❌ Page → Fact (skipping chunk layer)
❌ Index → Truth source (index is derived only)
```

### Rebuild Requirements

- Indexes MUST be rebuildable from chunks
- Facts MUST be rebuildable from chunks
- Derived assets MUST be rebuildable from chunks and facts
- Chunks MUST be rebuildable from pages
- Pages MUST be rebuildable from raw documents
