# MCP Server

Model Context Protocol server for AI-agent access to KnowFabric.

## Current Scope

The rebuild-track MCP server currently exposes:

- legacy chunk search compatibility tools
- ontology class explanation
- semantic fault knowledge retrieval
- semantic parameter profile retrieval
- semantic maintenance guidance retrieval

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
