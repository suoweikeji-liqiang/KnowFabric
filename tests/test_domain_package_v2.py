"""Tests for ontology-first domain package contracts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.domain_kit_v2.loader import load_domain_package_v2

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"


def test_hvac_v2_package_loads() -> None:
    """HVAC v2 package should validate against the rebuild schema."""

    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    class_ids = {item.id for item in bundle.ontology_classes.classes}

    assert bundle.package.domain_id == "hvac"
    assert bundle.package.package_version == "2.0.0-alpha"
    assert "centrifugal_chiller" in class_ids
    assert "project_a_chiller_01" not in class_ids


def test_hvac_v2_anchors_match_package_metadata() -> None:
    """Class anchors should come from package-level supported objects."""

    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    supported = set(bundle.package.supported_knowledge_objects)

    for ontology_class in bundle.ontology_classes.classes:
        assert set(ontology_class.knowledge_anchors).issubset(supported)


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


if __name__ == "__main__":
    test_hvac_v2_package_loads()
    test_hvac_v2_anchors_match_package_metadata()
    test_drive_v2_package_loads()
    test_drive_v2_anchors_match_package_metadata()
    print("Domain package v2 contract checks passed")
