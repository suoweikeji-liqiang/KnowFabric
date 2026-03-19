#!/usr/bin/env python3
"""Run service-level API smoke queries from a semantic example query file."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_semantic_demo_queries import default_demo_report_path, load_semantic_demo_queries

API_ROUTE_TEMPLATES = {
    "fault_knowledge": "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/fault-knowledge",
    "parameter_profile": "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/parameter-profiles",
    "maintenance_guidance": "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/maintenance-guidance",
    "application_guidance": "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/application-guidance",
    "operational_guidance": "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/operational-guidance",
    "equipment_class_explanation": "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}",
}


def default_api_smoke_report_path(example_path: str | Path, output_dir: str | Path = "output/demo") -> Path:
    """Build a stable JSON report path for one API smoke run."""

    semantic_path = default_demo_report_path(example_path, output_dir)
    return semantic_path.with_name(semantic_path.name.replace("__semantic_demo_report.json", "__api_smoke_report.json"))


def _http_fetcher(base_url: str) -> Callable[[str, dict[str, Any] | None], tuple[int, dict[str, Any]]]:
    normalized = base_url.rstrip("/")

    def fetch(path: str, params: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        query = {}
        for key, value in (params or {}).items():
            if value is None:
                continue
            if isinstance(value, bool):
                query[key] = "true" if value else "false"
            else:
                query[key] = str(value)
        url = f"{normalized}{path}"
        if query:
            url = f"{url}?{urlencode(query, doseq=True)}"
        try:
            with urlopen(url) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return response.getcode(), payload
        except HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            return exc.code, payload
        except URLError as exc:
            return 0, {"detail": str(exc)}

    return fetch


def _build_route(query_type: str, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    template = API_ROUTE_TEMPLATES.get(query_type)
    if template is None:
        raise ValueError(f"Unsupported query_type for API smoke: {query_type}")
    domain_id = request.get("domain_id")
    equipment_class_id = request.get("equipment_class_id")
    if not isinstance(domain_id, str) or not isinstance(equipment_class_id, str):
        raise ValueError("API smoke requests must include domain_id and equipment_class_id")
    path = template.format(domain_id=domain_id, equipment_class_id=equipment_class_id)
    query_params = {
        key: value
        for key, value in request.items()
        if key not in {"domain_id", "equipment_class_id"}
    }
    return path, query_params


def _response_items(query_type: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if query_type == "equipment_class_explanation":
        data = payload.get("data", {})
        return [data] if data else []
    return payload.get("data", {}).get("items", [])


def _response_canonical_keys(query_type: str, payload: dict[str, Any]) -> list[str]:
    if query_type == "equipment_class_explanation":
        equipment = payload.get("data", {}).get("equipment_class", {})
        equipment_class_id = equipment.get("equipment_class_id")
        return [equipment_class_id] if equipment_class_id else []
    return [
        str(item.get("canonical_key"))
        for item in _response_items(query_type, payload)
        if item.get("canonical_key")
    ]


def _response_review_statuses(query_type: str, payload: dict[str, Any]) -> dict[str, str]:
    if query_type == "equipment_class_explanation":
        return {}
    return {
        str(item.get("canonical_key")): str(item.get("review_status"))
        for item in _response_items(query_type, payload)
        if item.get("canonical_key") and item.get("review_status")
    }


def run_api_demo_smoke(
    example_path: str | Path,
    *,
    base_url: str = "http://localhost:8000",
    fetcher: Callable[[str, dict[str, Any] | None], tuple[int, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Execute API smoke queries from one example file against a running service."""

    examples = load_semantic_demo_queries(example_path)
    active_fetcher = fetcher or _http_fetcher(base_url)
    health_status, health_payload = active_fetcher("/health", None)

    results = []
    for example in examples:
        path, query_params = _build_route(example["query_type"], dict(example["request"]))
        status_code, payload = active_fetcher(path, query_params)
        canonical_keys = _response_canonical_keys(example["query_type"], payload)
        review_statuses = _response_review_statuses(example["query_type"], payload)
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
        success_flag = bool(payload.get("success")) if isinstance(payload, dict) else False
        status = "passed" if status_code == 200 and success_flag and not missing_keys and not wrong_review_status else "failed"
        results.append(
            {
                "id": example["id"],
                "description": example["description"],
                "query": example["query"],
                "query_type": example["query_type"],
                "expected_contract": example["expected_contract"],
                "request": example["request"],
                "route_path": path,
                "query_params": query_params,
                "http_status": status_code,
                "status": status,
                "response_query_type": payload.get("metadata", {}).get("query_type") if isinstance(payload, dict) else None,
                "item_count": len(_response_items(example["query_type"], payload)) if isinstance(payload, dict) else 0,
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
        "smoke_mode": "semantic_api_demo_smoke",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "example_file": str(Path(example_path)),
        "health": {
            "http_status": health_status,
            "status": "passed" if health_status == 200 else "failed",
            "payload": health_payload,
        },
        "summary": {
            "total_examples": len(results),
            "passed": passed,
            "failed": failed,
        },
        "results": results,
    }


def build_api_demo_smoke_summary_text(report: dict[str, Any]) -> str:
    """Render a terminal-friendly summary of API smoke results."""

    lines = [
        "API Demo Smoke Summary",
        f"Base URL: {report['base_url']}",
        f"Health: {report['health']['status'].upper()} ({report['health']['http_status']})",
        (
            f"Examples: {report['summary']['total_examples']} total, "
            f"{report['summary']['passed']} passed, {report['summary']['failed']} failed"
        ),
    ]
    for item in report["results"]:
        line = f"- {item['status'].upper()} {item['id']}: http={item['http_status']} items={item['item_count']}"
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
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for the running API service")
    parser.add_argument("--output", help="Optional JSON output path for the smoke report")
    parser.add_argument("--output-dir", help="Optional directory where a stable JSON report should be written")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = run_api_demo_smoke(
        args.example_path,
        base_url=args.base_url,
    )
    output_path = Path(args.output) if args.output else None
    if output_path is None and args.output_dir:
        output_path = default_api_smoke_report_path(args.example_path, args.output_dir)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(build_api_demo_smoke_summary_text(report))
    return 0 if report["health"]["status"] == "passed" and report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"API demo smoke failed: {exc}")
        raise SystemExit(1)
