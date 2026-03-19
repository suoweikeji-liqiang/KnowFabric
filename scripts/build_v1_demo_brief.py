#!/usr/bin/env python3
"""Build a Markdown brief from semantic demo query reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def discover_demo_report_paths(report_dir: str | Path = "output/demo") -> list[Path]:
    """Discover semantic demo report JSON files."""

    root = Path(report_dir)
    return sorted(root.glob("*__semantic_demo_report.json"))


def _load_demo_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _domain_label(report: dict[str, Any]) -> str:
    example_file = Path(report.get("example_file", ""))
    if len(example_file.parts) >= 2:
        return example_file.parts[1]
    return "unknown"


def _title_case(value: str) -> str:
    return value.replace("_", " ").title()


def _domain_summary(report: dict[str, Any]) -> dict[str, Any]:
    results = report.get("results", [])
    query_types = sorted({item.get("query_type") for item in results if item.get("query_type")})
    equipment_classes = sorted(
        {item.get("request", {}).get("equipment_class_id") for item in results if item.get("request", {}).get("equipment_class_id")}
    )
    canonical_keys = []
    for item in results:
        canonical_keys.extend(item.get("found_canonical_keys", []))
    return {
        "domain": _domain_label(report),
        "example_file": report.get("example_file"),
        "total_examples": report.get("summary", {}).get("total_examples", 0),
        "passed": report.get("summary", {}).get("passed", 0),
        "failed": report.get("summary", {}).get("failed", 0),
        "query_types": query_types,
        "equipment_classes": equipment_classes,
        "canonical_keys": canonical_keys,
        "results": results,
    }


def build_v1_demo_brief_markdown(reports: list[dict[str, Any]]) -> str:
    """Render a Markdown brief from one or more semantic demo reports."""

    if not reports:
        raise ValueError("At least one demo report is required")

    summaries = [_domain_summary(report) for report in reports]
    total_examples = sum(item["total_examples"] for item in summaries)
    total_passed = sum(item["passed"] for item in summaries)
    total_failed = sum(item["failed"] for item in summaries)
    generated_at = datetime.now(timezone.utc).isoformat()

    lines = [
        "# KnowFabric V1 Demo Brief",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Overall Status",
        "",
        f"- Domains covered: {len(summaries)}",
        f"- Demo queries: {total_examples} total",
        f"- Passed: {total_passed}",
        f"- Failed: {total_failed}",
        "",
        "## Domain Coverage",
        "",
    ]

    for item in summaries:
        lines.extend(
            [
                f"### {_title_case(item['domain'])}",
                "",
                f"- Example source: `{item['example_file']}`",
                f"- Query checks: {item['passed']}/{item['total_examples']} passed",
                f"- Equipment classes covered: {', '.join(item['equipment_classes']) if item['equipment_classes'] else 'none'}",
                f"- Query types covered: {', '.join(item['query_types']) if item['query_types'] else 'none'}",
                "",
                "Proven canonical knowledge objects:",
            ]
        )
        for canonical_key in item["canonical_keys"]:
            lines.append(f"- `{canonical_key}`")
        lines.append("")

    lines.extend(
        [
            "## Demo Commands",
            "",
            "```bash",
            "python3 scripts/run_semantic_demo_queries.py domain_packages/hvac/v2/examples/example_queries.yaml --output-dir output/demo",
            "python3 scripts/run_semantic_demo_queries.py domain_packages/drive/v2/examples/example_queries.yaml --output-dir output/demo",
            "```",
            "",
            "## Readiness Note",
            "",
            "These demo checks only pass when the expected canonical knowledge objects are present and match the required review status in the example query set.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_v1_demo_brief(
    report_paths: list[str | Path] | None = None,
    *,
    report_dir: str | Path = "output/demo",
    output_path: str | Path = "output/demo/v1_demo_brief.md",
) -> Path:
    """Build the v1 demo brief from discovered or explicit report paths."""

    resolved_paths = [Path(path) for path in report_paths] if report_paths else discover_demo_report_paths(report_dir)
    if not resolved_paths:
        raise ValueError("No demo report JSON files found")
    reports = [_load_demo_report(path) for path in resolved_paths]
    rendered = build_v1_demo_brief_markdown(reports)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    return target


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_paths", nargs="*", help="Optional explicit report JSON files")
    parser.add_argument("--report-dir", default="output/demo", help="Directory to scan when no report paths are given")
    parser.add_argument("--output", default="output/demo/v1_demo_brief.md", help="Markdown output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    target = build_v1_demo_brief(
        args.report_paths,
        report_dir=args.report_dir,
        output_path=args.output,
    )
    print(f"Wrote v1 demo brief to {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"V1 demo brief build failed: {exc}")
        raise SystemExit(1)
