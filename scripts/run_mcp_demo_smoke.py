#!/usr/bin/env python3
"""Run MCP-level smoke queries from a semantic example query file."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.mcp.main import KnowFabricMcpServer
from scripts.run_semantic_demo_queries import default_demo_report_path, load_semantic_demo_queries

TOOL_NAME_BY_QUERY_TYPE = {
    "fault_knowledge": "get_fault_knowledge",
    "parameter_profile": "get_parameter_profile",
    "maintenance_guidance": "get_maintenance_guidance",
    "application_guidance": "get_application_guidance",
    "operational_guidance": "get_operational_guidance",
    "equipment_class_explanation": "explain_equipment_class",
}


def default_mcp_smoke_report_path(example_path: str | Path, output_dir: str | Path = "output/demo") -> Path:
    """Build a stable JSON report path for one MCP smoke run."""

    semantic_path = default_demo_report_path(example_path, output_dir)
    return semantic_path.with_name(semantic_path.name.replace("__semantic_demo_report.json", "__mcp_smoke_report.json"))


def _server_fetcher(server: KnowFabricMcpServer) -> Callable[[str, dict[str, Any] | None], dict[str, Any]]:
    def fetch(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            request["params"] = params
        return server.handle_request(request)

    return fetch


def _parse_tool_payload(response: dict[str, Any]) -> dict[str, Any]:
    error = response.get("error")
    if error:
        return {"success": False, "error": error}
    text_payload = response.get("result", {}).get("content", [{}])[0].get("text", "{}")
    return json.loads(text_payload)


def _mcp_items(query_type: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if query_type == "equipment_class_explanation":
        data = payload.get("equipment_class")
        return [data] if isinstance(data, dict) else []
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


def _mcp_canonical_keys(query_type: str, payload: dict[str, Any]) -> list[str]:
    if query_type == "equipment_class_explanation":
        equipment_class_id = payload.get("equipment_class", {}).get("equipment_class_id")
        return [equipment_class_id] if equipment_class_id else []
    return [str(item.get("canonical_key")) for item in _mcp_items(query_type, payload) if item.get("canonical_key")]


def _mcp_review_statuses(query_type: str, payload: dict[str, Any]) -> dict[str, str]:
    if query_type == "equipment_class_explanation":
        return {}
    return {
        str(item.get("canonical_key")): str(item.get("review_status"))
        for item in _mcp_items(query_type, payload)
        if item.get("canonical_key") and item.get("review_status")
    }


def run_mcp_demo_smoke(
    example_path: str | Path,
    *,
    fetcher: Callable[[str, dict[str, Any] | None], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute MCP smoke queries from one example file against the MCP tool surface."""

    examples = load_semantic_demo_queries(example_path)
    server = KnowFabricMcpServer()
    active_fetcher = fetcher or _server_fetcher(server)

    initialize = active_fetcher("initialize", {})
    tools_list = active_fetcher("tools/list", {})
    tool_names = {
        tool["name"]
        for tool in tools_list.get("result", {}).get("tools", [])
        if isinstance(tool, dict) and tool.get("name")
    }

    results = []
    for example in examples:
        tool_name = TOOL_NAME_BY_QUERY_TYPE[example["query_type"]]
        response = active_fetcher(
            "tools/call",
            {
                "name": tool_name,
                "arguments": dict(example["request"]),
            },
        )
        payload = _parse_tool_payload(response)
        canonical_keys = _mcp_canonical_keys(example["query_type"], payload)
        review_statuses = _mcp_review_statuses(example["query_type"], payload)
        expected_keys = example["expected_canonical_keys"]
        missing_keys = [key for key in expected_keys if key not in canonical_keys]
        required_review_status = example.get("required_review_status")
        wrong_review_status = []
        if required_review_status:
            wrong_review_status = [
                key
                for key in expected_keys
                if key in review_statuses and review_statuses[key] != required_review_status
            ]
        has_tool = tool_name in tool_names
        success_flag = isinstance(payload, dict) and (payload.get("success") is True or "success" not in payload)
        item_count = 0 if not isinstance(payload, dict) else len(_mcp_items(example["query_type"], payload))
        status = "passed" if has_tool and success_flag and not missing_keys and not wrong_review_status else "failed"
        results.append(
            {
                "id": example["id"],
                "description": example["description"],
                "query": example["query"],
                "query_type": example["query_type"],
                "tool_name": tool_name,
                "tool_listed": has_tool,
                "status": status,
                "item_count": item_count,
                "found_canonical_keys": canonical_keys,
                "found_review_statuses": review_statuses,
                "expected_canonical_keys": expected_keys,
                "missing_canonical_keys": missing_keys,
                "required_review_status": required_review_status,
                "wrong_review_status_canonical_keys": wrong_review_status,
            }
        )

    passed = sum(1 for item in results if item["status"] == "passed")
    failed = len(results) - passed
    return {
        "smoke_mode": "semantic_mcp_demo_smoke",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "example_file": str(Path(example_path)),
        "initialize_ok": "result" in initialize and "error" not in initialize,
        "tools_list_ok": "result" in tools_list and "error" not in tools_list,
        "tools_listed": sorted(tool_names),
        "summary": {
            "total_examples": len(results),
            "passed": passed,
            "failed": failed,
        },
        "results": results,
    }


def build_mcp_demo_smoke_summary_text(report: dict[str, Any]) -> str:
    """Render a terminal-friendly summary of MCP smoke results."""

    lines = [
        "MCP Demo Smoke Summary",
        f"Initialize: {'PASSED' if report['initialize_ok'] else 'FAILED'}",
        f"Tools List: {'PASSED' if report['tools_list_ok'] else 'FAILED'}",
        (
            f"Examples: {report['summary']['total_examples']} total, "
            f"{report['summary']['passed']} passed, {report['summary']['failed']} failed"
        ),
    ]
    for item in report["results"]:
        line = f"- {item['status'].upper()} {item['id']}: tool={item['tool_name']} listed={item['tool_listed']}"
        if item["missing_canonical_keys"]:
            line += f"; missing={', '.join(item['missing_canonical_keys'])}"
        elif item["wrong_review_status_canonical_keys"]:
            expected = item["required_review_status"]
            line += f"; review_status!={expected} for {', '.join(item['wrong_review_status_canonical_keys'])}"
        elif item["found_canonical_keys"]:
            line += f"; found={', '.join(item['found_canonical_keys'])}"
        lines.append(line)
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_path", help="Path to example_queries.yaml")
    parser.add_argument("--output", help="Optional JSON output path for the smoke report")
    parser.add_argument("--output-dir", help="Optional directory where a stable JSON report should be written")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = run_mcp_demo_smoke(args.example_path)
    output_path = Path(args.output) if args.output else None
    if output_path is None and args.output_dir:
        output_path = default_mcp_smoke_report_path(args.example_path, args.output_dir)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(build_mcp_demo_smoke_summary_text(report))
    return 0 if report["initialize_ok"] and report["tools_list_ok"] and report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"MCP demo smoke failed: {exc}")
        raise SystemExit(1)
