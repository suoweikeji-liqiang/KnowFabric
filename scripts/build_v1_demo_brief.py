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
SUPPORTED_BRIEF_LANGUAGES = {"en", "zh"}


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _normalize_brief_language(language: str) -> str:
    if language not in SUPPORTED_BRIEF_LANGUAGES:
        raise ValueError(f"Unsupported brief language: {language}")
    return language


def _brief_text(language: str, key: str) -> str:
    translations = {
        "en": {
            "title": "# KnowFabric V1 Demo Brief",
            "generated_at": "Generated at",
            "overall_status": "## Overall Status",
            "artifact_root": "Artifact root",
            "domains_covered": "Domains covered",
            "semantic_demo": "Semantic demo",
            "mcp_smoke": "MCP smoke",
            "api_smoke": "API smoke",
            "readiness_note": "## Readiness Note",
            "domain_coverage": "## Domain Coverage",
            "example_sources": "Example sources",
            "equipment_classes": "Equipment classes covered",
            "query_types": "Query types covered",
            "proven_knowledge": "Proven canonical knowledge objects",
            "artifact_inventory": "## Artifact Inventory",
            "semantic_reports": "Semantic reports",
            "mcp_reports": "MCP smoke reports",
            "api_reports": "API smoke reports",
            "operator_runbook": "## Operator Runbook",
            "recommended_path": "Recommended one-shot path:",
            "manual_path": "Manual fallback path:",
            "from_repo_root": "From another terminal at the repository root:",
            "standalone_mcp": "Use the standalone MCP smoke runner when you want to refresh the tool-surface report without rerunning the full bootstrap:",
            "pending": "pending",
            "none": "none",
        },
        "zh": {
            "title": "# KnowFabric 中文评估简报",
            "generated_at": "生成时间",
            "overall_status": "## 总体状态",
            "artifact_root": "产物目录",
            "domains_covered": "覆盖领域数",
            "semantic_demo": "语义演示",
            "mcp_smoke": "MCP 冒烟验证",
            "api_smoke": "API 冒烟验证",
            "readiness_note": "## 就绪说明",
            "domain_coverage": "## 领域覆盖",
            "example_sources": "示例来源",
            "equipment_classes": "覆盖设备类型",
            "query_types": "覆盖查询类型",
            "proven_knowledge": "已验证知识对象",
            "artifact_inventory": "## 产物清单",
            "semantic_reports": "语义报告",
            "mcp_reports": "MCP 冒烟报告",
            "api_reports": "API 冒烟报告",
            "operator_runbook": "## 操作步骤",
            "recommended_path": "推荐的一键路径：",
            "manual_path": "手动回退路径：",
            "from_repo_root": "在仓库根目录的另一终端执行：",
            "standalone_mcp": "如需在不重跑完整 bootstrap 的情况下刷新 MCP 结果，可单独执行：",
            "pending": "待执行",
            "none": "无",
        },
    }
    return translations[language][key]


def _status_text(language: str, status: str) -> str:
    if language == "zh":
        return {"passed": "通过", "failed": "失败", "pending": "待执行"}.get(status, status)
    return status.upper() if status != "pending" else "pending"


def _format_domain_heading(domain: str, language: str) -> str:
    localized = {
        "en": {"hvac": "HVAC", "drive": "Drive"},
        "zh": {"hvac": "HVAC", "drive": "变频驱动"},
    }
    if domain in localized.get(language, {}):
        return localized[language][domain]
    if language == "zh":
        return domain.upper() if domain == "hvac" else domain
    return _title_case(domain)


