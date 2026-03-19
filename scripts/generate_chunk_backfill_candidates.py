#!/usr/bin/env python3
"""Generate review candidates for chunk-backed semantic backfill."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2
from packages.db.session import SessionLocal

FAULT_CONTEXT_MARKERS = (
    "fault",
    "alarm",
    "warning",
    "error",
    "protection",
    "trip",
    "故障",
    "报警",
    "保护",
    "告警",
)
PARAMETER_CONTEXT_MARKERS = (
    "parameter",
    "setting",
    "default",
    "threshold",
    "group",
    "参数",
    "设定",
    "阈值",
    "默认",
)
PERFORMANCE_CONTEXT_MARKERS = (
    "rated",
    "nominal",
    "capacity",
    "efficiency",
    "cop",
    "eer",
    "performance",
    "specification",
    "rating",
    "output",
    "额定",
    "性能",
    "效率",
    "能力",
)
PERFORMANCE_CATEGORY_KEYWORDS = {
    "capacity": ("capacity", "cooling capacity", "heating capacity", "output", "rt", "kw", "能力", "制冷量"),
    "efficiency": ("efficiency", "cop", "eer", "kw/rt", "效率"),
    "temperature": ("temperature", "leaving temp", "approach", "°c", "c", "温度"),
    "flow": ("flow", "water flow", "air flow", "m3/h", "l/s", "流量"),
}
COMMISSIONING_CONTEXT_MARKERS = (
    "commission",
    "startup",
    "start-up",
    "getting started",
    "backup settings",
    "upload settings",
    "调试",
    "启动",
    "设置备份",
    "上传变频器设置",
)
WIRING_CONTEXT_MARKERS = (
    "wiring",
    "terminal",
    "cable",
    "shield",
    "ground",
    "modbus",
    "bacnet",
    "rs485",
    "communication port",
    "接线",
    "端子",
    "屏蔽",
    "接地",
    "通讯",
)
APPLICATION_CONTEXT_MARKERS = (
    "application",
    "pump",
    "fan",
    "flow",
    "pressure",
    "hvac",
    "应用",
    "风机",
    "水泵",
    "流量",
    "压力",
)
MAINTENANCE_CONTEXT_MARKERS = (
    "maintenance",
    "service",
    "procedure",
    "clean",
    "wash",
    "inspect",
    "check",
    "replace",
    "lubricate",
    "maintain",
    "guide",
    "维护",
    "保养",
    "检查",
    "清洗",
    "清洁",
)
MAINTENANCE_TASK_KEYWORDS = {
    "cleaning": ("clean", "wash", "清洗", "清洁"),
    "inspection": ("inspect", "check", "检查"),
    "replacement": ("replace", "更换"),
    "lubrication": ("lubricate", "润滑"),
}
STRONG_MAINTENANCE_MARKERS = (
    "clean",
    "wash",
    "replace",
    "lubricate",
    "maintain",
    "regularly",
    "periodic",
    "清洗",
    "清洁",
    "更换",
    "润滑",
    "保养",
)
DIAGNOSTIC_STEP_MARKERS = (
    "check",
    "inspect",
    "verify",
    "increase",
    "decrease",
    "vent",
    "排气",
    "检查",
    "确认",
)
FAULT_CODE_PATTERN = re.compile(r"\b([A-Z]\d[A-Z0-9]{1,6})\b", re.IGNORECASE)
NUMERIC_FAULT_CODE_PATTERN = re.compile(r"\b(\d{2,4})\b")
PARAMETER_CODE_PATTERN = re.compile(r"\b(p\d{3,5})\b", re.IGNORECASE)
VALUE_WITH_UNIT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:rt|kw|cop|eer|kw/rt|m3/h|l/s|°c|c|%)\b",
    re.IGNORECASE,
)
PREFIXED_VALUE_PATTERN = re.compile(
    r"\b(?:cop|eer)\s*\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AliasTerm:
    normalized: str
    display: str
    is_preferred: bool
    source: str


@dataclass(frozen=True)
class EquipmentClassProfile:
    ontology_class_key: str
    ontology_class_id: str
    primary_label: str
    knowledge_anchors: tuple[str, ...]
    terms: tuple[AliasTerm, ...]


@lru_cache(maxsize=8)
def _load_document_profile_map(domain_id: str) -> dict[str, set[str]]:
    path = Path(__file__).resolve().parent.parent / "domain_packages" / domain_id / "v2" / "coverage" / "document_profiles.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    profiles = {}
    for item in data.get("document_profiles", []):
        profile_id = item.get("id")
        preferred = item.get("preferred_knowledge_objects", [])
        if profile_id and isinstance(preferred, list):
            profiles[str(profile_id)] = {str(value) for value in preferred}
    return profiles


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _short_text(text: str, limit: int = 220) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 3]}..."


def _stable_candidate_id(*parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"cand_{digest}"


def _iter_label_terms(ontology_class: OntologyClassV2) -> list[AliasTerm]:
    labels = list((ontology_class.labels_json or {}).values())
    labels.append(ontology_class.primary_label)
    unique = []
    seen = set()
    for label in labels:
        normalized = _normalize_text(label)
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(
                AliasTerm(
                    normalized=normalized,
                    display=label,
                    is_preferred=False,
                    source="label",
                )
            )
    return unique


def _build_equipment_profiles(db: Session, domain_id: str) -> list[EquipmentClassProfile]:
    classes = (
        db.query(OntologyClassV2)
        .filter(OntologyClassV2.domain_id == domain_id)
        .filter(OntologyClassV2.class_kind == "equipment")
        .filter(OntologyClassV2.is_active.is_(True))
        .order_by(OntologyClassV2.ontology_class_id)
        .all()
    )
    aliases = (
        db.query(OntologyAliasV2)
        .filter(OntologyAliasV2.domain_id == domain_id)
        .order_by(OntologyAliasV2.ontology_class_id, OntologyAliasV2.is_preferred.desc())
        .all()
    )
    alias_map: dict[str, list[AliasTerm]] = defaultdict(list)
    for alias in aliases:
        alias_map[alias.ontology_class_key].append(
            AliasTerm(
                normalized=alias.normalized_alias,
                display=alias.alias_text,
                is_preferred=alias.is_preferred,
                source="alias",
            )
        )

    profiles = []
    for ontology_class in classes:
        terms = alias_map[ontology_class.ontology_class_key] + _iter_label_terms(ontology_class)
        profiles.append(
            EquipmentClassProfile(
                ontology_class_key=ontology_class.ontology_class_key,
                ontology_class_id=ontology_class.ontology_class_id,
                primary_label=ontology_class.primary_label,
                knowledge_anchors=tuple(ontology_class.knowledge_anchors_json or ()),
                terms=tuple(terms),
            )
        )
    return profiles


def _score_alias_match(text: str, term: AliasTerm) -> float | None:
    if term.normalized not in text:
        return None
    length_boost = min(len(term.normalized), 24) / 36
    preferred_boost = 0.06 if term.is_preferred else 0.0
    source_boost = 0.03 if term.source == "label" else 0.0
    return min(0.3 + length_boost + preferred_boost + source_boost, 0.98)


def _match_equipment_class(
    profiles: list[EquipmentClassProfile],
    search_text: str,
    equipment_class_id: str | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if equipment_class_id:
        for profile in profiles:
            if profile.ontology_class_id == equipment_class_id:
                return (
                    {
                        "equipment_class_id": profile.ontology_class_id,
                        "equipment_class_key": profile.ontology_class_key,
                        "label": profile.primary_label,
                        "confidence": 1.0,
                        "matched_aliases": [],
                        "selection_method": "input_filter",
                        "knowledge_anchors": list(profile.knowledge_anchors),
                    },
                    [],
                )
        raise ValueError(f"Unknown equipment class for domain: {equipment_class_id}")

    scored = []
    for profile in profiles:
        matches = []
        best_score = 0.0
        for term in profile.terms:
            score = _score_alias_match(search_text, term)
            if score is None:
                continue
            best_score = max(best_score, score)
            matches.append(term.display)
        if matches:
            scored.append((best_score, profile, sorted(set(matches))))
    scored.sort(key=lambda item: (-item[0], -len(item[1].ontology_class_id), item[1].ontology_class_id))
    if not scored:
        return None, []

    primary_score, primary_profile, primary_matches = scored[0]
    alternatives = [
        {
            "equipment_class_id": profile.ontology_class_id,
            "equipment_class_key": profile.ontology_class_key,
            "confidence": round(score, 3),
            "matched_aliases": matches,
        }
        for score, profile, matches in scored[1:4]
    ]
    return (
        {
            "equipment_class_id": primary_profile.ontology_class_id,
            "equipment_class_key": primary_profile.ontology_class_key,
            "label": primary_profile.primary_label,
            "confidence": round(primary_score, 3),
            "matched_aliases": primary_matches,
            "selection_method": "alias_match",
            "knowledge_anchors": list(primary_profile.knowledge_anchors),
        },
        alternatives,
    )


def _has_context(markers: tuple[str, ...], *texts: str) -> bool:
    combined = " ".join(texts)
    return any(marker in combined for marker in markers)


def _is_parameter_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(PARAMETER_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_performance_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    if _has_context(("maintenance", "fault", "alarm"), chunk_type, page_type or ""):
        return False
    return _has_context(PERFORMANCE_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_commissioning_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(COMMISSIONING_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_wiring_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(WIRING_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_application_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    if _is_fault_context(normalized_chunk, chunk_type, page_type):
        return False
    return _has_context(APPLICATION_CONTEXT_MARKERS, normalized_chunk, chunk_type, page_type or "")


def _is_fault_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    typed_fault = _has_context(("fault", "alarm"), chunk_type, page_type or "")
    if typed_fault:
        return True
    if _has_context(("parameter",), chunk_type, page_type or ""):
        return False
    return _has_context(FAULT_CONTEXT_MARKERS, normalized_chunk)


def _candidate_confidence(base: float, equipment_confidence: float, context_bonus: float) -> float:
    return round(min(base + context_bonus + (equipment_confidence - 0.6) * 0.25, 0.99), 3)


def _slug_from_text(text: str, limit: int = 6) -> str:
    tokens = re.findall(r"[a-z0-9]+", _normalize_text(text))
    return "_".join(tokens[:limit]) or "candidate"


def _infer_maintenance_task(text: str) -> str:
    normalized = _normalize_text(text)
    for task_type, keywords in MAINTENANCE_TASK_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return task_type
    return "maintenance"


def _infer_performance_category(text: str) -> str:
    normalized = _normalize_text(text)
    for category, keywords in PERFORMANCE_CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "performance"


def _infer_application_type(text: str) -> str:
    normalized = _normalize_text(text)
    if "pump" in normalized and "fan" in normalized:
        return "pump_fan"
    if "pump" in normalized or "水泵" in normalized:
        return "pump"
    if "fan" in normalized or "风机" in normalized:
        return "fan"
    if "flow" in normalized or "流量" in normalized:
        return "flow"
    return "application"


def _procedure_context_text(chunk_type: str, page_type: str | None, normalized_chunk: str) -> str:
    return " ".join(filter(None, [chunk_type, page_type or "", normalized_chunk]))


def _is_procedure_context(normalized_chunk: str, chunk_type: str, page_type: str | None) -> bool:
    return _has_context(MAINTENANCE_CONTEXT_MARKERS, _procedure_context_text(chunk_type, page_type, normalized_chunk))


def _detect_parameter_candidates(
    normalized_chunk: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_parameter_context(normalized_chunk, chunk_type, page_type):
        return []
    candidates = []
    for token in sorted({match.lower() for match in PARAMETER_CODE_PATTERN.findall(normalized_chunk)}):
        candidates.append(
            {
                "knowledge_object_type": "parameter_spec",
                "canonical_key_candidate": token,
                "structured_payload_candidate": {"parameter_name": token},
                "confidence_score": _candidate_confidence(0.8, equipment_confidence, 0.05),
                "knowledge_signal": {"matched_token": token, "detection_method": "parameter_regex"},
            }
        )
    return candidates


def _detect_performance_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_performance_context(normalized_chunk, chunk_type, page_type):
        return []
    category = _infer_performance_category(display_text)
    rated_value = None
    match = VALUE_WITH_UNIT_PATTERN.search(display_text)
    if match:
        rated_value = match.group(0)
    else:
        prefixed_match = PREFIXED_VALUE_PATTERN.search(display_text)
        if prefixed_match:
            rated_value = prefixed_match.group(0).upper()
    structured_payload = {
        "parameter_name": _slug_from_text(display_text),
        "parameter_category": category,
    }
    if rated_value:
        structured_payload["rated_value"] = rated_value
    return [
        {
            "knowledge_object_type": "performance_spec",
            "canonical_key_candidate": f"{category}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": structured_payload,
            "confidence_score": _candidate_confidence(0.79, equipment_confidence, 0.04),
            "knowledge_signal": {"matched_category": category, "detection_method": "performance_context"},
        }
    ]


def _detect_commissioning_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_commissioning_context(normalized_chunk, chunk_type, page_type):
        return []
    if _is_wiring_context(normalized_chunk, chunk_type, page_type):
        return []
    return [
        {
            "knowledge_object_type": "commissioning_step",
            "canonical_key_candidate": _slug_from_text(display_text),
            "structured_payload_candidate": {
                "step": display_text,
                "commissioning_phase": "startup",
            },
            "confidence_score": _candidate_confidence(0.78, equipment_confidence, 0.03),
            "knowledge_signal": {"detection_method": "commissioning_context"},
        }
    ]


def _detect_wiring_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_wiring_context(normalized_chunk, chunk_type, page_type):
        return []
    topic = "wiring"
    if "modbus" in normalized_chunk or "bacnet" in normalized_chunk or "rs485" in normalized_chunk:
        topic = "communication_wiring"
    elif "shield" in normalized_chunk or "ground" in normalized_chunk or "接地" in normalized_chunk:
        topic = "shield_grounding"
    elif "terminal" in normalized_chunk or "端子" in normalized_chunk:
        topic = "terminal_connection"
    return [
        {
            "knowledge_object_type": "wiring_guidance",
            "canonical_key_candidate": f"{topic}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "wiring_topic": topic,
                "guidance": display_text,
            },
            "confidence_score": _candidate_confidence(0.77, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_topic": topic, "detection_method": "wiring_context"},
        }
    ]


def _detect_application_guidance_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_application_context(normalized_chunk, chunk_type, page_type):
        return []
    application_type = _infer_application_type(display_text)
    return [
        {
            "knowledge_object_type": "application_guidance",
            "canonical_key_candidate": f"{application_type}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "application_type": application_type,
                "guidance": display_text,
            },
            "confidence_score": _candidate_confidence(0.76, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_application_type": application_type, "detection_method": "application_context"},
        }
    ]


def _detect_fault_candidates(
    normalized_chunk: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_fault_context(normalized_chunk, chunk_type, page_type):
        return []
    alphanumeric = {
        match.upper()
        for match in FAULT_CODE_PATTERN.findall(normalized_chunk)
        if not match.lower().startswith("p")
    }
    numeric = set(NUMERIC_FAULT_CODE_PATTERN.findall(normalized_chunk))
    tokens = sorted(alphanumeric) + sorted(numeric)
    candidates = []
    for token in tokens:
        candidates.append(
            {
                "knowledge_object_type": "fault_code",
                "canonical_key_candidate": token,
                "structured_payload_candidate": {"fault_code": token},
                "confidence_score": _candidate_confidence(0.85, equipment_confidence, 0.04),
                "knowledge_signal": {"matched_token": token, "detection_method": "fault_regex"},
            }
        )
    return candidates


def _detect_maintenance_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_procedure_context(normalized_chunk, chunk_type, page_type):
        return []
    if _has_context(DIAGNOSTIC_STEP_MARKERS, normalized_chunk) and not _has_context(STRONG_MAINTENANCE_MARKERS, normalized_chunk):
        return []
    task_type = _infer_maintenance_task(normalized_chunk)
    return [
        {
            "knowledge_object_type": "maintenance_procedure",
            "canonical_key_candidate": f"{task_type}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "maintenance_task": task_type,
                "task_type": task_type,
                "steps": [display_text],
            },
            "confidence_score": _candidate_confidence(0.75, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_task_type": task_type, "detection_method": "procedure_context"},
        }
    ]


def _detect_diagnostic_step_candidates(
    normalized_chunk: str,
    display_text: str,
    chunk_type: str,
    page_type: str | None,
    equipment_confidence: float,
) -> list[dict[str, Any]]:
    if not _is_procedure_context(normalized_chunk, chunk_type, page_type):
        return []
    if not _has_context(DIAGNOSTIC_STEP_MARKERS, normalized_chunk):
        return []
    task_type = _infer_maintenance_task(normalized_chunk)
    return [
        {
            "knowledge_object_type": "diagnostic_step",
            "canonical_key_candidate": f"{task_type}_{_slug_from_text(display_text)}",
            "structured_payload_candidate": {
                "task_type": task_type,
                "step": display_text,
            },
            "confidence_score": _candidate_confidence(0.74, equipment_confidence, 0.03),
            "knowledge_signal": {"matched_task_type": task_type, "detection_method": "diagnostic_procedure_context"},
        }
    ]


def _build_search_text(chunk: ContentChunk, document: Document) -> str:
    return _normalize_text(" ".join(filter(None, [chunk.cleaned_text, chunk.text_excerpt, document.file_name])))


def _detect_knowledge_candidates(
    chunk: ContentChunk,
    page: DocumentPage,
    equipment_match: dict[str, Any],
) -> list[dict[str, Any]]:
    display_text = chunk.text_excerpt or _short_text(chunk.cleaned_text)
    normalized_chunk = _normalize_text(" ".join(filter(None, [chunk.cleaned_text, chunk.text_excerpt])))
    knowledge_anchors = set(equipment_match["knowledge_anchors"])
    preferred = _load_document_profile_map(equipment_match["equipment_class_key"].split(":", 1)[0]).get(page.page_type or "")
    if preferred:
        knowledge_anchors &= preferred
    candidates = []
    if "parameter_spec" in knowledge_anchors:
        candidates.extend(
            _detect_parameter_candidates(
                normalized_chunk,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "fault_code" in knowledge_anchors:
        candidates.extend(
            _detect_fault_candidates(
                normalized_chunk,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "performance_spec" in knowledge_anchors:
        candidates.extend(
            _detect_performance_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "commissioning_step" in knowledge_anchors:
        candidates.extend(
            _detect_commissioning_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "wiring_guidance" in knowledge_anchors:
        candidates.extend(
            _detect_wiring_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "application_guidance" in knowledge_anchors:
        candidates.extend(
            _detect_application_guidance_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "maintenance_procedure" in knowledge_anchors:
        candidates.extend(
            _detect_maintenance_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    if "diagnostic_step" in knowledge_anchors:
        candidates.extend(
            _detect_diagnostic_step_candidates(
                normalized_chunk,
                display_text,
                chunk.chunk_type,
                page.page_type,
                equipment_match["confidence"],
            )
        )
    return candidates


def _load_chunk_rows(
    db: Session,
    domain_id: str,
    doc_id: str | None,
    chunk_id: str | None,
) -> list[tuple[ContentChunk, DocumentPage, Document]]:
    query = (
        db.query(ContentChunk, DocumentPage, Document)
        .join(DocumentPage, ContentChunk.page_id == DocumentPage.page_id)
        .join(Document, ContentChunk.doc_id == Document.doc_id)
        .filter(Document.source_domain == domain_id)
        .order_by(ContentChunk.doc_id, ContentChunk.page_no, ContentChunk.chunk_index)
    )
    if doc_id:
        query = query.filter(ContentChunk.doc_id == doc_id)
    if chunk_id:
        query = query.filter(ContentChunk.chunk_id == chunk_id)
    return query.all()


def _build_candidate_entry(
    domain_id: str,
    chunk: ContentChunk,
    page: DocumentPage,
    document: Document,
    equipment_match: dict[str, Any],
    alternatives: list[dict[str, Any]],
    knowledge_candidate: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = _stable_candidate_id(
        domain_id,
        chunk.chunk_id,
        equipment_match["equipment_class_key"],
        knowledge_candidate["knowledge_object_type"],
        knowledge_candidate["canonical_key_candidate"],
    )
    return {
        "candidate_id": candidate_id,
        "domain_id": domain_id,
        "doc_id": document.doc_id,
        "doc_name": document.file_name,
        "page_id": page.page_id,
        "page_no": page.page_no,
        "chunk_id": chunk.chunk_id,
        "chunk_index": chunk.chunk_index,
        "chunk_type": chunk.chunk_type,
        "page_type": page.page_type,
        "text_excerpt": chunk.text_excerpt or _short_text(chunk.cleaned_text),
        "evidence_text": _short_text(chunk.cleaned_text),
        "equipment_class_candidate": {
            "equipment_class_id": equipment_match["equipment_class_id"],
            "equipment_class_key": equipment_match["equipment_class_key"],
            "label": equipment_match["label"],
            "confidence": equipment_match["confidence"],
            "matched_aliases": equipment_match["matched_aliases"],
        },
        "knowledge_object_type": knowledge_candidate["knowledge_object_type"],
        "canonical_key_candidate": knowledge_candidate["canonical_key_candidate"],
        "structured_payload_candidate": knowledge_candidate["structured_payload_candidate"],
        "confidence_score": knowledge_candidate["confidence_score"],
        "review_status": "candidate",
        "match_metadata": {
            "equipment_selection_method": equipment_match["selection_method"],
            "alternative_equipment_class_candidates": alternatives,
            "knowledge_signal": knowledge_candidate["knowledge_signal"],
        },
    }


def _build_doc_summaries(
    rows: list[tuple[ContentChunk, DocumentPage, Document]],
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scanned: dict[str, dict[str, Any]] = {}
    matched_chunks_by_doc: defaultdict[str, set[str]] = defaultdict(set)
    candidate_counts: Counter[str] = Counter()

    for _, _, document in rows:
        scanned.setdefault(
            document.doc_id,
            {"doc_id": document.doc_id, "doc_name": document.file_name, "scanned_chunks": 0},
        )
        scanned[document.doc_id]["scanned_chunks"] += 1

    for entry in entries:
        matched_chunks_by_doc[entry["doc_id"]].add(entry["chunk_id"])
        candidate_counts[entry["doc_id"]] += 1

    summaries = []
    for doc_id, info in sorted(scanned.items()):
        scanned_chunks = info["scanned_chunks"]
        matched_chunks = len(matched_chunks_by_doc.get(doc_id, set()))
        summaries.append(
            {
                "doc_id": doc_id,
                "doc_name": info["doc_name"],
                "scanned_chunks": scanned_chunks,
                "matched_chunks": matched_chunks,
                "candidate_entries": candidate_counts.get(doc_id, 0),
                "candidate_hit_rate": round((matched_chunks / scanned_chunks), 3) if scanned_chunks else 0.0,
            }
        )
    return summaries


def generate_chunk_backfill_candidates(
    domain_id: str,
    *,
    doc_id: str | None = None,
    chunk_id: str | None = None,
    equipment_class_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Generate review candidates from existing chunk rows."""

    session = SessionLocal()
    try:
        profiles = _build_equipment_profiles(session, domain_id)
        rows = _load_chunk_rows(session, domain_id, doc_id, chunk_id)
        entries = []
        for chunk, page, document in rows:
            equipment_match, alternatives = _match_equipment_class(
                profiles,
                _build_search_text(chunk, document),
                equipment_class_id,
            )
            if equipment_match is None:
                continue
            for knowledge_candidate in _detect_knowledge_candidates(chunk, page, equipment_match):
                entries.append(
                    _build_candidate_entry(
                        domain_id,
                        chunk,
                        page,
                        document,
                        equipment_match,
                        alternatives,
                        knowledge_candidate,
                    )
                )
        entries.sort(key=lambda item: (-item["confidence_score"], item["doc_id"], item["page_no"], item["chunk_index"]))
        limited = entries[:limit]
        matched_chunks = len({entry["chunk_id"] for entry in limited})
        doc_summaries = _build_doc_summaries(rows, limited)
        return {
            "generation_mode": "chunk_backfill_review_candidate",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "domain_id": domain_id,
            "filters_applied": {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "equipment_class_id": equipment_class_id,
                "limit": limit,
            },
            "candidate_entries": limited,
            "metadata": {
                "total_candidates": len(limited),
                "scanned_chunks": len(rows),
                "matched_chunks": matched_chunks,
                "candidate_hit_rate": round((matched_chunks / len(rows)), 3) if rows else 0.0,
                "candidate_knowledge_types": sorted({item["knowledge_object_type"] for item in limited}),
                "doc_summaries": doc_summaries,
            },
        }
    finally:
        session.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain_id", help="Domain scope such as 'hvac' or 'drive'")
    parser.add_argument("--doc-id", dest="doc_id", help="Limit candidate generation to one document")
    parser.add_argument("--chunk-id", dest="chunk_id", help="Limit candidate generation to one chunk")
    parser.add_argument(
        "--equipment-class-id",
        dest="equipment_class_id",
        help="Optional known equipment class to avoid ambiguous alias matching",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of candidate entries to return")
    parser.add_argument("--output", help="Optional JSON file path for generated candidates")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    payload = generate_chunk_backfill_candidates(
        args.domain_id,
        doc_id=args.doc_id,
        chunk_id=args.chunk_id,
        equipment_class_id=args.equipment_class_id,
        limit=args.limit,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {payload['metadata']['total_candidates']} candidates to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Chunk backfill candidate generation failed: {exc}")
        raise SystemExit(1)
