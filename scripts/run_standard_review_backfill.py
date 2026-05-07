#!/usr/bin/env python3
"""Run the post-review standard backfill pipeline for reviewed packs."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.session import SessionLocal
from packages.retrieval.semantic_service import SemanticRetrievalService
from scripts.apply_review_packs_batch import apply_review_packs_in_directory, discover_review_pack_paths
from scripts.check_review_pack_readiness import check_review_pack_directory
from scripts.print_review_pipeline_summary import build_review_pipeline_summary_text
from scripts.summarize_review_pipeline_stats import summarize_review_pipeline_stats

SUMMARY_FILE = "standard_review_backfill_summary.json"
SUMMARY_MD_FILE = "STANDARD_REVIEW_BACKFILL_SUMMARY.md"
API_SMOKE_REPORT_FILE = "api_smoke_report.json"

PARAMETER_TYPES = {"parameter_spec", "performance_spec"}
FAULT_TYPES = {"fault_code", "fault_diagnostic_rule", "symptom", "diagnostic_step"}
MAINTENANCE_TYPES = {"maintenance_procedure"}
APPLICATION_TYPES = {"application_guidance"}
OPERATIONAL_TYPES = {"commissioning_step", "operational_sequence", "wiring_guidance"}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _service_family(knowledge_object_type: str) -> str:
    if knowledge_object_type in PARAMETER_TYPES:
        return "parameter_profiles"
    if knowledge_object_type in FAULT_TYPES:
        return "fault_knowledge"
    if knowledge_object_type in MAINTENANCE_TYPES:
        return "maintenance_guidance"
    if knowledge_object_type in APPLICATION_TYPES:
        return "application_guidance"
    if knowledge_object_type in OPERATIONAL_TYPES:
        return "operational_guidance"
    raise ValueError(f"Unsupported knowledge_object_type for smoke test: {knowledge_object_type}")


def _accepted_smoke_targets(pack_dir: str | Path) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for pack_path in discover_review_pack_paths(pack_dir):
        payload = _load_json(pack_path)
        domain_id = payload["domain_id"]
        equipment_class_id = payload["equipment_class"]["equipment_class_id"]
        for entry in payload.get("candidate_entries", []):
            if entry.get("review_decision") != "accepted":
                continue
            ko_type = entry.get("knowledge_object_type")
            if not ko_type:
                continue
            counts[(domain_id, equipment_class_id, ko_type)] += 1
    return [
        {
            "domain_id": domain_id,
            "equipment_class_id": equipment_class_id,
            "knowledge_object_type": ko_type,
            "service_family": _service_family(ko_type),
            "expected_accepted_count": expected,
        }
        for (domain_id, equipment_class_id, ko_type), expected in sorted(counts.items())
    ]


def _query_service(
    service: SemanticRetrievalService,
    db: Any,
    target: dict[str, Any],
    *,
    min_trust_level: str,
    limit: int,
) -> dict[str, Any] | None:
    kwargs = {
        "db": db,
        "domain_id": target["domain_id"],
        "equipment_class_id": target["equipment_class_id"],
        "min_trust_level": min_trust_level,
        "limit": limit,
    }
    family = target["service_family"]
    if family == "operational_guidance":
        kwargs["guidance_type"] = target["knowledge_object_type"]
    if family == "fault_knowledge":
        return service.get_fault_knowledge(**kwargs)
    if family == "parameter_profiles":
        return service.get_parameter_profiles(**kwargs)
    if family == "maintenance_guidance":
        return service.get_maintenance_guidance(**kwargs)
    if family == "application_guidance":
        return service.get_application_guidance(**kwargs)
    if family == "operational_guidance":
        return service.get_operational_guidance(**kwargs)
    raise ValueError(f"Unsupported service family: {family}")


def run_semantic_smoke(
    pack_dir: str | Path,
    *,
    min_trust_level: str = "L3",
    limit: int = 100,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify accepted review-pack entries are visible through semantic services."""

    targets = _accepted_smoke_targets(pack_dir)
    service = SemanticRetrievalService()
    db = SessionLocal()
    try:
        results = [
            _smoke_one_target(service, db, target, min_trust_level=min_trust_level, limit=limit)
            for target in targets
        ]
    finally:
        db.close()
    failed = sum(1 for item in results if item["status"] != "pass")
    report = {
        "report_mode": "standard_review_backfill_api_smoke",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_dir": str(Path(pack_dir)),
        "min_trust_level": min_trust_level,
        "limit": limit,
        "summary": {"targets": len(targets), "passed": len(targets) - failed, "failed": failed},
        "results": results,
    }
    target_path = Path(report_path) if report_path else Path(pack_dir) / API_SMOKE_REPORT_FILE
    target_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(target_path)
    return report


def _smoke_one_target(
    service: SemanticRetrievalService,
    db: Any,
    target: dict[str, Any],
    *,
    min_trust_level: str,
    limit: int,
) -> dict[str, Any]:
    payload = _query_service(service, db, target, min_trust_level=min_trust_level, limit=limit)
    items = payload.get("items", []) if payload else []
    visible = sum(1 for item in items if item.get("knowledge_object_type") == target["knowledge_object_type"])
    total_count = payload.get("total_count", 0) if payload else 0
    returned_count = payload.get("returned_count", 0) if payload else 0
    has_more = payload.get("has_more", False) if payload else False
    status = smoke_status(
        expected=target["expected_accepted_count"],
        visible=visible,
        total_count=total_count,
        returned_count=returned_count,
        has_more=has_more,
    )
    return {
        **target,
        "service_total_count": total_count,
        "service_returned_count": returned_count,
        "service_has_more": has_more,
        "visible_matching_count": visible,
        "status": status,
    }


