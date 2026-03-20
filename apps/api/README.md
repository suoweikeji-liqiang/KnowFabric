# API Service

REST entry point for KnowFabric.

Current read surfaces:

- `GET /health`
- `GET /api/v1/chunks/search` for legacy chunk-search compatibility
- rebuild-track semantic routes under `/api/v2/`

The current semantic contract is documented in
[`docs/14_semantic-api-mcp-contract.md`](../../docs/14_semantic-api-mcp-contract.md).
The current operator flow is documented in
[`docs/22_external-evaluation-guide.md`](../../docs/22_external-evaluation-guide.md).

## Running Locally

From the repository root:

```bash
cd apps/api
python main.py
```

API defaults:

- base URL: `http://127.0.0.1:8000`
- health: `http://127.0.0.1:8000/health`
- docs: `http://127.0.0.1:8000/docs`

## Live Smoke Path

After bootstrapping the demo bundle, verify the same fixed HVAC and drive query
sets through real HTTP routes:

```bash
python3 scripts/run_api_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo
python3 scripts/run_api_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo
python3 scripts/build_v1_demo_brief.py --report-dir output/demo --output output/demo/v1_demo_brief.md
```

## Notes

- The API path is read-only for the current external evaluation bundle.
- Semantic delivery remains evidence-backed and scoped to ontology identifiers.
- Project-instance/runtime/control logic remains out of scope.
