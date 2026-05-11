"""LLM-assisted document/section routing for standard-reference pipelines.

Classifies document mission, active knowledge lane, and per-section topic/object
routing before extraction — so methodology guides don't get forced into
equipment-operational lanes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from packages.compiler.llm_compiler import _request_json_completion, resolve_backend

DOC_FAMILIES = [
    "equipment_manual",
    "design_handbook",
    "standard_reference",
    "methodology_guide",
    "system_topic_guide",
    "cross_domain_sustainability_guide",
]
DOC_LANES = ["equipment_operational", "system_design", "audit_methodology", "sustainability_topic", "mixed"]
SECTION_TOPICS = [
    "chiller", "ahu", "cooling_tower", "pump", "boiler", "valve_control",
    "desiccant_system", "dynamic_glazing", "air_distribution",
    "general_hvac_design", "audit_process", "reporting_requirement",
    "sustainability_general", "unknown",
]
ALLOWED_TYPES = [
    "application_guidance", "parameter_spec", "operational_sequence",
    "performance_spec", "maintenance_procedure", "fault_code",
    "fault_diagnostic_rule", "diagnostic_step", "symptom",
]


@dataclass(frozen=True)
class SectionSeed:
    section_index: int
    section_title: str
    page_start: int
    page_end: int
    confidence: str
    candidate_knowledge_types: list[str]
    sample_text: str


def confidence_rank(value: str) -> int:
    return {"none": 0, "low": 1, "medium": 2, "high": 3}.get(str(value or "none"), 0)


def choose_section_seeds(payload: dict[str, Any], limit: int) -> list[SectionSeed]:
    rows = []
    for idx, row in enumerate(payload.get("sections", [])):
        types = [str(item) for item in row.get("candidate_knowledge_types", [])]
        score = confidence_rank(row.get("confidence")) * 10 + len(types) * 3
        rows.append((score, idx, row, types))
    selected = sorted(rows, key=lambda item: (-item[0], item[2].get("page_start", 0)))[:limit]
    return [
        SectionSeed(
            section_index=idx,
            section_title=str(row.get("section_title") or "untitled"),
            page_start=int(row.get("page_start") or 0),
            page_end=int(row.get("page_end") or 0),
            confidence=str(row.get("confidence") or "none"),
            candidate_knowledge_types=types,
            sample_text=str(row.get("sample_text") or "")[:800],
        )
        for _, idx, row, types in selected
    ]


def build_document_messages(payload: dict[str, Any], seeds: list[SectionSeed]) -> list[dict[str, str]]:
    brief = [
        {
            "section_index": item.section_index,
            "title": item.section_title,
            "pages": f"{item.page_start}-{item.page_end}",
            "types": item.candidate_knowledge_types,
            "sample": item.sample_text[:220],
        }
        for item in seeds[:12]
    ]
    system = (
        "You are routing one industrial reference document before extraction. "
        "Classify the document mission and active knowledge lane. "
        "Reply with strict JSON only."
    )
    user = {
        "doc_name": payload.get("doc_name"),
        "allowed_document_families": DOC_FAMILIES,
        "allowed_document_lanes": DOC_LANES,
        "section_samples": brief,
        "required_output": {
            "document_family": "one allowed label",
            "document_lane": "one allowed label",
            "default_equipment_anchor": "chiller|general_hvac|mixed|none",
            "should_run_equipment_pipeline": True,
            "reason": "short reason",
            "confidence": "high|medium|low",
        },
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def build_section_messages(
    payload: dict[str, Any],
    doc_route: dict[str, Any],
    batch: list[SectionSeed],
) -> list[dict[str, str]]:
    system = (
        "You route section-level extraction targets for industrial standards. "
        "Decide topic, extraction lane fit, allowed knowledge types, and equipment anchor. "
        "Reply with strict JSON only."
    )
    user = {
        "doc_name": payload.get("doc_name"),
        "document_route": doc_route,
        "allowed_section_topics": SECTION_TOPICS,
        "allowed_knowledge_types": ALLOWED_TYPES,
        "sections": [item.__dict__ for item in batch],
        "required_output": {
            "sections": [
                {
                    "section_index": 0,
                    "section_topic": "one allowed label",
                    "knowledge_goal": "equipment_operational|system_design|audit_methodology|system_topic_reference|out_of_scope",
                    "allowed_knowledge_types": ["application_guidance"],
                    "equipment_anchor": "chiller|general_hvac|mixed|none",
                    "should_extract": True,
                    "reason": "short reason",
                    "confidence": "high|medium|low",
                }
            ]
        },
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def route_document(
    payload: dict[str, Any],
    seeds: list[SectionSeed],
    *,
    backend_name: str | None = None,
) -> dict[str, Any]:
    backend = resolve_backend(backend_name=backend_name)
    if backend is None:
        raise RuntimeError("No LLM backend available for document routing")
    return _request_json_completion(
        build_document_messages(payload, seeds),
        backend,
        response_format={"type": "json_object"},
    )


def route_sections(
    payload: dict[str, Any],
    doc_route: dict[str, Any],
    seeds: list[SectionSeed],
    *,
    batch_size: int = 5,
    backend_name: str | None = None,
) -> dict[int, dict[str, Any]]:
    backend = resolve_backend(backend_name=backend_name)
    if backend is None:
        raise RuntimeError("No LLM backend available for section routing")
    routed: dict[int, dict[str, Any]] = {}
    for start in range(0, len(seeds), batch_size):
        batch = seeds[start: start + batch_size]
        response = _request_json_completion(
            build_section_messages(payload, doc_route, batch),
            backend,
            response_format={"type": "json_object"},
        )
        for row in response.get("sections", []):
            routed[int(row["section_index"])] = row
    return routed


def merge_payload(
    payload: dict[str, Any],
    doc_route: dict[str, Any],
    routed_sections: dict[int, dict[str, Any]],
    backend_name: str,
) -> dict[str, Any]:
    merged = json.loads(json.dumps(payload, ensure_ascii=False))
    merged["llm_routing"] = {
        "backend": backend_name,
        "document_route": doc_route,
        "section_routes": {
            str(k): v for k, v in sorted(routed_sections.items())
        },
    }
    for idx, section in enumerate(merged.get("sections", [])):
        route = routed_sections.get(idx)
        if route is None:
            continue
        section["llm_section_topic"] = route.get("section_topic")
        section["llm_knowledge_goal"] = route.get("knowledge_goal")
        section["llm_allowed_knowledge_types"] = route.get("allowed_knowledge_types")
        section["llm_should_extract"] = route.get("should_extract")
        section["llm_equipment_anchor"] = route.get("equipment_anchor")
        section["llm_route_reason"] = route.get("reason")
        section["llm_route_confidence"] = route.get("confidence")
    return merged
