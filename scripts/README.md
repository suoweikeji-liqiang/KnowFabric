# Scripts

Utility scripts and quality gate checks.

## Quality Gates

- `check-docs` - Verify documentation completeness
- `check-boundaries` - Verify module boundaries
- `check-forbidden-deps` - Check for forbidden dependencies
- `check-all` - Run all quality checks

## Utilities

- Database migration scripts
- Data import/export utilities
- Development helpers

## Usage

```bash
# Run quality gates
npm run check:all

# Run specific gate
npm run check:boundaries
```

See [Quality Gates](../docs/06_quality-gates.md) for details.
