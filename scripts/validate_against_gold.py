#!/usr/bin/env python3
"""Validate standard subset extraction outputs against a small gold set."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pipeline_candidates(pipeline_summary: Path) -> dict[tuple[str, str], dict[str, Any]]:
    pipeline = load_json(pipeline_summary)
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for item in pipeline.get("results", []):
        extract_dir = Path(item["extract_dir"])
        candidate_files = list(extract_dir.glob("*/0001_*/*/candidates.json"))
        for candidate_file in candidate_files:
            payload = load_json(candidate_file)
            for entry in payload.get("candidate_entries", []):
                key = (str(entry.get("doc_id")), str(entry.get("canonical_key_candidate")))
                found[key] = entry
    return found


def validate_gold_entries(gold_path: Path, found: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    gold = load_json(gold_path)
    results = []
    for row in gold.get("entries", []):
        key = (str(row["doc_id"]), str(row["canonical_key_candidate"]))
        matched = found.get(key)
        status = "pass" if matched else "fail"
        evidence_match = False
        if matched:
            evidence_match = str(row.get("evidence_text") or "")[:120] in str(matched.get("evidence_text") or "")
        results.append(
            {
                "doc_id": row["doc_id"],
                "doc_name": row["doc_name"],
                "canonical_key_candidate": row["canonical_key_candidate"],
                "knowledge_object_type": row["knowledge_object_type"],
                "expected_equipment_class_id": row["expected_equipment_class_id"],
                "status": status,
                "evidence_match": evidence_match,
                "matched_equipment_class_id": matched.get("equipment_class_candidate", {}).get("equipment_class_id") if matched else None,
                "matched_task_dir": matched.get("task_dir") if matched else None,
            }
        )
    counts = Counter(item["status"] for item in results)
    evidence_counts = Counter("pass" if item["evidence_match"] else "fail" for item in results if item["status"] == "pass")
    return {
        "validation_mode": "gold_set_exact_match",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "entries": len(results),
            "pass": counts.get("pass", 0),
            "fail": counts.get("fail", 0),
            "evidence_match_pass": evidence_counts.get("pass", 0),
            "evidence_match_fail": evidence_counts.get("fail", 0),
        },
        "results": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Gold Set Validation",
        "",
        f"- Entries: `{report['summary']['entries']}`",
        f"- Pass: `{report['summary']['pass']}`",
        f"- Fail: `{report['summary']['fail']}`",
        f"- Evidence match pass: `{report['summary']['evidence_match_pass']}`",
        f"- Evidence match fail: `{report['summary']['evidence_match_fail']}`",
        "",
        "| Document | Canonical Key | Status | Evidence Match | Expected Anchor | Matched Anchor |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["results"]:
        lines.append(
            f"| {row['doc_name']} | {row['canonical_key_candidate']} | {row['status']} | "
            f"{row['evidence_match']} | {row['expected_equipment_class_id']} | {row['matched_equipment_class_id'] or '-'} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline-summary", type=Path, required=True)
    parser.add_argument("--gold-set", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    found = load_pipeline_candidates(args.pipeline_summary)
    report = validate_gold_entries(args.gold_set, found)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "gold_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "GOLD_VALIDATION.md").write_text(render_markdown(report), encoding="utf-8")
    print(args.output_dir / "GOLD_VALIDATION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
