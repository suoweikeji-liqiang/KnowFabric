"""Merge knowledge object candidates from multiple sources into authority-layered KOs.

Groups candidates by canonical_key, compares values across sources, determines
consensus_state, and produces merged KO + evidence rows ready for persistence.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Mapping

from packages.compiler.authority_arbitration import arbitrate
from packages.compiler.canonical_key import group_and_normalize, resolve_single_name
from packages.compiler.llm_compiler import _hashed_slug, _knowledge_type_prefix, _slugify_part
from packages.compiler.unit_facet_detector import detect_facet_v2
from packages.core.semantic_contract_v2 import ConsensusState

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
FINAL_MAX_GROUP_LAYERS = 8


def assert_valid_ko_identity(ko: Mapping[str, Any], *, context: str = "knowledge_object") -> None:
    """Fail fast when a KO identity would violate the semantic key contract."""

    ontology_class_id = str(ko.get("ontology_class_id") or "").strip()
    if not ontology_class_id:
        raise ValueError(f"{context}: ontology_class_id must be non-empty")

    canonical_key = str(ko.get("canonical_key") or "").strip()
    if not canonical_key:
        raise ValueError(f"{context}: canonical_key must be non-empty")
    if "::" in canonical_key or not re.match(r"^[^:]+:[^:]+:[^:]+:.+$", canonical_key):
        raise ValueError(f"{context}: canonical_key must have non-empty domain/ontology/type/suffix")

    canonical_ontology = canonical_key.split(":", 3)[1]
    if canonical_ontology != ontology_class_id:
        raise ValueError(
            f"{context}: canonical_key ontology '{canonical_ontology}' "
            f"does not match ontology_class_id '{ontology_class_id}'"
        )


def _safe_slug_for_merger(name: str) -> str:
    slug = _slugify_part(name)
    if not slug or len(slug) <= 2 or slug.isdigit():
        return _hashed_slug(name)
    return slug


def _normalize_canonical_key_for_anchor(
    canonical_key: str,
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    fallback_name: str,
) -> str:
    """Ensure persisted canonical keys match the final ontology anchor."""

    domain_slug = _slugify_part(domain_id)
    equipment_slug = _slugify_part(equipment_class_id)
    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    if not domain_slug:
        raise ValueError("canonical_key normalization requires non-empty domain_id")
    if not equipment_slug:
        raise ValueError("canonical_key normalization requires non-empty equipment_class_id")
    if not type_prefix:
        raise ValueError("canonical_key normalization requires non-empty knowledge_object_type")
    parts = [part for part in str(canonical_key or "").split(":") if part]
    suffix = parts[-1] if len(parts) >= 4 else str(canonical_key or "")
    if not suffix or suffix.startswith("key_") or len(suffix) <= 2 or suffix.isdigit():
        suffix = _safe_slug_for_merger(fallback_name or suffix or "unknown")
    normalized = f"{domain_slug}:{equipment_slug}:{type_prefix}:{suffix}"
    assert_valid_ko_identity(
        {"ontology_class_id": equipment_slug, "canonical_key": normalized},
        context="normalized canonical_key",
    )
    return normalized


def _normalize_existing_ko_keys(
    session: Any,
    existing_kos: list[Any],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
) -> None:
    """Re-key existing rows in-place before regrouping.

    Regroup may split old clusters and leave some rows unmatched by source name.
    Those rows still need structural key repair, otherwise legacy prefixes and
    CJK hash fallbacks survive the regroup pass.
    """

    if not existing_kos:
        return

    from packages.db.models_v2 import KnowledgeObjectV2

    ko_ids = {ko.knowledge_object_id for ko in existing_kos}
    reserved = {
        key
        for (key,) in session.query(KnowledgeObjectV2.canonical_key)
        .filter(~KnowledgeObjectV2.knowledge_object_id.in_(ko_ids))
        .all()
    }
    used: set[str] = set()
    final_keys: dict[str, str] = {}
    for ko in sorted(existing_kos, key=lambda item: item.knowledge_object_id):
        normalized = _normalize_canonical_key_for_anchor(
            ko.canonical_key,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
            fallback_name=ko.title or "unknown",
        )
        candidate = _unique_canonical_key(normalized, reserved | used)
        used.add(candidate)
        if ko.canonical_key != candidate:
            final_keys[ko.knowledge_object_id] = candidate
    if not final_keys:
        return

    # Move through unique temporary keys first. PostgreSQL checks unique
    # constraints row-by-row for this table, so direct swaps collide.
    for ko in existing_kos:
        if ko.knowledge_object_id in final_keys:
            ko.canonical_key = f"__phase2_tmp__:{ko.knowledge_object_id}"
            session.add(ko)
    session.flush()

    for ko in existing_kos:
        final_key = final_keys.get(ko.knowledge_object_id)
        if final_key:
            ko.canonical_key = final_key
            session.add(ko)
    session.flush()


def _unique_canonical_key(base_key: str, reserved: set[str]) -> str:
    if base_key not in reserved:
        return base_key
    counter = 2
    while f"{base_key}_{counter}" in reserved:
        counter += 1
    return f"{base_key}_{counter}"


def _split_oversize_groups_by_source_name(
    groups: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    refined: dict[str, list[dict[str, Any]]] = {}
    for canonical_key, group in groups.items():
        if len(group) <= FINAL_MAX_GROUP_LAYERS:
            refined[canonical_key] = group
            continue

        by_name: dict[str, list[dict[str, Any]]] = {}
        for candidate in group:
            by_name.setdefault(_candidate_source_name(candidate) or "unknown", []).append(candidate)

        for name, name_group in by_name.items():
            slug = _safe_slug_for_merger(name)
            for offset in range(0, len(name_group), FINAL_MAX_GROUP_LAYERS):
                suffix = slug if offset == 0 else f"{slug}_{offset // FINAL_MAX_GROUP_LAYERS + 1}"
                refined[f"{canonical_key}_{suffix}"] = name_group[offset:offset + FINAL_MAX_GROUP_LAYERS]
    return refined


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


def _compute_consensus_state(layers: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Determine consensus_state by comparing value_summary across layers.

    R3: empty-value handling.
    """
    if len(layers) <= 1:
        return "single_source", None

    values = [layer.get("value_summary") for layer in layers]
    non_empty = [v for v in values if not _is_empty(v)]

    # R3: all sources lack explicit values
    if len(non_empty) == 0:
        return "single_value_unknown", "all sources lack explicit values; only parameter name confirmed"

    # R3: only one source has a value → agreed (insufficient data for conflict)
    if len(non_empty) == 1:
        return ConsensusState.AGREED.value, None

    base = non_empty[0]
    all_agree = all(_values_agree(base, v) for v in non_empty[1:])
    if all_agree:
        return ConsensusState.AGREED.value, None

    if len(non_empty) == 2:
        return (
            classify_conflicting_layers(layers),
            "Two sources disagree on value",
        )

    agree_count = sum(1 for v in non_empty if _values_agree(base, v))
    if agree_count > len(non_empty) // 2:
        return ConsensusState.PARTIAL_CONFLICT.value, f"{agree_count}/{len(non_empty)} sources agree on value; minority diverges"

    return (
        classify_conflicting_layers(layers),
        f"Significant value disagreement across {len(non_empty)} sources",
    )


