"""Apply review-pack candidates to persisted knowledge objects and evidence anchors."""

from __future__ import annotations

import hashlib
from typing import Any


def visual_evidence_id(knowledge_object_id: str, page_image_id: str, evidence_role: str) -> str:
    raw = f"{knowledge_object_id}:{page_image_id}:{evidence_role}"
    return f"vev_{hashlib.sha1(raw.encode()).hexdigest()[:14]}"


def build_visual_evidence_rows(
    knowledge_object_id: str,
    visual_refs: list[dict[str, Any]],
    *,
    default_role: str = "primary_visual",
    default_model: str | None = None,
) -> list[dict[str, Any]]:
    """Build VisualEvidenceAnchorV2 rows from candidate visual references.

    Args:
        knowledge_object_id: The KO these visual anchors attach to.
        visual_refs: List of dicts with keys matching visual_evidence_anchor columns
            (page_image_id required, others optional).
        default_role: Default evidence_role if not specified in ref.
        default_model: Default model_used if not specified in ref.

    Returns:
        List of row dicts ready for insertion into visual_evidence_anchor table.
    """
    rows = []
    for ref in visual_refs:
        page_image_id = ref.get("page_image_id") or ref.get("visual_evidence_id") or ""
        if not page_image_id:
            continue
        role = ref.get("evidence_role") or default_role
        vev_id = visual_evidence_id(knowledge_object_id, page_image_id, role)
        rows.append({
            "visual_evidence_id": vev_id,
            "knowledge_object_id": knowledge_object_id,
            "page_image_id": page_image_id,
            "doc_id": ref.get("doc_id", ""),
            "page_id": ref.get("page_id", ""),
            "page_no": ref.get("page_no") or 0,
            "bbox": ref.get("bbox"),
            "evidence_role": role,
            "extracted_entities_json": ref.get("extracted_entities_json") or ref.get("extracted_entities"),
            "extracted_relationships_json": ref.get("extracted_relationships_json") or ref.get("extracted_relationships"),
            "model_used": ref.get("model_used") or default_model,
            "confidence": ref.get("confidence"),
        })
    return rows


def apply_visual_evidence(
    session: Any,
    knowledge_object_id: str,
    visual_refs: list[dict[str, Any]],
    *,
    default_model: str | None = None,
) -> int:
    """Write visual evidence anchor rows for one KO.

    Skips rows that already exist (by unique constraint on
    knowledge_object_id + page_image_id + evidence_role).

    Returns count of newly inserted rows.
    """
    from packages.db.models_v2 import VisualEvidenceAnchorV2

    rows = build_visual_evidence_rows(
        knowledge_object_id,
        visual_refs,
        default_model=default_model,
    )
    inserted = 0
    for row in rows:
        existing = (
            session.query(VisualEvidenceAnchorV2)
            .filter(VisualEvidenceAnchorV2.visual_evidence_id == row["visual_evidence_id"])
            .first()
        )
        if existing is None:
            session.add(VisualEvidenceAnchorV2(**row))
            inserted += 1
    if inserted:
        session.flush()
    return inserted
