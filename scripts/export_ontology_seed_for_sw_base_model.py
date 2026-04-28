#!/usr/bin/env python3
"""Export KnowFabric ontology rows as a sw_base_model ontology seed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2, OntologyMappingV2
from packages.db.session import SessionLocal

NAMESPACES = {
    "brick": "https://brickschema.org/schema/Brick#",
    "ext": "https://sw-platform.example.com/ontology/ext#",
}
EQUIPMENT_CLASS_KINDS = {"equipment", "component"}
MAPPING_TYPE_ALIASES = {
    "brick": "brick_to_external_standard",
    "223p": "brick_to_223p",
    "open223": "brick_to_open223",
}


def _parse_mapping_types(value: str | None) -> set[str]:
    if not value:
        return {"brick_to_external_standard", "brick_to_223p", "brick_to_open223"}
    return {item.strip() for item in value.split(",") if item.strip()}


def _mapping_type(row: OntologyMappingV2) -> str:
    metadata = row.mapping_metadata_json or {}
    if isinstance(metadata, dict) and metadata.get("mapping_type"):
        return str(metadata["mapping_type"])
    return MAPPING_TYPE_ALIASES.get(row.mapping_system, row.mapping_system)


def _load_structural_mappings(db, include_mapping_types: set[str]) -> dict[str, OntologyMappingV2]:
    selected: dict[str, OntologyMappingV2] = {}
    rows = db.query(OntologyMappingV2).order_by(OntologyMappingV2.is_primary.desc()).all()
    for row in rows:
        candidates = {_mapping_type(row), row.mapping_system}
        if not candidates.intersection(include_mapping_types):
            continue
        selected.setdefault(row.ontology_class_key, row)
    return selected


def _title_class_id(value: str) -> str:
    return "_".join(part[:1].upper() + part[1:] for part in value.split("_") if part)


def _class_ref(row: OntologyClassV2, mappings: dict[str, OntologyMappingV2]) -> tuple[str, str]:
    mapping = mappings.get(row.ontology_class_key)
    if mapping and ":" in mapping.external_id:
        namespace, class_name = mapping.external_id.split(":", 1)
        return class_name if namespace == "brick" else mapping.external_id, namespace
    return f"ext:{_title_class_id(row.ontology_class_id)}", "ext"


def _parent_ref(
    row: OntologyClassV2,
    classes_by_key: dict[str, OntologyClassV2],
    mappings: dict[str, OntologyMappingV2],
) -> str | None:
    if not row.parent_class_key:
        return None
    parent = classes_by_key.get(row.parent_class_key)
    if parent is None:
        return row.parent_class_key
    return _class_ref(parent, mappings)[0]


def _metadata(row: OntologyClassV2) -> dict[str, Any]:
    value = row.knowledge_anchors_json or {}
    return value if isinstance(value, dict) else {}


def _equipment_entry(
    row: OntologyClassV2,
    classes_by_key: dict[str, OntologyClassV2],
    mappings: dict[str, OntologyMappingV2],
) -> dict[str, Any]:
    class_name, namespace = _class_ref(row, mappings)
    metadata = _metadata(row)
    return {
        "class": class_name,
        "parent": _parent_ref(row, classes_by_key, mappings),
        "namespace": namespace,
        "typical_points": metadata.get("typical_points", []),
        "typical_relations": metadata.get("typical_relations", []),
    }


def _point_entry(
    row: OntologyClassV2,
    classes_by_key: dict[str, OntologyClassV2],
    mappings: dict[str, OntologyMappingV2],
) -> dict[str, Any]:
    class_name, namespace = _class_ref(row, mappings)
    return {
        "class": class_name,
        "parent": _parent_ref(row, classes_by_key, mappings),
        "namespace": namespace,
        "tags": _metadata(row).get("tags", {}),
    }


def _relation_entry(row: OntologyClassV2, mappings: dict[str, OntologyMappingV2]) -> dict[str, Any]:
    type_name, namespace = _class_ref(row, mappings)
    metadata = _metadata(row)
    return {
        "type": type_name,
        "namespace": namespace,
        "inverse": metadata.get("inverse"),
        "description": metadata.get("description"),
    }


def _seed_document(db, include_mapping_types: set[str]) -> tuple[dict[str, Any], dict[str, int]]:
    db.query(OntologyAliasV2).count()
    classes = db.query(OntologyClassV2).order_by(OntologyClassV2.ontology_class_key).all()
    classes_by_key = {row.ontology_class_key: row for row in classes}
    mappings = _load_structural_mappings(db, include_mapping_types)
    equipment_rows = [row for row in classes if row.class_kind in EQUIPMENT_CLASS_KINDS]
    point_rows = [row for row in classes if row.class_kind == "point"]
    relation_rows = [row for row in classes if row.class_kind == "relation"]
    seed = {
        "namespace": NAMESPACES,
        "ontology_version": "0.1.0",
        "equipment_classes": [_equipment_entry(row, classes_by_key, mappings) for row in equipment_rows],
        "point_classes": [_point_entry(row, classes_by_key, mappings) for row in point_rows],
        "relation_types": [_relation_entry(row, mappings) for row in relation_rows],
    }
    summary = {
        "equipment_classes": len(seed["equipment_classes"]),
        "point_classes": len(seed["point_classes"]),
        "relation_types": len(seed["relation_types"]),
    }
    return seed, summary


def export_ontology_seed(db, output_path: Path, include_mapping_types: set[str]) -> dict[str, int]:
    """Write the ontology seed YAML and return exported row counts."""

    seed, summary = _seed_document(db, include_mapping_types)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(seed, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--include-mapping-types")
    args = parser.parse_args()
    include_mapping_types = _parse_mapping_types(args.include_mapping_types)

    db = SessionLocal()
    try:
        summary = export_ontology_seed(db, args.output, include_mapping_types)
    finally:
        db.close()

    print(
        "Exported "
        f"{summary['equipment_classes']} equipment_classes, "
        f"{summary['point_classes']} point_classes, "
        f"{summary['relation_types']} relation_types"
    )
    print(f"Output: {args.output}")
    print("Next: hand this file to sw_base_model side Task 1, then resume KnowFabric Task 4.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