def classify_conflicting_layers(layers: list[dict[str, Any]]) -> str:
    """Classify non-agreeing layers as value disagreement or over-merge."""

    signatures = [_layer_facet_signature(layer) for layer in layers]
    if not signatures:
        return ConsensusState.MATERIAL_CONFLICT.value

    saw_signal = False
    saw_partial = False
    for axis in range(7):
        values = [sig[axis] for sig in signatures]
        known = {value for value in values if value}
        if len(known) > 1:
            return ConsensusState.OVER_MERGE.value
        if len(known) == 1:
            if axis != 0:
                saw_signal = True
            if any(value is None for value in values):
                saw_partial = True

    if saw_partial:
        return ConsensusState.PARTIAL_CONFLICT.value
    if saw_signal or (_all_layers_share_source_name(layers) and _layers_have_explicit_parameter_names(layers)):
        return ConsensusState.VALUE_DISAGREEMENT.value
    return ConsensusState.MATERIAL_CONFLICT.value


def _layer_facet_signature(layer: dict[str, Any]) -> tuple[str | None, ...]:
    payload = layer.get("structured_payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    name = str(layer.get("source_name") or payload.get("parameter_name") or "")
    facet_payload = dict(payload)
    for key in ("value_summary", "citation"):
        if layer.get(key) is not None:
            facet_payload.setdefault(key, layer.get(key))
    return detect_facet_v2(name, facet_payload)


def _all_layers_share_source_name(layers: list[dict[str, Any]]) -> bool:
    names = {
        str(layer.get("source_name") or "").strip().lower()
        for layer in layers
        if str(layer.get("source_name") or "").strip()
    }
    return len(names) == 1


def _layers_have_explicit_parameter_names(layers: list[dict[str, Any]]) -> bool:
    for layer in layers:
        payload = layer.get("structured_payload") or {}
        if isinstance(payload, dict) and str(payload.get("parameter_name") or "").strip():
            return True
    return False


_PROSE_RANGE_PATTERNS = [
    # 中文: 20℃～34℃ / 20℃~34℃ / 20℃ ~ 34℃ / 20℃ 到 34℃ / 20℃ 至 34℃
    re.compile(
        r"(-?\d+(?:\.\d+)?)\s*[℃°]?[CF]?\s*[~～\-—–到至]\s*(-?\d+(?:\.\d+)?)\s*[℃°][CF]?",
        re.UNICODE,
    ),
    # 英文 explicit unit: 20 °C to 34 °C / 20°C-34°C
    re.compile(
        r"(-?\d+(?:\.\d+)?)\s*°[CF]\s*(?:to|~|-|–|—)\s*(-?\d+(?:\.\d+)?)\s*°[CF]",
        re.IGNORECASE,
    ),
    # 英文 to-keyword: "between 20 and 34" / "20 to 34"
    re.compile(
        r"(-?\d+(?:\.\d+)?)\s*(?:to|and)\s*(-?\d+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
]


def _extract_prose_range(text: str | None) -> tuple[str, str] | None:
    """F9 fallback: best-effort extract a single numeric (min, max) from prose.

    Conservative — only returns a range when exactly one consistent
    (min, max) pair is found across patterns. Returns None on
    ambiguity (multiple distinct ranges) or no match. Keeps wire-type
    as string (caller may pass back to structured_payload.range_min/
    range_max which are documented as string|null in contract §4.2).
    """
    if not text:
        return None
    candidates: set[tuple[str, str]] = set()
    for pattern in _PROSE_RANGE_PATTERNS:
        for match in pattern.findall(text):
            min_s, max_s = match[0], match[1]
            try:
                min_v = float(min_s)
                max_v = float(max_s)
                if min_v < max_v:
                    candidates.add((min_s, max_s))
            except (ValueError, TypeError):
                continue
        if candidates:
            break  # use first matching pattern's results only
    if len(candidates) == 1:
        return candidates.pop()
    return None


def _enrich_layer_range_from_prose(layer: dict[str, Any], evidence: list[dict[str, Any]]) -> None:
    """F9 fix: if a layer's structured_payload has no parseable range but
    its evidence_text contains a prose range, populate range_min/range_max
    in-place. Sets `range_source = "prose_extracted"` flag for transparency.
    Forward-only fix: existing KOs in DB are not retroactively patched.
    """
    payload = layer.get("structured_payload")
    if not isinstance(payload, dict):
        return
    if payload.get("range_min") not in (None, "") and payload.get("range_max") not in (None, ""):
        return  # already has parseable range
    for ev in evidence:
        text = ev.get("evidence_text") if isinstance(ev, dict) else None
        result = _extract_prose_range(text)
        if result:
            payload["range_min"] = result[0]
            payload["range_max"] = result[1]
            payload["range_source"] = "prose_extracted"
            return  # use first successful evidence


def _extract_value_summary(candidate: dict[str, Any]) -> str | None:
    """Extract a concise value summary from a candidate's structured payload.

    F6 fix: do not double-append unit when the raw value already ends in
    the unit string (e.g. value="20～34℃" + unit="℃" must NOT produce
    "20～34℃℃"; value="40SEC" + unit="SEC" must NOT produce "40SECSEC").
    """
    payload = candidate.get("structured_payload") or candidate.get("structured_payload_candidate") or {}
    if isinstance(payload, str):
        return payload[:100]
    value = payload.get("value") or payload.get("default_value")
    if value is not None:
        value_str = str(value).strip()
        unit = str(payload.get("unit") or "").strip()
        if unit and not value_str.endswith(unit):
            return f"{value_str}{unit}"
        return value_str
    range_min = payload.get("range_min")
    range_max = payload.get("range_max")
    if range_min is not None and range_max is not None:
        return f"[{range_min}, {range_max}]"
    return candidate.get("title") or candidate.get("summary")


def _candidate_source_name(candidate: dict[str, Any]) -> str:
    payload = candidate.get("structured_payload") or candidate.get("structured_payload_candidate") or {}
    return str(payload.get("parameter_name") or candidate.get("title") or candidate.get("summary", "")).strip()


def _build_contextual_name(payload: dict[str, Any]) -> str:
    """Build embedding text from the raw parameter name plus compact context."""

    name = str(payload.get("parameter_name") or payload.get("title") or "").strip()
    summary = str(payload.get("summary") or "").strip()[:120]
    value_parts = []
    for key in ("value", "default_value", "range_min", "range_max", "unit"):
        value = payload.get(key)
        if not _is_empty(value):
            value_parts.append(f"{key}={value}")

    parts = [part for part in (name, summary, " ".join(value_parts)) if part]
    return "。".join(parts)


def _candidate_doc_id(candidate: dict[str, Any]) -> str:
    evidence = candidate.get("evidence") or []
    if evidence:
        return str(evidence[0].get("doc_id") or "")
    return str(candidate.get("doc_id") or "")


SOURCE_NAME_CONFLICT_QUALIFIERS = [
    ("quantity", [
        "温度", "油温", "temperature",
        "压力", "压差", "pressure", "differential",
        "电流", "current",
        "容量", "制冷量", "capacity",
        "时间", "time",
    ]),
    ("bound", [
        "最大", "最小", "最高", "最低", "maximum", "minimum", "max", "min",
        "启动", "起动", "运行", "start", "stop",
    ]),
    ("reference", [
        "供油", "油箱", "润滑油", "oil tank", "supply oil", "lubricating oil",
        "蒸发器", "冷凝器", "evaporator", "condenser",
        "水侧", "制冷剂侧", "water side", "refrigerant side",
        "front panel", "external", "active", "bas", "tracer",
    ]),
]


def _has_conflicting_source_names(names: set[str]) -> bool:
    if len(names) <= 1:
        return False
    for _, patterns in SOURCE_NAME_CONFLICT_QUALIFIERS:
        qualifiers = {
            pattern
            for name in names
            for pattern in patterns
            if pattern in name.lower()
        }
        if len(qualifiers) > 1:
            return True
    return False


def _split_same_document_name_conflicts(
    groups: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Split groups that collapse distinct named parameters from one document."""

    refined: dict[str, list[dict[str, Any]]] = {}
    for canonical_key, group in groups.items():
        names_by_doc: dict[str, set[str]] = {}
        for candidate in group:
            doc_id = _candidate_doc_id(candidate)
            name = _candidate_source_name(candidate)
            if doc_id and name:
                names_by_doc.setdefault(doc_id, set()).add(name)

        has_same_doc_conflict = (
            len(names_by_doc) == 1
            and any(_has_conflicting_source_names(names) for names in names_by_doc.values())
        )
        if not has_same_doc_conflict:
            refined[canonical_key] = group
            continue

        by_name: dict[str, list[dict[str, Any]]] = {}
        for candidate in group:
            by_name.setdefault(_candidate_source_name(candidate) or "unknown", []).append(candidate)
        for name, name_group in by_name.items():
            suffix = _safe_slug_for_merger(name)
            refined[f"{canonical_key}_{suffix}"] = name_group
    return refined


def _split_fault_code_groups(
    groups: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    refined: dict[str, list[dict[str, Any]]] = {}
    for canonical_key, group in groups.items():
        by_signature: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for candidate in group:
            signature = _fault_signature(candidate)
            by_signature.setdefault(signature, []).append(candidate)
        if len(by_signature) <= 1:
            refined[canonical_key] = group
            continue
        for signature, signature_group in by_signature.items():
            name = _candidate_source_name(signature_group[0]) or "_".join(signature)
            refined[f"{canonical_key}_{_safe_slug_for_merger(name)}"] = signature_group
    return refined


def _fault_signature(candidate: dict[str, Any]) -> tuple[str, str, str]:
    payload = candidate.get("structured_payload") or candidate.get("structured_payload_candidate") or {}
    name = _candidate_source_name(candidate)
    text = " ".join(str(payload.get(key) or "") for key in ("parameter_name", "title", "summary", "condition", "trigger_condition"))
    text = f"{name} {candidate.get('summary', '')} {text}".lower()
    facets = detect_facet_v2(name, payload if isinstance(payload, dict) else {})
    quantity = facets[0] if len(facets) > 0 else None
    subtype = facets[1] if len(facets) > 1 else None
    polarity = facets[2] if len(facets) > 2 else None
    subsystem = facets[4] if len(facets) > 4 else None
    return (
        subtype or subsystem or quantity or "unknown_subsystem",
        polarity or _detect_fault_polarity(text),
        _trigger_condition_signature(text),
    )


def _detect_fault_polarity(text: str) -> str:
    if _contains_any(text, ["传感器", "sensor fault", "sensor failure", "断线"]):
        return "sensor_fault"
    if _contains_any(text, ["丢失", "无信号", "loss", "lost", "missing", "no signal"]):
        return "loss"
    if _contains_any(text, ["过高", "高温", "高压", "超限", "high", "over"]):
        return "high"
    if _contains_any(text, ["过低", "低温", "低压", "不足", "low", "under"]):
        return "low"
    if _contains_any(text, ["越限", "out of range", "range out"]):
        return "range_out"
    return "unknown"


def _trigger_condition_signature(text: str) -> str:
    for marker in ("油", "水", "制冷剂", "冷媒", "轴承", "电机", "相序", "压缩机"):
        if marker in text:
            return marker
    for marker in ("oil", "water", "refrigerant", "bearing", "motor", "phase", "compressor"):
        if marker in text:
            return marker
    return "unknown"


def _contains_any(value: str, needles: list[str]) -> bool:
    return any(needle.lower() in value for needle in needles)


def _prefer_raw_canonical_key(
    group: list[dict[str, Any]],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
) -> str:
    raw_keys = [
        resolve_single_name(
            _candidate_source_name(candidate),
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
        )
        for candidate in group
        if _candidate_source_name(candidate)
    ]
    if not raw_keys:
        return resolve_single_name(
            group[0].get("title", "unknown"),
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
        )
    semantic_keys = [
        key for key in raw_keys
        if not key.rsplit(":", 1)[-1].startswith("key_")
    ]
    return semantic_keys[0] if semantic_keys else raw_keys[0]


def _rename_groups_with_raw_canonical_keys(
    groups: dict[str, list[dict[str, Any]]],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
) -> dict[str, list[dict[str, Any]]]:
    renamed: dict[str, list[dict[str, Any]]] = {}
    for group in groups.values():
        canonical_key = _prefer_raw_canonical_key(
            group,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
        )
        renamed.setdefault(canonical_key, []).extend(group)
    return renamed


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
    protect_single_source_distinct_names: bool = True,
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
    raw_names_by_candidate = []
    facet_hints: dict[str, tuple[str | None, str | None]] = {}
    publisher_hints: dict[str, str | None] = {}
    for c in candidates:
        payload = c.get("structured_payload") or c.get("structured_payload_candidate") or {}
        raw_payload = payload if isinstance(payload, dict) else {}
        name = raw_payload.get("parameter_name") or c.get("title") or c.get("summary", "")
        context_payload = dict(raw_payload)
        context_payload.setdefault("title", c.get("title"))
        context_payload.setdefault("summary", c.get("summary"))
        contextual_name = _build_contextual_name(context_payload)
        names_by_candidate.append(contextual_name)
        raw_names_by_candidate.append(name)
        facet_payload = dict(raw_payload)
        facet_payload.setdefault("title", c.get("title"))
        facet_payload.setdefault("summary", c.get("summary"))
        facet_payload.setdefault("value_summary", _extract_value_summary(c))
        facet_hints[contextual_name] = detect_facet_v2(str(name), facet_payload)
        publisher_hints[contextual_name] = c.get("publisher")

    # Phase 1: LLM-assisted cross-lingual grouping (T1 plumbing fix, docs/35 §T1)
    canonical_map: dict[str, str] = {}
    try:
        canonical_map = group_and_normalize(
            names=names_by_candidate,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
            backend_name=backend_name,
            facet_hints=facet_hints,
            publisher_hints=publisher_hints,
        )
    except Exception:
        canonical_map = {}

    # Phase 2: mechanical fallback for any names LLM didn't cover
    canonical_keys = []
    for name, raw_name in zip(names_by_candidate, raw_names_by_candidate):
        key = canonical_map.get(name) or canonical_map.get(raw_name)
        if not key:
            key = resolve_single_name(
                raw_name,
                domain_id=domain_id,
                equipment_class_id=equipment_class_id,
                knowledge_object_type=knowledge_object_type,
            )
        canonical_keys.append(key)

    groups: dict[str, list[dict[str, Any]]] = {}
    for c, ck in zip(candidates, canonical_keys):
        groups.setdefault(ck, []).append(c)
    groups = _rename_groups_with_raw_canonical_keys(
        groups,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
    )
    if knowledge_object_type == "fault_code":
        groups = _split_fault_code_groups(groups)
    if protect_single_source_distinct_names:
        groups = _split_same_document_name_conflicts(groups)
    groups = _split_oversize_groups_by_source_name(groups)

    # E3 defensive sanity: force-split pathological groups (LLM path only)
    # Embedding-first path handles grouping via clustering — trust it.
    import os as _os
    if _os.environ.get("KNOWFABRIC_USE_EMBEDDING_FIRST", "1") != "1":
        pathological_keys = [k for k, v in groups.items() if len(v) > MERGER_MAX_GROUP_CANDIDATES]
        if pathological_keys:
            split_groups: dict[str, list[dict[str, Any]]] = {}
            for ck, group in groups.items():
                if ck in pathological_keys:
                    for c in group:
                        payload = c.get("structured_payload") or c.get("structured_payload_candidate") or {}
                        fallback_name = payload.get("parameter_name") or c.get("title", "unknown")
                        slug = _safe_slug_for_merger(fallback_name)
                        split_groups[f"{ck}_{slug}"] = [c]
                else:
                    split_groups[ck] = group
            groups = split_groups
            if protect_single_source_distinct_names:
                groups = _split_same_document_name_conflicts(groups)

    # Step 2: Build merged KOs
    merged = []
    for canonical_key, group in groups.items():
        canonical_key = _normalize_canonical_key_for_anchor(
            canonical_key,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
            fallback_name=_candidate_source_name(group[0]) or group[0].get("title", "unknown"),
        )
        layers = []
        # F8 fix: track (publisher, doc_id, chunk_id) tuples already added
        # as a layer. Two candidates pointing to the same chunk from the same
        # publisher are not independent sources — they are the same source
        # counted twice. Skip duplicates so layer count reflects real source
        # diversity, not chunk-level fanout from upstream pipeline.
        seen_layer_keys: set[tuple] = set()
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
            primary_layer_chunk_id = cand_evidence[0].get("chunk_id", "") if cand_evidence else ""
            cand_payload = cand.get("structured_payload") or cand.get("structured_payload_candidate") or {}
            # F9 fix: make a shallow copy so prose-extracted range doesn't
            # mutate the source candidate's payload (which may be referenced
            # by other code paths). Then enrich from prose if needed.
            if isinstance(cand_payload, dict):
                cand_payload = dict(cand_payload)
            # F8 fix: skip candidates that point to the same (publisher,
            # doc_id, chunk_id) as a layer already added. Same chunk from
            # same publisher is the same source, not "multi-source consensus".
            # Note: still add to evidence_rows below (chunk content is real),
            # but don't inflate layer count.
            layer_key = (
                cand.get("publisher"),
                doc_id,
                primary_layer_chunk_id,
            )
            is_duplicate_layer = layer_key in seen_layer_keys
            if not is_duplicate_layer:
                seen_layer_keys.add(layer_key)
                # Re-evaluate is_primary based on accepted-layers count, not
                # raw iteration index, so that the first accepted layer per
                # cluster gets primary role even if it came after a duplicate.
                is_primary = len(layers) == 0
                layer = {
                    "authority_level": authority_level,
                    "publisher": cand.get("publisher"),
                    "citation": cand.get("citation") or cand.get("evidence_citation"),
                    "source_name": _candidate_source_name(cand),
                    "structured_payload": cand_payload,
                    "value_summary": _extract_value_summary(cand),
                    "evidence_role": "primary" if is_primary else "corroborating",
                    "doc_id": doc_id,
                    "chunk_id": primary_layer_chunk_id,
                }
                _enrich_layer_range_from_prose(layer, cand_evidence)
                layers.append(layer)

            # F8: skip evidence_row creation for duplicate-layer candidates.
            # Their chunk evidence was already attached by the original layer
            # whose (publisher, doc_id, chunk_id) match. Adding again would
            # produce duplicate evidence_role rows on same chunk (FK
            # uniqueness violation downstream + inflated evidence count).
            if is_duplicate_layer:
                continue

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
            name = _candidate_source_name(cand)
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
            "review_status": "pending" if consensus_state == ConsensusState.OVER_MERGE.value else "published",
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
        assert_valid_ko_identity(merged[-1], context="merged KO")

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
    layer_by_chunk = {
        str(layer.get("chunk_id")): layer
        for layer in layers
        if isinstance(layer, dict) and layer.get("chunk_id")
    }
    layer_by_doc = {
        str(layer.get("doc_id")): layer
        for layer in layers
        if isinstance(layer, dict) and layer.get("doc_id")
    }

    expanded: list[dict[str, Any]] = []
    for ev in evidence_rows:
        layer = (
            layer_by_chunk.get(str(ev.get("chunk_id") or ""))
            or layer_by_doc.get(str(ev.get("doc_id") or ""), {})
        )
        layer_payload = layer.get("structured_payload")
        ev_payload = dict(layer_payload if isinstance(layer_payload, dict) else payload)
        layer_name = str(layer.get("source_name") or "").strip()
        ev_payload["parameter_name"] = layer_name if _looks_like_parameter_name(layer_name) else fallback_name
        layer_summary = (
            ev_payload.get("summary")
            or ev_payload.get("evidence_quote")
            or ev.get("evidence_text")
            or layer.get("value_summary")
            or ev_payload["parameter_name"]
        )
        expanded.append({
            **base,
            "title": ev_payload["parameter_name"] or base.get("title"),
            "summary": str(layer_summary or ""),
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
    _normalize_existing_ko_keys(
        session,
        existing_kos,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
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
    protect_single_source_distinct_names = not existing_candidates

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
        protect_single_source_distinct_names=protect_single_source_distinct_names,
    )

    stats = {"new_merged": 0, "updated_existing": 0, "merged_existing": 0, "material_conflicts": 0}

    removed_ko_ids: set[str] = set()
    assigned_ko_ids: set[str] = set()
    for ko_dict in merged:
        ko_dict["canonical_key"] = _normalize_canonical_key_for_anchor(
            ko_dict["canonical_key"],
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
            fallback_name=ko_dict.get("title", "unknown"),
        )
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
        matched_ids = _available_matched_ids(
            matched_ids,
            removed_ko_ids=removed_ko_ids,
            assigned_ko_ids=assigned_ko_ids,
        )

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
                removed_ko_ids.add(src_id)
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
        assigned_ko_ids.add(ko_dict["knowledge_object_id"])

        decision = {
            "canonical_key": canonical_key,
            "knowledge_object_id": ko_dict["knowledge_object_id"],
            "member_names": sorted(member_names),
            "matched_ids": sorted(matched_ids),
            "layers": _summarize_layers(ko_dict.get("authority_summary_json", {}).get("layers", [])),
            "evidence_rows": _summarize_evidence_rows(evidence_rows),
        }

        if ko_dict["consensus_state"] in {
            ConsensusState.OVER_MERGE.value,
            ConsensusState.MATERIAL_CONFLICT.value,
        }:
            ko_dict["review_status"] = "conflict_review_required"
            stats["material_conflicts"] += 1

        assert_valid_ko_identity(ko_dict, context="merge_with_existing upsert")

        # Preserve primary_chunk_id if missing
        if ko_dict["knowledge_object_id"] in removed_ko_ids:
            continue

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
            target_exists = session.query(KnowledgeObjectV2).filter(
                KnowledgeObjectV2.knowledge_object_id == ko_dict["knowledge_object_id"]
            ).first()
            if not target_exists:
                assigned_ko_ids.discard(ko_dict["knowledge_object_id"])
                ko_dict["knowledge_object_id"] = ck_conflict.knowledge_object_id
                assigned_ko_ids.add(ko_dict["knowledge_object_id"])
                decision["knowledge_object_id"] = ko_dict["knowledge_object_id"]
                decision["canonical_key_conflict_adopted"] = ck_conflict.knowledge_object_id
                ck_conflict = None

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
            removed_ko_ids.add(ck_conflict.knowledge_object_id)
            decision["canonical_key_conflict_deleted"] = ck_conflict.knowledge_object_id

        session.merge(KnowledgeObjectV2(**ko_dict))
        session.flush()
        _dump_upsert_trace(decision)

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


def _available_matched_ids(
    matched_ids: set[str],
    *,
    removed_ko_ids: set[str],
    assigned_ko_ids: set[str],
) -> set[str]:
    """Return existing KO ids that are still safe to update in this upsert pass."""

    return matched_ids - removed_ko_ids - assigned_ko_ids


def _summarize_layers(layers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "publisher": layer.get("publisher"),
            "source_name": layer.get("source_name"),
            "doc_id": layer.get("doc_id"),
            "chunk_id": layer.get("chunk_id"),
            "value_summary": layer.get("value_summary"),
        }
        for layer in layers
    ]


def _summarize_evidence_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "doc_id": row.get("doc_id"),
            "chunk_id": row.get("chunk_id"),
            "evidence_role": row.get("evidence_role"),
        }
        for row in rows
    ]


def _dump_upsert_trace(decision: dict[str, Any]) -> None:
    import json as _json
    import os as _os
    from pathlib import Path as _Path

    trace_dir = _os.environ.get("KNOWFABRIC_UPSERT_TRACE_DIR")
    if not trace_dir:
        return
    out_dir = _Path(trace_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "upsert_trace.jsonl", "a", encoding="utf-8") as fh:
        fh.write(_json.dumps(decision, ensure_ascii=False) + "\n")


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
