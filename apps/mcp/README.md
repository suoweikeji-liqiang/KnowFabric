# MCP Server

Model Context Protocol entry point for KnowFabric's read-only semantic tools.

Current tool surface:

- legacy chunk-search compatibility tools
- ontology class explanation
- semantic fault knowledge retrieval
- semantic parameter profile retrieval
- semantic maintenance guidance retrieval
- semantic application guidance retrieval
- semantic operational guidance retrieval

The semantic contract is documented in
[`docs/14_semantic-api-mcp-contract.md`](../../docs/14_semantic-api-mcp-contract.md).
The operator flow is documented in
[`docs/22_external-evaluation-guide.md`](../../docs/22_external-evaluation-guide.md).

## Running Locally

From the repository root:

```bash
cd apps/mcp
python main.py
```

Transport is stdio over JSON-RPC.

## Smoke Path

Bootstrap now runs MCP smoke as part of the demo bundle. To refresh MCP smoke
without rerunning the full bootstrap:

```bash
python3 scripts/run_mcp_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --output-dir output/demo
python3 scripts/run_mcp_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --output-dir output/demo
python3 scripts/build_v1_demo_brief.py --report-dir output/demo --output output/demo/v1_demo_brief.md
```

## Notes

- The MCP server reuses the same storage-backed semantic retrieval path as REST.
- It does not introduce a second knowledge path.
- Write-capable MCP tools remain out of scope.
