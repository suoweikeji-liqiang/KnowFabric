# Admin Web

React + TypeScript + Vite admin console for the KnowFabric knowledge engineering workflow.

This rewrite now uses:

- React
- TypeScript
- Vite
- backend-first data loading by default

Current scope is focused on the real operator flow:

- 文档录入
- 审阅中心
- 发布记录
- 工作区内的文档 → 审阅 → 发布主链

## Frontend Development

From `apps/admin-web/`:

```bash
npm install
npm run dev
```

Vite dev server:

- `http://127.0.0.1:5173/`

The frontend defaults to real backend APIs. Set `VITE_ADMIN_DATA_SOURCE=mock`
only when you explicitly want the mock console data source.

## Static Build

Build output is emitted into `apps/admin-web/static/`, which is what the Python
entrypoint serves.

```bash
npm install
npm run build
```

## Python Preview

After building:

```bash
cd apps/admin-web
python main.py
```

Then open:

- `http://127.0.0.1:4173/`
