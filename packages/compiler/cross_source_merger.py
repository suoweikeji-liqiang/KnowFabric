"""Merge knowledge object candidates from multiple sources into authority-layered KOs.

Groups candidates by canonical_key, compares values across sources, determines
consensus_state, and produces merged KO + evidence rows ready for persistence.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from packages.compiler.canonical_key import group_and_normalize, resolve_single_name
from packages.compiler.llm_compiler import _hashed_slug, _slugify_part

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


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    return s == "" or s.lower() in ("none", "null", "n/a", "-")


def _values_agree(v1: Any, v2: Any) -> bool:
    """Check if two values agree within tolerance.

    R3: empty values treated as agree (no data to compare).
    R4: temperature °F/°C and pressure psi/bar/kPa/MPa unit conversion.
    """
    # R3: empty-value short-circuit
    if _is_empty(v1) and _is_empty(v2):
        return True
    if _is_empty(v1) or _is_empty(v2):
        return True

    s1, s2 = str(v1).strip(), str(v2).strip()
    if s1.lower() == s2.lower():
        return True

    # R4: temperature unit conversion (°F ↔ °C)
    t1, t2 = _normalize_temperature(s1), _normalize_temperature(s2)
    if t1 is not None and t2 is not None:
        return abs(t1 - t2) / max(abs(t1), abs(t2), 1.0) <= 0.10

    # R4: pressure unit conversion (psi ↔ bar ↔ kPa ↔ MPa)
    p1, p2 = _normalize_pressure(s1), _normalize_pressure(s2)
    if p1 is not None and p2 is not None:
        return abs(p1 - p2) / max(abs(p1), abs(p2), 1.0) <= 0.10

    # Legacy: numeric comparison
    n1, n2 = _coerce_numeric(v1), _coerce_numeric(v2)
    if n1 is not None and n2 is not None:
        if n1 == 0 and n2 == 0:
            return True
        if n1 == 0 or n2 == 0:
            return False
        return abs(n1 - n2) / max(abs(n1), abs(n2)) <= NUMERIC_TOLERANCE

    return False


def _resolve_authority_role(authority_level: str, is_primary: bool) -> str:
    if authority_level == "industry_standard":
        return "primary_standard" if is_primary else "corroborating_standard"
    if authority_level == "oem_manual":
        return "primary_oem" if is_primary else "corroborating_oem"
    if authority_level == "field_observation":
        return "field_validation"
    return "unspecified"


def _normalize_temperature(value_str: str) -> float | None:
    import re
    s = value_str.strip().lower().replace(" ", "")
    m = re.match(r"^(-?\d+\.?\d*)°?([fc])$", s)
    if not m:
        return None
    num = float(m.group(1))
    if m.group(2) == "f":
        return (num - 32) * 5 / 9
    return num


def _normalize_pressure(value_str: str) -> float | None:
    import re
    s = value_str.strip().lower().replace(" ", "")
    m = re.match(r"^(\d+\.?\d*)(psi|bar|mpa|kpa)$", s)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2)
    if unit == "psi":
        return num * 0.0689476
    if unit == "mpa":
        return num * 10
    if unit == "kpa":
        return num / 100
    return num


FACET_KEYWORDS = [
    ("setpoint", ["setpoint", "set point", "set-point", "default", "设定", "设置"]),
    ("limit",    ["limit", "cutout", "max", "min", "maximum", "minimum", "限制", "最高", "最低"]),
    ("alarm",    ["alarm", "warning", "trip", "shutdown", "报警", "保护"]),
    ("range",    ["range", "between", "from", "范围"]),
]
MERGER_MAX_GROUP_CANDIDATES = 5


def _detect_facets(layers: list[dict]) -> set[str]:
    facets = set()
    for layer in layers:
        vs = (layer.get("value_summary") or "").lower()
        for facet, keywords in FACET_KEYWORDS:
            if any(kw in vs for kw in keywords):
                facets.add(facet)
                break
        title = (layer.get("citation") or "").lower()
        for facet, keywords in FACET_KEYWORDS:
            if any(kw in title for kw in keywords):
                facets.add(facet)
                break
    return facets


def _compute_consensus_state(layers: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Determine consensus_state by comparing value_summary across layers.

    R3: empty-value handling. E3: multi-facet detection.
    """
    if len(layers) <= 1:
        return "single_source", None

    # E3: multi-facet detection — same concept different facets, not conflict
    facets = _detect_facets(layers)
    if len(facets) >= 2:
        return "multi_facet", f"covers facets: {sorted(facets)}"

    values = [layer.get("value_summary") for layer in layers]
    non_empty = [v for v in values if not _is_empty(v)]

    # R3: all sources lack explicit values
    if len(non_empty) == 0:
        return "single_value_unknown", "all sources lack explicit values; only parameter name confirmed"

    # R3: only one source has a value → agreed (insufficient data for conflict)
    if len(non_empty) == 1:
        return "agreed", None

    base = non_empty[0]
    all_agree = all(_values_agree(base, v) for v in non_empty[1:])
    if all_agree:
        return "agreed", None

    if len(non_empty) == 2:
        return "material_conflict", "Two sources disagree on value"

    agree_count = sum(1 for v in non_empty if _values_agree(base, v))
    if agree_count > len(non_empty) // 2:
        return "partial_conflict", f"{agree_count}/{len(non_empty)} sources agree on value; minority diverges"

    return "material_conflict", f"Significant value disagreement across {len(non_empty)} sources"


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

    # E3 defensive sanity: force-split pathological groups
    pathological_keys = [k for k, v in groups.items() if len(v) > MERGER_MAX_GROUP_CANDIDATES]
    if pathological_keys:
        for c, ck in zip(candidates, canonical_keys):
            if ck in pathological_keys:
                payload = c.get("structured_payload") or c.get("structured_payload_candidate") or {}
                fallback_name = payload.get("parameter_name") or c.get("title", "unknown")
                slug = _slugify_part(fallback_name) or _hashed_slug(fallback_name)
                idx = candidates.index(c)
                canonical_keys[idx] = slug
        groups = {}
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
            # D2 fix: doc_id must come from evidence (doc_xxx), not KO id (ko_xxx)
            cand_evidence = cand.get("evidence", [])
            doc_id = (
                (cand_evidence[0].get("doc_id") if cand_evidence else None)
                or cand.get("doc_id")
                or ""
            )
            layer = {
                "authority_level": authority_level,
                "publisher": cand.get("publisher"),
                "citation": cand.get("citation") or cand.get("evidence_citation"),
                "value_summary": _extract_value_summary(cand),
                "evidence_role": "primary" if is_primary else "corroborating",
                "doc_id": doc_id,
            }
            layers.append(layer)

            for ev in cand_evidence:
                evidence_rows.append({
                    "chunk_id": ev.get("chunk_id", ""),
                    "doc_id": ev.get("doc_id", doc_id),
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
