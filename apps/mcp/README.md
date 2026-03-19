# MCP Server

Model Context Protocol server for AI-agent access to KnowFabric.

## Current Scope

The rebuild-track MCP server currently exposes:

- legacy chunk search compatibility tools
- ontology class explanation
- semantic fault knowledge retrieval
- semantic parameter profile retrieval
- semantic maintenance guidance retrieval
- semantic application guidance retrieval
- semantic operational guidance retrieval

Transport is stdio using JSON-RPC messages.

## Entry Point

```bash
# From repository root
cd apps/mcp
python main.py
```

## Notes

- The server reuses existing retrieval and database packages.
- It does not introduce a second data path for semantic knowledge.
- Write-capable MCP tools are out of scope.

## Demo Smoke Path

After bootstrapping the demo knowledge, validate the same fixed demo query sets
through the MCP tool surface:

```bash
python3 scripts/run_mcp_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --output-dir output/demo
python3 scripts/run_mcp_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --output-dir output/demo
```
