#!/usr/bin/env python3
"""Cleanup batch 1 for structural over-merge audit findings."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.cross_source_merger import assert_valid_ko_identity
from packages.compiler.llm_compiler import _knowledge_type_prefix, _slugify_part
from packages.db.session import SessionLocal


STRUCTURAL_IDS = {
    "ko_11becc6d84e45ec3",
    "ko_2a48a81c382ba634",
    "ko_591ae739b27c71b9",
    "ko_eb13c84bd93a04e3",
    "ko_4e94733f46e8b8a1",
    "ko_33a96a59e127e69a",
    "ko_6718ae939ea97fff",
    "ko_4f473c89ca544582",
}

VALUE_DISAGREEMENT_IDS = {
    "ko_1d071b6223568b3b",
    "ko_534fd0c2b1bac8ab",
    "ko_bdb23b9ca27b48e5",
    "ko_2d3b188217c0b0d4",
    "ko_4fe798a5fee250e2",
    "ko_d9a76c77bbe67132",
    "ko_bd10ecd70736fb0b",
}

AGREED_IDS = {
    "ko_2b176becc0c0144b",
    "ko_206163c136ed5d4b",
}

GARBAGE_IDS = {
    "ko_01a4a4047927d344",
    "ko_75c3a5d18c8eaa43",
}


def _json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if value is not None else {}


def _layers(row: dict[str, Any]) -> list[dict[str, Any]]:
    payload = _json(row.get("authority_summary_json"))
    if not isinstance(payload, dict):
        return []
    return [layer for layer in payload.get("layers", []) if isinstance(layer, dict)]


def _primary_doc_id(row: dict[str, Any]) -> str:
    for layer in _layers(row):
        doc_id = str(layer.get("doc_id") or "").strip()
        if doc_id:
            return doc_id
    return str(row.get("evidence_doc_id") or "").strip()


def _text_for_route(row: dict[str, Any], doc: dict[str, Any] | None) -> str:
    parts = [
        row.get("title"),
        row.get("canonical_key"),
        row.get("structured_payload_json"),
        row.get("authority_summary_json"),
    ]
    if doc:
        parts.extend([
            doc.get("file_name"),
            doc.get("vendor_brand"),
            doc.get("publisher"),
            doc.get("authority_metadata_json"),
        ])
    return " ".join(json.dumps(part, ensure_ascii=False) if isinstance(part, (dict, list)) else str(part or "") for part in parts).lower()


def infer_ontology_class(row: dict[str, Any], doc: dict[str, Any] | None) -> str:
    text = _text_for_route(row, doc)
    if any(term in text for term in ("standard", "ashrae", "ahri", "gb/t", "gb ")):
        return "standard_reference"
    if "etw" in text or "高温水源热泵" in text or "水源热泵" in text or "水地源热泵" in text:
        return "water_source_heat_pump"
    ahu_terms = ("空气处理", "air handling", "ahu", "空调箱", "组合式", "直膨", "吊顶")
    chiller_terms = ("冷水机", "冷水", "冰水机", "螺杆", "离心", "chiller", "水源热泵")
    if any(term in text for term in ahu_terms) and not any(term in text for term in chiller_terms):
        return "ahu"
    if "磁悬浮" in text or "magnetic" in text or "wmc" in text or "wme" in text:
        return "magnetic_bearing_chiller"
    if "风冷" in text and ("热泵" in text or "模块" in text or "涡旋" in text):
        return "air_cooled_modular_heat_pump"
    if "涡旋" in text or "scroll" in text:
        return "air_cooled_modular_heat_pump"
    if "螺杆" in text or "screw" in text:
        return "screw_chiller"
    if "离心" in text or "centrifugal" in text or "wsc" in text or "wdc" in text or "wcc" in text:
        return "centrifugal_chiller"
    if any(term in text for term in ahu_terms):
        return "ahu"
    return "chiller"


def _canonical_base(row: dict[str, Any], ontology_class_id: str) -> str:
    title = str(row.get("title") or "").strip()
    payload = _json(row.get("structured_payload_json"))
    if isinstance(payload, dict):
        title = title or str(payload.get("parameter_name") or payload.get("title") or "").strip()
    slug = _slugify_part(title) or _slugify_part(str(row.get("knowledge_object_id") or "unknown"))
    type_prefix = _knowledge_type_prefix(str(row.get("knowledge_object_type") or "parameter_spec"))
    return f"hvac:{ontology_class_id}:{type_prefix}:{slug}"


def _unique_key(session: Any, base_key: str, ko_id: str, reserved: set[str]) -> str:
    candidate = base_key
    counter = 2
    while candidate in reserved or session.execute(
        text(
            "SELECT 1 FROM knowledge_object "
            "WHERE canonical_key = :key AND knowledge_object_id <> :ko_id LIMIT 1"
        ),
        {"key": candidate, "ko_id": ko_id},
    ).first():
        candidate = f"{base_key}_{counter}"
        counter += 1
    reserved.add(candidate)
    return candidate


def _with_ontology_payload(payload: Any, ontology_class_id: str) -> Any:
    if not isinstance(payload, dict):
        return payload
    updated = dict(payload)
    for key in ("ontology_class_id", "equipment_class_id"):
        if key in updated or key == "equipment_class_id":
            updated[key] = ontology_class_id
    for key in ("ontology_class_key", "equipment_class_key"):
        if key in updated:
            updated[key] = f"hvac:{ontology_class_id}"
    return updated


def _load_blank_rows(session: Any) -> list[dict[str, Any]]:
    rows = session.execute(text(
        "SELECT ko.*, "
        "(SELECT ev.doc_id FROM knowledge_object_evidence ev "
        " WHERE ev.knowledge_object_id = ko.knowledge_object_id "
        " ORDER BY ev.created_at, ev.knowledge_evidence_id LIMIT 1) AS evidence_doc_id "
        "FROM knowledge_object ko "
        "WHERE ko.ontology_class_id = '' OR ko.canonical_key LIKE 'hvac::%' "
        "ORDER BY ko.knowledge_object_id"
    )).mappings().all()
    return [dict(row) for row in rows]


def _load_docs(session: Any, doc_ids: set[str]) -> dict[str, dict[str, Any]]:
    if not doc_ids:
        return {}
    rows = session.execute(
        text(
            "SELECT doc_id, file_name, vendor_brand, publisher, authority_metadata_json "
            "FROM document WHERE doc_id = ANY(:doc_ids)"
        ),
        {"doc_ids": list(doc_ids)},
    ).mappings().all()
    return {row["doc_id"]: dict(row) for row in rows}


def _snapshot(session: Any, ko_ids: set[str]) -> dict[str, dict[str, Any]]:
    rows = session.execute(
        text(
            "SELECT knowledge_object_id, ontology_class_id, canonical_key, "
            "consensus_state, review_status, title "
            "FROM knowledge_object WHERE knowledge_object_id = ANY(:ko_ids)"
        ),
        {"ko_ids": list(ko_ids)},
    ).mappings().all()
    return {row["knowledge_object_id"]: dict(row) for row in rows}


def run_cleanup(session: Any, *, dry_run: bool = False) -> dict[str, Any]:
    target_ids = STRUCTURAL_IDS | VALUE_DISAGREEMENT_IDS | AGREED_IDS | GARBAGE_IDS
    before_targets = _snapshot(session, target_ids)
    blank_rows = _load_blank_rows(session)
    docs = _load_docs(session, {_primary_doc_id(row) for row in blank_rows if _primary_doc_id(row)})
    reserved: set[str] = set()
    structural_changes = []

    for row in blank_rows:
        ko_id = row["knowledge_object_id"]
        doc = docs.get(_primary_doc_id(row))
        ontology_class_id = infer_ontology_class(row, doc)
        base_key = _canonical_base(row, ontology_class_id)
        canonical_key = _unique_key(session, base_key, ko_id, reserved)
        structured_payload = _with_ontology_payload(_json(row.get("structured_payload_json")), ontology_class_id)
        assert_valid_ko_identity(
            {"ontology_class_id": ontology_class_id, "canonical_key": canonical_key},
            context=f"cleanup structural {ko_id}",
        )
        structural_changes.append({
            "knowledge_object_id": ko_id,
            "title": row.get("title"),
            "old_ontology_class_id": row.get("ontology_class_id"),
            "new_ontology_class_id": ontology_class_id,
            "old_canonical_key": row.get("canonical_key"),
            "new_canonical_key": canonical_key,
            "primary_doc_id": _primary_doc_id(row),
            "primary_file_name": doc.get("file_name") if doc else "",
        })
        if not dry_run:
            session.execute(
                text(
                    "UPDATE knowledge_object SET ontology_class_id = :ontology, "
                    "ontology_class_key = :ontology_key, canonical_key = :canonical_key, "
                    "structured_payload_json = :payload "
                    "WHERE knowledge_object_id = :ko_id"
                ),
                {
                    "ontology": ontology_class_id,
                    "ontology_key": f"hvac:{ontology_class_id}",
                    "canonical_key": canonical_key,
                    "payload": json.dumps(structured_payload, ensure_ascii=False),
                    "ko_id": ko_id,
                },
            )

    if not dry_run and STRUCTURAL_IDS:
        session.execute(
            text("UPDATE knowledge_object SET consensus_state = 'value_disagreement' WHERE knowledge_object_id = ANY(:ids)"),
            {"ids": list(STRUCTURAL_IDS)},
        )
    if not dry_run and VALUE_DISAGREEMENT_IDS:
        session.execute(
            text("UPDATE knowledge_object SET consensus_state = 'value_disagreement' WHERE knowledge_object_id = ANY(:ids)"),
            {"ids": list(VALUE_DISAGREEMENT_IDS)},
        )
    if not dry_run and AGREED_IDS:
        session.execute(
            text("UPDATE knowledge_object SET consensus_state = 'agreed' WHERE knowledge_object_id = ANY(:ids)"),
            {"ids": list(AGREED_IDS)},
        )
    if not dry_run and GARBAGE_IDS:
        session.execute(
            text("UPDATE knowledge_object SET review_status = 'rejected' WHERE knowledge_object_id = ANY(:ids)"),
            {"ids": list(GARBAGE_IDS)},
        )

    after_targets = _snapshot(session, target_ids) if dry_run else {}
    if not dry_run:
        session.flush()
        after_targets = _snapshot(session, target_ids)

    return {
        "dry_run": dry_run,
        "structural_total": len(structural_changes),
        "structural_audit_ids": sorted(STRUCTURAL_IDS),
        "state_value_disagreement": sorted(VALUE_DISAGREEMENT_IDS),
        "state_agreed": sorted(AGREED_IDS),
        "garbage_rejected": sorted(GARBAGE_IDS),
        "before_targets": before_targets,
        "after_targets": after_targets,
        "structural_changes": structural_changes,
        "structural_by_ontology": dict(Counter(row["new_ontology_class_id"] for row in structural_changes)),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    session = SessionLocal()
    try:
        result = run_cleanup(session, dry_run=args.dry_run)
        if args.dry_run:
            session.rollback()
        else:
            session.commit()
        _write_csv(output_dir / "structural_changes.csv", result["structural_changes"])
        (output_dir / "cleanup_summary.json").write_text(
            json.dumps({**result, "generated_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "dry_run": args.dry_run,
            "structural_total": result["structural_total"],
            "structural_by_ontology": result["structural_by_ontology"],
            "output_dir": str(output_dir),
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
