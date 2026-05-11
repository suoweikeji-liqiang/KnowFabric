"""Health checks for compiler candidates, review bundles, and knowledge objects.

Checks follow a scan→finding→review pattern. Never auto-modify KOs.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from packages.compiler.cross_source_merger import _coerce_numeric, _values_agree


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


# --- P1: Conflict detection (KO-to-KO, different canonical_key same concept) ---


def detect_ko_conflicts(
    knowledge_objects: list[dict[str, Any]],
    *,
    tolerance: float = 0.05,
) -> list[dict[str, Any]]:
    """Scan same-anchor + same-type KO pairs for value conflicts.

    Pairs different canonical_keys under the same ontology_class_id +
    knowledge_object_type. If their structured payloads have similar-looking
    parameter names but different values, flag as potential conflict.

    Returns list of findings with: code, severity, ko_a, ko_b, reason.
    """
    findings = []
    for i, ko_a in enumerate(knowledge_objects):
        for ko_b in knowledge_objects[i + 1:]:
            if ko_a.get("ontology_class_id") != ko_b.get("ontology_class_id"):
                continue
            if ko_a.get("knowledge_object_type") != ko_b.get("knowledge_object_type"):
                continue
            if ko_a.get("canonical_key") == ko_b.get("canonical_key"):
                continue

            payload_a = ko_a.get("structured_payload_json") or {}
            payload_b = ko_b.get("structured_payload_json") or {}

            name_a = str(payload_a.get("parameter_name") or ko_a.get("title") or "")
            name_b = str(payload_b.get("parameter_name") or ko_b.get("title") or "")

            # Only flag if names look similar (shared words) but values differ
            words_a = set(re.findall(r"[a-zA-Z0-9]+", name_a.lower()))
            words_b = set(re.findall(r"[a-zA-Z0-9]+", name_b.lower()))
            overlap = words_a & words_b
            if len(overlap) < 2:
                continue

            val_a = payload_a.get("value") or payload_a.get("default_value")
            val_b = payload_b.get("value") or payload_b.get("default_value")
            if val_a is None or val_b is None:
                continue
            if _values_agree(val_a, val_b):
                continue

            findings.append({
                "code": "ko_conflict",
                "severity": "medium",
                "scope": "knowledge_object_pair",
                "ko_a": ko_a.get("knowledge_object_id"),
                "ko_b": ko_b.get("knowledge_object_id"),
                "canonical_key_a": ko_a.get("canonical_key"),
                "canonical_key_b": ko_b.get("canonical_key"),
                "name_a": name_a,
                "name_b": name_b,
                "value_a": val_a,
                "value_b": val_b,
                "message": (
                    f"Possible duplicate concept with conflicting values: "
                    f"'{name_a}' ({val_a}) vs '{name_b}' ({val_b})"
                ),
            })
    return findings


# --- P2: Terminology drift (vendor naming variants) ---


def detect_terminology_drift(
    knowledge_objects: list[dict[str, Any]],
    aliases: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Detect parameter names that may be vendor-specific variants of the same concept.

    Heuristic: within same ontology_class_id + knowledge_object_type, flag names
    that share significant word overlap but have different canonical_keys.

    Returns findings suggesting alias candidates.
    """
    existing_aliases: dict[str, set[str]] = {}
    if aliases:
        for a in aliases:
            cid = a.get("ontology_class_id") or a.get("class_id", "")
            existing_aliases.setdefault(cid, set()).add(
                str(a.get("alias_text") or a.get("normalized_alias", "")).lower()
            )

    findings = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for ko in knowledge_objects:
        key = (ko.get("ontology_class_id", ""), ko.get("knowledge_object_type", ""))
        grouped[key].append(ko)

    for (class_id, ko_type), kos in grouped.items():
        for i, ko_a in enumerate(kos):
            for ko_b in kos[i + 1:]:
                payload_a = ko_a.get("structured_payload_json") or {}
                payload_b = ko_b.get("structured_payload_json") or {}
                name_a = str(payload_a.get("parameter_name") or ko_a.get("title") or "").lower()
                name_b = str(payload_b.get("parameter_name") or ko_b.get("title") or "").lower()
                if name_a == name_b:
                    continue

                words_a = set(re.findall(r"[a-zA-Z0-9]+", name_a))
                words_b = set(re.findall(r"[a-zA-Z0-9]+", name_b))
                overlap = words_a & words_b
                total = words_a | words_b
                if not total:
                    continue
                jaccard = len(overlap) / len(total)
                if jaccard < 0.4:
                    continue

                # Check if already aliased
                existing = existing_aliases.get(class_id, set())
                if name_a in existing and name_b in existing:
                    continue

                findings.append({
                    "code": "terminology_drift",
                    "severity": "low",
                    "scope": "knowledge_object_pair",
                    "ontology_class_id": class_id,
                    "knowledge_object_type": ko_type,
                    "ko_a": ko_a.get("knowledge_object_id"),
                    "ko_b": ko_b.get("knowledge_object_id"),
                    "name_a": name_a,
                    "name_b": name_b,
                    "overlap_ratio": round(jaccard, 3),
                    "message": f"Possible vendor naming variant: '{name_a}' ↔ '{name_b}' (Jaccard={jaccard:.2f})",
                })
    return findings


