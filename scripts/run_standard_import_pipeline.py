#!/usr/bin/env python3
"""Run a staged official-standard import pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_review_packs_batch import discover_review_pack_paths
from scripts.build_review_packs_from_candidates import write_review_packs_from_candidate_file
from scripts.run_standard_review_backfill import run_standard_review_backfill

PIPELINE_SUMMARY_FILE = "standard_import_pipeline_summary.json"
PIPELINE_SUMMARY_MD_FILE = "STANDARD_IMPORT_PIPELINE_SUMMARY.md"


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path} must contain JSON object lines")
            rows.append(payload)
    return rows


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_ashrae_g36_extract(args: argparse.Namespace) -> Path:
    from scripts.run_ashrae_guideline36_vertical import build_parser, run

    required = {
        "--doc-id": args.doc_id,
        "--sections": args.sections,
        "--extract-backend": args.extract_backend,
        "--judge-backend": args.judge_backend,
        "--output-dir": args.extract_output_dir,
        "--budget-rmb": str(args.budget_rmb),
        "--max-section-tokens": str(args.max_section_tokens),
        "--max-candidates-per-section": str(args.max_candidates_per_section),
    }
    argv = [item for pair in required.items() for item in pair]
    summary = run(build_parser().parse_args(argv))
    return Path(summary["output_dir"])


def materialize_candidate_file_from_run(
    run_dir: str | Path,
    workspace_dir: str | Path,
    *,
    standard: str = "ashrae-g36",
) -> dict[str, Any]:
    """Convert a standard extraction run directory into review-pack candidate JSON."""

    source_dir = Path(run_dir)
    destination = Path(workspace_dir)
    destination.mkdir(parents=True, exist_ok=True)
    entries = [
        _normalize_standard_candidate(entry, standard=standard)
        for entry in _load_jsonl(source_dir / "candidates_llm_verified.jsonl")
    ]
    summary = _load_json(source_dir / "summary.json")
    payload = {
        "generation_mode": f"{standard}_standard_import_pipeline",
        "domain_id": "hvac",
        "candidate_entries": entries,
        "metadata": {
            "source_run_dir": str(source_dir),
            "source_report_path": str(source_dir / "REPORT.md"),
            "standard": standard,
            "standard_id": summary.get("standard_id"),
            "doc_id": summary.get("doc_id"),
            "doc_name": summary.get("manual"),
            "sections": summary.get("sections", []),
            "total_candidates": len(entries),
            "judge_accepted": summary.get("judge_accepted"),
            "judge_rejected": summary.get("judge_rejected"),
            "l4_final": summary.get("l4_final"),
            "l3_final": summary.get("l3_final"),
        },
    }
    candidate_path = destination / "candidates_input.json"
    _write_json(candidate_path, payload)
    payload["candidate_path"] = str(candidate_path)
    return payload


def _normalize_standard_candidate(entry: dict[str, Any], *, standard: str) -> dict[str, Any]:
    normalized = dict(entry)
    _normalize_knowledge_type(normalized)
    if "equipment_class_candidate" not in normalized:
        normalized["equipment_class_candidate"] = _infer_equipment_class_candidate(normalized, standard=standard)
    return normalized


def _normalize_knowledge_type(entry: dict[str, Any]) -> None:
    if entry.get("knowledge_object_type") != "commissioning_procedure":
        return
    entry["knowledge_object_type"] = "commissioning_step"
    entry["canonical_key_candidate"] = str(entry.get("canonical_key_candidate", "")).replace(
        ":commissioning_procedure:",
        ":commissioning_step:",
    )
    payload = entry.get("structured_payload_candidate")
    if isinstance(payload, dict):
        payload["knowledge_type"] = "commissioning_step"


def _infer_equipment_class_candidate(entry: dict[str, Any], *, standard: str) -> dict[str, Any]:
    if standard != "ashrae-g36":
        raise ValueError(f"Cannot infer equipment class for standard: {standard}")
    payload = entry.get("structured_payload_candidate", {})
    section_id = str(payload.get("section_id") or entry.get("source_section_id") or "")
    if _section_starts_with(section_id, ("5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10", "5.11", "5.12", "5.13", "5.14", "5.15", "5.16", "5.17", "5.18")):
        return _equipment_ref("ahu", "Air Handling Unit")
    if section_id.startswith("5.20"):
        return _equipment_ref("chiller", "Chiller")
    if section_id.startswith("5.21"):
        return _equipment_ref("hot_water_plant", "Hot Water Plant")
    return _equipment_ref("chiller", "Chiller")


def _section_starts_with(section_id: str, prefixes: tuple[str, ...]) -> bool:
    return any(section_id == prefix or section_id.startswith(f"{prefix}.") for prefix in prefixes)


def _equipment_ref(equipment_class_id: str, label: str) -> dict[str, Any]:
    return {
        "equipment_class_id": equipment_class_id,
        "equipment_class_key": f"hvac:{equipment_class_id}",
        "label": label,
        "supported_knowledge_anchors": [
            "application_guidance",
            "operational_sequence",
            "commissioning_step",
            "fault_diagnostic_rule",
            "parameter_spec",
        ],
    }


def build_standard_review_packs(
    candidate_path: str | Path,
    review_pack_dir: str | Path,
    *,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Build pending review packs from standard extraction candidates."""

    manifest = write_review_packs_from_candidate_file(
        candidate_path,
        review_pack_dir,
        default_trust_level=default_trust_level,
    )
    manifest["manifest_path"] = str(Path(review_pack_dir) / "review_pack_manifest.json")
    return manifest


