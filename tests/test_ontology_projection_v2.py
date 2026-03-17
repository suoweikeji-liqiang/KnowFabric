"""Tests for ontology projection helpers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
    make_ontology_class_key,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"


def test_domain_scoped_keys_do_not_collide() -> None:
    """Shared local ids should diverge once scoped by domain."""

    assert make_ontology_class_key("hvac", "fault_code") != make_ontology_class_key("drive", "fault_code")


def test_hvac_projection_contains_scoped_class_rows() -> None:
    """HVAC projection should emit storage keys and parent references."""

    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    rows = build_ontology_class_rows(bundle)
    by_id = {row["ontology_class_id"]: row for row in rows}

    assert by_id["centrifugal_chiller"]["ontology_class_key"] == "hvac:centrifugal_chiller"
    assert by_id["centrifugal_chiller"]["parent_class_key"] == "hvac:chiller"


def test_drive_projection_emits_aliases_and_mappings() -> None:
    """Drive projection should emit alias and mapping rows for sync."""

    bundle = load_domain_package_v2(DRIVE_V2_ROOT)
    alias_rows = build_ontology_alias_rows(bundle)
    mapping_rows = build_ontology_mapping_rows(bundle)

    assert any(row["ontology_class_key"] == "drive:variable_frequency_drive" for row in alias_rows)
    assert any(row["mapping_system"] == "brick" for row in mapping_rows)


if __name__ == "__main__":
    test_domain_scoped_keys_do_not_collide()
    test_hvac_projection_contains_scoped_class_rows()
    test_drive_projection_emits_aliases_and_mappings()
    print("Ontology projection v2 checks passed")
