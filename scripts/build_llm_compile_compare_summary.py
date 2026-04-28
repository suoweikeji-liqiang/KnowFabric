#!/usr/bin/env python3
"""Render a concise Markdown summary from an LLM compile comparison report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_candidate_keys(candidate_path: str | Path) -> list[str]:
    payload = _load_json(candidate_path)
    return [
        str(entry.get("canonical_key_candidate"))
        for entry in payload.get("candidate_entries", [])
    ]


def build_llm_compile_compare_summary(report_path: str | Path) -> str:
    """Build a Markdown summary from one compare report artifact."""

    report = _load_json(report_path)
    report_root = Path(report_path).resolve().parent
    runs = report.get("runs", [])
    baseline = next((run for run in runs if run.get("name") == "rule-baseline"), None)
    baseline_keys = set(_load_candidate_keys(report_root / Path(baseline["candidate_path"]).name)) if baseline else set()

    lines = [
        "# LLM Compile Compare Summary",
        "",
        f"- Domain: `{report.get('domain_id')}`",
        f"- Filters: `{json.dumps(report.get('filters_applied', {}), ensure_ascii=False)}`",
        "",
        "## Runs",
    ]

    for run in runs:
        candidate_path = report_root / Path(run["candidate_path"]).name
        keys = _load_candidate_keys(candidate_path)
        unique_over_baseline = sorted(set(keys) - baseline_keys) if run["name"] != "rule-baseline" else []
        lines.append(
            f"- `{run['name']}`: {run['candidate_count']} candidate(s), "
            f"methods={', '.join(run.get('compiler_methods', [])) or 'none'}, "
            f"types={', '.join(run.get('knowledge_types', [])) or 'none'}"
        )
        if unique_over_baseline:
            lines.append(f"  unique_over_baseline: {', '.join(unique_over_baseline)}")

    lines.extend(
        [
            "",
            "## Pairwise Overlap",
        ]
    )
    for item in report.get("overlap_matrix", []):
        if item["left"] == item["right"]:
            continue
        lines.append(
            f"- `{item['left']}` vs `{item['right']}`: "
            f"shared={item['shared_candidates']}, left_total={item['left_total']}, right_total={item['right_total']}"
        )

    return "\n".join(lines) + "\n"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_path", help="Path to llm_compile_backend_compare_report.json")
    parser.add_argument("--output", help="Optional Markdown output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rendered = build_llm_compile_compare_summary(args.report_path)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Wrote compare summary to {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
