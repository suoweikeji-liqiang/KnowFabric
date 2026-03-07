# Test Fixtures

This directory contains test fixtures and sample documents for Phase 1 P0 testing.

## Structure

```
tests/
├── fixtures/
│   ├── documents/          # Sample PDF documents
│   └── __init__.py        # Fixture definitions
└── test_main_chain.py     # Integration test
```

## Sample Documents

Place sample PDF documents in `tests/fixtures/documents/` for testing:

- `sample_hvac_manual.pdf` - Sample HVAC manual
- `sample_text_document.pdf` - Sample text document

## Running Tests

```bash
# Run integration test
python tests/test_main_chain.py
```

## Test Coverage

Phase 1 P0 tests cover:
- Service instantiation
- Main chain structure validation

Future tests will cover:
- Document import
- Page generation
- Chunk generation
- Retrieval with traceability
