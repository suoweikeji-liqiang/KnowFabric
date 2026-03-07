# Quality Gates

## Purpose

Quality gates ensure all code meets repository standards before merge. These gates are automated checks that validate documentation completeness, boundary compliance, code quality, and test coverage.

## Gate Categories

### 1. Documentation Completeness Gate

**Command:** `npm run check:docs`

**Validates:**
- All modules have README files
- All domain packages have required files (manifest, schemas)
- API endpoints are documented
- Migration scripts have descriptions
- ADRs are properly formatted

**Failure Conditions:**
- Missing README in any package
- Missing manifest.yaml in domain package
- Undocumented API endpoint
- Migration without description

---

### 2. Boundary Compliance Gate

**Command:** `npm run check:boundaries`

**Validates:**
- No forbidden imports between modules
- No circular dependencies
- Core module has no external dependencies
- Domain packages don't import code modules

**Failure Conditions:**
- `ingest` imports from `parser`
- `parser` imports from `chunking`
- `extraction` imports from `retrieval`
- Circular dependency detected
- Domain package imports core code

**Example Violations:**
```typescript
// ❌ FORBIDDEN: parser importing from chunking
import { chunkText } from '@knowfabric/chunking';

// ❌ FORBIDDEN: core importing from db
import { Database } from '@knowfabric/db';

// ✅ ALLOWED: chunking importing from core
import { Chunk } from '@knowfabric/core';
```

---

### 3. Forbidden Dependencies Gate

**Command:** `npm run check:forbidden-deps`

**Validates:**
- No direct database access from domain packages
- No hardcoded domain logic in core modules
- No skipping of intermediate layers

**Failure Conditions:**
- Domain package contains SQL queries
- Core module contains HVAC-specific logic
- Code creates facts directly from documents (skipping chunks)

---

### 4. Lint Gate

**Command:** `npm run lint`

**Validates:**
- Code style consistency
- No unused variables
- No console.log statements
- Proper TypeScript types

**Failure Conditions:**
- ESLint errors
- Unused imports
- Any/unknown types without justification

---

### 5. Type Check Gate

**Command:** `npm run typecheck`

**Validates:**
- All TypeScript code type-checks
- No implicit any
- Proper interface definitions

**Failure Conditions:**
- Type errors
- Missing type definitions
- Unsafe type assertions

---

### 6. Test Gate

**Command:** `npm run test`

**Validates:**
- All tests pass
- Minimum 70% code coverage
- Critical paths have 100% coverage

**Failure Conditions:**
- Any test failure
- Coverage below 70%
- Critical path not covered

**Critical Paths:**
- Document ingestion
- Page parsing
- Chunk generation
- Fact extraction
- Traceability chain
- API endpoints

---

### 7. Build Gate

**Command:** `npm run build`

**Validates:**
- All packages build successfully
- No build errors or warnings
- Output artifacts are valid

**Failure Conditions:**
- Build errors
- Missing dependencies
- Invalid configuration

---

## Phase-Specific Gates

### Phase 1 Acceptance Gate

**Command:** `npm run check:phase1`

**Validates:**
1. Can import 100+ documents
2. Document/page/chunk structure is stable
3. Chunks are searchable
4. Traceability fields present in results
5. Incremental import works
6. Partial re-processing works

**Test Procedure:**
```bash
# Import sample documents
npm run test:import -- --sample-set phase1

# Verify structure
npm run test:verify-structure

# Test search
npm run test:search

# Test traceability
npm run test:traceability

# Test incremental
npm run test:incremental
```

---

### Phase 2 Acceptance Gate

**Command:** `npm run check:phase2`

**Validates:**
1. Facts extracted with evidence
2. Facts link to source chunks
3. Fact query API works
4. Review workflow operational
5. Review audit trail complete

---

### Phase 3 Acceptance Gate

**Command:** `npm run check:phase3`

**Validates:**
1. Domain packages validated
2. Export APIs functional
3. External APIs documented
4. Traceability in all responses
5. Rate limiting works

---

## Pre-Commit Checks

**Automated via Git hooks:**

```bash
# Run before every commit
npm run pre-commit
```

**Includes:**
- Lint staged files
- Type check affected files
- Run affected tests
- Validate commit message format

---

## Pre-Merge Checks

**Required before PR merge:**

```bash
# Run full gate suite
npm run check:all
```

**Includes:**
- All documentation gates
- All boundary gates
- All code quality gates
- All test gates
- Phase-specific gates (if applicable)

---

## Quality Metrics

### Code Quality Metrics

```
Lines per file:        < 800
Lines per function:    < 50
Cyclomatic complexity: < 10
Test coverage:         > 70%
Critical path coverage: 100%
```

### Documentation Metrics

```
Modules with README:     100%
APIs documented:         100%
Domain packages complete: 100%
```

### Boundary Metrics

```
Forbidden imports:     0
Circular dependencies: 0
Boundary violations:   0
```

---

## Continuous Monitoring

### Daily Checks

- Run full gate suite on main branch
- Monitor test flakiness
- Track coverage trends
- Check for new boundary violations

### Weekly Reviews

- Review failed gate reports
- Update quality thresholds if needed
- Address technical debt
- Update documentation

---

## Exemption Process

In rare cases, a gate failure may need exemption:

1. Document reason in ADR
2. Get approval from tech lead
3. Create tracking issue for resolution
4. Set deadline for fix
5. Add exemption to gate config

**Example exemption:**
```yaml
# .quality-gates.yaml
exemptions:
  - gate: boundary-check
    module: legacy-parser
    reason: "Temporary coupling during migration"
    issue: "#123"
    deadline: "2026-04-01"
    approved_by: "tech-lead"
```

---

## Gate Failure Response

### When a Gate Fails

1. **Identify root cause** - Review failure logs
2. **Fix immediately** - Don't bypass gates
3. **Verify fix** - Re-run gate locally
4. **Update tests** - Add regression test if needed
5. **Document** - Update docs if gate revealed gap

### Common Failures and Fixes

**Boundary violation:**
```
Error: packages/parser imports from packages/chunking
Fix: Remove import, use core interfaces instead
```

**Missing traceability:**
```
Error: API response missing source_doc_id
Fix: Add traceability fields to response schema
```

**Test coverage low:**
```
Error: Coverage 65% (threshold 70%)
Fix: Add tests for uncovered code paths
```

---

## Quality Gate Configuration

**File:** `.quality-gates.yaml`

```yaml
gates:
  documentation:
    enabled: true
    required_files:
      - README.md
      - manifest.yaml (domain packages)

  boundaries:
    enabled: true
    forbidden_imports:
      - from: "packages/ingest"
        to: "packages/parser"
      - from: "packages/parser"
        to: "packages/chunking"

  tests:
    enabled: true
    min_coverage: 70
    critical_paths:
      - "packages/ingest/**"
      - "packages/parser/**"
      - "packages/chunking/**"
      - "packages/extraction/**"

  lint:
    enabled: true
    rules: ".eslintrc.json"

  typecheck:
    enabled: true
    strict: true
```
