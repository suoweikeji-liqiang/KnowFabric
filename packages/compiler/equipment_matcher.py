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

from packages.db.models import ContentChunk, Document
from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2


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


def _iter_label_terms(ontology_class: OntologyClassV2) -> list[AliasTerm]:
    labels = list((ontology_class.labels_json or {}).values())
    labels.append(ontology_class.primary_label)
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


def build_equipment_profiles(db: Session, domain_id: str) -> list[EquipmentClassProfile]:
    """Load equipment classes and alias terms for one domain."""

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
