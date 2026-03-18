"""Pydantic models for ontology-first domain package contracts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _clean_text(value: str, field_name: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text


def _normalize_identifier(value: str, field_name: str) -> str:
    text = _clean_text(value, field_name)
    if not IDENTIFIER_PATTERN.fullmatch(text):
        raise ValueError(f"{field_name} must be stable snake_case")
    return text


def _dedupe_strings(values: list[str], field_name: str, snake_case: bool = False) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in values:
        value = _normalize_identifier(item, field_name) if snake_case else _clean_text(item, field_name)
        if value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return cleaned


def _normalize_labels(value: dict[str, str]) -> dict[str, str]:
    if not value:
        raise ValueError("label must include at least one language")
    cleaned: dict[str, str] = {}
    for language, label in value.items():
        cleaned[_clean_text(language, "label language")] = _clean_text(label, "label")
    return cleaned


class PackageMaintainer(BaseModel):
    """Human owner for a v2 domain package."""

    model_config = ConfigDict(extra="forbid")

    name: str
    email: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _clean_text(value, "maintainer name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _clean_text(value, "maintainer email")


class PackageMetadata(BaseModel):
    """Metadata contract for `domain_packages/*/v2/package.yaml`."""

    model_config = ConfigDict(extra="forbid")

    domain_id: str
    domain_name: str
    package_version: str
    ontology_version: str
    supported_languages: list[str] = Field(min_length=1)
    supported_knowledge_objects: list[str] = Field(min_length=1)
    maintainers: list[PackageMaintainer] = Field(min_length=1)
    description: str | None = None

    @field_validator("domain_id")
    @classmethod
    def validate_domain_id(cls, value: str) -> str:
        return _normalize_identifier(value, "domain_id")

    @field_validator("domain_name", "package_version", "ontology_version", "description")
    @classmethod
    def validate_text_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return value
        return _clean_text(value, info.field_name)

    @field_validator("supported_languages")
    @classmethod
    def validate_languages(cls, value: list[str]) -> list[str]:
        return _dedupe_strings(value, "supported_languages")

    @field_validator("supported_knowledge_objects")
    @classmethod
    def validate_knowledge_objects(cls, value: list[str]) -> list[str]:
        return _dedupe_strings(value, "supported_knowledge_objects", snake_case=True)


class OntologyClass(BaseModel):
    """Canonical ontology class definition for `ontology/classes.yaml`."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: dict[str, str]
    parent_id: str | None = None
    kind: Literal["equipment", "component", "concept"]
    external_mappings: dict[str, str] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)
    knowledge_anchors: list[str] = Field(default_factory=list)

    @field_validator("id", "parent_id")
    @classmethod
    def validate_ids(cls, value: str | None, info) -> str | None:
        if value is None:
            return value
        return _normalize_identifier(value, info.field_name)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: dict[str, str]) -> dict[str, str]:
        return _normalize_labels(value)

    @field_validator("external_mappings")
    @classmethod
    def validate_external_mappings(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for system, external_id in value.items():
            cleaned[_clean_text(system, "mapping system")] = _clean_text(external_id, "mapping id")
        return cleaned

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, value: list[str]) -> list[str]:
        return _dedupe_strings(value, "aliases")

    @field_validator("knowledge_anchors")
    @classmethod
    def validate_anchors(cls, value: list[str]) -> list[str]:
        return _dedupe_strings(value, "knowledge_anchors", snake_case=True)


class OntologyClassesDocument(BaseModel):
    """Container for ontology class definitions."""

    model_config = ConfigDict(extra="forbid")

    classes: list[OntologyClass] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_relationships(self) -> "OntologyClassesDocument":
        ids = [item.id for item in self.classes]
        if len(ids) != len(set(ids)):
            raise ValueError("ontology class ids must be unique")
        known_ids = set(ids)
        for item in self.classes:
            if item.parent_id and item.parent_id not in known_ids:
                raise ValueError(f"parent_id '{item.parent_id}' is not defined in classes.yaml")
        return self


class DomainPackageV2(BaseModel):
    """Aggregate rebuild-track package contract."""

    model_config = ConfigDict(extra="forbid")

    root_path: Path
    package: PackageMetadata
    ontology_classes: OntologyClassesDocument

    @model_validator(mode="after")
    def validate_supported_anchors(self) -> "DomainPackageV2":
        supported = set(self.package.supported_knowledge_objects)
        unknown: set[str] = set()
        for item in self.ontology_classes.classes:
            for anchor in item.knowledge_anchors:
                if anchor not in supported:
                    unknown.add(anchor)
        if unknown:
            joined = ", ".join(sorted(unknown))
            raise ValueError(f"unsupported knowledge_anchors: {joined}")
        concept_ids = {
            item.id
            for item in self.ontology_classes.classes
            if item.kind == "concept"
        }
        missing_metadata = sorted(supported - concept_ids)
        if missing_metadata:
            joined = ", ".join(missing_metadata)
            raise ValueError(
                "supported_knowledge_objects must have matching concept metadata classes: "
                f"{joined}"
            )
        return self
