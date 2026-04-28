"""Health checks for compiler candidates and review bundles."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


def candidate_health_findings(candidate_entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute lightweight candidate-level health findings."""

    findings = []
    confidence_score = float(candidate_entry.get("confidence_score") or 0.0)
    evidence_text = str(candidate_entry.get("evidence_text") or "")
    equipment = candidate_entry.get("equipment_class_candidate", {})
    alternatives = candidate_entry.get("match_metadata", {}).get("alternative_equipment_class_candidates", [])
    if confidence_score < 0.78 or len(evidence_text.strip()) < 40:
        findings.append(
            {
                "code": "weak_evidence",
                "severity": "medium",
                "message": "Candidate relies on limited confidence or a short evidence span.",
            }
        )
    if float(equipment.get("confidence") or 0.0) < 0.85 or alternatives:
        findings.append(
            {
                "code": "anchor_uncertainty",
                "severity": "medium",
                "message": "Equipment-class anchoring is ambiguous or has close alternatives.",
            }
        )
    return findings


def build_bundle_health_report(
    review_pack_manifest: dict[str, Any],
    bootstrapped_packs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one machine-readable health report for a prepared review bundle."""

    findings: list[dict[str, Any]] = []
    coverage_by_class: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"supported": set(), "present": set()})

    for pack in bootstrapped_packs:
        equipment = pack.get("equipment_class", {})
        class_key = str(equipment.get("equipment_class_key") or equipment.get("equipment_class_id") or "unknown")
        supported = equipment.get("supported_knowledge_anchors", [])
        if isinstance(supported, list):
            coverage_by_class[class_key]["supported"].update(str(item) for item in supported)

        for entry in pack.get("candidate_entries", []):
            entry_supported = entry.get("equipment_class_candidate", {}).get("supported_knowledge_anchors", [])
            if isinstance(entry_supported, list):
                coverage_by_class[class_key]["supported"].update(str(item) for item in entry_supported)
            knowledge_type = entry.get("knowledge_object_type")
            if isinstance(knowledge_type, str):
                coverage_by_class[class_key]["present"].add(knowledge_type)
            for finding in entry.get("health_findings", []):
                findings.append(
                    {
                        "scope": "candidate",
                        "equipment_class_key": class_key,
                        "doc_id": entry.get("doc_id"),
                        "candidate_id": entry.get("candidate_id"),
                        **finding,
                    }
                )
            if entry.get("review_decision") == "accepted":
                applicability = entry.get("curation", {}).get("applicability", {})
                if isinstance(applicability, dict) and not applicability:
                    findings.append(
                        {
                            "scope": "candidate",
                            "equipment_class_key": class_key,
                            "doc_id": entry.get("doc_id"),
                            "candidate_id": entry.get("candidate_id"),
                            "code": "applicability_missing",
                            "severity": "low",
                            "message": "Accepted entry still has an empty applicability block.",
                        }
                    )

    for class_key, coverage in sorted(coverage_by_class.items()):
        missing = sorted(coverage["supported"] - coverage["present"])
        if missing:
            findings.append(
                {
                    "scope": "equipment_class",
                    "equipment_class_key": class_key,
                    "code": "coverage_gap",
                    "severity": "medium",
                    "message": "Supported knowledge anchors are missing from the prepared candidate set.",
                    "missing_knowledge_types": missing,
                }
            )

    summary = {
        "total_findings": len(findings),
        "by_code": defaultdict(int),
        "review_packs": review_pack_manifest.get("total_packs", 0),
    }
    for finding in findings:
        summary["by_code"][finding["code"]] += 1

    return {
        "health_mode": "review_bundle_health_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_findings": summary["total_findings"],
            "by_code": dict(summary["by_code"]),
            "review_packs": summary["review_packs"],
        },
        "findings": findings,
    }
