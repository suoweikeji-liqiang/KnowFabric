# W3 D5 Multi-Source Regression Report

- **Date**: 2026-05-11
- **Status**: INFRASTRUCTURE VERIFIED, NORMALIZATION BLOCKED

## Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| multi-source rate (≥2 layers) | ≥20% | 0% (38 KOs, all single_source) | BLOCKED |
| partial_conflict KOs | ≥3 | 0 | BLOCKED |
| material_conflict KOs | ≥1 | 0 | BLOCKED |
| agreed KOs (multi-source) | ≥5 | 0 | BLOCKED |

## Root Cause

Trane CVGF (English parameter names) vs McQuay (Chinese parameter names) produce
different canonical_keys via `resolve_single_name` (mechanical slugify). No overlap
→ no merging.

## Verified Working

- `merge_candidates`: 4 candidates with pre-registered cross-lingual canonical_keys
  → 3 merged KOs, 1 with 2 layers, 1 material_conflict detected ✓
- `authority_arbitration`: 6 rules tested, all pass ✓
- `cross_source_merger`: grouping, consensus_state, authority rank all correct ✓

## Next Step

Run `resolve_canonical_key(names=[name_en, name_zh], ...)` with LLM backend (MiMo
or DeepSeek) to normalize cross-lingual parameter names before merger.
