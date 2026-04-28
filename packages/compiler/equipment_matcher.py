"""Ontology equipment matching helpers for compilation."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from packages.core.sw_base_model_ontology_client import SwBaseModelOntologyClient
from packages.db.models import ContentChunk, Document
from packages.db.models_v2 import OntologyAliasV2
from packages.domain_kit_v2.loader import load_domain_package_v2


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
def load_document_profile_map(domain_id: str) -> dict[str, set[str]]:
    """Load preferred knowledge-object hints by document profile."""

    path = (
        Path(__file__).resolve().parents[2]
        / "domain_packages"
        / domain_id
        / "v2"
        / "coverage"
        / "document_profiles.yaml"
    )
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


def normalize_text(text: str) -> str:
    """Normalize free-form text for matching."""

    return re.sub(r"\s+", " ", text.strip().lower())


def build_search_text(chunk: ContentChunk, document: Document) -> str:
    """Build matching text from one chunk/document pair."""

    return normalize_text(" ".join(filter(None, [chunk.cleaned_text, chunk.text_excerpt, document.file_name])))


def _iter_label_terms(equipment_class: dict[str, Any]) -> list[AliasTerm]:
    labels = list((equipment_class.get("labels") or {}).values())
    labels.append(equipment_class["primary_label"])
    unique = []
    seen = set()
    for label in labels:
        normalized = normalize_text(label)
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


class EquipmentMatcher:
    """Build equipment matching profiles from sw_base_model classes and local aliases."""

    def __init__(self, ontology_client: SwBaseModelOntologyClient | None = None) -> None:
        self.ontology_client = ontology_client or SwBaseModelOntologyClient()

    def build_equipment_profiles(self, db: Session, domain_id: str) -> list[EquipmentClassProfile]:
        """Load equipment classes and alias terms for one domain."""

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
        for class_row in _load_domain_equipment_rows(domain_id):
            equipment_class = self.ontology_client.get_equipment_class(class_row["ontology_class_id"])
            if equipment_class is None:
                continue
            class_key = class_row["ontology_class_key"]
            terms = alias_map[class_key] + _iter_label_terms(equipment_class)
            profiles.append(
                EquipmentClassProfile(
                    ontology_class_key=class_key,
                    ontology_class_id=class_row["ontology_class_id"],
                    primary_label=equipment_class["primary_label"],
                    knowledge_anchors=tuple(class_row["knowledge_anchors"]),
                    terms=tuple(terms),
                )
            )
        return profiles


def _load_domain_equipment_rows(domain_id: str) -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[2] / "domain_packages" / domain_id / "v2"
    bundle = load_domain_package_v2(root)
    rows = []
    for item in bundle.ontology_classes.classes:
        if item.kind != "equipment":
            continue
        rows.append(
            {
                "ontology_class_key": f"{domain_id}:{item.id}",
                "ontology_class_id": item.id,
                "knowledge_anchors": item.knowledge_anchors,
            }
        )
    return rows


def build_equipment_profiles(
    db: Session,
    domain_id: str,
    ontology_client: SwBaseModelOntologyClient | None = None,
) -> list[EquipmentClassProfile]:
    """Load equipment classes and alias terms for one domain."""

    return EquipmentMatcher(ontology_client).build_equipment_profiles(db, domain_id)


def _score_alias_match(text: str, term: AliasTerm) -> float | None:
    if term.normalized not in text:
        return None
    length_boost = min(len(term.normalized), 24) / 36
    preferred_boost = 0.06 if term.is_preferred else 0.0
    source_boost = 0.03 if term.source == "label" else 0.0
    return min(0.3 + length_boost + preferred_boost + source_boost, 0.98)


def match_equipment_class(
    profiles: list[EquipmentClassProfile],
    search_text: str,
    equipment_class_id: str | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Resolve one equipment class candidate from free-form search text."""

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