def run_standard_import_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    """Run selected import stages and return the pipeline summary."""

    workspace_dir = Path(args.workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    run_dir = _resolve_run_dir(args)
    candidate_payload = _resolve_candidates(args, run_dir, workspace_dir)
    review_pack_dir = _resolve_review_pack_dir(args, workspace_dir)
    pack_manifest = _maybe_build_review_packs(args, candidate_payload, review_pack_dir)
    backfill_summary = _maybe_run_review_backfill(args, candidate_payload, review_pack_dir)
    summary = _build_pipeline_summary(args, run_dir, candidate_payload, review_pack_dir, pack_manifest, backfill_summary)
    _write_pipeline_outputs(workspace_dir, summary)
    return summary


def _resolve_run_dir(args: argparse.Namespace) -> Path | None:
    if args.extract:
        return _run_ashrae_g36_extract(args)
    if args.from_run_dir:
        return Path(args.from_run_dir)
    return None


def _resolve_candidates(args: argparse.Namespace, run_dir: Path | None, workspace_dir: Path) -> dict[str, Any] | None:
    if args.candidate_file:
        return {"candidate_path": str(Path(args.candidate_file)), "metadata": _load_json(args.candidate_file).get("metadata", {})}
    if run_dir:
        return materialize_candidate_file_from_run(run_dir, workspace_dir, standard=args.standard)
    return None


def _resolve_review_pack_dir(args: argparse.Namespace, workspace_dir: Path) -> Path:
    return Path(args.review_pack_dir) if args.review_pack_dir else workspace_dir / "review_packs"


def _maybe_build_review_packs(
    args: argparse.Namespace,
    candidate_payload: dict[str, Any] | None,
    review_pack_dir: Path,
) -> dict[str, Any] | None:
    if args.skip_review_pack_build or not candidate_payload:
        return None
    return build_standard_review_packs(
        candidate_payload["candidate_path"],
        review_pack_dir,
        default_trust_level=args.default_trust_level,
    )


def _maybe_run_review_backfill(
    args: argparse.Namespace,
    candidate_payload: dict[str, Any] | None,
    review_pack_dir: Path,
) -> dict[str, Any] | None:
    if args.skip_readiness and not args.apply and not args.smoke:
        return None
    candidate_file = candidate_payload["candidate_path"] if candidate_payload else None
    return run_standard_review_backfill(
        review_pack_dir=review_pack_dir,
        candidate_file=candidate_file,
        apply=args.apply,
        smoke=args.smoke,
        min_trust_level=args.min_trust_level,
    )


def _build_pipeline_summary(
    args: argparse.Namespace,
    run_dir: Path | None,
    candidate_payload: dict[str, Any] | None,
    review_pack_dir: Path,
    pack_manifest: dict[str, Any] | None,
    backfill_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata = candidate_payload.get("metadata", {}) if candidate_payload else {}
    source_run_dir = str(run_dir) if run_dir else metadata.get("source_run_dir")
    return {
        "pipeline_mode": "official_standard_import_pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "standard": args.standard,
        "workspace_dir": str(Path(args.workspace_dir)),
        "source_run_dir": source_run_dir,
        "candidate_path": candidate_payload.get("candidate_path") if candidate_payload else None,
        "review_pack_dir": str(review_pack_dir),
        "review_pack_manifest_path": pack_manifest.get("manifest_path") if pack_manifest else None,
        "candidate_count": _candidate_count(candidate_payload),
        "review_pack_count": _review_pack_count(pack_manifest, review_pack_dir),
        "readiness_summary": backfill_summary.get("readiness_summary") if backfill_summary else None,
        "apply_summary": backfill_summary.get("apply_summary") if backfill_summary else None,
        "api_smoke_summary": backfill_summary.get("api_smoke_summary") if backfill_summary else None,
        "next_action": _next_action(backfill_summary, pack_manifest),
    }


def _review_pack_count(pack_manifest: dict[str, Any] | None, review_pack_dir: Path) -> int | None:
    if pack_manifest:
        return pack_manifest.get("total_packs")
    if review_pack_dir.exists():
        return len(discover_review_pack_paths(review_pack_dir))
    return None


def _candidate_count(candidate_payload: dict[str, Any] | None) -> int | None:
    if not candidate_payload:
        return None
    metadata = candidate_payload.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get("total_candidates") is not None:
        return int(metadata["total_candidates"])
    return len(_load_json(candidate_payload["candidate_path"]).get("candidate_entries", []))


def _next_action(backfill_summary: dict[str, Any] | None, pack_manifest: dict[str, Any] | None) -> str:
    if not backfill_summary:
        return "Run readiness/backfill after review packs are prepared."
    readiness = backfill_summary.get("readiness_summary") or {}
    apply_summary = backfill_summary.get("apply_summary")
    smoke_summary = backfill_summary.get("api_smoke_summary")
    if readiness.get("blocked_pending", 0) > 0:
        return "Complete review decisions in generated review packs, then rerun with --apply --smoke."
    if apply_summary and apply_summary.get("failed", 0) > 0:
        return "Investigate failed review-pack applies before consuming the standard knowledge."
    if smoke_summary and smoke_summary.get("failed", 0) > 0:
        return "Investigate semantic service smoke failures before consuming the standard knowledge."
    if apply_summary and smoke_summary:
        return "Pipeline passed through backfill and semantic smoke; ready for consumer validation."
    if pack_manifest:
        return "Review packs generated; complete human/model review before applying."
    return "Review-pack readiness checked."


def _write_pipeline_outputs(workspace_dir: Path, summary: dict[str, Any]) -> None:
    json_path = workspace_dir / PIPELINE_SUMMARY_FILE
    md_path = workspace_dir / PIPELINE_SUMMARY_MD_FILE
    _write_json(json_path, summary)
    md_path.write_text(_render_markdown(summary) + "\n", encoding="utf-8")
    summary["summary_path"] = str(json_path)
    summary["markdown_path"] = str(md_path)


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Standard Import Pipeline Summary",
        "",
        f"- Standard: `{summary['standard']}`",
        f"- Source run: `{summary['source_run_dir'] or '(not run)'}`",
        f"- Candidates: {summary['candidate_count'] if summary['candidate_count'] is not None else '(not generated)'}",
        f"- Review packs: {summary['review_pack_count'] if summary['review_pack_count'] is not None else '(not generated)'}",
        f"- Review pack dir: `{summary['review_pack_dir']}`",
        f"- Next action: {summary['next_action']}",
    ]
    if summary["readiness_summary"]:
        lines.extend(["", "## Readiness", "", f"```json\n{json.dumps(summary['readiness_summary'], ensure_ascii=False, indent=2)}\n```"])
    if summary["apply_summary"]:
        lines.extend(["", "## Apply", "", f"```json\n{json.dumps(summary['apply_summary'], ensure_ascii=False, indent=2)}\n```"])
    if summary["api_smoke_summary"]:
        lines.extend(["", "## API Smoke", "", f"```json\n{json.dumps(summary['api_smoke_summary'], ensure_ascii=False, indent=2)}\n```"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard", default="ashrae-g36", choices=["ashrae-g36"])
    parser.add_argument("--workspace-dir", required=True)
    parser.add_argument("--from-run-dir", help="Existing standard extraction run directory")
    parser.add_argument("--candidate-file", help="Existing candidate JSON with candidate_entries")
    parser.add_argument("--review-pack-dir", help="Existing or target review pack directory")
    parser.add_argument("--skip-review-pack-build", action="store_true")
    parser.add_argument("--skip-readiness", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--default-trust-level", default="L3")
    parser.add_argument("--min-trust-level", default="L3")
    parser.add_argument("--extract", action="store_true", help="Run ASHRAE G36 extraction before review-pack creation")
    parser.add_argument("--doc-id")
    parser.add_argument("--sections", default="5.1.14,5.20,5.21")
    parser.add_argument("--extract-backend")
    parser.add_argument("--judge-backend")
    parser.add_argument("--extract-output-dir", default="output/ashrae_guideline36_vertical")
    parser.add_argument("--budget-rmb", type=float, default=30.0)
    parser.add_argument("--max-section-tokens", type=int, default=250_000)
    parser.add_argument("--max-candidates-per-section", type=int, default=24)
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    if args.extract and args.from_run_dir:
        raise ValueError("Use either --extract or --from-run-dir, not both")
    if args.extract:
        missing = [name for name in ("doc_id", "extract_backend", "judge_backend") if not getattr(args, name)]
        if missing:
            raise ValueError(f"--extract requires: {', '.join('--' + item.replace('_', '-') for item in missing)}")
    if args.skip_review_pack_build and not args.review_pack_dir:
        raise ValueError("--skip-review-pack-build requires --review-pack-dir for readiness/apply stages")
    if not args.from_run_dir and not args.candidate_file and not args.extract and not args.review_pack_dir:
        raise ValueError("Provide --extract, --from-run-dir, --candidate-file, or --review-pack-dir")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _validate_args(args)
    summary = run_standard_import_pipeline(args)
    print(
        f"standard={summary['standard']} candidates={summary['candidate_count']} "
        f"packs={summary['review_pack_count']} next={summary['next_action']} "
        f"summary={summary['summary_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Standard import pipeline failed: {exc}")
        raise SystemExit(1)
