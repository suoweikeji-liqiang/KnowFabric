"""Merge knowledge object candidates from multiple sources into authority-layered KOs.

Groups candidates by canonical_key, compares values across sources, determines
consensus_state, and produces merged KO + evidence rows ready for persistence.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from packages.compiler.canonical_key import group_and_normalize, resolve_single_name

AUTHORITY_RANK = {
    "field_observation": 6,
    "industry_standard": 5,
    "regulatory_code": 4,
    "oem_manual": 3,
    "vendor_application_note": 2,
    "academic_reference": 1,
    "internal_sop": 0,
    "unspecified": -1,
}

NUMERIC_TOLERANCE = 0.05


def _coerce_numeric(value: Any) -> float | None:
    """Try to convert a value to float for numeric comparison."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            pass
        import re
        match = re.search(r"[-+]?\d+\.?\d*", cleaned)
        if match:
            return float(match.group(0))
    return None


def _values_agree(v1: Any, v2: Any) -> bool:
    """Check if two values agree within tolerance."""
    if v1 is None and v2 is None:
        return True
    if v1 is None or v2 is None:
        return False

    n1, n2 = _coerce_numeric(v1), _coerce_numeric(v2)
    if n1 is not None and n2 is not None:
        if n1 == 0 and n2 == 0:
            return True
        if n1 == 0 or n2 == 0:
            return False
        return abs(n1 - n2) / max(abs(n1), abs(n2)) <= NUMERIC_TOLERANCE

    return str(v1).strip().lower() == str(v2).strip().lower()


def _resolve_authority_role(authority_level: str, is_primary: bool) -> str:
    if authority_level == "industry_standard":
        return "primary_standard" if is_primary else "corroborating_standard"
    if authority_level == "oem_manual":
        return "primary_oem" if is_primary else "corroborating_oem"
    if authority_level == "field_observation":
        return "field_validation"
    return "unspecified"


