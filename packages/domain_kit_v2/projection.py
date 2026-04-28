"""Helpers for projecting ontology-first domain packages into database rows."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from .models import DomainPackageV2

ALIASES_FILE = Path("ontology/aliases.yaml")
MAPPINGS_FILE = Path("ontology/mappings.yaml")
STRUCTURAL_MAPPING_SYSTEMS = {"brick", "223p", "open223"}


def make_ontology_class_key(domain_id: str, ontology_class_id: str) -> str:
    """Build the persisted scoped key for a local ontology id."""

    return f"{domain_id}:{ontology_class_id}"


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object at the top level")
    return data


def _normalize_alias(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    if not normalized:
        raise ValueError("alias_text must not be empty")
    return normalized


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _primary_label(labels: dict[str, str]) -> str:
    if "en" in labels:
        return labels["en"]
    return next(iter(labels.values()))


def build_ontology_class_rows(bundle: DomainPackageV2) -> list[dict[str, Any]]:
    """Project ontology classes into database row dictionaries."""

    rows: list[dict[str, Any]] = []
    for item in bundle.ontology_classes.classes:
        rows.append(
            {
                "ontology_class_key": make_ontology_class_key(bundle.package.domain_id, item.id),
                "domain_id": bundle.package.domain_id,
                "ontology_class_id": item.id,
                "package_version": bundle.package.package_version,
                "ontology_version": bundle.package.ontology_version,
                "parent_class_key": (
                    make_ontology_class_key(bundle.package.domain_id, item.parent_id)
                    if item.parent_id
                    else None
                ),
                "class_kind": item.kind,
                "primary_label": _primary_label(item.label),
                "labels_json": item.label,
                "knowledge_anchors_json": item.knowledge_anchors,
                "is_active": True,
            }
        )
    return rows


def build_ontology_alias_rows(bundle: DomainPackageV2) -> list[dict[str, Any]]:
    """Project alias sources from classes.yaml and aliases.yaml."""

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    domain_id = bundle.package.domain_id

    for item in bundle.ontology_classes.classes:
        for index, alias in enumerate(item.aliases):
            normalized = _normalize_alias(alias)
            key = (item.id, "und", normalized)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "alias_id": _stable_id("alias", domain_id, item.id, "und", normalized),
                    "ontology_class_key": make_ontology_class_key(domain_id, item.id),
                    "domain_id": domain_id,
                    "ontology_class_id": item.id,
                    "language_code": "und",
                    "alias_text": alias,
                    "normalized_alias": normalized,
                    "is_preferred": index == 0,
                }
            )

    alias_data = _load_yaml_file(bundle.root_path / ALIASES_FILE)
    for item in alias_data.get("aliases", []):
        canonical_id = item["canonical_id"]
        terms = item.get("terms", {})
        for language_code, alias_terms in terms.items():
            for index, alias in enumerate(alias_terms):
                normalized = _normalize_alias(alias)
                key = (canonical_id, language_code, normalized)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "alias_id": _stable_id("alias", domain_id, canonical_id, language_code, normalized),
                        "ontology_class_key": make_ontology_class_key(domain_id, canonical_id),
                        "domain_id": domain_id,
                        "ontology_class_id": canonical_id,
                        "language_code": language_code,
                        "alias_text": alias,
                        "normalized_alias": normalized,
                        "is_preferred": index == 0,
                    }
                )

    return rows


def build_ontology_mapping_rows(bundle: DomainPackageV2) -> list[dict[str, Any]]:
    """Project OEM naming mappings from classes.yaml and mappings.yaml."""

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    domain_id = bundle.package.domain_id

    for item in bundle.ontology_classes.classes:
        for mapping_system, external_id in item.external_mappings.items():
            if mapping_system in STRUCTURAL_MAPPING_SYSTEMS:
                continue
            key = (item.id, mapping_system, external_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "mapping_id": _stable_id("map", domain_id, item.id, mapping_system, external_id),
                    "ontology_class_key": make_ontology_class_key(domain_id, item.id),
                    "domain_id": domain_id,
                    "ontology_class_id": item.id,
                    "mapping_system": mapping_system,
                    "external_id": external_id,
                    "mapping_metadata_json": {"source": "classes.yaml"},
                    "is_primary": True,
                }
            )

    mapping_data = _load_yaml_file(bundle.root_path / MAPPINGS_FILE)
    for mapping_system, definitions in mapping_data.get("mappings", {}).items():
        if mapping_system in STRUCTURAL_MAPPING_SYSTEMS:
            continue
        for index, item in enumerate(definitions):
            canonical_id = item["canonical_id"]
            external_id = item["external_id"]
            metadata = {
                key: value
                for key, value in item.items()
                if key not in {"canonical_id", "external_id", "is_primary", "mapping_metadata"}
            }
            if isinstance(item.get("mapping_metadata"), dict):
                metadata.update(item["mapping_metadata"])
            metadata["source"] = "mappings.yaml"
            key = (canonical_id, mapping_system, external_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "mapping_id": _stable_id("map", domain_id, canonical_id, mapping_system, external_id),
                    "ontology_class_key": make_ontology_class_key(domain_id, canonical_id),
                    "domain_id": domain_id,
                    "ontology_class_id": canonical_id,
                    "mapping_system": mapping_system,
                    "external_id": external_id,
                    "mapping_metadata_json": metadata,
                    "is_primary": item.get("is_primary", index == 0),
                }
            )

    return rows
