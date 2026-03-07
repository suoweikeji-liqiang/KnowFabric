# Engineering Standards

## Naming Conventions

### Database Tables

- Use lowercase with underscores: `snake_case`
- Use singular form consistently
- Be descriptive and unambiguous

**Examples:**
```
✅ document
✅ document_page
✅ content_chunk
✅ extracted_fact
✅ review_record

❌ docs
❌ pages
❌ chunks
❌ facts
```

### Database Fields

- Use `snake_case`
- Be semantically clear
- Avoid abbreviations

**Examples:**
```
✅ page_no
✅ chunk_type
✅ confidence_score
✅ review_status
✅ source_doc_id

❌ pno
❌ ctype
❌ conf
❌ stat2
❌ src_doc
```

### API Endpoints

- Use resource-oriented naming
- Use nouns, not verbs
- Include version prefix

**Examples:**
```
✅ /api/v1/documents
✅ /api/v1/chunks/search
✅ /api/v1/facts/query
✅ /api/v1/exports/finetune-samples

❌ /api/getDocuments
❌ /api/searchChunks
❌ /documents (no version)
```

### Domain Identifiers

Use stable, lowercase identifiers:

```
✅ hvac
✅ drive
✅ energy_storage
✅ photovoltaics

❌ HVAC
❌ 暖通
❌ nuantong
❌ drv
```

### Relation Names

Use controlled vocabulary with consistent naming:

```
✅ belongs_to
✅ contains
✅ monitors
✅ controls
✅ indicates
✅ causes
✅ may_cause
✅ applies_to
✅ recommends

❌ Free-form relation names
❌ Synonyms (has/contains/includes mixed usage)
```

## Repository Structure

### Directory Organization

```
KnowFabric/
├── apps/                    # Application entry points
├── packages/               # Shared packages (by responsibility)
├── domain_packages/        # Domain configurations (by domain)
├── pipelines/             # Processing pipelines
├── scripts/               # Utility scripts
├── tests/                 # Test suites
├── docs/                  # Documentation
└── final_docs/            # Original requirements
```

### Module Organization Principles

1. **By responsibility, not by type**
   - ✅ `packages/extraction/` (responsibility)
   - ❌ `packages/utils/` (type)

2. **High cohesion, low coupling**
   - Each package has clear purpose
   - Minimal dependencies between packages

3. **No "common" or "shared" dumping grounds**
   - ❌ `packages/common/everything.ts`
   - ✅ Specific packages with clear scope

## Migration Standards

### Migration Files

**Naming:** `YYYYMMDDHHMMSS_description.sql`

**Example:** `20260307120000_create_document_table.sql`

### Migration Rules

1. ✅ ALL schema changes via migrations
2. ✅ Migrations are immutable (never edit after merge)
3. ✅ Include both up and down migrations
4. ✅ Test migrations on sample data before merge
5. ❌ NEVER modify schema directly in database

### Migration Template

```sql
-- Migration: 20260307120000_create_document_table
-- Description: Create document table for raw document storage

-- UP
CREATE TABLE document (
    doc_id VARCHAR(64) PRIMARY KEY,
    file_name VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL,
    source_domain VARCHAR(64),
    import_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_hash ON document(file_hash);
CREATE INDEX idx_document_domain ON document(source_domain);

-- DOWN
DROP TABLE IF EXISTS document;
```

## API Standards

