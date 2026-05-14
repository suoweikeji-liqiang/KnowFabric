"""Apply review-pack candidates to persisted knowledge objects and evidence anchors.

Task E (docs/36 §4.2): apply_with_merger routes candidates through
merge_with_existing for cross-source dedup instead of direct INSERT.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
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


# --- Task E: merger-aware apply path (docs/36 §4.2) ---


def _candidate_evidence(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    nested = _nested_chain_evidence(candidate)
    if nested:
        return [nested]

    evidence = candidate.get("evidence") or []
    if isinstance(evidence, dict):
        evidence = [evidence]
    if not evidence and candidate.get("chunk_id"):
        evidence = [candidate]

    ev_dicts = []
    for ev in evidence:
        if isinstance(ev, dict):
            ev_dicts.append({
                "chunk_id": ev.get("chunk_id", ""),
                "doc_id": ev.get("doc_id", ""),
                "page_id": ev.get("page_id", ""),
                "page_no": ev.get("page_no", 0),
                "evidence_text": ev.get("evidence_text", ""),
                "evidence_role": ev.get("evidence_role", "primary"),
            })
    return ev_dicts


def _nested_chain_evidence(candidate: dict[str, Any]) -> dict[str, Any] | None:
    chunk = candidate.get("chunk")
    page = candidate.get("page")
    doc = candidate.get("doc")
    evidence = candidate.get("evidence")
    if not all(isinstance(item, dict) for item in (chunk, page, doc, evidence)):
        return None
    if not chunk.get("chunk_id"):
        return None
    return {
        "chunk_id": chunk.get("chunk_id", ""),
        "doc_id": doc.get("doc_id", ""),
        "page_id": page.get("page_id", ""),
        "page_no": page.get("page_no", 0),
        "evidence_text": evidence.get("evidence_text", ""),
        "evidence_role": evidence.get("evidence_role", "primary"),
    }


def candidate_to_merger_dict(candidate: dict[str, Any]) -> dict[str, Any]:
    """Convert a review-pack candidate entry to the dict format merge_candidates expects.

    Ensures evidence[].doc_id is doc_xxx format (D2 fix).
    """
    ev_dicts = _candidate_evidence(candidate)

    authority = candidate.get("authority_summary_json") or {}
    layers = authority.get("layers", []) if isinstance(authority, dict) else []
    first_layer = layers[0] if layers else {}

    return {
        "title": candidate.get("title") or candidate.get("canonical_key", ""),
        "summary": candidate.get("summary", ""),
        "structured_payload": candidate.get("structured_payload") or candidate.get("structured_payload_candidate") or {},
        "confidence_score": candidate.get("confidence_score") or 0.85,
        "trust_level": candidate.get("trust_level", "L3"),
        "authority_level": first_layer.get("authority_level") or "unspecified",
        "publisher": first_layer.get("publisher") or candidate.get("publisher"),
        "citation": first_layer.get("citation"),
        "evidence": ev_dicts,
    }


def apply_with_merger(
    session: Any,
    verified_candidates: list[dict[str, Any]],
    *,
    domain_id: str = "hvac",
    equipment_class_id: str = "",
    ontology_class_key: str = "",
    knowledge_object_type: str = "parameter_spec",
    backend_name: str | None = None,
    package_version: str = "2.0.0-alpha",
    ontology_version: str = "2.0.0-alpha",
) -> dict[str, Any]:
    """Apply verified review-pack candidates through merge_with_existing.

    Groups candidates by (equipment_class_id, knowledge_object_type),
    converts to merger dicts, and calls merge_with_existing per group.

    Returns stats dict: {new_merged, updated_existing, material_conflicts, groups_processed}.
    """
    from packages.compiler.cross_source_merger import merge_with_existing

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for cand in verified_candidates:
        ec_id = equipment_class_id or cand.get("equipment_class_id") or cand.get("ontology_class_id", "")
        ko_type = knowledge_object_type or cand.get("knowledge_object_type", "parameter_spec")
        grouped[(ec_id, ko_type)].append(cand)

    total_stats = {"new_merged": 0, "updated_existing": 0, "material_conflicts": 0, "groups_processed": 0}

    for (ec_id, ko_type), cands in grouped.items():
        merger_dicts = [candidate_to_merger_dict(c) for c in cands]
        ock = ontology_class_key or f"hvac:{ec_id}"
        stats = merge_with_existing(
            session=session,
            new_candidates=merger_dicts,
            domain_id=domain_id,
            equipment_class_id=ec_id,
            ontology_class_key=ock,
            knowledge_object_type=ko_type,
            backend_name=backend_name,
            package_version=package_version,
            ontology_version=ontology_version,
        )
        for k in ("new_merged", "updated_existing", "material_conflicts"):
            total_stats[k] += stats.get(k, 0)
        total_stats["groups_processed"] += 1

    return total_stats
