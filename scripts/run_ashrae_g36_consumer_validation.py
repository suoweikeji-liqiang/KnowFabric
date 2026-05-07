#!/usr/bin/env python3
"""Validate ASHRAE G36 knowledge from a consumer-query perspective."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.session import SessionLocal  # noqa: E402
from packages.retrieval.semantic_service import SemanticRetrievalService  # noqa: E402


@dataclass(frozen=True)
class ConsumerScenario:
    scenario_id: str
    question: str
    equipment_class_id: str
    service_family: str
    knowledge_object_type: str
    expected_sections: tuple[str, ...]
    keyword_groups: tuple[tuple[str, ...], ...]
    min_matches: int = 1


SCENARIOS = (
    ConsumerScenario(
        "ahu_low_airflow_alarm",
        "For an AHU or VAV terminal, what does G36 say about low airflow alarms?",
        "ahu",
        "fault_knowledge",
        "fault_diagnostic_rule",
        ("5.5.6.1", "5.6.6.1", "5.7.6.1", "5.8.6.1", "5.10.6.1", "5.12.6.1", "5.13.6.1", "5.14.6.1"),
        (("low", "airflow"), ("alarm",)),
        min_matches=3,
    ),
    ConsumerScenario(
        "ahu_sat_reset",
        "How are AHU SAT reset requests generated?",
        "ahu",
        "operational_guidance",
        "operational_sequence",
        ("5.6.8.1", "5.8.8.1", "5.10.8.1", "5.12.8.1", "5.14.8.1"),
        (("sat", "reset"), ("request",)),
        min_matches=3,
    ),
    ConsumerScenario(
        "ahu_static_pressure_reset",
        "How are duct static pressure reset requests generated?",
        "ahu",
        "operational_guidance",
        "operational_sequence",
        ("5.6.8.2", "5.8.8.2", "5.10.8.2", "5.12.8.2", "5.14.8.2", "5.16.1.2", "5.17.1.2"),
        (("static", "pressure"), ("reset",)),
        min_matches=3,
    ),
    ConsumerScenario(
        "ahu_afdd",
        "What AFDD rules and fault conditions are available for AHUs?",
        "ahu",
        "fault_knowledge",
        "fault_diagnostic_rule",
        ("5.16.14", "5.17.4", "5.18.13", "5.22.6"),
        (("afdd",), ("fc",)),
        min_matches=3,
    ),
    ConsumerScenario(
        "chiller_plant_enable_disable",
        "How should the chilled water plant be enabled and disabled?",
        "chiller",
        "operational_guidance",
        "operational_sequence",
        ("5.20.2.2", "5.20.2.3"),
        (("plant",), ("enable", "disable")),
        min_matches=2,
    ),
    ConsumerScenario(
        "chiller_stage_up_down",
        "What does G36 say about chiller stage up and stage down logic?",
        "chiller",
        "operational_guidance",
        "operational_sequence",
        ("5.20.4.15",),
        (("stage",), ("up", "down")),
        min_matches=3,
    ),
    ConsumerScenario(
        "chiller_afdd",
        "What AFDD fault diagnostics are available for the chilled water plant?",
        "chiller",
        "fault_knowledge",
        "fault_diagnostic_rule",
        ("5.20.18.6",),
        (("afdd",), ("fc",)),
        min_matches=3,
    ),
    ConsumerScenario(
        "hot_water_plant_enable_disable",
        "How should the hot water plant or boiler plant be enabled and disabled?",
        "hot_water_plant",
        "operational_guidance",
        "operational_sequence",
        ("5.21.2.2", "5.21.2.3"),
        (("plant", "boiler"), ("enable", "disable")),
        min_matches=2,
    ),
    ConsumerScenario(
        "hot_water_boiler_staging",
        "What does G36 say about boiler stage up and stage down logic?",
        "hot_water_plant",
        "operational_guidance",
        "operational_sequence",
        ("5.21.3.9",),
        (("boiler",), ("stage",)),
        min_matches=3,
    ),
    ConsumerScenario(
        "hot_water_fault_diagnostics",
        "What hot water plant AFDD fault conditions are available?",
        "hot_water_plant",
        "fault_knowledge",
        "fault_diagnostic_rule",
        ("5.21.11.6",),
        (("afdd",), ("fc",)),
        min_matches=3,
    ),
)


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def item_section(item: dict[str, Any]) -> str:
    payload = item.get("structured_payload") or {}
    return str(payload.get("section_id") or payload.get("source_section_id") or "")


def item_text(item: dict[str, Any]) -> str:
    payload = item.get("structured_payload") or {}
    evidence = " ".join(str(row.get("evidence_text") or "") for row in item.get("evidence") or [])
    return normalize_text(" ".join([item.get("title") or "", item.get("summary") or "", json.dumps(payload, ensure_ascii=False), evidence]))


def item_has_evidence(item: dict[str, Any]) -> bool:
    return any(str(row.get("evidence_text") or "").strip() for row in item.get("evidence") or [])


def section_matches(section_id: str, expected_sections: tuple[str, ...]) -> bool:
    return any(section_id == expected or section_id.startswith(f"{expected}.") for expected in expected_sections)


def keyword_matches(text: str, groups: tuple[tuple[str, ...], ...]) -> bool:
    text = normalize_text(text)
    return all(any(keyword.lower() in text for keyword in group) for group in groups)


def query_service(
    service: SemanticRetrievalService,
    db: Any,
    scenario: ConsumerScenario,
    *,
    min_trust_level: str,
    limit: int,
) -> dict[str, Any] | None:
    kwargs = {
        "db": db,
        "domain_id": "hvac",
        "equipment_class_id": scenario.equipment_class_id,
        "min_trust_level": min_trust_level,
        "limit": limit,
    }
    if scenario.service_family == "fault_knowledge":
        return service.get_fault_knowledge(**kwargs)
    if scenario.service_family == "operational_guidance":
        return service.get_operational_guidance(**kwargs, guidance_type=scenario.knowledge_object_type)
    if scenario.service_family == "parameter_profiles":
        return service.get_parameter_profiles(**kwargs)
    if scenario.service_family == "application_guidance":
        return service.get_application_guidance(**kwargs)
    raise ValueError(f"Unsupported service_family: {scenario.service_family}")


def matching_items(items: list[dict[str, Any]], scenario: ConsumerScenario) -> list[dict[str, Any]]:
    matches = []
    for item in items:
        if item.get("knowledge_object_type") != scenario.knowledge_object_type:
            continue
        text = item_text(item)
        section_id = item_section(item)
        if section_matches(section_id, scenario.expected_sections) and keyword_matches(text, scenario.keyword_groups):
            matches.append(item)
    return matches


def evaluate_scenario(payload: dict[str, Any] | None, scenario: ConsumerScenario) -> dict[str, Any]:
    items = payload.get("items", []) if payload else []
    matches = matching_items(items, scenario)
    evidence_ok = [item for item in matches if item_has_evidence(item)]
    status = "pass" if len(evidence_ok) >= scenario.min_matches else "fail"
    return {
        "scenario_id": scenario.scenario_id,
        "question": scenario.question,
        "equipment_class_id": scenario.equipment_class_id,
        "service_family": scenario.service_family,
        "knowledge_object_type": scenario.knowledge_object_type,
        "expected_sections": list(scenario.expected_sections),
        "keyword_groups": [list(group) for group in scenario.keyword_groups],
        "min_matches": scenario.min_matches,
        "service_total_count": payload.get("total_count", 0) if payload else 0,
        "service_returned_count": payload.get("returned_count", 0) if payload else 0,
        "service_has_more": payload.get("has_more", False) if payload else False,
        "matched_count": len(matches),
        "matched_with_evidence_count": len(evidence_ok),
        "status": status,
        "sample_matches": [public_item(item) for item in evidence_ok[:8]],
    }


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") or []
    return {
        "canonical_key": item.get("canonical_key"),
        "knowledge_object_type": item.get("knowledge_object_type"),
        "title": item.get("title"),
        "section_id": item_section(item),
        "trust_level": item.get("trust_level"),
        "page_nos": [row.get("page_no") for row in evidence if row.get("page_no") is not None],
        "evidence_sample": str(evidence[0].get("evidence_text"))[:240] if evidence else "",
    }


def run_validation(*, min_trust_level: str = "L3", limit: int = 500) -> dict[str, Any]:
    service = SemanticRetrievalService()
    db = SessionLocal()
    try:
        results = [
            evaluate_scenario(
                query_service(service, db, scenario, min_trust_level=min_trust_level, limit=limit),
                scenario,
            )
            for scenario in SCENARIOS
        ]
    finally:
        db.close()
    passed = sum(1 for row in results if row["status"] == "pass")
    return {
        "validation_mode": "ashrae_g36_consumer_validation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "min_trust_level": min_trust_level,
        "limit": limit,
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "results": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ASHRAE G36 Consumer Validation Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Min trust level: `{report['min_trust_level']}`",
        f"- Service limit: {report['limit']}",
        f"- Passed/failed: {report['summary']['passed']}/{report['summary']['failed']}",
        "",
        "| Scenario | Equipment | Service | Status | Matches | Expected Sections |",
        "|---|---|---|---|---:|---|",
    ]
    for row in report["results"]:
        lines.append(
            f"| `{row['scenario_id']}` | `{row['equipment_class_id']}` | `{row['service_family']}` | "
            f"{row['status']} | {row['matched_with_evidence_count']} / {row['min_matches']} | "
            f"`{', '.join(row['expected_sections'])}` |"
        )
    lines.extend(render_samples(report))
    return "\n".join(lines)


def render_samples(report: dict[str, Any]) -> list[str]:
    lines = ["", "## Samples", ""]
    for row in report["results"]:
        lines.append(f"### {row['scenario_id']} ({row['status']})")
        lines.append("")
        lines.append(f"Question: {row['question']}")
        lines.append("")
        for item in row["sample_matches"][:5]:
            pages = ", ".join(str(page) for page in item["page_nos"][:5])
            lines.append(f"- §{item['section_id']} / {item['trust_level']} / p{pages}: {item['title']}")
            if item["evidence_sample"]:
                lines.append(f"  Evidence: {item['evidence_sample']}")
        if not row["sample_matches"]:
            lines.append("- No matching evidence-backed items found.")
        lines.append("")
    return lines


def write_outputs(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "consumer_validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "CONSUMER_VALIDATION_REPORT.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def default_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("workspace/ashrae_g36_consumer_validation") / stamp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--min-trust-level", default="L3")
    parser.add_argument("--limit", type=int, default=500)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_validation(min_trust_level=args.min_trust_level, limit=args.limit)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    write_outputs(output_dir, report)
    print(
        f"consumer_validation passed={report['summary']['passed']}/{report['summary']['total']} "
        f"failed={report['summary']['failed']} report={output_dir / 'CONSUMER_VALIDATION_REPORT.md'}"
    )
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
