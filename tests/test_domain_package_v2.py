"""Tests for ontology-first domain package contracts."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.domain_kit_v2.loader import load_domain_package_v2

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"


def _load_coverage_inventory(root: Path) -> dict:
    payload = yaml.safe_load((root / "coverage" / "knowledge_inventory.yaml").read_text(encoding="utf-8"))
    return payload["coverage_inventory"]


def test_hvac_v2_package_loads() -> None:
    """HVAC v2 package should validate against the rebuild schema."""

    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    class_ids = {item.id for item in bundle.ontology_classes.classes}

    assert bundle.package.domain_id == "hvac"
    assert bundle.package.package_version == "2.0.0-alpha"
    assert "centrifugal_chiller" in class_ids
    assert "air_cooled_modular_heat_pump" in class_ids
    assert "project_a_chiller_01" not in class_ids


def test_hvac_v2_anchors_match_package_metadata() -> None:
    """Class anchors should come from package-level supported objects."""

    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    supported = set(bundle.package.supported_knowledge_objects)

    for ontology_class in bundle.ontology_classes.classes:
        assert set(ontology_class.knowledge_anchors).issubset(supported)


def test_hvac_v2_supported_knowledge_objects_have_concept_metadata() -> None:
    """Supported knowledge object ids should have matching concept classes."""

    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    concept_ids = {
        item.id
        for item in bundle.ontology_classes.classes
        if item.kind == "concept"
    }

    assert set(bundle.package.supported_knowledge_objects).issubset(concept_ids)


def test_drive_v2_package_loads() -> None:
    """Drive v2 package should validate against the rebuild schema."""

    bundle = load_domain_package_v2(DRIVE_V2_ROOT)
    class_ids = {item.id for item in bundle.ontology_classes.classes}

    assert bundle.package.domain_id == "drive"
    assert bundle.package.package_version == "2.0.0-alpha"
    assert "variable_frequency_drive" in class_ids
    assert "project_a_vfd_01" not in class_ids


def test_drive_v2_anchors_match_package_metadata() -> None:
    """Drive class anchors should come from package-level supported objects."""

    bundle = load_domain_package_v2(DRIVE_V2_ROOT)
    supported = set(bundle.package.supported_knowledge_objects)

    for ontology_class in bundle.ontology_classes.classes:
        assert set(ontology_class.knowledge_anchors).issubset(supported)


def test_drive_v2_supported_knowledge_objects_have_concept_metadata() -> None:
    """Drive supported knowledge object ids should have matching concept classes."""

    bundle = load_domain_package_v2(DRIVE_V2_ROOT)
    concept_ids = {
        item.id
        for item in bundle.ontology_classes.classes
        if item.kind == "concept"
    }

    assert set(bundle.package.supported_knowledge_objects).issubset(concept_ids)


def test_hvac_v2_coverage_inventory_stays_in_sync() -> None:
    """HVAC coverage inventory should reference real fixtures and valid ontology ids."""

    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    inventory = _load_coverage_inventory(HVAC_V2_ROOT)
    supported = set(bundle.package.supported_knowledge_objects)
    equipment_ids = {item.id for item in bundle.ontology_classes.classes if item.kind == "equipment"}

    covered: set[str] = set()
    for item in inventory["current_fixture_coverage"]["equipment_classes"]:
        assert item["equipment_class_id"] in equipment_ids
        assert set(item["covered_knowledge_objects"]).issubset(supported)
        for fixture_path in item["fixture_paths"]:
            assert (REPO_ROOT / fixture_path).exists()
        covered.update(item["covered_knowledge_objects"])

    assert set(inventory["current_fixture_coverage"]["package_supported_but_without_fixture_coverage"]) == supported - covered
    assert set(inventory["current_fixture_coverage"]["package_supported_but_without_fixture_coverage"]) == {
        "parameter_spec",
        "symptom",
    }
    assert set(inventory["current_fixture_coverage"]["currently_uncovered_equipment_classes"]).issubset(equipment_ids)
    for item in inventory["internal_priority_queue"]:
        assert item["equipment_class_id"] in equipment_ids
        assert set(item["target_knowledge_objects"]).issubset(supported)


def test_drive_v2_coverage_inventory_stays_in_sync() -> None:
    """Drive coverage inventory should reference real fixtures and valid ontology ids."""

    bundle = load_domain_package_v2(DRIVE_V2_ROOT)
    inventory = _load_coverage_inventory(DRIVE_V2_ROOT)
    supported = set(bundle.package.supported_knowledge_objects)
    equipment_ids = {item.id for item in bundle.ontology_classes.classes if item.kind == "equipment"}

    covered: set[str] = set()
    for item in inventory["current_fixture_coverage"]["equipment_classes"]:
        assert item["equipment_class_id"] in equipment_ids
        assert set(item["covered_knowledge_objects"]).issubset(supported)
        for fixture_path in item["fixture_paths"]:
            assert (REPO_ROOT / fixture_path).exists()
        covered.update(item["covered_knowledge_objects"])

    assert set(inventory["current_fixture_coverage"]["package_supported_but_without_fixture_coverage"]) == supported - covered
    assert set(inventory["current_fixture_coverage"]["package_supported_but_without_fixture_coverage"]) == set()
    assert set(inventory["current_fixture_coverage"]["currently_uncovered_equipment_classes"]).issubset(equipment_ids)
    for item in inventory["internal_priority_queue"]:
        assert item["equipment_class_id"] in equipment_ids
        assert set(item["target_knowledge_objects"]).issubset(supported)


if __name__ == "__main__":
    test_hvac_v2_package_loads()
    test_hvac_v2_anchors_match_package_metadata()
    test_hvac_v2_supported_knowledge_objects_have_concept_metadata()
    test_drive_v2_package_loads()
    test_drive_v2_anchors_match_package_metadata()
    test_drive_v2_supported_knowledge_objects_have_concept_metadata()
    test_hvac_v2_coverage_inventory_stays_in_sync()
    test_drive_v2_coverage_inventory_stays_in_sync()
    print("Domain package v2 contract checks passed")
