# Manual Validation Round 2

**Status:** Rebuild Validation Note
**Last Updated:** 2026-03-18

This note captures the second manual-driven validation pass, focused on
`parameter_profile` and `maintenance_guidance`.

---

## Goal

Check whether the rebuild can represent real parameter and maintenance material,
not only fault-code material.

---

## Manuals Used

### HVAC maintenance validation

- `/Users/asteroida/a00238/21、国祥/【国祥】KMS模块机操作用户手册-20RT30RT40RT（56页）.pdf`

### Drive parameter validation

- `/Volumes/TSD302/pan/vfd/西门子/G120XA.pdf`

---

## What Was Validated

### 1. Manual-backed parameter profiles are viable

The Siemens G120XA manual provides concrete parameter rows such as:

- `p0604` motor temperature alarm threshold
- `p0605` motor temperature fault threshold

These fit the current `parameter_spec` object type without introducing a new
knowledge object type.

### 2. Manual-backed maintenance guidance is viable

The Guoxiang KMS module-unit manual provides operational corrective guidance
that can be represented as:

- `maintenance_procedure`
- linked `diagnostic_step`

This supports the current split between maintenance and diagnostic knowledge
without introducing project-instance logic.

### 3. The semantic write path is now more realistic

These entries are no longer inserted manually in each API test. They are loaded
through the reusable seed path:

`manual fixture -> seed_manual_validation_fixtures.py -> semantic tables`

That means the rebuild now has a practical intermediate ingestion step for
manual-backed curation.

---

## Fixtures Added

- `/Users/asteroida/work/KnowFabric/tests/fixtures/manual_validation/drive_parameter_profiles.json`
- `/Users/asteroida/work/KnowFabric/tests/fixtures/manual_validation/hvac_maintenance_guidance.json`

---

## Validation Outcome

### Confirmed

- `parameter_profile` route works against real parameter material.
- `maintenance_guidance` route works against real maintenance material.
- The reusable seed path is sufficient for curated manual-backed population of
  semantic tables.

### Still Not Proven

- automatic extraction from parsed chunks into these semantic rows
- large-scale fixture/backfill workflows
- manual-backed `parameter_profile` validation for a second drive vendor

### Immediate Implication

The next highest-value step is not more contract work. It is a first
semi-automated backfill path from chunk-level evidence into curated semantic
rows.
