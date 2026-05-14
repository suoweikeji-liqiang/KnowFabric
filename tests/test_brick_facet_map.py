import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.canonical_key import _split_clusters_by_facet
from packages.compiler.unit_facet_detector import detect_brick_subtype, detect_facet_v2


BRICK_MAP = Path("domain_packages/hvac/v2/brick_facet_map.yaml")


def test_brick_map_covers_chiller_reference_points():
    data = yaml.safe_load(BRICK_MAP.read_text(encoding="utf-8"))
    tags = data["brick_reference_points"]

    assert len(tags) >= 20
    for tag, config in tags.items():
        assert config["parent"]
        assert config["facet_subtype"]
        assert len(config["keywords"]) >= 3, tag


def test_detects_oil_temperature_subtype():
    assert detect_brick_subtype("油温控制设定值", {}) == "oil_temperature"


def test_detects_cooling_water_inlet_temperature_subtype_en():
    assert detect_brick_subtype("Cooling Water Inlet Temperature", {}) == (
        "cooling_water_inlet_temperature"
    )


def test_detects_cooling_water_inlet_temperature_subtype_zh():
    assert detect_brick_subtype("油冷/变频器冷却最低进水温度", {}) == (
        "cooling_water_inlet_temperature"
    )


def test_detect_facet_v2_returns_quantity_and_reference_point():
    assert detect_facet_v2("油箱温度", {"summary": "油箱温度保持在48～52℃之间"}) == (
        "temperature",
        "oil_temperature",
    )


def test_split_clusters_by_different_brick_subtype():
    clusters = [["油温控制设定值", "Cooling Water Inlet Temperature"]]
    facet_hints = {
        "油温控制设定值": ("temperature", "oil_temperature"),
        "Cooling Water Inlet Temperature": (
            "temperature",
            "cooling_water_inlet_temperature",
        ),
    }

    assert sorted(_split_clusters_by_facet(clusters, facet_hints)) == [
        ["Cooling Water Inlet Temperature"],
        ["油温控制设定值"],
    ]


def test_unknown_subtype_does_not_force_split():
    clusters = [["油箱温度", "Generic Temperature"]]
    facet_hints = {
        "油箱温度": ("temperature", "oil_temperature"),
        "Generic Temperature": ("temperature", None),
    }

    assert _split_clusters_by_facet(clusters, facet_hints) == clusters
