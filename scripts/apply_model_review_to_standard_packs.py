#!/usr/bin/env python3
"""Convert judge-accepted standard candidates into model-reviewed draft packs."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_review_packs_batch import discover_review_pack_paths

MODEL_REVIEW_REPORT_FILE = "model_review_report.json"
SUPPORTED_REVIEW_TYPES = {
    "application_guidance",
    "commissioning_step",
    "fault_code",
    "fault_diagnostic_rule",
    "maintenance_procedure",
    "operational_sequence",
    "parameter_spec",
    "performance_spec",
}


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_model_review_to_pack_dir(
    pack_dir: str | Path,
    *,
    rejected_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Mark judge-accepted candidates accepted and unsupported candidates rejected."""

    root = Path(pack_dir)
    rejected_rows = _load_jsonl(rejected_path) if rejected_path else []
    rejected_by_id = {row.get("candidate_id"): row for row in rejected_rows}
    results = []
    summary = Counter()
    for pack_path in discover_review_pack_paths(root):
        result = _apply_model_review_to_pack(pack_path, rejected_by_id)
        results.append(result)
        summary.update(result["decisions"])
    report = {
        "review_mode": "model_review_standard_packs",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_dir": str(root),
        "rejected_source": str(rejected_path) if rejected_path else None,
        "summary": dict(summary),
        "results": results,
    }
    target = Path(report_path) if report_path else root / MODEL_REVIEW_REPORT_FILE
    _write_json(target, report)
    report["report_path"] = str(target)
    return report


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _apply_model_review_to_pack(pack_path: Path, rejected_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = _load_json(pack_path)
    decisions = Counter()
    updated_entries = []
    for entry in payload["candidate_entries"]:
        updated = _model_review_entry(entry, rejected_by_id)
        decisions[updated["review_decision"]] += 1
        updated_entries.append(updated)
    payload["candidate_entries"] = updated_entries
    payload["model_review_metadata"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_source": "llm_judge",
        "notes": [
            "Model-reviewed draft only; operator may still edit or override decisions.",
            "Unsupported KO types are rejected because they cannot pass current semantic API/backfill contracts.",
        ],
    }
    _write_json(pack_path, payload)
    return {
        "pack_file": pack_path.name,
        "candidate_count": len(updated_entries),
        "decisions": dict(decisions),
    }


def _model_review_entry(entry: dict[str, Any], rejected_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    updated = dict(entry)
    rejected = rejected_by_id.get(entry.get("candidate_id"))
    if rejected:
        return _reject_entry(updated, rejected.get("judge_reason"), rejected.get("judge_category") or "judge_rejected")
    if entry.get("knowledge_object_type") not in SUPPORTED_REVIEW_TYPES:
        return _reject_entry(updated, "Unsupported knowledge_object_type for current semantic backfill/API contract.", "unsupported_ko_type")
    updated["review_decision"] = "accepted"
    updated["review_notes"] = _review_note(entry)
    updated["curation"] = _curation_from_entry(entry)
    return updated


def _reject_entry(entry: dict[str, Any], reason: str | None, category: str) -> dict[str, Any]:
    entry["review_decision"] = "rejected"
    entry["review_notes"] = f"model_review_rejected:{category}: {reason or 'No reason provided'}"
    return entry


def _review_note(entry: dict[str, Any]) -> str:
    reason = entry.get("judge_reason") or "Accepted by model judge."
    return f"model_review_accepted: {reason}"


def _curation_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    payload = entry.get("structured_payload_candidate", {})
    return {
        "title": str(payload.get("title") or entry["canonical_key_candidate"]),
        "summary": str(payload.get("summary") or entry.get("judge_reason") or payload.get("title") or entry["canonical_key_candidate"]),
        "canonical_key": entry["canonical_key_candidate"],
        "structured_payload": payload,
        "applicability": {
            "brand": "ASHRAE",
            "model_family": "Guideline 36",
            "standard_id": entry.get("standard_id"),
        },
        "trust_level": entry.get("trust_level") or "L3",
        "review_status": "approved",
        "evidence_text": entry.get("evidence_text") or entry.get("evidence_quote"),
        "evidence_role": "primary",
        "source_chunk_ids": entry.get("source_chunk_ids") or [entry.get("chunk_id")],
        "review_source": "llm_judge",
        "judge_verdict": entry.get("judge_verdict"),
        "judge_reason": entry.get("judge_reason"),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", required=True, help="Directory containing generated standard review packs")
    parser.add_argument("--judge-rejected-jsonl", help="Optional candidates_llm_judge_rejected.jsonl source")
    parser.add_argument("--report-path", help="Optional model review report path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = apply_model_review_to_pack_dir(
        args.pack_dir,
        rejected_path=args.judge_rejected_jsonl,
        report_path=args.report_path,
    )
    print(f"model_review={report['summary']} report={report['report_path']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Model review apply failed: {exc}")
        raise SystemExit(1)
