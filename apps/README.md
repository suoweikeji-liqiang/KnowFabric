# Apps

Application entry points for KnowFabric.

## Structure

- **api/** - REST API service for external queries
- **mcp/** - MCP server for AI-agent tool access
- **worker/** - Background processing worker entry point
- **admin-web/** - Placeholder shell, not part of the current external-evaluation path

## Development

Each app is independently deployable but shares packages from the monorepo.

For current productization work, the operator-facing path is:

1. bootstrap the read-only demo bundle
2. run API/MCP smoke
3. hand off `output/demo/v1_demo_brief.md`

See [`docs/22_external-evaluation-guide.md`](../docs/22_external-evaluation-guide.md).
