#!/usr/bin/env python3
"""Run fixed semantic demo queries from a YAML file and validate results."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.session import SessionLocal
from packages.retrieval.semantic_service import SemanticRetrievalService

QUERY_METHODS = {
    "fault_knowledge": "get_fault_knowledge",
    "parameter_profile": "get_parameter_profiles",
    "maintenance_guidance": "get_maintenance_guidance",
    "application_guidance": "get_application_guidance",
    "operational_guidance": "get_operational_guidance",
    "equipment_class_explanation": "explain_equipment_class",
}


def default_demo_report_path(example_path: str | Path, output_dir: str | Path = "output/demo") -> Path:
    """Build a stable JSON report path for one example query file."""

    example_file = Path(example_path)
    scope_hint = None
    if len(example_file.parents) >= 3:
        scope_hint = example_file.parents[2].name
    file_name = f"{example_file.stem}__semantic_demo_report.json"
    if scope_hint:
        file_name = f"{scope_hint}__{file_name}"
    return Path(output_dir) / file_name


def _load_example_payload(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("example query file must contain a YAML object")
    examples = payload.get("examples")
    if not isinstance(examples, list):
        raise ValueError("example query file must include an examples list")
    return payload


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _require_text_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field_name} must be a list of non-empty strings")
    return [item.strip() for item in value]


def _normalize_example(raw: dict[str, Any]) -> dict[str, Any]:
    query_type = _require_text(raw.get("query_type"), "examples[].query_type")
    if query_type not in QUERY_METHODS:
        raise ValueError(f"Unsupported query_type: {query_type}")
    required_review_status = raw.get("required_review_status")
    if required_review_status is not None:
        required_review_status = _require_text(required_review_status, "examples[].required_review_status")
    return {
        "id": _require_text(raw.get("id"), "examples[].id"),
        "description": _require_text(raw.get("description"), "examples[].description"),
        "query": _require_text(raw.get("query"), "examples[].query"),
        "query_type": query_type,
        "expected_contract": _require_text(raw.get("expected_contract"), "examples[].expected_contract"),
        "request": _require_dict(raw.get("request"), "examples[].request"),
        "expected_canonical_keys": _require_text_list(raw.get("expected_canonical_keys"), "examples[].expected_canonical_keys"),
        "required_review_status": required_review_status,
    }


def load_semantic_demo_queries(path: str | Path) -> list[dict[str, Any]]:
    """Load and validate semantic demo queries from YAML."""

    payload = _load_example_payload(path)
    return [_normalize_example(item) for item in payload["examples"]]


def _dispatch_query(
    service: SemanticRetrievalService,
    db,
    query_type: str,
    request: dict[str, Any],
) -> dict[str, Any] | None:
    method_name = QUERY_METHODS[query_type]
    method = getattr(service, method_name)
    return method(db=db, **request)


def _result_canonical_keys(query_type: str, payload: dict[str, Any] | None) -> list[str]:
    if payload is None:
        return []
    if query_type == "equipment_class_explanation":
        equipment = payload.get("equipment_class", {})
        equipment_class_id = equipment.get("equipment_class_id")
        return [equipment_class_id] if equipment_class_id else []
    items = payload.get("items", [])
    return [str(item.get("canonical_key")) for item in items if item.get("canonical_key")]


def _result_found_items(query_type: str, payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if payload is None or query_type == "equipment_class_explanation":
        return []
    items = payload.get("items", [])
    return [
        {
            "canonical_key": str(item.get("canonical_key")),
            "title": item.get("title"),
            "summary": item.get("summary"),
            "display_language": item.get("display_language"),
        }
        for item in items
        if item.get("canonical_key")
    ]


def _result_review_statuses(query_type: str, payload: dict[str, Any] | None) -> dict[str, str]:
    if payload is None or query_type == "equipment_class_explanation":
        return {}
    items = payload.get("items", [])
    return {
        str(item.get("canonical_key")): str(item.get("review_status"))
        for item in items
        if item.get("canonical_key") and item.get("review_status")
    }


def run_semantic_demo_queries(example_path: str | Path) -> dict[str, Any]:
    """Execute semantic demo queries and report whether expected keys are present."""

    examples = load_semantic_demo_queries(example_path)
    service = SemanticRetrievalService()
    session = SessionLocal()
    try:
        results = []
        for example in examples:
            payload = _dispatch_query(service, session, example["query_type"], dict(example["request"]))
            found_keys = _result_canonical_keys(example["query_type"], payload)
            found_items = _result_found_items(example["query_type"], payload)
            found_review_statuses = _result_review_statuses(example["query_type"], payload)
            expected_keys = example["expected_canonical_keys"]
            missing_keys = [key for key in expected_keys if key not in found_keys]
            wrong_review_status = []
            required_review_status = example.get("required_review_status")
            if required_review_status:
                wrong_review_status = [
                    key
                    for key in expected_keys
                    if key in found_review_statuses and found_review_statuses[key] != required_review_status
                ]
            item_count = 0 if payload is None else len(payload.get("items", []))
            status = "passed" if payload is not None and not missing_keys and not wrong_review_status else "failed"
            results.append(
                {
                    "id": example["id"],
                    "description": example["description"],
                    "query": example["query"],
                    "query_type": example["query_type"],
                    "expected_contract": example["expected_contract"],
                    "request": example["request"],
                    "status": status,
                    "item_count": item_count,
                    "found_canonical_keys": found_keys,
                    "found_items": found_items,
                    "found_review_statuses": found_review_statuses,
                    "expected_canonical_keys": expected_keys,
                    "missing_canonical_keys": missing_keys,
                    "required_review_status": required_review_status,
                    "wrong_review_status_canonical_keys": wrong_review_status,
                }
            )

        passed = sum(1 for item in results if item["status"] == "passed")
        failed = len(results) - passed
        return {
            "demo_mode": "semantic_example_query_runner",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "example_file": str(Path(example_path)),
            "summary": {
                "total_examples": len(results),
                "passed": passed,
                "failed": failed,
            },
            "results": results,
        }
    finally:
        session.close()


def build_semantic_demo_summary_text(report: dict[str, Any]) -> str:
    """Render a terminal-friendly summary of semantic demo query results."""

    lines = [
        "Semantic Demo Query Summary",
        (
            f"Examples: {report['summary']['total_examples']} total, "
            f"{report['summary']['passed']} passed, {report['summary']['failed']} failed"
        ),
    ]
    for item in report["results"]:
        line = f"- {item['status'].upper()} {item['id']}: {item['item_count']} item(s)"
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
    parser.add_argument("--output", help="Optional JSON output path for the report")
    parser.add_argument(
        "--output-dir",
        help="Optional directory where a stable JSON report name should be written",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = run_semantic_demo_queries(args.example_path)
    output_path = Path(args.output) if args.output else None
    if output_path is None and args.output_dir:
        output_path = default_demo_report_path(args.example_path, args.output_dir)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(build_semantic_demo_summary_text(report))
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Semantic demo query runner failed: {exc}")
        raise SystemExit(1)
