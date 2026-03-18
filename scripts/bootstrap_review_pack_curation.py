#!/usr/bin/env python3
"""Bootstrap editable curation drafts inside one review pack."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TYPE_LABELS = {
    "fault_code": "Fault Code",
    "parameter_spec": "Parameter Spec",
    "maintenance_procedure": "Maintenance Procedure",
    "diagnostic_step": "Diagnostic Step",
}
DEFAULT_TARGET_DECISIONS = {"accepted", "pending"}


def _load_review_pack(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("review pack must contain a JSON object")
    if payload.get("review_mode") != "chunk_backfill_review_pack":
        raise ValueError("JSON file is not a review pack")
    entries = payload.get("candidate_entries")
    if not isinstance(entries, list):
        raise ValueError("review pack must contain candidate_entries")
    return payload


def _non_empty_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _draft_title(entry: dict[str, Any], equipment_label: str) -> str:
    type_label = TYPE_LABELS.get(entry["knowledge_object_type"], entry["knowledge_object_type"].replace("_", " ").title())
    return f"Draft {type_label} {entry['canonical_key_candidate']} for {equipment_label}"


def _draft_summary(entry: dict[str, Any], equipment_label: str) -> str:
    type_label = TYPE_LABELS.get(entry["knowledge_object_type"], entry["knowledge_object_type"])
    return (
        f"Draft review summary for {type_label.lower()} {entry['canonical_key_candidate']} "
        f"derived from chunk {entry['chunk_id']} on page {entry['page_no']} for {equipment_label}."
    )


def _bootstrap_curation(entry: dict[str, Any], equipment_label: str, default_trust_level: str) -> bool:
    curation = entry.setdefault("curation", {})
    changed = False
    if _non_empty_text(curation.get("title")) is None:
        curation["title"] = _draft_title(entry, equipment_label)
        changed = True
    if _non_empty_text(curation.get("summary")) is None:
        curation["summary"] = _draft_summary(entry, equipment_label)
        changed = True
    if _non_empty_text(curation.get("canonical_key")) is None:
        curation["canonical_key"] = entry["canonical_key_candidate"]
        changed = True
    if not isinstance(curation.get("structured_payload"), dict) or not curation["structured_payload"]:
        curation["structured_payload"] = entry["structured_payload_candidate"]
        changed = True
    if not isinstance(curation.get("applicability"), dict):
        curation["applicability"] = {}
        changed = True
    if _non_empty_text(curation.get("trust_level")) is None:
        curation["trust_level"] = default_trust_level
        changed = True
    if _non_empty_text(curation.get("evidence_text")) is None:
        curation["evidence_text"] = entry["evidence_text"]
        changed = True
    if _non_empty_text(curation.get("evidence_role")) is None:
        curation["evidence_role"] = "primary"
        changed = True
    if _non_empty_text(curation.get("review_status")) is None:
        curation["review_status"] = "approved"
        changed = True
    return changed


def bootstrap_review_pack_curation(
    payload: dict[str, Any],
    *,
    target_decisions: set[str] | None = None,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Fill obvious empty curation fields with editable draft values."""

    decisions = target_decisions or set(DEFAULT_TARGET_DECISIONS)
    result = dict(payload)
    entries = []
    changed_count = 0
    equipment_label = payload.get("equipment_class", {}).get("label", "equipment")
    for entry in payload["candidate_entries"]:
        updated = dict(entry)
        if entry.get("review_decision", "pending") in decisions:
            if _bootstrap_curation(updated, equipment_label, default_trust_level):
                changed_count += 1
        entries.append(updated)
    result["candidate_entries"] = entries
    result["bootstrap_metadata"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_decisions": sorted(decisions),
        "entries_updated": changed_count,
    }
    return result


def bootstrap_review_pack_file(
    path: str | Path,
    *,
    target_decisions: set[str] | None = None,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Load one review pack file and return a bootstrapped payload."""

    return bootstrap_review_pack_curation(
        _load_review_pack(path),
        target_decisions=target_decisions,
        default_trust_level=default_trust_level,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_path", help="Path to one review pack JSON file")
    parser.add_argument("--output", help="Optional output path for the bootstrapped pack JSON")
    parser.add_argument(
        "--default-trust-level",
        default="L3",
        help="Fallback trust level for empty curation blocks",
    )
    parser.add_argument(
        "--target-decisions",
        nargs="+",
        default=sorted(DEFAULT_TARGET_DECISIONS),
        help="Only bootstrap entries whose review_decision is in this set",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    payload = bootstrap_review_pack_file(
        args.pack_path,
        target_decisions=set(args.target_decisions),
        default_trust_level=args.default_trust_level,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(
            f"Wrote bootstrapped review pack with "
            f"{payload['bootstrap_metadata']['entries_updated']} updated entrie(s) to {args.output}"
        )
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pack bootstrap failed: {exc}")
        raise SystemExit(1)
