"""Read-only access to the sw_base_model ontology contract file."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY_PATH = REPO_ROOT.parent / "sw_base_model" / "ontology" / "v1" / "ontology.yaml"


class SwBaseModelOntologyClient:
    """Phase 1 contract v0.1: file-cached. Phase 2: HTTP API."""

    def __init__(self, path_or_url: str | Path | None = None) -> None:
        path = Path(path_or_url or os.environ.get("SW_BASE_MODEL_ONTOLOGY_PATH") or DEFAULT_ONTOLOGY_PATH)
        self._data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        self._equipment_by_id = {
            self._normalize_class_id(item.get("class")): self._normalize_equipment_item(item)
            for item in self._data.get("equipment_classes", [])
            if item.get("class")
        }

    def get_equipment_class(self, class_id: str) -> dict[str, Any] | None:
        """Return one equipment class metadata dictionary by local or namespaced id."""

        normalized = self._normalize_class_id(class_id)
        item = self._equipment_by_id.get(normalized)
        return dict(item) if item else None

    def get_typical_points(self, class_id: str) -> list[str]:
        """Return typical point class ids declared for an equipment class."""

        item = self.get_equipment_class(class_id)
        return list(item.get("typical_points", [])) if item else []

    def get_typical_relations(self, class_id: str) -> list[dict[str, Any]]:
        """Return typical relation declarations for an equipment class."""

        item = self.get_equipment_class(class_id)
        relations = item.get("typical_relations", []) if item else []
        return [dict(relation) for relation in relations if isinstance(relation, dict)]

    def ontology_version(self) -> str:
        """Return the sw_base_model ontology version string."""

        return str(self._data.get("ontology_version") or "")

    def _normalize_equipment_item(self, item: dict[str, Any]) -> dict[str, Any]:
        class_ref = str(item["class"])
        class_id = self._normalize_class_id(class_ref)
        parent_ref = item.get("parent")
        labels = self._labels_for_item(item, class_id)
        return {
            **item,
            "ontology_class_id": class_id,
            "primary_label": labels.get("en") or self._display_label(class_id),
            "labels": labels,
            "parent_class_id": self._normalize_class_id(parent_ref) if parent_ref else None,
        }

    def _labels_for_item(self, item: dict[str, Any], class_id: str) -> dict[str, str]:
        raw_labels = item.get("labels") or item.get("labels_json") or {}
        labels = {
            str(language): str(label)
            for language, label in raw_labels.items()
            if isinstance(label, str) and label.strip()
        }
        labels.setdefault("en", self._display_label(class_id))
        return labels

    @staticmethod
    def _normalize_class_id(class_id: Any) -> str:
        value = str(class_id or "").strip()
        if ":" in value:
            value = value.split(":", 1)[1]
        value = value.replace("-", "_").replace(" ", "_")
        if "_" not in value and not value.isupper():
            value = re.sub(r"(?<!^)(?=[A-Z])", "_", value)
        value = value.lower()
        return re.sub(r"_+", "_", value).strip("_")

    @staticmethod
    def _display_label(class_id: str) -> str:
        return " ".join(part.upper() if part in {"ahu", "vrf"} else part.title() for part in class_id.split("_"))