# --- P3: Applicability ambiguity ---


def detect_applicability_ambiguity(
    knowledge_objects: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Detect KOs with missing or thin applicability that may have brand/model
    hints in evidence text.

    Heuristic: flag KOs where applicability_json is empty/near-empty but
    evidence_text contains brand-like patterns.
    """
    brand_patterns = [
        r"\b(Trane|York|Carrier|Daikin|McQuay|ABB|Siemens|Danfoss|Hitachi|Mitsubishi|LG|Samsung|Panasonic|Schneider|Emerson|Toshiba|Honeywell)\b",
        r"\b(特灵|约克|开利|大金|麦克维尔|三菱|日立|格力|美的|海尔|天加)\b",
    ]

    evidence_by_ko: dict[str, list[str]] = defaultdict(list)
    if evidence_rows:
        for ev in evidence_rows:
            ko_id = ev.get("knowledge_object_id", "")
            text = ev.get("evidence_text", "")
            if ko_id and text:
                evidence_by_ko[ko_id].append(text)

    findings = []
    for ko in knowledge_objects:
        applicability = ko.get("applicability_json") or {}
        has_brand = bool(applicability.get("brand"))
        has_model = bool(applicability.get("model_family"))

        if has_brand or has_model:
            continue

        texts = evidence_by_ko.get(ko.get("knowledge_object_id", ""), [])
        combined_text = " ".join(texts)

        found_brands = set()
        for pattern in brand_patterns:
            found_brands.update(re.findall(pattern, combined_text, re.IGNORECASE))

        if found_brands and (not has_brand or not has_model):
            findings.append({
                "code": "applicability_ambiguity",
                "severity": "low",
                "scope": "knowledge_object",
                "knowledge_object_id": ko.get("knowledge_object_id"),
                "ko_type": ko.get("knowledge_object_type"),
                "current_applicability": applicability,
                "potential_brands_in_evidence": sorted(found_brands),
                "message": (
                    f"KO lacks full applicability but evidence mentions: "
                    f"{', '.join(sorted(found_brands))}"
                ),
            })
    return findings


# --- P4: Anchor quality ---


def detect_anchor_quality_issues(
    knowledge_objects: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Detect KOs whose ontology_anchor may be questionable.

    Heuristic: flag KOs where the evidence text doesn't contain any token
    related to the equipment class name, suggesting the anchor may be wrong.
    """
    evidence_by_ko: dict[str, list[str]] = defaultdict(list)
    if evidence_rows:
        for ev in evidence_rows:
            ko_id = ev.get("knowledge_object_id", "")
            text = ev.get("evidence_text", "")
            if ko_id and text:
                evidence_by_ko[ko_id].append(text)

    findings = []
    for ko in knowledge_objects:
        class_id = ko.get("ontology_class_id", "")
        if not class_id:
            continue

        class_tokens = set(re.findall(r"[a-zA-Z0-9]+", class_id.lower()))
        if not class_tokens:
            continue

        texts = evidence_by_ko.get(ko.get("knowledge_object_id", ""), [])
        if not texts:
            continue

        combined = " ".join(texts).lower()
        matched = {t for t in class_tokens if t in combined}
        match_ratio = len(matched) / len(class_tokens) if class_tokens else 1.0

        if match_ratio < 0.3:
            findings.append({
                "code": "anchor_quality",
                "severity": "medium",
                "scope": "knowledge_object",
                "knowledge_object_id": ko.get("knowledge_object_id"),
                "ontology_class_id": class_id,
                "class_tokens_in_evidence": sorted(matched),
                "class_tokens_missing": sorted(class_tokens - matched),
                "match_ratio": round(match_ratio, 3),
                "message": (
                    f"Weak anchor: only {len(matched)}/{len(class_tokens)} class tokens "
                    f"found in evidence for '{class_id}'"
                ),
            })
    return findings


def build_full_health_report(
    knowledge_objects: list[dict[str, Any]],
    *,
    evidence_rows: list[dict[str, Any]] | None = None,
    aliases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run all health checks and produce a unified report.

    Args:
        knowledge_objects: List of KO dicts (from DB or review packs).
        evidence_rows: Optional evidence dicts with knowledge_object_id and evidence_text.
        aliases: Optional OntologyAliasV2 dicts for drift detection.

    Returns:
        Unified health report dict with summary + all findings.
    """
    all_findings: list[dict[str, Any]] = []

    conflicts = detect_ko_conflicts(knowledge_objects)
    all_findings.extend(conflicts)

    drifts = detect_terminology_drift(knowledge_objects, aliases=aliases)
    all_findings.extend(drifts)

    ambiguities = detect_applicability_ambiguity(knowledge_objects, evidence_rows=evidence_rows)
    all_findings.extend(ambiguities)

    anchor_issues = detect_anchor_quality_issues(knowledge_objects, evidence_rows=evidence_rows)
    all_findings.extend(anchor_issues)

    by_code: dict[str, int] = defaultdict(int)
    for f in all_findings:
        by_code[f["code"]] += 1

    return {
        "health_mode": "full_health_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_findings": len(all_findings),
            "by_code": dict(by_code),
        },
        "findings": all_findings,
    }
