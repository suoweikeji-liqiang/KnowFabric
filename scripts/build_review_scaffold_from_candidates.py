#!/usr/bin/env python3
"""Build a review scaffold from chunk backfill candidate JSON."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_candidate_payload(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("candidate file must contain a JSON object")
    entries = payload.get("candidate_entries")
    if not isinstance(entries, list):
        raise ValueError("candidate file must include a candidate_entries list")
    return payload


def _scaffold_entry(entry: dict[str, Any], default_trust_level: str) -> dict[str, Any]:
    scaffold = dict(entry)
    scaffold["review_decision"] = "pending"
    scaffold["review_notes"] = ""
    scaffold["curation"] = {
        "title": "",
        "summary": "",
        "canonical_key": entry["canonical_key_candidate"],
        "structured_payload": entry["structured_payload_candidate"],
        "applicability": {},
        "trust_level": default_trust_level,
        "review_status": "approved",
        "evidence_text": entry["evidence_text"],
        "evidence_role": "primary",
    }
    scaffold["curation_checklist"] = [
        "Confirm or reject this candidate.",
        "For accepted entries, fill title and summary.",
        "Adjust structured_payload and applicability to match the manual evidence.",
        "Keep doc/page/chunk traceability unchanged.",
    ]
    return scaffold


def build_review_scaffold_from_candidates(
    payload: dict[str, Any],
    *,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Convert candidate JSON into a review-ready scaffold."""

    entries = payload.get("candidate_entries")
    if not isinstance(entries, list):
        raise ValueError("candidate payload must include a candidate_entries list")
    return {
        "review_mode": "chunk_backfill_review_scaffold",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_generation_mode": payload.get("generation_mode"),
        "domain_id": payload.get("domain_id"),
        "filters_applied": payload.get("filters_applied", {}),
        "review_metadata": {
            "default_trust_level": default_trust_level,
            "candidate_count": len(entries),
            "workflow": [
                "Set review_decision to accepted or rejected.",
                "Accepted entries must complete the curation block before fixture build.",
                "Reviewed files can be passed to build_manual_fixture_from_review_candidates.py.",
            ],
        },
        "candidate_entries": [
            _scaffold_entry(entry, default_trust_level)
            for entry in entries
        ],
    }


def build_review_scaffold_from_candidate_file(
    path: str | Path,
    *,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Load one candidate file and return a scaffold JSON object."""

    return build_review_scaffold_from_candidates(
        _load_candidate_payload(path),
        default_trust_level=default_trust_level,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_path", help="Path to generated candidate JSON")
    parser.add_argument("--output", help="Optional output path for the review scaffold JSON")
    parser.add_argument(
        "--default-trust-level",
        default="L3",
        help="Default trust level to prefill in each curation block",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    scaffold = build_review_scaffold_from_candidate_file(
        args.candidate_path,
        default_trust_level=args.default_trust_level,
    )
    rendered = json.dumps(scaffold, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {len(scaffold['candidate_entries'])} review scaffold entries to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review scaffold build failed: {exc}")
        raise SystemExit(1)
