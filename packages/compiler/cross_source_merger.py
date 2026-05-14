"""Merge knowledge object candidates from multiple sources into authority-layered KOs.

Groups candidates by canonical_key, compares values across sources, determines
consensus_state, and produces merged KO + evidence rows ready for persistence.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from packages.compiler.authority_arbitration import arbitrate
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
MERGER_MAX_GROUP_CANDIDATES = 5  # E3: only for LLM path. Embedding path handles grouping via clustering.


def _dedupe_and_migrate_evidence(session: Any, *, target_id: str, src_id: str) -> None:
    """Move evidence between KOs without violating the evidence ref uniqueness."""

    if target_id == src_id:
        return

    sql_text = __import__('sqlalchemy').text
    session.execute(
        sql_text(
            "DELETE FROM knowledge_object_evidence AS duplicate "
            "USING knowledge_object_evidence AS kept "
            "WHERE duplicate.knowledge_object_id = :src "
            "AND kept.knowledge_object_id = :src "
            "AND duplicate.knowledge_evidence_id > kept.knowledge_evidence_id "
            "AND duplicate.chunk_id = kept.chunk_id "
            "AND duplicate.evidence_role = kept.evidence_role"
        ),
        {"src": src_id},
    )
    session.execute(
        sql_text(
            "DELETE FROM knowledge_object_evidence AS src_ev "
            "WHERE src_ev.knowledge_object_id = :src "
            "AND EXISTS ("
            "  SELECT 1 FROM knowledge_object_evidence AS target_ev "
            "  WHERE target_ev.knowledge_object_id = :target "
            "  AND target_ev.chunk_id = src_ev.chunk_id "
            "  AND target_ev.evidence_role = src_ev.evidence_role"
            ")"
        ),
        {"target": target_id, "src": src_id},
    )
    session.execute(
        sql_text(
            "UPDATE knowledge_object_evidence "
            "SET knowledge_object_id = :target "
            "WHERE knowledge_object_id = :src"
        ),
        {"target": target_id, "src": src_id},
    )


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

    # E3 defensive sanity: force-split pathological groups (LLM path only)
    # Embedding-first path handles grouping via clustering — trust it.
    import os as _os
    if _os.environ.get("KNOWFABRIC_USE_EMBEDDING_FIRST", "1") != "1":
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

            for ev_idx, ev in enumerate(cand_evidence):
                auth_role = _resolve_authority_role(authority_level, is_primary)
                evidence_rows.append({
                    "chunk_id": ev.get("chunk_id", ""),
                    "doc_id": ev.get("doc_id", doc_id),
                    "page_id": ev.get("page_id", ""),
                    "page_no": ev.get("page_no", 0),
                    "evidence_text": ev.get("evidence_text", ""),
                    "evidence_role": f"primary_{auth_role}" if is_primary and ev_idx == 0 else f"supporting_{auth_role}",
                    "authority_role": auth_role,
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
        deviation_justification = {
            "authority_arbitration": arbitrate(layers),
        }
        first_payload = group[0].get("structured_payload") or group[0].get("structured_payload_candidate") or {}

        # Collect all source names for N1 name-based matching
        source_names = []
        for cand in group:
            payload = cand.get("structured_payload") or cand.get("structured_payload_candidate") or {}
            name = payload.get("parameter_name") or cand.get("title", "")
            if name:
                source_names.append(str(name).strip())

        merged.append({
            "domain_id": domain_id,
            "ontology_class_key": ontology_class_key,
            "ontology_class_id": equipment_class_id,
            "knowledge_object_type": knowledge_object_type,
            "canonical_key": canonical_key,
            "title": title,
            "_source_names": list(dict.fromkeys(source_names)),
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
            "deviation_justification_json": deviation_justification,
            "package_version": package_version,
            "ontology_version": ontology_version,
            "evidence_rows": evidence_rows,
        })

    return merged


def _ko_to_candidate(ko_row, session=None) -> dict[str, Any]:
    """Convert a KnowledgeObjectV2 ORM row to a candidate dict for the merger.

    L2 fix: query evidence rows via session (model has no evidence_rows relationship).
    """
    payload = ko_row.structured_payload_json or {}
    authority = ko_row.authority_summary_json or {}
    layers = authority.get("layers", []) if isinstance(authority, dict) else []
    first_layer = layers[0] if layers else {}

    evidence = []
    if session is not None:
        from packages.db.models_v2 import KnowledgeObjectEvidenceV2
        ev_rows = session.query(KnowledgeObjectEvidenceV2).filter(
            KnowledgeObjectEvidenceV2.knowledge_object_id == ko_row.knowledge_object_id
        ).all()
        for ev in ev_rows:
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
        "evidence": evidence,
    }


def _looks_like_parameter_name(text: str) -> bool:
    import re

    cleaned = str(text or "").strip()
    if len(cleaned) < 2:
        return False
    if re.search(r"[\u4e00-\u9fff]{2,}", cleaned):
        return True
    if re.search(r"[A-Za-z].*[A-Za-z]", cleaned):
        return True
    return False


def _source_name_from_evidence(evidence_text: str, fallback: str) -> str:
    cleaned = str(evidence_text or "").strip()
    if not cleaned:
        return fallback

    first_line = cleaned.splitlines()[0].strip()
    if _looks_like_parameter_name(first_line):
        return first_line[:120]
    return fallback


def _ko_to_candidates(ko_row, session=None) -> list[dict[str, Any]]:
    base = _ko_to_candidate(ko_row, session=session)
    payload = dict(base.get("structured_payload") or {})
    fallback_name = str(payload.get("parameter_name") or ko_row.title or "").strip()
    evidence_rows = list(base.get("evidence") or [])
    if not evidence_rows:
        return [base]

    authority = ko_row.authority_summary_json or {}
    layers = authority.get("layers", []) if isinstance(authority, dict) else []
    layer_by_doc = {
        str(layer.get("doc_id")): layer
        for layer in layers
        if isinstance(layer, dict) and layer.get("doc_id")
    }

    expanded: list[dict[str, Any]] = []
    for ev in evidence_rows:
        layer = layer_by_doc.get(str(ev.get("doc_id") or ""), {})
        ev_payload = dict(payload)
        layer_name = str(layer.get("value_summary") or "").strip()
        ev_payload["parameter_name"] = layer_name if _looks_like_parameter_name(layer_name) else fallback_name
        expanded.append({
            **base,
            "title": ev_payload["parameter_name"] or base.get("title"),
            "structured_payload": ev_payload,
            "authority_level": layer.get("authority_level", base.get("authority_level")),
            "publisher": layer.get("publisher", base.get("publisher")),
            "citation": layer.get("citation", base.get("citation")),
            "evidence": [ev],
        })
    return expanded


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

    # N1: name-based matching (not canonical_key)
    existing_candidates = []
    existing_by_name: dict[str, str] = {}  # parameter_name → knowledge_object_id
    for ko in existing_kos:
        ko_candidates = _ko_to_candidates(ko, session=session)
        existing_candidates.extend(ko_candidates)
        for cand in ko_candidates:
            payload = cand.get("structured_payload") or {}
            name = payload.get("parameter_name") or cand.get("title") or ""
            if name:
                existing_by_name[str(name).strip()] = ko.knowledge_object_id

    # L1 diagnostic: dump what reaches the merger
    _dump_merger_input(existing_candidates, new_candidates, equipment_class_id, knowledge_object_type)

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

    stats = {"new_merged": 0, "updated_existing": 0, "merged_existing": 0, "material_conflicts": 0}

    for ko_dict in merged:
        canonical_key = ko_dict["canonical_key"]
        evidence_rows = ko_dict.pop("evidence_rows", [])

        # N1: name-based matching — use _source_names from merge_candidates
        member_names = set(ko_dict.pop("_source_names", []))
        if not member_names:
            member_names.add(ko_dict.get("title", ""))

        matched_ids = set()
        for name in member_names:
            if name in existing_by_name:
                matched_ids.add(existing_by_name[name])

        if len(matched_ids) >= 2:
            # N1: multiple old KOs merge into one → keep earliest, migrate others
            target_id = min(matched_ids)
            ko_dict["knowledge_object_id"] = target_id
            for src_id in matched_ids - {target_id}:
                _dedupe_and_migrate_evidence(session, target_id=target_id, src_id=src_id)
                session.execute(
                    __import__('sqlalchemy').text("DELETE FROM knowledge_object WHERE knowledge_object_id = :src"),
                    {"src": src_id}
                )
            stats["merged_existing"] += 1
        elif len(matched_ids) == 1:
            # N1: single match → update existing KO
            ko_dict["knowledge_object_id"] = matched_ids.pop()
            stats["updated_existing"] += 1
        else:
            # N1: no match → genuinely new concept
            ko_dict["knowledge_object_id"] = _generate_ko_id(
                domain_id, equipment_class_id, knowledge_object_type, canonical_key
            )
            stats["new_merged"] += 1

        if ko_dict["consensus_state"] == "material_conflict":
            ko_dict["review_status"] = "conflict_review_required"
            stats["material_conflicts"] += 1

        # Preserve primary_chunk_id if missing
        if not ko_dict.get("primary_chunk_id"):
            existing = session.query(KnowledgeObjectV2).filter(
                KnowledgeObjectV2.knowledge_object_id == ko_dict["knowledge_object_id"]
            ).first()
            if existing and existing.primary_chunk_id:
                ko_dict["primary_chunk_id"] = existing.primary_chunk_id

        # Handle canonical_key conflicts: if another KO already has this ck, merge them
        ck_conflict = session.query(KnowledgeObjectV2).filter(
            KnowledgeObjectV2.canonical_key == canonical_key,
            KnowledgeObjectV2.knowledge_object_id != ko_dict["knowledge_object_id"],
            KnowledgeObjectV2.ontology_class_id == equipment_class_id,
        ).first()
        if ck_conflict:
            # Migrate evidence from conflict KO to this one, then delete conflict
            _dedupe_and_migrate_evidence(
                session,
                target_id=ko_dict["knowledge_object_id"],
                src_id=ck_conflict.knowledge_object_id,
            )
            session.execute(
                __import__('sqlalchemy').text("DELETE FROM knowledge_object WHERE knowledge_object_id = :src"),
                {"src": ck_conflict.knowledge_object_id}
            )

        session.merge(KnowledgeObjectV2(**ko_dict))
        session.flush()

        session.query(KnowledgeObjectEvidenceV2).filter(
            KnowledgeObjectEvidenceV2.knowledge_object_id == ko_dict["knowledge_object_id"]
        ).delete()
        session.flush()

        for idx, ev in enumerate(evidence_rows):
            ev_src = f"{ev.get('chunk_id', '')}:{ev.get('evidence_role', 'supporting')}:{idx}"
            ev_id = _generate_evidence_id(ko_dict["knowledge_object_id"], ev_src, "")
            session.execute(
                __import__('sqlalchemy').text(
                    "INSERT INTO knowledge_object_evidence (knowledge_evidence_id, knowledge_object_id, "
                    "chunk_id, doc_id, page_id, page_no, evidence_text, evidence_role, "
                    "authority_role, evidence_citation, confidence_score) "
                    "VALUES (:eid, :kid, :cid, :did, :pid, :pno, :text, :role, :arole, :cite, :conf) "
                    "ON CONFLICT ON CONSTRAINT uq_knowledge_object_evidence_ref DO NOTHING"
                ),
                {"eid": ev_id, "kid": ko_dict["knowledge_object_id"],
                 "cid": ev.get("chunk_id", ""), "did": ev.get("doc_id", ""),
                 "pid": ev.get("page_id", ""), "pno": ev.get("page_no", 0),
                 "text": ev.get("evidence_text", ""), "role": ev.get("evidence_role", "primary"),
                 "arole": ev.get("authority_role", ""), "cite": ev.get("evidence_citation", ""),
                 "conf": ev.get("confidence_score", ko_dict.get("confidence_score"))},
            )

    session.commit()
    return stats


def _dump_merger_input(
    existing_candidates: list[dict[str, Any]],
    new_candidates: list[dict[str, Any]],
    equipment_class_id: str,
    knowledge_object_type: str,
) -> None:
    """L1: Dump what candidates reach merge_with_existing."""
    import json as _json
    import os as _os
    from datetime import datetime as _dt, timezone as _tz
    from pathlib import Path as _Path

    run_id = _dt.now(_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = _Path(f"output/diagnostic/{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)

    existing_names = []
    by_doc: dict[str, int] = {}
    for c in existing_candidates:
        payload = c.get("structured_payload") or {}
        name = payload.get("parameter_name") or c.get("title", "")
        existing_names.append(str(name))
        for ev in c.get("evidence", []):
            did = ev.get("doc_id", "?")
            by_doc[did] = by_doc.get(did, 0) + 1

    new_names = []
    for c in new_candidates:
        payload = c.get("structured_payload") or {}
        name = payload.get("parameter_name") or c.get("title", "")
        new_names.append(str(name))

    entry = {
        "anchor": equipment_class_id,
        "type": knowledge_object_type,
        "existing_count": len(existing_candidates),
        "new_count": len(new_candidates),
        "sample_existing_names": existing_names[:20],
        "sample_new_names": new_names[:20],
        "by_doc_existing": by_doc,
    }
    with open(out_dir / "merger_input.jsonl", "a", encoding="utf-8") as f:
        f.write(_json.dumps(entry, ensure_ascii=False) + "\n")


def _generate_ko_id(domain_id: str, equipment_class_id: str, knowledge_object_type: str, canonical_key: str) -> str:
    raw = f"{domain_id}:{equipment_class_id}:{knowledge_object_type}:{canonical_key}"
    return f"ko_{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def _generate_evidence_id(knowledge_object_id: str, chunk_id: str, evidence_role: str) -> str:
    raw = f"{knowledge_object_id}:{chunk_id}:{evidence_role}"
    return f"koev_{hashlib.sha1(raw.encode()).hexdigest()[:16]}"
