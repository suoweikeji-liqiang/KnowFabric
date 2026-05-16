# D Concurrency Refactor Report

Run ID: `20260516T143213Z_d_concurrency_refactor`

## Scope

Implemented pure performance plumbing for LLM-bound work:

- Added async rate-limited LLM call wrapper with semaphore, RPM throttling, 429/5xx retry, and sync compatibility.
- Batched LLM arbiter adjudication through async gather while preserving cluster output order.
- Added document-level extraction runner concurrency with a global LLM-side rate limit.
- Added env-based concurrency controls.

No semantic prompt, facet, merger, schema, oracle, embedding, or DB apply behavior was intentionally changed.

## Backup

Pre-work database backup:

```text
/tmp/d_concurrency_pre_20260516T143140Z.sql
```

Size check: `262M`.

## Files Changed

- `packages/compiler/rate_limited_client.py`
- `packages/compiler/canonical_key.py`
- `packages/compiler/llm_compiler.py`
- `scripts/run_hvac_doclevel_extraction_batch.py`
- `packages/core/config.py`
- `.env.llm.example`
- `tests/test_concurrent_llm.py`

## Configuration

New env vars:

```text
LLM_MAX_CONCURRENT=8
LLM_MAX_RPM=60
LLM_MAX_RETRIES=5
EXTRACTION_DOC_CONCURRENCY=8
```

Defaults are conservative and preserve serial DB apply.

## Speed Benchmark

Benchmarks used deterministic mock LLM/extraction work to isolate concurrency scheduling from LLM nondeterminism and DB writes.

| Workload | Serial | Concurrent | Speedup |
| --- | ---: | ---: | ---: |
| LLM arbiter / regroup proxy | 1.6774s | 0.2130s | 7.87x |
| Doc extraction proxy | 0.8748s | 0.1143s | 7.65x |

Production speed is bounded by configured provider quota, especially `LLM_MAX_RPM`.

## Correctness Diff

Deterministic hash comparison:

| Workload | Serial hash | Concurrent hash | Diff |
| --- | --- | --- | ---: |
| LLM arbiter / regroup proxy | `b6d67b38824e61bbe92c02a9f6d92ddc2a6d7c69` | `b6d67b38824e61bbe92c02a9f6d92ddc2a6d7c69` | 0 |
| Doc extraction proxy | `36c59d7228db315179f034d0ec2193e329857ba3` | `36c59d7228db315179f034d0ec2193e329857ba3` | 0 |

No real KO regroup write was run for the benchmark. DB apply remains serial by design.

## Rate Limit Coverage

Covered by `tests/test_concurrent_llm.py`:

- 429 retry eventually succeeds.
- Exhausted retries raises `MaxRetriesExceeded`.
- Semaphore caps active calls at configured concurrency.
- RPM limiter throttles request cadence.
- Serial and concurrent arbiter outputs match.
- Serial and concurrent extraction outputs match.

## Verification

Commands run:

```bash
venv/bin/python -m pytest tests/test_concurrent_llm.py -q
venv/bin/python -m pytest tests/test_concurrent_llm.py tests/test_llm_arbiter.py tests/test_canonical_key_embedding.py tests/test_cross_source_merger.py tests/test_cross_source_merger_regroup.py tests/test_run_hvac_doclevel_extraction_batch.py -q
venv/bin/python -m py_compile packages/compiler/rate_limited_client.py packages/compiler/canonical_key.py packages/compiler/llm_compiler.py scripts/run_hvac_doclevel_extraction_batch.py packages/core/config.py
rm -rf /tmp/knowfabric_embedding_cache && OMLX_API_KEY=4496 LLM_MAX_RPM=6000 venv/bin/python scripts/verify_cross_publisher_merge.py --skip-precheck
venv/bin/python -m pytest tests -q
bash scripts/check-all
```

Results:

- New concurrency tests: `6 passed`
- Affected regression slice: `62 passed`
- Full pytest: `427 passed`
- Oracle: `PASS`
- Quality gates: `4/4 PASS`

## Notes

- The rate-limited wrapper is integrated under the existing sync LLM call path, so current callers can remain synchronous.
- Arbiter calls now run concurrently only for eligible LLM adjudication clusters; non-LLM and skipped clusters keep existing behavior.
- Extraction concurrency is at the document task level, while the LLM wrapper enforces global in-flight and RPM limits.
- DB writes and review-pack apply are intentionally not parallelized.
