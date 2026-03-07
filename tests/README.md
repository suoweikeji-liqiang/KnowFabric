# Tests

Test suites for KnowFabric.

## Structure

- `unit/` - Unit tests for individual modules
- `integration/` - Integration tests for pipelines
- `fixtures/` - Test fixtures and sample documents

## Running Tests

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests
npm run test:integration

# Run with coverage
npm run test:coverage
```

## Test Coverage Requirements

- Minimum 70% overall coverage
- 100% coverage for critical paths:
  - Document ingestion
  - Traceability chain
  - Fact extraction
  - API endpoints

See [Engineering Standards](../docs/04_engineering-standards.md) for testing standards.
