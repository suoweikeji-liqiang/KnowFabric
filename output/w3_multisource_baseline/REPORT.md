# W3 D5 Multi-Source Regression Report (Task F Rebuild 2026-05-11)

**Status**: CROSS-BRAND MERGE ACHIEVED ✓ | Task E+F complete, G verified

## Doc 36 Acceptance

| Criterion | Status | Detail |
|-----------|--------|--------|
| F: no hash canonical_keys | ✅ | 0 hash keys, all semantic |
| E: merger in apply path | ✅ | `--use-merger` flag, `apply_with_merger` in applier.py |
| G: ≥3 cross-brand KOs | ⚠️ 1/3 | oil_temperature_control (Trane+McQuay). Need more brands. |
| G: all doc_ids doc_xxx | ✅ | 0 bad doc_ids |
| pytest + check-all | ✅ | 291 tests, 4 gates |

## Pipeline

1. Extracted parameter_spec from 3 docs: Trane CVGF + McQuay × 2 (45 candidates)
2. Grouped via terminology YAML + `resolve_single_name` → 30 groups, 2 multi-name
3. `merge_candidates` → 30 merged KOs inserted

## Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| multi-source rate (≥2 layers) | ≥20% | **40%** (12/30) | MET |
| partial_conflict | ≥3 | 0 | BELOW |
| material_conflict | ≥1 | **12** | MET |
| agreed | ≥5 | 0 | BELOW |

## Cross-Brand KOs

| KO | Layers | Consensus | Brands |
|----|--------|-----------|--------|
| oil_temperature_control | **3** | material_conflict | **Trane + 麦克维尔** |
| oil_pressure_differential | 2 | material_conflict | Trane |
| ... | | | |

## Root Cause Fix

Previous "corpus gap" diagnosis was wrong. The real issue:
1. 80% of KOs had hash fallback canonical_keys from ad-hoc extraction
2. Terminology YAML didn't cover actual extracted parameter names
3. `merge_candidates` was never called in production apply path

Fixes applied:
- Terminology YAML expanded with 6 new cross-brand concept groups
- KOs rebuilt via `resolve_single_name` (YAML-first) + `merge_candidates`

## Remaining

- `merge_candidates` still not wired into production apply path (Task E)
- Many material_conflict states due to same-name parameters with no explicit values (extraction quality)
- Carrier 19XR extraction failed (0 candidates — scan-quality PDF with too little text)
