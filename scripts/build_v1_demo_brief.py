#!/usr/bin/env python3
"""Build a Markdown demo brief and handoff guide from demo artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SEMANTIC_REPORT_SUFFIX = "semantic_demo_report"
MCP_REPORT_SUFFIX = "mcp_smoke_report"
API_REPORT_SUFFIX = "api_smoke_report"
DEFAULT_REPORT_DIR = "output/demo"
DEFAULT_BRIEF_PATH = "output/demo/v1_demo_brief.md"


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _discover_report_paths(report_dir: str | Path, suffix: str) -> list[Path]:
    root = Path(report_dir)
    return sorted(root.glob(f"*__{suffix}.json"))


def discover_demo_report_paths(report_dir: str | Path = DEFAULT_REPORT_DIR) -> list[Path]:
    """Discover semantic demo report JSON files."""

    return _discover_report_paths(report_dir, SEMANTIC_REPORT_SUFFIX)


def discover_mcp_smoke_report_paths(report_dir: str | Path = DEFAULT_REPORT_DIR) -> list[Path]:
    """Discover MCP smoke report JSON files."""

    return _discover_report_paths(report_dir, MCP_REPORT_SUFFIX)


def discover_api_smoke_report_paths(report_dir: str | Path = DEFAULT_REPORT_DIR) -> list[Path]:
    """Discover API smoke report JSON files."""

    return _discover_report_paths(report_dir, API_REPORT_SUFFIX)


def _load_demo_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _entry_from_report(report: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    return {
        "path": str(path) if path is not None else None,
        "report": report,
    }


def _domain_label(report: dict[str, Any]) -> str:
    example_file = Path(report.get("example_file", ""))
    if len(example_file.parts) >= 2:
        return example_file.parts[1]
    return "unknown"


def _title_case(value: str) -> str:
    return value.replace("_", " ").title()


def _surface_status(surface: str, report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    if surface == "semantic":
        return "passed" if summary.get("failed", 0) == 0 else "failed"
    if surface == "mcp":
        ready = report.get("initialize_ok") and report.get("tools_list_ok")
        return "passed" if ready and summary.get("failed", 0) == 0 else "failed"
    health = report.get("health", {})
    return "passed" if health.get("status") == "passed" and summary.get("failed", 0) == 0 else "failed"


def _surface_detail(surface: str, report: dict[str, Any]) -> str | None:
    if surface == "mcp":
        initialize = "passed" if report.get("initialize_ok") else "failed"
        tools_list = "passed" if report.get("tools_list_ok") else "failed"
        return f"initialize={initialize}, tools_list={tools_list}"
    if surface == "api":
        health = report.get("health", {})
        status = health.get("status", "unknown")
        code = health.get("http_status", "n/a")
        return f"health={status} ({code})"
    return None


def _surface_report_summary(entry: dict[str, Any], surface: str) -> dict[str, Any]:
    report = entry["report"]
    results = report.get("results", [])
    query_types = sorted({item.get("query_type") for item in results if item.get("query_type")})
    equipment_classes = sorted(
        {
            item.get("request", {}).get("equipment_class_id")
            for item in results
            if item.get("request", {}).get("equipment_class_id")
        }
    )
    canonical_keys: list[str] = []
    for item in results:
        canonical_keys.extend(item.get("found_canonical_keys", []))
    summary = report.get("summary", {})
    return {
        "surface": surface,
        "status": _surface_status(surface, report),
        "detail": _surface_detail(surface, report),
        "domain": _domain_label(report),
        "example_file": report.get("example_file"),
        "report_path": entry.get("path"),
        "total_examples": summary.get("total_examples", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "query_types": query_types,
        "equipment_classes": equipment_classes,
        "canonical_keys": canonical_keys,
    }


def _normalize_surface_entries(entries: list[dict[str, Any]], surface: str) -> list[dict[str, Any]]:
    return [_surface_report_summary(entry, surface) for entry in entries]


def _surface_rollup(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {
            "status": "pending",
            "report_count": 0,
            "total_examples": 0,
            "passed": 0,
            "failed": 0,
        }
    return {
        "status": "passed" if all(item["status"] == "passed" for item in entries) else "failed",
        "report_count": len(entries),
        "total_examples": sum(item["total_examples"] for item in entries),
        "passed": sum(item["passed"] for item in entries),
        "failed": sum(item["failed"] for item in entries),
    }


def _surface_rollup_line(label: str, rollup: dict[str, Any]) -> str:
    if rollup["status"] == "pending":
        return f"- {label}: pending"
    return (
        f"- {label}: {rollup['status'].upper()} "
        f"({rollup['passed']}/{rollup['total_examples']} checks across {rollup['report_count']} report(s))"
    )


def _domain_inventory(surface_entries: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    domains: dict[str, dict[str, Any]] = {}
    for surface in ("semantic", "mcp", "api"):
        for item in surface_entries[surface]:
            domain = item["domain"]
            current = domains.setdefault(
                domain,
                {
                    "domain": domain,
                    "example_files": set(),
                    "equipment_classes": set(),
                    "query_types": set(),
                    "canonical_keys": [],
                    "surface_statuses": {
                        "semantic": "pending",
                        "mcp": "pending",
                        "api": "pending",
                    },
                    "surface_notes": {},
                    "surface_report_paths": {},
                    "surface_examples": {},
                },
            )
            current["example_files"].add(item["example_file"])
            current["equipment_classes"].update(item["equipment_classes"])
            current["query_types"].update(item["query_types"])
            current["canonical_keys"].extend(item["canonical_keys"])
            current["surface_statuses"][surface] = item["status"]
            current["surface_notes"][surface] = item["detail"]
            current["surface_report_paths"][surface] = item["report_path"]
            current["surface_examples"][surface] = item["total_examples"]

    inventory = []
    for item in domains.values():
        inventory.append(
            {
                "domain": item["domain"],
                "example_files": sorted(path for path in item["example_files"] if path),
                "equipment_classes": sorted(item["equipment_classes"]),
                "query_types": sorted(item["query_types"]),
                "canonical_keys": _dedupe_preserve_order(item["canonical_keys"]),
                "surface_statuses": item["surface_statuses"],
                "surface_notes": item["surface_notes"],
                "surface_report_paths": item["surface_report_paths"],
                "surface_examples": item["surface_examples"],
            }
        )
    return sorted(inventory, key=lambda item: item["domain"])


def _readiness_note(
    semantic_rollup: dict[str, Any],
    mcp_rollup: dict[str, Any],
    api_rollup: dict[str, Any],
) -> str:
    if semantic_rollup["status"] != "passed":
        return "Semantic demo checks are not yet green, so the bundle is not ready for external evaluation."
    if mcp_rollup["status"] != "passed":
        return "Semantic queries pass, but MCP smoke is not yet green; keep the handoff internal until the tool surface is stable."
    if api_rollup["status"] == "pending":
        return "Semantic queries and MCP smoke pass. Start the API service and run the live API smoke to complete the external-evaluation handoff."
    if api_rollup["status"] == "failed":
        return "Live API smoke is failing; investigate `/health` or the `/api/v2/` routes before handing this environment to evaluators."
    return "Semantic queries, MCP smoke, and live API smoke all pass for the current demo bundle."


def _artifact_lines(label: str, entries: list[dict[str, Any]]) -> list[str]:
    lines = [f"{label}:"]
    if not entries:
        lines.append("- pending")
        return lines
    for item in entries:
        path = item.get("report_path") or "generated in memory"
        lines.append(f"- `{path}`")
    return lines


def _surface_status_line(domain_item: dict[str, Any], surface: str, label: str) -> str:
    status = domain_item["surface_statuses"][surface]
    if status == "pending":
        return f"- {label}: pending"
    examples = domain_item["surface_examples"].get(surface, 0)
    path = domain_item["surface_report_paths"].get(surface)
    detail = domain_item["surface_notes"].get(surface)
    line = f"- {label}: {status.upper()} ({examples} checks)"
    if detail:
        line += f"; {detail}"
    if path:
        line += f"; report=`{path}`"
    return line


def _overall_status_lines(
    artifact_root: Path,
    domain_count: int,
    semantic_rollup: dict[str, Any],
    mcp_rollup: dict[str, Any],
    api_rollup: dict[str, Any],
) -> list[str]:
    return [
        "## Overall Status",
        "",
        f"- Artifact root: `{artifact_root}`",
        f"- Domains covered: {domain_count}",
        _surface_rollup_line("Semantic demo", semantic_rollup),
        _surface_rollup_line("MCP smoke", mcp_rollup),
        _surface_rollup_line("API smoke", api_rollup),
        "",
        "## Readiness Note",
        "",
        _readiness_note(semantic_rollup, mcp_rollup, api_rollup),
        "",
    ]


def _domain_coverage_lines(domain_inventory: list[dict[str, Any]]) -> list[str]:
    lines = ["## Domain Coverage", ""]
    for item in domain_inventory:
        canonical_keys = item["canonical_keys"] or ["none"]
        lines.extend(
            [
                f"### {_title_case(item['domain'])}",
                "",
                f"- Example sources: {', '.join(f'`{path}`' for path in item['example_files']) if item['example_files'] else 'none'}",
                _surface_status_line(item, "semantic", "Semantic demo"),
                _surface_status_line(item, "mcp", "MCP smoke"),
                _surface_status_line(item, "api", "API smoke"),
                f"- Equipment classes covered: {', '.join(item['equipment_classes']) if item['equipment_classes'] else 'none'}",
                f"- Query types covered: {', '.join(item['query_types']) if item['query_types'] else 'none'}",
                "",
                "Proven canonical knowledge objects:",
            ]
        )
        lines.extend(f"- `{canonical_key}`" for canonical_key in canonical_keys)
        lines.append("")
    return lines


def _artifact_inventory_lines(surface_entries: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [
        "## Artifact Inventory",
        "",
        *_artifact_lines("Semantic reports", surface_entries["semantic"]),
        "",
        *_artifact_lines("MCP smoke reports", surface_entries["mcp"]),
        "",
        *_artifact_lines("API smoke reports", surface_entries["api"]),
        "",
    ]


def _operator_runbook_lines(artifact_root: Path) -> list[str]:
    return [
        "## Operator Runbook",
        "",
        "Recommended one-shot path:",
        "",
        "```bash",
        f"python3 scripts/run_live_demo_evaluation.py --output-dir {artifact_root}",
        "```",
        "",
        "Manual fallback path:",
        "",
        "```bash",
        f"python3 scripts/check_demo_environment.py --output-dir {artifact_root}",
        f"python3 scripts/bootstrap_v1_demo.py --output-dir {artifact_root} --brief-output {artifact_root / 'v1_demo_brief.md'}",
        "cd apps/api",
        "python main.py",
        "```",
        "",
        "From another terminal at the repository root:",
        "",
        "```bash",
        "python3 scripts/run_api_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo",
        "python3 scripts/run_api_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo",
        "python3 scripts/build_v1_demo_brief.py --report-dir output/demo --output output/demo/v1_demo_brief.md",
        "```",
        "",
        "Use the standalone MCP smoke runner when you want to refresh the tool-surface report without rerunning the full bootstrap:",
        "",
        "```bash",
        "python3 scripts/run_mcp_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --output-dir output/demo",
        "python3 scripts/run_mcp_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --output-dir output/demo",
        "```",
    ]


def _build_brief_markdown(
    semantic_entries: list[dict[str, Any]],
    mcp_entries: list[dict[str, Any]],
    api_entries: list[dict[str, Any]],
    artifact_dir: str | Path,
) -> str:
    if not semantic_entries:
        raise ValueError("At least one semantic demo report is required")

    artifact_root = Path(artifact_dir)
    surface_entries = {
        "semantic": _normalize_surface_entries(semantic_entries, "semantic"),
        "mcp": _normalize_surface_entries(mcp_entries, "mcp"),
        "api": _normalize_surface_entries(api_entries, "api"),
    }
    domain_inventory = _domain_inventory(surface_entries)
    semantic_rollup = _surface_rollup(surface_entries["semantic"])
    mcp_rollup = _surface_rollup(surface_entries["mcp"])
    api_rollup = _surface_rollup(surface_entries["api"])
    lines = [
        "# KnowFabric V1 Demo Brief",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        *_overall_status_lines(artifact_root, len(domain_inventory), semantic_rollup, mcp_rollup, api_rollup),
        *_domain_coverage_lines(domain_inventory),
        *_artifact_inventory_lines(surface_entries),
        *_operator_runbook_lines(artifact_root),
    ]
    return "\n".join(lines) + "\n"


def build_v1_demo_brief_markdown(
    reports: list[dict[str, Any]],
    *,
    mcp_reports: list[dict[str, Any]] | None = None,
    api_reports: list[dict[str, Any]] | None = None,
    artifact_dir: str | Path = DEFAULT_REPORT_DIR,
) -> str:
    """Render a Markdown brief from semantic, MCP, and optional API reports."""

    semantic_entries = [_entry_from_report(report) for report in reports]
    mcp_entries = [_entry_from_report(report) for report in (mcp_reports or [])]
    api_entries = [_entry_from_report(report) for report in (api_reports or [])]
    return _build_brief_markdown(semantic_entries, mcp_entries, api_entries, artifact_dir)


def _resolved_report_dir(
    report_paths: list[str | Path] | None,
    report_dir: str | Path | None,
) -> Path:
    if report_dir is not None:
        return Path(report_dir)
    if report_paths:
        return Path(report_paths[0]).parent
    return Path(DEFAULT_REPORT_DIR)


def _load_entries(paths: list[Path]) -> list[dict[str, Any]]:
    return [_entry_from_report(_load_demo_report(path), path) for path in paths]


def build_v1_demo_brief(
    report_paths: list[str | Path] | None = None,
    *,
    report_dir: str | Path | None = None,
    output_path: str | Path = DEFAULT_BRIEF_PATH,
) -> Path:
    """Build the v1 demo brief from discovered or explicit report paths."""

    artifact_dir = _resolved_report_dir(report_paths, report_dir)
    semantic_paths = [Path(path) for path in report_paths] if report_paths else discover_demo_report_paths(artifact_dir)
    if not semantic_paths:
        raise ValueError("No demo report JSON files found")
    rendered = _build_brief_markdown(
        _load_entries(semantic_paths),
        _load_entries(discover_mcp_smoke_report_paths(artifact_dir)),
        _load_entries(discover_api_smoke_report_paths(artifact_dir)),
        artifact_dir,
    )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    return target


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_paths", nargs="*", help="Optional explicit semantic report JSON files")
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR, help="Directory to scan when no report paths are given")
    parser.add_argument("--output", default=DEFAULT_BRIEF_PATH, help="Markdown output path")
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
