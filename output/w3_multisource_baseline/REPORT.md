# W3 D5 Multi-Source Regression Report (H3 Embedding-First Re-run 2026-05-11)

**Status**: Embedding-first grouping deployed. Cross-brand merge depends on extraction name stability.

## H3 Pipeline

1. Extracted 129 candidates from 4 docs (Trane CVGF + McQuay ×2 + Carrier 19XR visual)
2. Embedding-first group_and_normalize (BGE-M3 1024-dim, cosine ≥0.78)
3. merge_candidates → 98 merged KOs inserted

## Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Cross-publisher KOs | ≥5 | 0 | BELOW |
| Cross-language merges | ≥3 | 0 | BELOW |
| Trane+Carrier chilled water merge | ≥1 | 0 | BELOW |
| Max layers per KO | ≤8 | **4** | MET |
| Degenerate canonical_keys | 0 | **0** | MET |
| Consensus states | ≥3 | **3** (single_source, material_conflict, agreed) | MET |
| Total KOs (was 129) | significantly less | **98** (24% reduction) | MET |

## Consensus Distribution

- single_source: 75
- material_conflict: 20
- agreed: 3

## Root Cause: Extraction Name Instability

The expected cross-brand pairs from docs/39 §1 are NOT in the current KO set:
- "External Chilled Water Setpoint" → not extracted
- "Evaporator Leaving Water Temperature" → not extracted
- "Motor Current Limit" → not extracted

Each LLM extraction run produces different parameter names. Cross-brand merge
requires stable, consistent naming across documents. Embedding clustering works
(87-name cross-brand cluster detected at 0.78) but names are inconsistent.

## What Works

- E2 batching: max 4 layers (no 280-monster) ✓
- E3 defensive sanity: 0 degenerate keys ✓
- R3 empty-value: 3 agreed states ✓
- H2 embedding-first: clustering functional, terminology YAML override ✓
- pg_dump backup: 125MB ✓
