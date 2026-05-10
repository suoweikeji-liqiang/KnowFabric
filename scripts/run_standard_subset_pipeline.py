#!/usr/bin/env python3
"""Run the standard section-first subset extraction pipeline with model policy routing."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


ROOT = Path(__file__).resolve().parent.parent


def load_standard_tasks(paths: list[Path]) -> list[dict[str, Any]]:
    tasks = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for task in payload.get("tasks", []):
            if task.get("status") not in {"chunked", "chunked_via_retry"}:
                continue
            if task.get("doc_id"):
                tasks.append(task)
    return tasks


def model_policy(task: dict[str, Any]) -> dict[str, Any]:
    name = str(task.get("file_name") or "")
    pages = int(task.get("processing", {}).get("pages_after") or task.get("page_count") or 0)
    if "211" in name:
        return {
            "backend": "deepseek-v4-pro",
            "knowledge_types": "application_guidance,parameter_spec,operational_sequence",
            "target_candidates": 15,
            "max_pages": 18,
            "max_sections": 3,
            "min_confidence": "high",
        }
    if pages >= 450:
        return {
            "backend": "mimo-v2-omni",
            "knowledge_types": "application_guidance,parameter_spec,operational_sequence",
            "target_candidates": 15,
            "max_pages": 18,
            "max_sections": 3,
            "min_confidence": "high",
        }
    return {
        "backend": "deepseek-parameter-spec",
        "knowledge_types": "application_guidance,parameter_spec,operational_sequence",
        "target_candidates": 15,
        "max_pages": 16,
        "max_sections": 3,
        "min_confidence": "high",
    }


def suggested_standard_equipment_anchor(task: dict[str, Any]) -> tuple[str, str]:
    name = str(task.get("file_name") or "")
    pages = int(task.get("processing", {}).get("pages_after") or task.get("page_count") or 0)
    if "211" in name:
        return "chiller", "small_standard_guidance_default"
    if "设计" in name or "design" in name:
        return "chiller", "design_manual_general_hvac_default"
    if "绿色建筑指南" in name:
        return "chiller", "green_guidance_general_hvac_default"
    if pages >= 450:
        return "chiller", "large_handbook_general_hvac_default"
    return "chiller", "fallback_general_hvac_standard"


def matrix_path(doc_id: str, matrix_root: Path | None = None) -> Path:
    root = matrix_root or (ROOT / "output" / "hvac_standard_reference_review" / "section_matrices")
    return root / doc_id / "section_target_matrix.json"


def route_matrix_if_enabled(task: dict[str, Any], matrix_json: Path, task_dir: Path, route_backend: str, backend_config: str | None) -> Path:
    if not route_backend:
        return matrix_json
    routing_dir = task_dir / "routing"
    cmd = [
        sys.executable,
        "scripts/route_standard_sections_with_llm.py",
        "--matrix-json",
        str(matrix_json),
        "--output-dir",
        str(routing_dir),
        "--backend-name",
        route_backend,
    ]
    if backend_config:
        cmd.extend(["--backend-config", backend_config])
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    return routing_dir / "section_target_matrix_routed.json"


def load_routing_payload(matrix_json: Path) -> dict[str, Any]:
    payload = json.loads(matrix_json.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def route_aware_policy(base_policy: dict[str, Any], routing_payload: dict[str, Any]) -> dict[str, Any]:
    policy = dict(base_policy)
    doc_route = routing_payload.get("llm_routing", {}).get("document_route", {})
    lane = str(doc_route.get("document_lane") or "")
    family = str(doc_route.get("document_family") or "")
    should_run_equipment = bool(doc_route.get("should_run_equipment_pipeline", True))

    if lane == "audit_methodology" or family == "methodology_guide":
        policy["backend"] = "deepseek-v4-pro"
        policy["knowledge_types"] = "application_guidance,parameter_spec,operational_sequence"
        policy["target_candidates"] = max(int(policy.get("target_candidates", 15)), 15)
        policy["min_confidence"] = "medium"
        policy["max_sections"] = max(int(policy.get("max_sections", 3)), 5)
        policy["max_pages"] = max(int(policy.get("max_pages", 18)), 12)
    elif lane == "sustainability_topic" or family == "cross_domain_sustainability_guide":
        policy["backend"] = "mimo-v2-omni"
        policy["min_confidence"] = "high"
        policy["max_sections"] = max(int(policy.get("max_sections", 3)), 4)
        policy["max_pages"] = max(int(policy.get("max_pages", 18)), 12)
    elif lane == "system_design":
        policy["max_sections"] = max(int(policy.get("max_sections", 3)), 4)
        policy["max_pages"] = max(int(policy.get("max_pages", 18)), 12)

    if not should_run_equipment:
        policy["knowledge_types"] = "application_guidance,parameter_spec,operational_sequence"
    return policy


def route_aware_anchor(task: dict[str, Any], routing_payload: dict[str, Any]) -> tuple[str, str]:
    fallback_anchor, fallback_reason = suggested_standard_equipment_anchor(task)
    doc_route = routing_payload.get("llm_routing", {}).get("document_route", {})
    route_anchor = str(doc_route.get("default_equipment_anchor") or "").strip()
    lane = str(doc_route.get("document_lane") or "")
    family = str(doc_route.get("document_family") or "")
    if route_anchor and route_anchor not in {"mixed", "none"}:
        return route_anchor, f"llm_document_route:{lane or family}"
    if lane == "audit_methodology" or family == "methodology_guide":
        return "general_hvac", "llm_methodology_route_default"
    if lane in {"system_design", "sustainability_topic"}:
        return "general_hvac", f"llm_document_route:{lane}"
    return fallback_anchor, fallback_reason


def run_subset_selection(
    task: dict[str, Any],
    policy: dict[str, Any],
    output_dir: Path,
    matrix_json: Path,
    equipment_scope_id: str,
) -> Path:
    cmd = [
        sys.executable,
        "scripts/prepare_standard_subset_from_matrix.py",
        "--matrix-json",
        str(matrix_json),
        "--source-pdf",
        str(task["path"]),
        "--output-dir",
        str(output_dir),
        "--knowledge-types",
        str(policy["knowledge_types"]),
        "--min-confidence",
        str(policy.get("min_confidence", "high")),
        "--max-sections",
        str(policy["max_sections"]),
        "--max-pages",
        str(policy["max_pages"]),
        "--subset-name",
        f"auto_{task['doc_id']}",
        "--equipment-scope-id",
        equipment_scope_id,
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    return output_dir / "manifest.csv"


def run_subset_extraction(manifest_path: Path, policy: dict[str, Any], output_dir: Path) -> None:
    cmd = [
        sys.executable,
        "scripts/run_hvac_doclevel_extraction_batch.py",
        "--manifest",
        str(manifest_path),
        "--groups",
        "A_standard_authority_first",
        "--output-dir",
        str(output_dir),
        "--limit",
        "1",
        "--execute",
        "--backends",
        str(policy["backend"]),
        "--judge-backend",
        "deepseek-v4-pro-judge",
        "--knowledge-types",
        "application_guidance,operational_sequence,parameter_spec,performance_spec,maintenance_procedure",
        "--target-candidates",
        str(policy["target_candidates"]),
        "--backend-timeout-seconds",
        "600",
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def build_summary(results: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    return {
        "pipeline_mode": "standard_section_first_extraction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "results": results,
    }


def write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--standard-batch-summary",
        action="append",
        dest="standard_batch_summaries",
        help="Path to standard source batch summary JSON. May be repeated.",
    )
    parser.add_argument("--doc-id", action="append", help="Optional doc_id filter. May be repeated.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--matrix-root", help="Optional root directory containing <doc_id>/section_target_matrix.json")
    parser.add_argument("--route-backend", default="deepseek-parameter-spec", help="Optional backend name for LLM section routing; empty disables routing")
    parser.add_argument("--backend-config", help="Optional backend config path for LLM section routing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary_paths = [
        Path(path)
        for path in (
            args.standard_batch_summaries
            or [
                str(ROOT / "output" / "hvac_standard_reference_batch" / "20260509T153925Z_hvac_source_batch" / "batch_summary.json"),
                str(ROOT / "output" / "hvac_standard_reference_retry" / "20260509T155102Z_hvac_source_batch" / "batch_summary.json"),
            ]
        )
    ]
    tasks = load_standard_tasks(summary_paths)
    allowed = set(args.doc_id or [])
    if allowed:
        tasks = [task for task in tasks if str(task["doc_id"]) in allowed]
    matrix_root = Path(args.matrix_root) if args.matrix_root else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for task in tasks:
        base_policy = model_policy(task)
        task_slug = str(task["doc_id"])
        task_dir = output_dir / task_slug
        subset_dir = task_dir / "subset"
        extract_dir = task_dir / "extract"
        current_matrix = matrix_path(str(task["doc_id"]), matrix_root)
        routed_matrix = route_matrix_if_enabled(task, current_matrix, task_dir, args.route_backend, args.backend_config)
        routing_payload = load_routing_payload(routed_matrix)
        effective_policy = route_aware_policy(base_policy, routing_payload)
        effective_anchor, anchor_reason = route_aware_anchor(task, routing_payload)
        manifest_path = run_subset_selection(task, effective_policy, subset_dir, routed_matrix, effective_anchor)
        run_subset_extraction(manifest_path, effective_policy, extract_dir)
        results.append(
            {
                "doc_id": task["doc_id"],
                "file_name": task["file_name"],
                "source_pdf": task["path"],
                "backend": effective_policy["backend"],
                "knowledge_types": effective_policy["knowledge_types"],
                "min_confidence": effective_policy.get("min_confidence", "high"),
                "max_sections": effective_policy["max_sections"],
                "max_pages": effective_policy["max_pages"],
                "suggested_equipment_class_id": effective_anchor,
                "suggested_equipment_class_reason": anchor_reason,
                "subset_dir": str(subset_dir),
                "extract_dir": str(extract_dir),
                "matrix_json": str(current_matrix),
                "routed_matrix_json": str(routed_matrix),
                "route_backend": args.route_backend,
                "document_route": routing_payload.get("llm_routing", {}).get("document_route", {}),
            }
        )

    summary = build_summary(results, output_dir)
    write_summary(output_dir / "standard_subset_pipeline_summary.json", summary)
    print(output_dir / "standard_subset_pipeline_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
