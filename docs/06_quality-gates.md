# Quality Gates

**Status:** Enforcement Contract - Automated CI Checks
**Last Updated:** 2026-03-07

Quality gates are automated checks that validate repository standards before merge. All gates must pass - no exceptions.

---

## Gate 1: Documentation Completeness

**Purpose:** Ensure all modules and domain packages have required documentation.

**Command:** `scripts/check-docs`

**What it checks:**
- Core docs exist (00-06 series)
- All packages have README files
- All domain packages have manifest.yaml, label_schema.yaml, entity_schema.yaml
- Root README has standards entry

**Minimum implementation for now:**
- File existence checks only
- No content validation yet

**What causes failure:**
- Missing core doc files
- Missing package README
- Missing domain package required files
- Missing root README standards section

**When it must run:**
- Pre-commit hook
- CI pipeline on PR
- Before merge

**What it does not yet check:**
- Documentation content quality
- API documentation completeness
- Migration script descriptions

---

## Gate 2: Boundary Compliance

**Purpose:** Ensure modules respect dependency boundaries and no forbidden imports exist.

**Command:** `scripts/check-boundaries`

**What it checks:**
- Core directories exist (packages/core, packages/db, etc.)
- Simple static import/path checks
- Core package doesn't import from other packages
- Ingest doesn't import from parser/chunking/extraction/retrieval
- Parser doesn't import from chunking/extraction/retrieval
- Domain packages don't have runtime code imports

**Minimum implementation for now:**
- Directory structure validation
- Basic import pattern matching (grep-based)
- Covers critical boundaries only

**What causes failure:**
- Forbidden import detected (e.g., ingest → parser)
- Core importing from any other package
- Domain package importing runtime code

**When it must run:**
- Pre-commit hook
- CI pipeline on PR
- Before merge

**What it does not yet check:**
- Circular dependencies (complex analysis)
- All possible boundary violations
- Transitive dependencies

---

## Gate 3: Forbidden Dependencies

**Purpose:** Catch specific forbidden patterns beyond basic boundaries.

**Command:** `scripts/check-forbidden-deps`

**What it checks:**
- Domain packages don't contain SQL queries
- Core modules don't contain domain-specific logic
- No layer-skipping shortcuts in code

**Minimum implementation for now:**
- Simple pattern matching
- Checks for obvious violations
- Minimal but functional

**What causes failure:**
- SQL in domain package files
- Domain-specific keywords in core package
- Direct chunk creation from documents

**When it must run:**
- Pre-commit hook
- CI pipeline on PR
- Before merge

**What it does not yet check:**
- Complex semantic analysis
- All possible forbidden patterns
- Runtime behavior violations

---

## Gate 4: All Gates Combined

**Purpose:** Run all quality gates in sequence and report aggregate results.

**Command:** `scripts/check-all`

**What it checks:**
- Runs check-docs
- Runs check-boundaries
- Runs check-forbidden-deps
- Aggregates exit codes

**Minimum implementation for now:**
- Sequential execution
- Proper exit code handling
- Clear summary output

**What causes failure:**
- Any individual gate fails

**When it must run:**
- Before PR merge
- CI pipeline final check

**What it does not yet check:**
- Lint, typecheck, tests (future gates)