def _compute_consensus_state(layers: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Determine consensus_state by comparing value_summary across layers."""
    if len(layers) <= 1:
        return "single_source", None

    values = [layer.get("value_summary") for layer in layers]
    base = values[0]

    all_agree = all(_values_agree(base, v) for v in values[1:])
    if all_agree:
        return "agreed", None

    # 2 sources with disagreement → material_conflict
    if len(values) == 2:
        return "material_conflict", "Two sources disagree on value"

    # 3+ sources: majority agree → partial, otherwise material
    agree_count = sum(1 for v in values if _values_agree(base, v))
    if agree_count > len(values) // 2:
        summary = f"{agree_count}/{len(values)} sources agree on value; minority diverges"
        return "partial_conflict", summary

    summary = f"Significant value disagreement across {len(values)} sources"
    return "material_conflict", summary


def _extract_value_summary(candidate: dict[str, Any]) -> str | None:
    """Extract a concise value summary from a candidate's structured payload."""
    payload = candidate.get("structured_payload") or candidate.get("structured_payload_candidate") or {}
    if isinstance(payload, str):
        return payload[:100]
    value = payload.get("value") or payload.get("default_value")
    if value is not None:
        unit = payload.get("unit", "")
        return f"{value}{unit}" if unit else str(value)
    range_min = payload.get("range_min")
    range_max = payload.get("range_max")
    if range_min is not None and range_max is not None:
        return f"[{range_min}, {range_max}]"
    return candidate.get("title") or candidate.get("summary")


def merge_candidates(
    candidates: list[dict[str, Any]],
    *,
    domain_id: str,
    equipment_class_id: str,
    ontology_class_key: str,
    knowledge_object_type: str,
    package_version: str = "2.0.0-alpha",
    ontology_version: str = "2.0.0-alpha",
    backend_name: str | None = None,
) -> list[dict[str, Any]]:
    """Merge a list of verified candidates into authority-layered knowledge objects.

    Each candidate dict must include at minimum:
    - title, summary, confidence_score, trust_level, review_status
    - evidence entries with: doc_id, page_no, chunk_id, evidence_text, evidence_role
    - authority context: authority_level, publisher, citation

    Returns a list of merged KO dicts, each with embedded evidence rows.
    """
    # Step 1: Normalize canonical keys and group
    names_by_candidate = []
    for c in candidates:
        payload = c.get("structured_payload") or c.get("structured_payload_candidate") or {}
        name = payload.get("parameter_name") or c.get("title") or c.get("summary", "")
        names_by_candidate.append(name)

    # Phase 1: LLM-assisted cross-lingual grouping (T1 plumbing fix, docs/35 §T1)
    canonical_map: dict[str, str] = {}
    try:
        canonical_map = group_and_normalize(
            names=names_by_candidate,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
            backend_name=backend_name,
        )
    except Exception:
        canonical_map = {}

    # Phase 2: mechanical fallback for any names LLM didn't cover
    canonical_keys = []
    for name in names_by_candidate:
        key = canonical_map.get(name)
        if not key:
            key = resolve_single_name(
                name,
                domain_id=domain_id,
                equipment_class_id=equipment_class_id,
                knowledge_object_type=knowledge_object_type,
            )
        canonical_keys.append(key)

    groups: dict[str, list[dict[str, Any]]] = {}
    for c, ck in zip(candidates, canonical_keys):
        groups.setdefault(ck, []).append(c)

    # Step 2: Build merged KOs
    merged = []
    for canonical_key, group in groups.items():
        layers = []
        evidence_rows = []
        primary_chunk_id = None
        best_confidence = 0.0
        best_trust = "L1"

        for cand in group:
            authority_level = cand.get("authority_level", "unspecified")
            is_primary = len(layers) == 0
            layer = {
                "authority_level": authority_level,
                "publisher": cand.get("publisher"),
                "citation": cand.get("citation") or cand.get("evidence_citation"),
                "value_summary": _extract_value_summary(cand),
                "evidence_role": "primary" if is_primary else "corroborating",
                "doc_id": cand.get("doc_id"),
            }
            layers.append(layer)

            for ev in cand.get("evidence", []):
                evidence_rows.append({
                    "chunk_id": ev.get("chunk_id", ""),
                    "doc_id": ev.get("doc_id", ""),
                    "page_id": ev.get("page_id", ""),
                    "page_no": ev.get("page_no", 0),
                    "evidence_text": ev.get("evidence_text", ""),
                    "evidence_role": ev.get("evidence_role", "supporting"),
                    "authority_role": _resolve_authority_role(authority_level, is_primary),
                    "evidence_citation": layer["citation"],
                })

            if is_primary:
                primary_chunk_id = ev.get("chunk_id") if evidence_rows else None

            conf = cand.get("confidence_score", 0) or 0
            if conf > best_confidence:
                best_confidence = conf
            trust = cand.get("trust_level", "L1")
            if {"L1": 0, "L2": 1, "L3": 2, "L4": 3}.get(trust, -1) > {"L1": 0, "L2": 1, "L3": 2, "L4": 3}.get(best_trust, -1):
                best_trust = trust

        consensus_state, conflict_summary = _compute_consensus_state(layers)
        highest_authority_level = max(
            layers,
            key=lambda l: AUTHORITY_RANK.get(l["authority_level"], -1),
        )["authority_level"]

        title = group[0].get("title") or canonical_key
        summary_text = group[0].get("summary", "")

        authority_summary = {"layers": layers}
        first_payload = group[0].get("structured_payload") or group[0].get("structured_payload_candidate") or {}

        merged.append({
            "domain_id": domain_id,
            "ontology_class_key": ontology_class_key,
            "ontology_class_id": equipment_class_id,
            "knowledge_object_type": knowledge_object_type,
            "canonical_key": canonical_key,
            "title": title,
            "summary": summary_text,
            "structured_payload_json": first_payload,
            "applicability_json": group[0].get("applicability", {}),
            "confidence_score": best_confidence,
            "trust_level": best_trust,
            "review_status": "pending" if consensus_state == "material_conflict" else "published",
            "primary_chunk_id": primary_chunk_id,
            "authority_summary_json": authority_summary,
            "consensus_state": consensus_state,
            "conflict_summary": conflict_summary,
            "highest_authority_level": highest_authority_level,
            "package_version": package_version,
            "ontology_version": ontology_version,
            "evidence_rows": evidence_rows,
        })

    return merged


def _ko_to_candidate(ko_row) -> dict[str, Any]:
    """Convert a KnowledgeObjectV2 ORM row to a candidate dict for the merger."""
    payload = ko_row.structured_payload_json or {}
    authority = ko_row.authority_summary_json or {}
    layers = authority.get("layers", []) if isinstance(authority, dict) else []
    first_layer = layers[0] if layers else {}

    evidence = []
    if hasattr(ko_row, "evidence_rows") and ko_row.evidence_rows:
        for ev in ko_row.evidence_rows:
            evidence.append({
                "chunk_id": getattr(ev, "chunk_id", ""),
                "doc_id": getattr(ev, "doc_id", ""),
                "page_id": getattr(ev, "page_id", ""),
                "page_no": getattr(ev, "page_no", 0),
                "evidence_text": getattr(ev, "evidence_text", ""),
                "evidence_role": getattr(ev, "evidence_role", "supporting"),
            })

    return {
        "title": ko_row.title,
        "summary": ko_row.summary,
        "structured_payload": payload,
        "confidence_score": ko_row.confidence_score,
        "trust_level": ko_row.trust_level,
        "review_status": ko_row.review_status,
        "authority_level": first_layer.get("authority_level", ko_row.highest_authority_level or "unspecified"),
        "publisher": first_layer.get("publisher"),
        "citation": first_layer.get("citation"),
        "doc_id": None,
        "evidence": evidence,
    }


def merge_with_existing(
    session: Any,
    new_candidates: list[dict[str, Any]],
    *,
    domain_id: str,
    equipment_class_id: str,
    ontology_class_key: str,
    knowledge_object_type: str,
    package_version: str = "2.0.0-alpha",
    ontology_version: str = "2.0.0-alpha",
    backend_name: str | None = None,
) -> dict[str, Any]:
    """Merge new candidates with existing DB KOs and upsert.

    Returns stats dict with: new_merged, updated_existing, material_conflicts.
    """
    from packages.db.models_v2 import KnowledgeObjectEvidenceV2, KnowledgeObjectV2

    # Query existing KOs with same anchor + type
    existing_kos = (
        session.query(KnowledgeObjectV2)
        .filter(KnowledgeObjectV2.ontology_class_id == equipment_class_id)
        .filter(KnowledgeObjectV2.knowledge_object_type == knowledge_object_type)
        .all()
    )

    # Convert existing KOs to candidate dicts
    existing_candidates = []
    ko_id_map: dict[str, str] = {}  # canonical_key → knowledge_object_id
    for ko in existing_kos:
        existing_candidates.append(_ko_to_candidate(ko))
        ko_id_map[ko.canonical_key] = ko.knowledge_object_id

    # Merge all candidates
    all_candidates = existing_candidates + list(new_candidates)
    merged = merge_candidates(
        all_candidates,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        ontology_class_key=ontology_class_key,
        knowledge_object_type=knowledge_object_type,
        package_version=package_version,
        ontology_version=ontology_version,
        backend_name=backend_name,
    )

    stats = {"new_merged": 0, "updated_existing": 0, "material_conflicts": 0}

    for ko_dict in merged:
        canonical_key = ko_dict["canonical_key"]
        evidence_rows = ko_dict.pop("evidence_rows", [])

        # Reuse existing KO ID or generate new one
        if canonical_key in ko_id_map:
            ko_dict["knowledge_object_id"] = ko_id_map[canonical_key]
            stats["updated_existing"] += 1
        else:
            ko_dict["knowledge_object_id"] = _generate_ko_id(
                domain_id, equipment_class_id, knowledge_object_type, canonical_key
            )
            stats["new_merged"] += 1

        if ko_dict["consensus_state"] == "material_conflict":
            ko_dict["review_status"] = "conflict_review_required"
            stats["material_conflicts"] += 1

        session.merge(KnowledgeObjectV2(**ko_dict))
        session.flush()

        # Upsert evidence rows
        for ev in evidence_rows:
            ev_id = _generate_evidence_id(ko_dict["knowledge_object_id"], ev.get("chunk_id", ""), ev.get("evidence_role", "supporting"))
            ev["knowledge_evidence_id"] = ev_id
            ev["knowledge_object_id"] = ko_dict["knowledge_object_id"]
            if "confidence_score" not in ev:
                ev["confidence_score"] = ko_dict.get("confidence_score")
            session.merge(KnowledgeObjectEvidenceV2(**ev))

    session.commit()
    return stats


def _generate_ko_id(domain_id: str, equipment_class_id: str, knowledge_object_type: str, canonical_key: str) -> str:
    raw = f"{domain_id}:{equipment_class_id}:{knowledge_object_type}:{canonical_key}"
    return f"ko_{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def _generate_evidence_id(knowledge_object_id: str, chunk_id: str, evidence_role: str) -> str:
    raw = f"{knowledge_object_id}:{chunk_id}:{evidence_role}"
    return f"koev_{hashlib.sha1(raw.encode()).hexdigest()[:16]}"
