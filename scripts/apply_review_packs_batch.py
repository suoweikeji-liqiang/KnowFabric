#!/usr/bin/env python3
"""Apply reviewed chunk backfill packs in batch and emit a report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.backfill_manual_knowledge_from_chunks import backfill_manual_fixture_from_chunks
from scripts.build_manual_fixture_from_review_candidates import build_manual_fixture_from_review_candidate_file
from packages.compiler.audit import (
    build_compiler_audit_packet,
    build_compiler_run,
    build_file_source_manifest_entry,
    build_review_pack_source_manifest_entry,
    utc_now_iso,
    write_compiler_audit_packet,
)
from packages.db.session import SessionLocal
from packages.review.applier import apply_with_merger

PACK_MANIFEST_FILE = "review_pack_manifest.json"
APPLY_REPORT_FILE = "review_pack_apply_report.json"
AUDIT_PACKET_FILE = "review_pack_compiler_audit_packet.json"
READINESS_REPORT_FILE = "review_pack_readiness_report.json"
BOOTSTRAP_REPORT_FILE = "review_pack_bootstrap_report.json"
VALID_DECISIONS = {"accepted", "rejected", "pending"}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def discover_review_pack_paths(pack_dir: str | Path) -> list[Path]:
    """Discover review pack JSON files in one directory."""

    root = Path(pack_dir)
    return sorted(path for path in root.glob("*.json") if path.is_file() and _is_review_pack_path(path))


def _is_review_pack_path(path: Path) -> bool:
    try:
        payload = _load_json(path)
    except Exception:
        return False
    return payload.get("review_mode") == "chunk_backfill_review_pack"


def inspect_review_pack(payload: dict[str, Any]) -> dict[str, Any]:
    """Return review pack status metadata without applying it."""

    if payload.get("review_mode") != "chunk_backfill_review_pack":
        raise ValueError("JSON file is not a review pack")
    entries = payload.get("candidate_entries")
    if not isinstance(entries, list):
        raise ValueError("review pack must contain candidate_entries")
    decisions = [entry.get("review_decision", "pending") for entry in entries]
    invalid = sorted({decision for decision in decisions if decision not in VALID_DECISIONS})
    if invalid:
        raise ValueError(f"review pack contains invalid decisions: {', '.join(invalid)}")
    counts = Counter(decisions)
    return {
        "candidate_count": len(entries),
        "accepted_count": counts.get("accepted", 0),
        "rejected_count": counts.get("rejected", 0),
        "pending_count": counts.get("pending", 0),
    }


def _fixture_path(fixtures_output_dir: Path, pack_path: Path) -> Path:
    return fixtures_output_dir / f"{pack_path.stem}__fixture.json"


def _ensure_dir(path: str | Path) -> Path:
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _default_compiler_run_id() -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _source_manifest_for_pack_paths(pack_paths: list[Path]) -> list:
    entries = []
    for pack_path in pack_paths:
        try:
            payload = _load_json(pack_path)
            entries.append(build_review_pack_source_manifest_entry(pack_path, payload))
        except Exception as exc:
            entries.append(build_file_source_manifest_entry(
                pack_path,
                metadata={"manifest_error": str(exc)},
            ))
    return entries


def _infer_run_domain(source_manifest: list) -> str | None:
    domains = sorted({entry.domain_id for entry in source_manifest if entry.domain_id})
    if len(domains) == 1:
        return domains[0]
    return "mixed" if domains else None


def _accepted_entries_from_pack(pack_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fixture = build_manual_fixture_from_review_candidate_file(pack_path)
    entries = fixture.get("manual_entries", [])
    accepted = [e for e in entries if e.get("review_status") == "published" or e.get("review_decision") == "accepted"]
    return fixture, accepted or entries


def _apply_pack_with_merger(
    pack_path: Path,
    *,
    merger_backend: str | None,
    package_version: str,
    ontology_version: str,
) -> dict[str, Any]:
    fixture, accepted = _accepted_entries_from_pack(pack_path)
    db = SessionLocal()
    try:
        ec_id = fixture.get("equipment_class_id", "")
        ock = fixture.get("equipment_class_key", f"hvac:{ec_id}")
        stats = apply_with_merger(
            session=db,
            verified_candidates=accepted,
            equipment_class_id=ec_id,
            ontology_class_key=ock,
            knowledge_object_type="",
            backend_name=merger_backend,
            package_version=package_version,
            ontology_version=ontology_version,
        )
        db.commit()
        return {
            "status": "applied_merger",
            "equipment_class_key": ock,
            "knowledge_object_count": stats["new_merged"] + stats["updated_existing"],
            "merger_stats": stats,
        }
    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"merger apply failed for {pack_path.name}: {exc}") from exc
    finally:
        db.close()


def _apply_pack_direct(pack_path: Path, fixture_root: Path) -> dict[str, Any]:
    fixture = build_manual_fixture_from_review_candidate_file(pack_path)
    fixture_path = _fixture_path(fixture_root, pack_path)
    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(fixture_path)
    return {
        "status": "applied",
        "equipment_class_key": equipment_class_key,
        "knowledge_object_count": knowledge_count,
        "fixture_path": str(fixture_path),
    }


def _apply_one_pack(pack_path: Path, fixture_root: Path, *,
                     use_merger: bool = True, merger_backend: str | None = None,
                     package_version: str = "2.0.0-alpha",
                     ontology_version: str = "2.0.0-alpha") -> dict[str, Any]:
    result = {
        "pack_file": pack_path.name,
        "pack_path": str(pack_path),
    }
    try:
        payload = _load_json(pack_path)
        inspection = inspect_review_pack(payload)
        result.update(inspection)
        if inspection["pending_count"] > 0:
            result["status"] = "skipped_pending"
        elif inspection["accepted_count"] == 0:
            result["status"] = "skipped_no_accepted"
        elif use_merger:
            result.update(_apply_pack_with_merger(
                pack_path,
                merger_backend=merger_backend,
                package_version=package_version,
                ontology_version=ontology_version,
            ))
        else:
            result.update(_apply_pack_direct(pack_path, fixture_root))
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = str(exc)
    return result


def _run_apply_results(
    pack_paths: list[Path],
    fixture_root: Path,
    *,
    use_merger: bool,
    merger_backend: str | None,
    package_version: str,
    ontology_version: str,
) -> tuple[list[dict[str, Any]], Counter]:
    results = []
    summary = Counter()
    for pack_path in pack_paths:
        result = _apply_one_pack(pack_path, fixture_root,
                                 use_merger=use_merger, merger_backend=merger_backend,
                                 package_version=package_version,
                                 ontology_version=ontology_version)
        summary[result["status"]] += 1
        results.append(result)
    return results, summary


def _public_summary(summary: Counter) -> dict[str, int]:
    return {
        "applied": summary.get("applied", 0) + summary.get("applied_merger", 0),
        "skipped_pending": summary.get("skipped_pending", 0),
        "skipped_no_accepted": summary.get("skipped_no_accepted", 0),
        "failed": summary.get("failed", 0),
    }


def _write_report_and_audit(report: dict[str, Any], report_target: Path, run, results) -> None:
    audit_packet = build_compiler_audit_packet(
        compiler_run=run,
        summary=report["summary"],
        results=results,
    )
    audit_target = report_target.parent / AUDIT_PACKET_FILE
    write_compiler_audit_packet(audit_target, audit_packet)
    report["compiler_audit_packet_path"] = str(audit_target)
    report_target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_run(
    *,
    compiler_run_id: str | None,
    source_manifest: list,
    use_merger: bool,
    merger_backend: str | None,
    package_version: str,
    ontology_version: str,
    started_at: str,
    finished_at: str,
):
    return build_compiler_run(
        compiler_run_id=compiler_run_id or _default_compiler_run_id(),
        pipeline="review_pack_batch_apply",
        domain_id=_infer_run_domain(source_manifest),
        package_version=package_version,
        ontology_version=ontology_version,
        llm_backend=merger_backend,
        parameters={"use_merger": use_merger},
        source_manifest=source_manifest,
        started_at=started_at,
        finished_at=finished_at,
    )


def _build_apply_report(
    *,
    run,
    source_manifest: list,
    source_label: str,
    fixture_root: Path,
    pack_count: int,
    summary: Counter,
    results: list[dict[str, Any]],
    finished_at: str,
) -> dict[str, Any]:
    return {
        "apply_mode": "chunk_backfill_review_pack_batch",
        "generated_at": finished_at,
        "compiler_run": run.model_dump(mode="json", exclude={"source_manifest"}),
        "source_manifest": [entry.model_dump(mode="json") for entry in source_manifest],
        "pack_dir": source_label,
        "fixtures_output_dir": str(fixture_root),
        "total_pack_files": pack_count,
        "summary": _public_summary(summary),
        "results": results,
    }


def apply_review_pack_paths(
    pack_paths: list[Path],
    *,
    source_label: str,
    fixtures_output_dir: str | Path,
    report_path: str | Path | None = None,
    use_merger: bool = True,
    merger_backend: str | None = None,
    compiler_run_id: str | None = None,
    package_version: str = "2.0.0-alpha",
    ontology_version: str = "2.0.0-alpha",
) -> dict[str, Any]:
    fixture_root = _ensure_dir(fixtures_output_dir)
    started_at = utc_now_iso()
    source_manifest = _source_manifest_for_pack_paths(pack_paths)
    results, summary = _run_apply_results(
        pack_paths,
        fixture_root,
        use_merger=use_merger,
        merger_backend=merger_backend,
        package_version=package_version,
        ontology_version=ontology_version,
    )

    finished_at = utc_now_iso()
    run = _build_run(
        compiler_run_id=compiler_run_id,
        source_manifest=source_manifest,
        use_merger=use_merger,
        merger_backend=merger_backend,
        package_version=package_version,
        ontology_version=ontology_version,
        started_at=started_at,
        finished_at=finished_at,
    )
    report = _build_apply_report(
        run=run,
        source_manifest=source_manifest,
        source_label=source_label,
        fixture_root=fixture_root,
        pack_count=len(pack_paths),
        summary=summary,
        results=results,
        finished_at=finished_at,
    )
    report_target = Path(report_path) if report_path else fixture_root.parent / APPLY_REPORT_FILE
    _write_report_and_audit(report, report_target, run, results)
    report["report_path"] = str(report_target)
    return report


def apply_review_packs_in_directory(
    pack_dir: str | Path,
    *,
    fixtures_output_dir: str | Path | None = None,
    report_path: str | Path | None = None,
    use_merger: bool = True,
    merger_backend: str | None = None,
    compiler_run_id: str | None = None,
    package_version: str = "2.0.0-alpha",
    ontology_version: str = "2.0.0-alpha",
) -> dict[str, Any]:
    """Apply all fully reviewed packs in one directory and write a report."""

    pack_root = Path(pack_dir)
    fixture_root = Path(fixtures_output_dir) if fixtures_output_dir else pack_root / "applied_fixtures"
    pack_paths = discover_review_pack_paths(pack_root)
    return apply_review_pack_paths(
        pack_paths,
        source_label=str(pack_root),
        fixtures_output_dir=fixture_root,
        report_path=report_path,
        use_merger=use_merger,
        merger_backend=merger_backend,
        compiler_run_id=compiler_run_id,
        package_version=package_version,
        ontology_version=ontology_version,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", help="Directory containing review packs")
    parser.add_argument(
        "--fixtures-output-dir",
        help="Optional directory for generated fixture JSON files",
    )
    parser.add_argument("--report-path", help="Optional output path for the apply report JSON")
    parser.add_argument("--no-merger", action="store_false", dest="use_merger",
                        help="Disable merger (emergency fallback: direct INSERT without cross-source dedup)")
    parser.add_argument("--merger-backend", default=None,
                        help="LLM backend for merger canonical_key grouping")
    parser.add_argument("--compiler-run-id", default=None,
                        help="Optional stable run id for audit correlation")
    parser.add_argument("--package-version", default="2.0.0-alpha",
                        help="Knowledge package version stamped into compiler run audit")
    parser.add_argument("--ontology-version", default="2.0.0-alpha",
                        help="Ontology version stamped into compiler run audit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = apply_review_packs_in_directory(
        args.pack_dir,
        fixtures_output_dir=args.fixtures_output_dir,
        report_path=args.report_path,
        use_merger=args.use_merger,
        merger_backend=args.merger_backend,
        compiler_run_id=args.compiler_run_id,
        package_version=args.package_version,
        ontology_version=args.ontology_version,
    )
    print(
        f"Applied {report['summary']['applied']} pack(s), "
        f"skipped {report['summary']['skipped_pending'] + report['summary']['skipped_no_accepted']} pack(s), "
        f"failed {report['summary']['failed']} pack(s). "
        f"Report: {report['report_path']}"
    )
    return 1 if report["summary"]["failed"] > 0 else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pack batch apply failed: {exc}")
        raise SystemExit(1)
