#!/usr/bin/env python3
"""Refresh the Chinese demo bundle and launch the read-only evaluation shell."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_live_demo_evaluation import run_live_demo_evaluation


def run_chinese_demo_shell(
    *,
    output_dir: str | Path = "output/demo",
    host: str = "127.0.0.1",
    port: int = 4173,
    skip_refresh: bool = False,
    bundle_language: str = "zh",
) -> int:
    """Optionally refresh the bundle, then launch the read-only admin shell."""

    artifact_root = Path(output_dir)
    if not skip_refresh:
        run_live_demo_evaluation(
            output_dir=artifact_root,
            bundle_language=bundle_language,
        )

    env = os.environ.copy()
    env["DEMO_ARTIFACT_DIR"] = str(artifact_root)
    env["ADMIN_WEB_HOST"] = host
    env["ADMIN_WEB_PORT"] = str(port)
    env["PYTHONUNBUFFERED"] = "1"
    repo_root = Path(__file__).resolve().parent.parent
    print(f"Launching Chinese demo shell at http://{host}:{port}/")
    return subprocess.run(
        [sys.executable, "apps/admin-web/main.py"],
        cwd=repo_root,
        env=env,
        check=False,
    ).returncode


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="output/demo", help="Demo bundle directory to serve")
    parser.add_argument("--host", default="127.0.0.1", help="Admin shell host")
    parser.add_argument("--port", type=int, default=4173, help="Admin shell port")
    parser.add_argument("--skip-refresh", action="store_true", help="Serve the current bundle without rerunning live evaluation")
    parser.add_argument("--bundle-language", default="zh", choices=["en", "zh"], help="Bundle language when refreshing before serve")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    return run_chinese_demo_shell(
        output_dir=args.output_dir,
        host=args.host,
        port=args.port,
        skip_refresh=args.skip_refresh,
        bundle_language=args.bundle_language,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Chinese demo shell failed: {exc}")
        raise SystemExit(1)