def _knowledge_highlight_lines(highlights: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in highlights:
        title = item.get("title")
        canonical_key = item["canonical_key"]
        if title:
            lines.append(f"- `{canonical_key}`: {title}")
        else:
            lines.append(f"- `{canonical_key}`")
    return lines


def _dedupe_highlights(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        canonical_key = item.get("canonical_key")
        if not canonical_key or canonical_key in seen:
            continue
        seen.add(str(canonical_key))
        ordered.append(
            {
                "canonical_key": str(canonical_key),
                "title": item.get("title"),
                "summary": item.get("summary"),
                "display_language": item.get("display_language"),
            }
        )
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
        "found_items": [dict(item) for result in results for item in result.get("found_items", [])],
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
                    "found_items": [],
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
            current["found_items"].extend(item["found_items"])
            current["surface_statuses"][surface] = item["status"]
            current["surface_notes"][surface] = item["detail"]
            current["surface_report_paths"][surface] = item["report_path"]
            current["surface_examples"][surface] = item["total_examples"]

    inventory = []
    for item in domains.values():
        knowledge_highlights = _dedupe_highlights(item["found_items"])
        if not knowledge_highlights:
            knowledge_highlights = [
                {
                    "canonical_key": canonical_key,
                    "title": None,
                    "summary": None,
                    "display_language": None,
                }
                for canonical_key in _dedupe_preserve_order(item["canonical_keys"])
            ]
        inventory.append(
            {
                "domain": item["domain"],
                "example_files": sorted(path for path in item["example_files"] if path),
                "equipment_classes": sorted(item["equipment_classes"]),
                "query_types": sorted(item["query_types"]),
                "canonical_keys": _dedupe_preserve_order(item["canonical_keys"]),
                "knowledge_highlights": knowledge_highlights,
                "surface_statuses": item["surface_statuses"],
                "surface_notes": item["surface_notes"],
                "surface_report_paths": item["surface_report_paths"],
                "surface_examples": item["surface_examples"],
            }
        )
    return sorted(inventory, key=lambda item: item["domain"])


def _readiness_note(
    language: str,
    semantic_rollup: dict[str, Any],
    mcp_rollup: dict[str, Any],
    api_rollup: dict[str, Any],
) -> str:
    if language == "zh":
        if semantic_rollup["status"] != "passed":
            return "语义演示检查尚未全部通过，因此该交付包还不适合对外评估。"
        if mcp_rollup["status"] != "passed":
            return "语义查询已通过，但 MCP 冒烟验证仍未全绿；建议在工具面稳定前继续内部使用。"
        if api_rollup["status"] == "pending":
            return "语义查询和 MCP 冒烟验证均已通过。启动 API 服务并完成 live API smoke 后，即可形成完整的对外交付包。"
        if api_rollup["status"] == "failed":
            return "Live API smoke 未通过；对外交付前请先检查 `/health` 和 `/api/v2/` 路由。"
        return "语义查询、MCP 冒烟验证和 live API smoke 均已通过，当前交付包可用于外部评估。"
    if semantic_rollup["status"] != "passed":
        return "Semantic demo checks are not yet green, so the bundle is not ready for external evaluation."
    if mcp_rollup["status"] != "passed":
        return "Semantic queries pass, but MCP smoke is not yet green; keep the handoff internal until the tool surface is stable."
    if api_rollup["status"] == "pending":
        return "Semantic queries and MCP smoke pass. Start the API service and run the live API smoke to complete the external-evaluation handoff."
    if api_rollup["status"] == "failed":
        return "Live API smoke is failing; investigate `/health` or the `/api/v2/` routes before handing this environment to evaluators."
    return "Semantic queries, MCP smoke, and live API smoke all pass for the current demo bundle."


def _artifact_lines(label: str, entries: list[dict[str, Any]], *, language: str) -> list[str]:
    lines = [f"{label}:"]
    if not entries:
        lines.append(f"- {_brief_text(language, 'pending')}")
        return lines
    for item in entries:
        path = item.get("report_path") or "generated in memory"
        lines.append(f"- `{path}`")
    return lines


def _surface_status_line(domain_item: dict[str, Any], surface: str, label: str, *, language: str) -> str:
    status = domain_item["surface_statuses"][surface]
    if status == "pending":
        return f"- {label}: {_brief_text(language, 'pending')}"
    examples = domain_item["surface_examples"].get(surface, 0)
    path = domain_item["surface_report_paths"].get(surface)
    detail = domain_item["surface_notes"].get(surface)
    checks_label = "checks" if language == "en" else "项检查"
    line = f"- {label}: {_status_text(language, status)} ({examples} {checks_label})"
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
    *,
    language: str,
) -> list[str]:
    total_checks_text = "checks across" if language == "en" else "项检查，覆盖"
    report_text = "report(s)" if language == "en" else "份报告"
    return [
        _brief_text(language, "overall_status"),
        "",
        f"- {_brief_text(language, 'artifact_root')}: `{artifact_root}`",
        f"- {_brief_text(language, 'domains_covered')}: {domain_count}",
        f"- {_brief_text(language, 'semantic_demo')}: {_status_text(language, semantic_rollup['status']) if semantic_rollup['status'] != 'pending' else _brief_text(language, 'pending')} ({semantic_rollup['passed']}/{semantic_rollup['total_examples']} {total_checks_text} {semantic_rollup['report_count']} {report_text})" if semantic_rollup["status"] != "pending" else f"- {_brief_text(language, 'semantic_demo')}: {_brief_text(language, 'pending')}",
        f"- {_brief_text(language, 'mcp_smoke')}: {_status_text(language, mcp_rollup['status']) if mcp_rollup['status'] != 'pending' else _brief_text(language, 'pending')} ({mcp_rollup['passed']}/{mcp_rollup['total_examples']} {total_checks_text} {mcp_rollup['report_count']} {report_text})" if mcp_rollup["status"] != "pending" else f"- {_brief_text(language, 'mcp_smoke')}: {_brief_text(language, 'pending')}",
        f"- {_brief_text(language, 'api_smoke')}: {_status_text(language, api_rollup['status']) if api_rollup['status'] != 'pending' else _brief_text(language, 'pending')} ({api_rollup['passed']}/{api_rollup['total_examples']} {total_checks_text} {api_rollup['report_count']} {report_text})" if api_rollup["status"] != "pending" else f"- {_brief_text(language, 'api_smoke')}: {_brief_text(language, 'pending')}",
        "",
        _brief_text(language, "readiness_note"),
        "",
        _readiness_note(language, semantic_rollup, mcp_rollup, api_rollup),
        "",
    ]


def _domain_coverage_lines(domain_inventory: list[dict[str, Any]], *, language: str) -> list[str]:
    lines = [_brief_text(language, "domain_coverage"), ""]
    for item in domain_inventory:
        highlights = item["knowledge_highlights"] or [{"canonical_key": _brief_text(language, "none")}]
        lines.extend(
            [
                f"### {_format_domain_heading(item['domain'], language)}",
                "",
                f"- {_brief_text(language, 'example_sources')}: {', '.join(f'`{path}`' for path in item['example_files']) if item['example_files'] else _brief_text(language, 'none')}",
                _surface_status_line(item, "semantic", _brief_text(language, "semantic_demo"), language=language),
                _surface_status_line(item, "mcp", _brief_text(language, "mcp_smoke"), language=language),
                _surface_status_line(item, "api", _brief_text(language, "api_smoke"), language=language),
                f"- {_brief_text(language, 'equipment_classes')}: {', '.join(item['equipment_classes']) if item['equipment_classes'] else _brief_text(language, 'none')}",
                f"- {_brief_text(language, 'query_types')}: {', '.join(item['query_types']) if item['query_types'] else _brief_text(language, 'none')}",
                "",
                f"{_brief_text(language, 'proven_knowledge')}:",
            ]
        )
        lines.extend(_knowledge_highlight_lines(highlights))
        lines.append("")
    return lines


def _artifact_inventory_lines(surface_entries: dict[str, list[dict[str, Any]]], *, language: str) -> list[str]:
    return [
        _brief_text(language, "artifact_inventory"),
        "",
        *_artifact_lines(_brief_text(language, "semantic_reports"), surface_entries["semantic"], language=language),
        "",
        *_artifact_lines(_brief_text(language, "mcp_reports"), surface_entries["mcp"], language=language),
        "",
        *_artifact_lines(_brief_text(language, "api_reports"), surface_entries["api"], language=language),
        "",
    ]


def _operator_runbook_lines(artifact_root: Path, *, language: str) -> list[str]:
    brief_language_flag = " --language zh" if language == "zh" else ""
    return [
        _brief_text(language, "operator_runbook"),
        "",
        _brief_text(language, "recommended_path"),
        "",
        "```bash",
        f"python3 scripts/run_live_demo_evaluation.py --output-dir {artifact_root}",
        "```",
        "",
        _brief_text(language, "manual_path"),
        "",
        "```bash",
        f"python3 scripts/check_demo_environment.py --output-dir {artifact_root}",
        f"python3 scripts/bootstrap_v1_demo.py --output-dir {artifact_root} --brief-output {artifact_root / 'v1_demo_brief.md'}",
        "cd apps/api",
        "python main.py",
        "```",
        "",
        _brief_text(language, "from_repo_root"),
        "",
        "```bash",
        "python3 scripts/run_api_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo",
        "python3 scripts/run_api_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo",
        f"python3 scripts/build_v1_demo_brief.py --report-dir output/demo --output output/demo/v1_demo_brief.md{brief_language_flag}",
        "```",
        "",
        _brief_text(language, "standalone_mcp"),
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
    language: str,
) -> str:
    if not semantic_entries:
        raise ValueError("At least one semantic demo report is required")

    resolved_language = _normalize_brief_language(language)
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
        _brief_text(resolved_language, "title"),
        "",
        f"{_brief_text(resolved_language, 'generated_at')}: {datetime.now(timezone.utc).isoformat()}",
        "",
        *_overall_status_lines(
            artifact_root,
            len(domain_inventory),
            semantic_rollup,
            mcp_rollup,
            api_rollup,
            language=resolved_language,
        ),
        *_domain_coverage_lines(domain_inventory, language=resolved_language),
        *_artifact_inventory_lines(surface_entries, language=resolved_language),
        *_operator_runbook_lines(artifact_root, language=resolved_language),
    ]
    return "\n".join(lines) + "\n"


def build_v1_demo_brief_markdown(
    reports: list[dict[str, Any]],
    *,
    mcp_reports: list[dict[str, Any]] | None = None,
    api_reports: list[dict[str, Any]] | None = None,
    artifact_dir: str | Path = DEFAULT_REPORT_DIR,
    language: str = "en",
) -> str:
    """Render a Markdown brief from semantic, MCP, and optional API reports."""

    semantic_entries = [_entry_from_report(report) for report in reports]
    mcp_entries = [_entry_from_report(report) for report in (mcp_reports or [])]
    api_entries = [_entry_from_report(report) for report in (api_reports or [])]
    return _build_brief_markdown(semantic_entries, mcp_entries, api_entries, artifact_dir, language)


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
    language: str = "en",
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
        language,
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
    parser.add_argument("--language", default="en", choices=sorted(SUPPORTED_BRIEF_LANGUAGES), help="Brief output language")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    target = build_v1_demo_brief(
        args.report_paths,
        report_dir=args.report_dir,
        output_path=args.output,
        language=args.language,
    )
    print(f"Wrote v1 demo brief to {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"V1 demo brief build failed: {exc}")
        raise SystemExit(1)
