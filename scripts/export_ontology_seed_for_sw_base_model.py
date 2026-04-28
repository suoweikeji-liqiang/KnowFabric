#!/usr/bin/env python3
"""Export the file-cached sw_base_model ontology YAML shape."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.core.sw_base_model_ontology_client import SwBaseModelOntologyClient


def _parse_mapping_types(value: str | None) -> set[str]:
    if not value:
        return {"brick_to_external_standard", "brick_to_223p", "brick_to_open223"}
    return {item.strip() for item in value.split(",") if item.strip()}


def _seed_document(client: SwBaseModelOntologyClient) -> tuple[dict[str, Any], dict[str, int]]:
    seed = {
        "namespace": client._data.get("namespace", {}),
        "ontology_version": client.ontology_version(),
        "equipment_classes": client._data.get("equipment_classes", []),
        "point_classes": client._data.get("point_classes", []),
        "relation_types": client._data.get("relation_types", []),
    }
    summary = {
        "equipment_classes": len(seed["equipment_classes"]),
        "point_classes": len(seed["point_classes"]),
        "relation_types": len(seed["relation_types"]),
    }
    return seed, summary


def export_ontology_seed(
    _db,
    output_path: Path,
    include_mapping_types: set[str],
    ontology_path: str | Path | None = None,
) -> dict[str, int]:
    """Write the ontology seed YAML and return exported row counts."""

    _ = include_mapping_types
    seed, summary = _seed_document(SwBaseModelOntologyClient(ontology_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(seed, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--include-mapping-types")
    parser.add_argument("--ontology-path", type=Path)
    args = parser.parse_args()
    include_mapping_types = _parse_mapping_types(args.include_mapping_types)
    summary = export_ontology_seed(None, args.output, include_mapping_types, ontology_path=args.ontology_path)

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
