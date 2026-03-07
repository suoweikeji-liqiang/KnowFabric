"""Test fixtures for Phase 1 P0."""

# Sample PDF paths for testing
SAMPLE_PDFS = [
    "tests/fixtures/documents/sample_hvac_manual.pdf",
    "tests/fixtures/documents/sample_text_document.pdf"
]

# Expected document structure
EXPECTED_DOC_FIELDS = [
    'doc_id',
    'file_hash',
    'storage_path',
    'file_name',
    'parse_status'
]

# Expected page structure
EXPECTED_PAGE_FIELDS = [
    'page_id',
    'doc_id',
    'page_no',
    'cleaned_text'
]

# Expected chunk structure
EXPECTED_CHUNK_FIELDS = [
    'chunk_id',
    'doc_id',
    'page_id',
    'page_no',
    'cleaned_text',
    'chunk_type'
]

# Expected retrieval result structure (with traceability)
EXPECTED_RETRIEVAL_FIELDS = [
    'chunk_id',
    'doc_id',
    'page_no',
    'evidence_text'
]