### Request/Response Format

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query parameter 'domain' is required",
    "details": { ... },
    "request_id": "req_abc123"
  }
}
```

### Pagination

All list endpoints must support:
```
?page=1&limit=20
```

### Filtering

Support common filters:
```
?domain=hvac
?brand=ABB
?equipment_type=chiller
?trust_level=L1,L2
?review_status=approved
```

## Logging Standards

### Structured Logging

All logs must be structured JSON:

```json
{
  "timestamp": "2026-03-07T12:51:09.691Z",
  "level": "info",
  "job_id": "job_abc123",
  "stage": "parsing",
  "doc_id": "doc_xyz789",
  "elapsed_ms": 1234,
  "status": "success",
  "message": "Document parsed successfully"
}
```

### Log Levels

```
ERROR   - System errors, failures
WARN    - Warnings, degraded performance
INFO    - Normal operations, milestones
DEBUG   - Detailed debugging information
```

### Required Fields

```
timestamp    # ISO 8601 timestamp
level        # Log level
job_id       # Job identifier (for long-running tasks)
stage        # Processing stage
doc_id       # Document ID (when applicable)
message      # Human-readable message
```

## Task/Job/Stage Standards

### Task States

```
pending      # Queued, not started
running      # Currently executing
success      # Completed successfully
failed       # Failed with error
skipped      # Skipped (e.g., already processed)
retrying     # Retrying after failure
canceled     # Canceled by user
```

### Stage Tracking

Each processing stage must record:

```
stage_id         # Unique stage identifier
job_id           # Parent job ID
stage_name       # Stage name (parsing, chunking, etc.)
status           # Stage status
started_at       # Start timestamp
completed_at     # Completion timestamp
elapsed_ms       # Elapsed time in milliseconds
error_message    # Error message (if failed)
retry_count      # Number of retries
```

### Idempotency

All processing tasks must be idempotent:
- Re-running same task produces same result
- No duplicate data on retry
- Use unique identifiers to detect duplicates

## Error Handling Standards

### Error Categories

```
VALIDATION_ERROR     # Input validation failed
NOT_FOUND           # Resource not found
PERMISSION_DENIED   # Access denied
RATE_LIMIT_EXCEEDED # Rate limit hit
INTERNAL_ERROR      # System error
EXTERNAL_ERROR      # External service error
```

### Error Handling Rules

1. ✅ Handle errors at every layer
2. ✅ Provide user-friendly messages in API responses
3. ✅ Log detailed error context server-side
4. ✅ Never expose internal details to users
5. ❌ Never silently swallow errors

## Testing Standards

### Test Organization

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
└── fixtures/          # Test fixtures and sample data
```

### Test Coverage Requirements

- Minimum 70% code coverage
- 100% coverage for critical paths:
  - Document ingestion
  - Traceability chain
  - Fact extraction
  - API endpoints

### Sample Document Set

Maintain fixed sample documents for regression testing:

```
tests/fixtures/documents/
├── text_pdf_sample.pdf
├── scanned_pdf_sample.pdf
├── mixed_content_sample.pdf
├── parameter_table_sample.pdf
├── fault_code_sample.pdf
├── training_ppt_sample.pptx
└── abb_manual_sample.pdf
```

## Configuration Management

### Environment Separation

```
config/
├── dev.yaml
├── test.yaml
└── prod.yaml
```

### Configuration Categories

```
model_config         # Model endpoints, versions
storage_config       # File/object storage settings
pipeline_config      # Processing pipeline settings
domain_config        # Domain package settings
database_config      # Database connection settings
```

### Secrets Management

- ❌ NEVER commit secrets to repository
- ✅ Use environment variables
- ✅ Use secret management service (production)
- ✅ Validate required secrets at startup

## Forbidden Practices

### Code Practices

```
❌ Hardcoding domain logic in core modules
❌ Skipping intermediate data layers
❌ Treating indexes as truth source
❌ Mutating input parameters
❌ Using magic numbers without constants
❌ Deep nesting (>4 levels)
❌ Functions >50 lines
❌ Files >800 lines
```

### Data Practices

```
❌ Deleting original documents without approval
❌ Modifying original files in place
❌ Creating facts without evidence
❌ Skipping traceability fields
❌ Mixing domain-specific logic into core tables
```

### API Practices

```
❌ Returning results without traceability fields
❌ Exposing internal error details
❌ Using verbs in endpoint names
❌ Omitting version prefix
❌ Returning unbounded result sets
```

## Code Quality Checklist

Before marking work complete:

- [ ] Code is readable with clear naming
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling at all layers
- [ ] No hardcoded values (use config)
- [ ] No mutation of input parameters
- [ ] Traceability fields included
- [ ] Tests written and passing
- [ ] Documentation updated
