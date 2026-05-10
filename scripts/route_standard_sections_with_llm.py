#!/usr/bin/env python3
"""LLM-assisted document/section routing for standard-reference section matrices."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import _request_json_completion
from scripts.llm_backend_config import load_backend


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
    "chiller",
    "ahu",
    "cooling_tower",
    "pump",
    "boiler",
    "valve_control",
    "desiccant_system",
    "dynamic_glazing",
    "air_distribution",
    "general_hvac_design",
    "audit_process",
    "reporting_requirement",
    "sustainability_general",
    "unknown",
]
ALLOWED_TYPES = [
    "application_guidance",
    "parameter_spec",
    "operational_sequence",
    "performance_spec",
    "maintenance_procedure",
    "fault_code",
    "fault_diagnostic_rule",
    "diagnostic_step",
    "symptom",
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


def load_matrix(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]


def build_section_messages(payload: dict[str, Any], doc_route: dict[str, Any], batch: list[SectionSeed]) -> list[dict[str, str]]:
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
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]


def route_document(payload: dict[str, Any], backend_name: str, config_path: str | None, seeds: list[SectionSeed]) -> dict[str, Any]:
    backend, _ = load_backend(backend_name, config_path)
    return _request_json_completion(build_document_messages(payload, seeds), backend, response_format={"type": "json_object"})


def route_sections(payload: dict[str, Any], backend_name: str, config_path: str | None, doc_route: dict[str, Any], seeds: list[SectionSeed], batch_size: int) -> dict[int, dict[str, Any]]:
    backend, _ = load_backend(backend_name, config_path)
    routed: dict[int, dict[str, Any]] = {}
    for start in range(0, len(seeds), batch_size):
        batch = seeds[start : start + batch_size]
        response = _request_json_completion(build_section_messages(payload, doc_route, batch), backend, response_format={"type": "json_object"})
        for row in response.get("sections", []):
            routed[int(row["section_index"])] = row
    return routed


def merge_payload(payload: dict[str, Any], doc_route: dict[str, Any], routed_sections: dict[int, dict[str, Any]], backend_name: str) -> dict[str, Any]:
    merged = json.loads(json.dumps(payload, ensure_ascii=False))
    merged["llm_routing"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend_name": backend_name,
        "document_route": doc_route,
        "routed_section_count": len(routed_sections),
    }
    for idx, row in enumerate(merged.get("sections", [])):
        route = routed_sections.get(idx)
        if not route:
            continue
        row["llm_section_topic"] = route.get("section_topic")
        row["llm_knowledge_goal"] = route.get("knowledge_goal")
        row["llm_allowed_knowledge_types"] = route.get("allowed_knowledge_types") or []
        row["llm_equipment_anchor"] = route.get("equipment_anchor")
        row["llm_should_extract"] = bool(route.get("should_extract"))
        row["llm_route_reason"] = route.get("reason")
        row["llm_route_confidence"] = route.get("confidence")
    return merged


def render_markdown(payload: dict[str, Any]) -> str:
    doc_route = payload.get("llm_routing", {}).get("document_route", {})
    lines = [
        "# LLM Routed Section Matrix",
        "",
        f"- Document: `{payload.get('doc_name')}`",
        f"- Doc ID: `{payload.get('doc_id')}`",
        f"- Backend: `{payload.get('llm_routing', {}).get('backend_name', '')}`",
        f"- Document family: `{doc_route.get('document_family', '')}`",
        f"- Document lane: `{doc_route.get('document_lane', '')}`",
        f"- Default equipment anchor: `{doc_route.get('default_equipment_anchor', '')}`",
        f"- Equipment pipeline: `{doc_route.get('should_run_equipment_pipeline', '')}`",
        "",
        "| Section | Pages | Topic | Goal | Extract | Anchor | Allowed Types | Reason |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for row in payload.get("sections", []):
        lines.append(
            f"| {str(row.get('section_title') or '')[:80]} | {row.get('page_start')}-{row.get('page_end')} | "
            f"{row.get('llm_section_topic') or '-'} | {row.get('llm_knowledge_goal') or '-'} | "
            f"{row.get('llm_should_extract')} | {row.get('llm_equipment_anchor') or '-'} | "
            f"{', '.join(row.get('llm_allowed_knowledge_types') or []) or '-'} | {str(row.get('llm_route_reason') or '')[:90].replace('|','/')} |"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--backend-name", default="deepseek-parameter-spec")
    parser.add_argument("--backend-config")
    parser.add_argument("--section-limit", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = load_matrix(args.matrix_json)
    seeds = choose_section_seeds(payload, args.section_limit)
    doc_route = route_document(payload, args.backend_name, args.backend_config, seeds)
    routed_sections = route_sections(payload, args.backend_name, args.backend_config, doc_route, seeds, args.batch_size)
    merged = merge_payload(payload, doc_route, routed_sections, args.backend_name)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "section_target_matrix_routed.json"
    md_path = args.output_dir / "SECTION_TARGET_MATRIX_ROUTED.md"
    json_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(merged), encoding="utf-8")
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
