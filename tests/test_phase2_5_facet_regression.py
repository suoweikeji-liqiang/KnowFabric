"""Phase 2.5 orthogonal facet regression tests."""

from __future__ import annotations

from unittest.mock import patch

from packages.compiler import canonical_key as ck
from packages.compiler.unit_facet_detector import detect_facet_v2


def test_phase2_5_refrigerant_splits_same_discharge_pressure_name() -> None:
    names = ["排气压力 R22", "排气压力 R134a"]

    mapping = _group(names, "performance_spec", "centrifugal_chiller")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_ahu_capacity_splits_fresh_air_and_return_air_conditions() -> None:
    names = ["制冷量 新风工况", "制冷量 回风工况"]

    mapping = _group(names, "performance_spec", "ahu")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_oil_pressure_fault_splits_from_water_pressure_fault() -> None:
    names = ["油压差报警", "水压差报警"]

    mapping = _group(names, "fault_code", "centrifugal_chiller")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_maintenance_intervals_split_by_reference_point() -> None:
    names = ["油换周期", "滤芯更换"]

    mapping = _group(names, "maintenance_procedure", "screw_chiller")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_test_method_document_type_does_not_split_same_axis() -> None:
    names = ["测试方法 A", "试验方法 B"]

    mapping = _group(names, "application_guidance", "standard_reference")

    assert mapping[names[0]] == mapping[names[1]]


def test_phase2_5_capacity_splits_standard_and_part_load_conditions() -> None:
    names = ["制冷量 标准制冷工况", "制冷量 部分负荷工况"]

    mapping = _group(names, "performance_spec", "ahu")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_oil_high_fault_splits_from_discharge_temperature_high_fault() -> None:
    names = ["油温高 fault", "排气温度高 fault"]

    mapping = _group(names, "fault_code", "centrifugal_chiller")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_absent_refrigerant_axis_does_not_split_same_name() -> None:
    names = ["排气压力", "排气压力"]

    mapping = _group(names, "performance_spec", "centrifugal_chiller")

    assert len(set(mapping.values())) == 1


def test_phase2_5_voltage_percentage_splits_from_current_limit_percentage() -> None:
    names = ["Line Voltage Percentage", "限流百分比"]

    mapping = _group(names, "parameter_spec", "centrifugal_chiller")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_heating_capacity_splits_from_cooling_input_power() -> None:
    names = ["名义制热量", "nominal_cooling_input_power"]

    mapping = _group(names, "parameter_spec", "air_cooled_modular_heat_pump")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_differential_pressure_points_split() -> None:
    names = ["最大负载点 ΔP2", "最小压差设定值", "激活压差"]

    mapping = _group(names, "parameter_spec", "centrifugal_chiller")

    assert len(set(mapping.values())) == 3


def test_phase2_5_chilled_water_reset_range_splits_from_plain_setpoint() -> None:
    names = ["远程模式下冷冻水出水温度重设范围", "冷冻水出水温度设定"]

    mapping = _group(names, "parameter_spec", "centrifugal_chiller")

    assert mapping[names[0]] != mapping[names[1]]


def test_phase2_5_low_oil_pressure_fault_splits_from_oil_pressure_differential_fault() -> None:
    names = ["低油压报警", "油压差过低"]

    mapping = _group(names, "fault_code", "centrifugal_chiller")

    assert mapping[names[0]] != mapping[names[1]]


def _group(names: list[str], knowledge_object_type: str, equipment_class_id: str) -> dict[str, str]:
    ck.HASH_CACHE.clear()
    facets = {name: detect_facet_v2(name, {"parameter_name": name}) for name in names}
    publishers = {name: ("A" if idx % 2 else "B") for idx, name in enumerate(names)}
    embeddings = [[1.0, 0.0, 0.0] for _ in names]

    with patch("packages.compiler.embedding_client.embed_batch", return_value=embeddings):
        with patch("packages.compiler.canonical_key._llm_adjudicate_cluster", side_effect=lambda cluster, **_: [cluster]):
            return ck._group_via_embedding(
                names,
                domain_id="hvac",
                equipment_class_id=equipment_class_id,
                knowledge_object_type=knowledge_object_type,
                facet_hints=facets,
                publisher_hints=publishers,
            )
