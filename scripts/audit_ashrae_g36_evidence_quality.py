#!/usr/bin/env python3
"""Audit evidence quality for approved ASHRAE G36 knowledge objects."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models_v2 import KnowledgeObjectEvidenceV2, KnowledgeObjectV2  # noqa: E402
from packages.db.session import SessionLocal  # noqa: E402
from scripts.run_ashrae_g36_full_book import weak_evidence_reason  # noqa: E402

STANDARD_ID = "ASHRAE Guideline 36-2021"


def is_g36_row(row: KnowledgeObjectV2) -> bool:
    app = row.applicability_json or {}
    payload = row.structured_payload_json or {}
    return (
        app.get("standard_id") == STANDARD_ID
        or payload.get("source_standard_id") == STANDARD_ID
        or str(row.canonical_key).startswith("ashrae:g36")
    )


def load_g36_rows() -> tuple[list[KnowledgeObjectV2], dict[str, list[KnowledgeObjectEvidenceV2]]]:
    db = SessionLocal()
    try:
        rows = [row for row in db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.review_status == "approved").all() if is_g36_row(row)]
        evidence_rows = (
            db.query(KnowledgeObjectEvidenceV2)
            .filter(KnowledgeObjectEvidenceV2.knowledge_object_id.in_([row.knowledge_object_id for row in rows]))
            .all()
        )
        evidence = group_evidence(evidence_rows)
        return rows, evidence
    finally:
        db.close()


def group_evidence(rows: list[KnowledgeObjectEvidenceV2]) -> dict[str, list[KnowledgeObjectEvidenceV2]]:
    grouped: dict[str, list[KnowledgeObjectEvidenceV2]] = {}
    for row in rows:
        grouped.setdefault(row.knowledge_object_id, []).append(row)
    return grouped


def audit_row(row: KnowledgeObjectV2, evidence_rows: list[KnowledgeObjectEvidenceV2]) -> dict[str, Any] | None:
    checks = [audit_evidence(row, evidence) for evidence in evidence_rows]
    weak = [item for item in checks if item["reason"]]
    strong = [item for item in checks if not item["reason"]]
    if strong:
        return None
    return public_finding(row, weak or [{"reason": "missing evidence", "page_no": None, "evidence_text": ""}])


def audit_evidence(row: KnowledgeObjectV2, evidence: KnowledgeObjectEvidenceV2) -> dict[str, Any]:
    candidate = {
        "knowledge_object_type": row.knowledge_object_type,
        "structured_payload_candidate": row.structured_payload_json or {},
        "evidence_quote": evidence.evidence_text or "",
    }
    return {
        "reason": weak_evidence_reason(candidate) or "",
        "page_no": evidence.page_no,
        "chunk_id": evidence.chunk_id,
        "evidence_text": evidence.evidence_text or "",
    }


def public_finding(row: KnowledgeObjectV2, weak_checks: list[dict[str, Any]]) -> dict[str, Any]:
    payload = row.structured_payload_json or {}
    reasons = sorted({item["reason"] for item in weak_checks if item["reason"]} or {"missing evidence"})
    return {
        "knowledge_object_id": row.knowledge_object_id,
        "canonical_key": row.canonical_key,
        "equipment_class_id": row.ontology_class_id,
        "knowledge_object_type": row.knowledge_object_type,
        "title": row.title or payload.get("title"),
        "section_id": payload.get("section_id"),
        "trust_level": row.trust_level,
        "confidence_score": row.confidence_score,
        "reasons": reasons,
        "weak_evidence_samples": [sample_evidence(item) for item in weak_checks[:3]],
    }


def sample_evidence(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_no": item.get("page_no"),
        "chunk_id": item.get("chunk_id"),
        "reason": item.get("reason"),
        "evidence_text": str(item.get("evidence_text") or "")[:500],
    }


def build_report(rows: list[KnowledgeObjectV2], evidence: dict[str, list[KnowledgeObjectEvidenceV2]]) -> dict[str, Any]:
    findings = [finding for row in rows if (finding := audit_row(row, evidence.get(row.knowledge_object_id, [])))]
    return {
        "audit_mode": "ashrae_g36_evidence_quality",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "standard_id": STANDARD_ID,
        "row_count": len(rows),
        "weak_row_count": len(findings),
        "weak_rate": round(len(findings) / len(rows) * 100, 2) if rows else 0.0,
        "by_reason": reason_counts(findings),
        "by_type": dict(Counter(item["knowledge_object_type"] for item in findings)),
        "by_equipment_class": dict(Counter(item["equipment_class_id"] for item in findings)),
        "findings": sorted(findings, key=finding_sort_key),
    }


def reason_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in findings:
        counter.update(item["reasons"])
    return dict(counter)


def finding_sort_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (str(item.get("equipment_class_id")), str(item.get("knowledge_object_type")), str(item.get("canonical_key")))


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ASHRAE G36 Evidence Quality Audit",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Rows audited: {report['row_count']}",
        f"- Weak rows: {report['weak_row_count']} ({report['weak_rate']}%)",
        f"- By reason: {format_counter(report['by_reason'])}",
        f"- By type: {format_counter(report['by_type'])}",
        f"- By equipment: {format_counter(report['by_equipment_class'])}",
        "",
        "## Findings",
        "",
    ]
    for index, item in enumerate(report["findings"][:100], start=1):
        lines.extend(render_finding(index, item))
    if len(report["findings"]) > 100:
        lines.append(f"_Markdown truncated: {len(report['findings']) - 100} more findings in JSON._")
    return "\n".join(lines)


def format_counter(counter: dict[str, int]) -> str:
    return ", ".join(f"{key}: {value}" for key, value in sorted(counter.items())) or "none"


def render_finding(index: int, item: dict[str, Any]) -> list[str]:
    sample = item["weak_evidence_samples"][0] if item["weak_evidence_samples"] else {}
    return [
        f"### {index}. {item['title']}",
        "",
        f"- Key: `{item['canonical_key']}`",
        f"- Scope: `{item['equipment_class_id']}` / `{item['knowledge_object_type']}` / §{item.get('section_id')} / {item.get('trust_level')}",
        f"- Reasons: {', '.join(item['reasons'])}",
        f"- Sample p{sample.get('page_no')}: {sample.get('evidence_text')}",
        "",
    ]


def write_outputs(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "evidence_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "EVIDENCE_QUALITY_REPORT.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def default_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("workspace/ashrae_g36_evidence_quality") / stamp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows, evidence = load_g36_rows()
    report = build_report(rows, evidence)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    write_outputs(output_dir, report)
    print(
        f"evidence_quality weak={report['weak_row_count']}/{report['row_count']} "
        f"rate={report['weak_rate']}% report={output_dir / 'EVIDENCE_QUALITY_REPORT.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