def smoke_status(
    *,
    expected: int,
    visible: int,
    total_count: int,
    returned_count: int,
    has_more: bool,
) -> str:
    if visible >= expected:
        return "pass"
    if has_more and total_count >= expected and visible >= min(expected, returned_count):
        return "pass"
    return "fail"


def run_standard_review_backfill(
    *,
    review_pack_dir: str | Path,
    candidate_file: str | Path | None = None,
    apply: bool = False,
    smoke: bool = False,
    fixtures_output_dir: str | Path | None = None,
    min_trust_level: str = "L3",
    output_summary: str | Path | None = None,
    output_markdown: str | Path | None = None,
) -> dict[str, Any]:
    """Run readiness, optional apply, optional smoke, and write summaries."""

    pack_dir = Path(review_pack_dir)
    readiness_report = check_review_pack_directory(pack_dir)
    apply_report = _run_apply_step(pack_dir, apply=apply, fixtures_output_dir=fixtures_output_dir)
    smoke_report = run_semantic_smoke(pack_dir, min_trust_level=min_trust_level) if smoke else None
    stats = summarize_review_pipeline_stats(
        candidate_path=candidate_file,
        pack_dir=pack_dir,
        readiness_report_path=readiness_report["report_path"],
        apply_report_path=apply_report["report_path"] if apply_report else None,
    )
    summary = _build_summary(pack_dir, candidate_file, readiness_report, apply_report, smoke_report, stats)
    _write_outputs(summary, output_summary, output_markdown)
    return summary


def _run_apply_step(
    pack_dir: Path,
    *,
    apply: bool,
    fixtures_output_dir: str | Path | None,
) -> dict[str, Any] | None:
    if not apply:
        return None
    return apply_review_packs_in_directory(pack_dir, fixtures_output_dir=fixtures_output_dir)


def _build_summary(
    pack_dir: Path,
    candidate_file: str | Path | None,
    readiness_report: dict[str, Any],
    apply_report: dict[str, Any] | None,
    smoke_report: dict[str, Any] | None,
    stats: dict[str, Any],
) -> dict[str, Any]:
    return {
        "pipeline_mode": "standard_review_backfill",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_pack_dir": str(pack_dir),
        "candidate_file": str(candidate_file) if candidate_file else None,
        "readiness_report_path": readiness_report["report_path"],
        "apply_report_path": apply_report["report_path"] if apply_report else None,
        "api_smoke_report_path": smoke_report["report_path"] if smoke_report else None,
        "readiness_summary": readiness_report["summary"],
        "apply_summary": apply_report["summary"] if apply_report else None,
        "api_smoke_summary": smoke_report["summary"] if smoke_report else None,
        "stats": stats,
    }


def _write_outputs(
    summary: dict[str, Any],
    output_summary: str | Path | None,
    output_markdown: str | Path | None,
) -> None:
    pack_dir = Path(summary["review_pack_dir"])
    summary_path = Path(output_summary) if output_summary else pack_dir / SUMMARY_FILE
    markdown_path = Path(output_markdown) if output_markdown else pack_dir / SUMMARY_MD_FILE
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(summary) + "\n", encoding="utf-8")
    summary["summary_path"] = str(summary_path)
    summary["markdown_path"] = str(markdown_path)


def _render_markdown(summary: dict[str, Any]) -> str:
    stats_text = build_review_pipeline_summary_text(summary["stats"])
    lines = [
        "# Standard Review Backfill Summary",
        "",
        f"- Review pack dir: `{summary['review_pack_dir']}`",
        f"- Readiness report: `{summary['readiness_report_path']}`",
        f"- Apply report: `{summary['apply_report_path'] or '(not run)'}`",
        f"- API smoke report: `{summary['api_smoke_report_path'] or '(not run)'}`",
        "",
        "## Pipeline Stats",
        "",
        "```text",
        stats_text,
        "```",
    ]
    if summary["api_smoke_summary"]:
        smoke = summary["api_smoke_summary"]
        lines.extend(["", "## API Smoke", "", f"- Passed: {smoke['passed']}/{smoke['targets']}", f"- Failed: {smoke['failed']}"])
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-pack-dir", required=True, help="Directory containing reviewed pack JSON files")
    parser.add_argument("--candidate-file", help="Optional original candidate JSON for richer stats")
    parser.add_argument("--apply", action="store_true", help="Apply ready review packs into the knowledge store")
    parser.add_argument("--smoke", action="store_true", help="Run semantic service visibility checks after apply")
    parser.add_argument("--fixtures-output-dir", help="Optional directory for generated fixture JSON files")
    parser.add_argument("--min-trust-level", default="L3", help="Minimum trust level for smoke queries")
    parser.add_argument("--output-summary", help="Optional standard pipeline summary JSON path")
    parser.add_argument("--output-markdown", help="Optional standard pipeline summary Markdown path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    summary = run_standard_review_backfill(
        review_pack_dir=args.review_pack_dir,
        candidate_file=args.candidate_file,
        apply=args.apply,
        smoke=args.smoke,
        fixtures_output_dir=args.fixtures_output_dir,
        min_trust_level=args.min_trust_level,
        output_summary=args.output_summary,
        output_markdown=args.output_markdown,
    )
    smoke = summary["api_smoke_summary"] or {"targets": 0, "passed": 0, "failed": 0}
    apply_summary = summary["apply_summary"] or {"applied": 0, "failed": 0}
    print(
        f"ready={summary['readiness_summary']['ready']} "
        f"applied={apply_summary['applied']} apply_failed={apply_summary['failed']} "
        f"smoke_passed={smoke['passed']}/{smoke['targets']} smoke_failed={smoke['failed']} "
        f"summary={summary['summary_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Standard review backfill failed: {exc}")
        raise SystemExit(1)
