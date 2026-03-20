# Admin Web

Read-only Chinese evaluation shell for the current KnowFabric demo bundle.

This is intentionally a thin UI:

- reads `output/demo/` bundle artifacts
- shows evaluation status, domain coverage, and query highlights
- stays read-only and evidence-oriented

It is not an admin platform, review workflow system, or UI-first product shell.

## Running

From the repository root:

```bash
python3 scripts/run_chinese_demo_shell.py --output-dir output/demo
```

Then open:

- `http://127.0.0.1:4173/`

Manual fallback:

```bash
python3 scripts/run_live_demo_evaluation.py --output-dir output/demo
cd apps/admin-web
python main.py
```
