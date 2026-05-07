#!/usr/bin/env python3
"""Generate a dry-run duplicate report for imported official-standard knowledge objects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models_v2 import KnowledgeObjectEvidenceV2, KnowledgeObjectV2  # noqa: E402
from packages.db.session import SessionLocal  # noqa: E402


@dataclass(frozen=True)
class DedupeRow:
    knowledge_object_id: str
    domain_id: str
    ontology_class_id: str
    knowledge_object_type: str
    canonical_key: str
    title: str
    summary: str
    section_id: str
    trust_level: str
    confidence_score: float
    evidence_count: int
    page_nos: tuple[int, ...]


def normalize_text(value: str | None) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9%#]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical_tail(canonical_key: str) -> str:
    parts = canonical_key.split(":")
    return normalize_text(parts[-1] if parts else canonical_key)


def section_prefix(section_id: str) -> str:
    parts = [part for part in str(section_id or "").split(".") if part]
    return ".".join(parts[:4]) if len(parts) >= 4 else ".".join(parts)


def row_signature(row: DedupeRow) -> str:
    return normalize_text(" ".join([row.title, row.summary, canonical_tail(row.canonical_key)]))


def text_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def duplicate_reason(left: DedupeRow, right: DedupeRow, threshold: float) -> str | None:
    if left.knowledge_object_id == right.knowledge_object_id:
        return None
    if section_prefix(left.section_id) != section_prefix(right.section_id):
        return None
    if has_conflicting_semantics(left.title, right.title):
        return None
    title_similarity = text_similarity(normalize_text(left.title), normalize_text(right.title))
    tail_similarity = text_similarity(canonical_tail(left.canonical_key), canonical_tail(right.canonical_key))
    body_similarity = text_similarity(row_signature(left), row_signature(right))
    if title_similarity >= threshold:
        return f"title_similarity={title_similarity:.2f}"
    if tail_similarity >= threshold:
        return f"canonical_tail_similarity={tail_similarity:.2f}"
    if body_similarity >= threshold:
        return f"body_similarity={body_similarity:.2f}"
    return None


def has_conflicting_semantics(left_title: str, right_title: str) -> bool:
    left = normalize_text(left_title)
    right = normalize_text(right_title)
    checks = (
        ("stage up", "stage down"),
        ("title 24", "ashrae 62 1"),
        ("constant speed", "variable speed"),
        ("heating", "cooling"),
        ("cwrt", "cwst"),
    )
    if any(has_opposed_terms(left, right, pair) for pair in checks):
        return True
    return has_opposed_condensing(left, right)


def has_opposed_terms(left: str, right: str, pair: tuple[str, str]) -> bool:
    first, second = pair
    return (first in left and second in right) or (second in left and first in right)


def has_opposed_condensing(left: str, right: str) -> bool:
    return condensing_mode(left) != "" and condensing_mode(right) != "" and condensing_mode(left) != condensing_mode(right)


def condensing_mode(title: str) -> str:
    if "non condensing" in title:
        return "non_condensing"
    if "condensing" in title:
        return "condensing"
    return ""


def trust_rank(value: str) -> int:
    return {"L4": 4, "L3": 3, "L2": 2, "L1": 1}.get(str(value or "").upper(), 0)


def keep_sort_key(row: DedupeRow) -> tuple[int, int, float, int]:
    return (trust_rank(row.trust_level), row.evidence_count, row.confidence_score, len(row.summary))


def group_duplicate_rows(rows: list[DedupeRow], threshold: float) -> list[dict[str, Any]]:
    groups = []
    for bucket_rows in bucket_rows_for_compare(rows).values():
        groups.extend(group_bucket(bucket_rows, threshold))
    return sorted(groups, key=lambda item: (item["keep"]["equipment_class_id"], item["keep"]["knowledge_object_type"], item["keep"]["section_id"]))


def bucket_rows_for_compare(rows: list[DedupeRow]) -> dict[tuple[str, str, str, str], list[DedupeRow]]:
    buckets: dict[tuple[str, str, str, str], list[DedupeRow]] = defaultdict(list)
    for row in rows:
        key = (row.domain_id, row.ontology_class_id, row.knowledge_object_type, section_prefix(row.section_id))
        buckets[key].append(row)
    return buckets


def group_bucket(rows: list[DedupeRow], threshold: float) -> list[dict[str, Any]]:
    parent = {row.knowledge_object_id: row.knowledge_object_id for row in rows}
    reasons: dict[tuple[str, str], str] = {}
    for index, left in enumerate(rows):
        for right in rows[index + 1 :]:
            reason = duplicate_reason(left, right, threshold)
            if reason:
                union(parent, left.knowledge_object_id, right.knowledge_object_id)
                reasons[tuple(sorted((left.knowledge_object_id, right.knowledge_object_id)))] = reason
    return build_groups(rows, parent, reasons)


def find(parent: dict[str, str], item: str) -> str:
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


def union(parent: dict[str, str], left: str, right: str) -> None:
    left_root, right_root = find(parent, left), find(parent, right)
    if left_root != right_root:
        parent[right_root] = left_root


def build_groups(rows: list[DedupeRow], parent: dict[str, str], reasons: dict[tuple[str, str], str]) -> list[dict[str, Any]]:
    by_root: dict[str, list[DedupeRow]] = defaultdict(list)
    for row in rows:
        by_root[find(parent, row.knowledge_object_id)].append(row)
    return [build_group(group, reasons) for group in by_root.values() if len(group) > 1]


def build_group(rows: list[DedupeRow], reasons: dict[tuple[str, str], str]) -> dict[str, Any]:
    keep = max(rows, key=keep_sort_key)
    duplicate_rows = [row for row in sorted(rows, key=lambda item: item.knowledge_object_id) if row_id(row) != row_id(keep)]
    return {
        "keep": public_row(keep),
        "duplicates": [public_row(row) for row in duplicate_rows],
        "pair_reasons": matching_reasons(rows, reasons),
    }


def row_id(row: DedupeRow) -> str:
    return row.knowledge_object_id


def matching_reasons(rows: list[DedupeRow], reasons: dict[tuple[str, str], str]) -> list[dict[str, str]]:
    ids = {row.knowledge_object_id for row in rows}
    return [
        {"left": left, "right": right, "reason": reason}
        for (left, right), reason in sorted(reasons.items())
        if left in ids and right in ids
    ]


def public_row(row: DedupeRow) -> dict[str, Any]:
    return {
        "knowledge_object_id": row.knowledge_object_id,
        "equipment_class_id": row.ontology_class_id,
        "knowledge_object_type": row.knowledge_object_type,
        "canonical_key": row.canonical_key,
        "title": row.title,
        "section_id": row.section_id,
        "trust_level": row.trust_level,
        "evidence_count": row.evidence_count,
        "page_nos": list(row.page_nos),
    }


def load_standard_rows(standard_id: str) -> list[DedupeRow]:
    db = SessionLocal()
    try:
        evidence = evidence_index(db)
        rows = db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.review_status == "approved").all()
        return [to_dedupe_row(row, evidence) for row in rows if is_standard_row(row, standard_id)]
    finally:
        db.close()


def evidence_index(db) -> dict[str, dict[str, Any]]:
    rows = db.query(KnowledgeObjectEvidenceV2.knowledge_object_id, KnowledgeObjectEvidenceV2.page_no).all()
    index: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "pages": set()})
    for row in rows:
        index[row.knowledge_object_id]["count"] += 1
        index[row.knowledge_object_id]["pages"].add(row.page_no)
    return index


def is_standard_row(row: KnowledgeObjectV2, standard_id: str) -> bool:
    app = row.applicability_json or {}
    payload = row.structured_payload_json or {}
    return (
        app.get("standard_id") == standard_id
        or payload.get("source_standard_id") == standard_id
        or str(row.canonical_key).startswith("ashrae:g36")
    )


def to_dedupe_row(row: KnowledgeObjectV2, evidence: dict[str, dict[str, Any]]) -> DedupeRow:
    payload = row.structured_payload_json or {}
    evidence_info = evidence.get(row.knowledge_object_id, {"count": 0, "pages": set()})
    return DedupeRow(
        knowledge_object_id=row.knowledge_object_id,
        domain_id=row.domain_id,
        ontology_class_id=row.ontology_class_id,
        knowledge_object_type=row.knowledge_object_type,
        canonical_key=row.canonical_key,
        title=row.title or str(payload.get("title") or ""),
        summary=row.summary or str(payload.get("summary") or ""),
        section_id=str(payload.get("section_id") or payload.get("source_section_id") or ""),
        trust_level=row.trust_level,
        confidence_score=float(row.confidence_score or 0.0),
        evidence_count=int(evidence_info["count"]),
        page_nos=tuple(sorted(evidence_info["pages"])),
    )


def write_report(output_dir: Path, rows: list[DedupeRow], groups: list[dict[str, Any]], args: argparse.Namespace) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    report = build_report(rows, groups, args)
    (output_dir / "dedupe_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "DEDUPE_REPORT.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def build_report(rows: list[DedupeRow], groups: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    duplicate_count = sum(len(group["duplicates"]) for group in groups)
    return {
        "mode": "standard_knowledge_dedupe_dry_run",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "standard_id": args.standard_id,
        "threshold": args.threshold,
        "row_count": len(rows),
        "duplicate_group_count": len(groups),
        "recommended_duplicate_count": duplicate_count,
        "estimated_unique_after_dedupe": len(rows) - duplicate_count,
        "groups": groups,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Standard Knowledge Dedupe Report",
        "",
        f"- Standard: `{report['standard_id']}`",
        f"- Approved rows scanned: {report['row_count']}",
        f"- Duplicate groups: {report['duplicate_group_count']}",
        f"- Recommended duplicate rows: {report['recommended_duplicate_count']}",
        f"- Estimated unique after dedupe: {report['estimated_unique_after_dedupe']}",
        f"- Similarity threshold: {report['threshold']}",
        "",
        "## Duplicate Groups",
        "",
    ]
    for index, group in enumerate(report["groups"][:50], start=1):
        lines.extend(render_group(index, group))
    if len(report["groups"]) > 50:
        lines.append(f"\n_Report truncated in Markdown: {len(report['groups']) - 50} additional groups in JSON._")
    return "\n".join(lines)


def render_group(index: int, group: dict[str, Any]) -> list[str]:
    keep = group["keep"]
    lines = [
        f"### Group {index}",
        "",
        f"Keep: `{keep['knowledge_object_id']}` {keep['equipment_class_id']} / {keep['knowledge_object_type']} / §{keep['section_id']} / {keep['trust_level']} / evidence={keep['evidence_count']}",
        f"- {keep['title']}",
        "",
        "Duplicates:",
    ]
    for row in group["duplicates"]:
        lines.append(f"- `{row['knowledge_object_id']}` {row['trust_level']} evidence={row['evidence_count']} - {row['title']}")
    lines.append("")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-id", default="ASHRAE Guideline 36-2021")
    parser.add_argument("--threshold", type=float, default=0.86)
    parser.add_argument("--output-dir", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    rows = load_standard_rows(args.standard_id)
    groups = group_duplicate_rows(rows, args.threshold)
    write_report(output_dir, rows, groups, args)
    print(f"rows={len(rows)} duplicate_groups={len(groups)} report={output_dir / 'DEDUPE_REPORT.md'}")
    return 0


def default_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return Path("workspace/ashrae_g36_dedupe_report") / stamp


if __name__ == "__main__":
    raise SystemExit(main())
