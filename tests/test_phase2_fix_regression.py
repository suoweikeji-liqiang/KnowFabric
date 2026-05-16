"""Phase 2 quality fixes for Chinese keys and over-merge regressions."""

from __future__ import annotations

from unittest.mock import patch

from packages.compiler import canonical_key as ck
from packages.compiler.cross_source_merger import _normalize_canonical_key_for_anchor
from packages.compiler.llm_compiler import _slugify_part
from packages.compiler.unit_facet_detector import detect_facet_v2


def test_slugify_preserves_cjk_parameter_names() -> None:
    cases = [
        "启动电流",
        "制冷剂",
        "油加热器预热时间",
        "排气压力",
        "重启抑制时间设定值",
        "全自动启动顺序",
        "排水管接口尺寸",
        "能量调节范围",
        "性能系数",
        "油压差报警/保护",
        "推力轴承—油温传感器",
    ]

    slugs = [_slugify_part(name) for name in cases]

    assert all(slug and not slug.startswith("key_") for slug in slugs)
    assert slugs[0] == "启动电流"
    assert slugs[9] == "油压差报警_保护"


def test_normalize_canonical_key_rewrites_wrong_ontology_prefix() -> None:
    assert _normalize_canonical_key_for_anchor(
        "hvac:ahu:performance_spec:key_bc82deec2d",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="performance_spec",
        fallback_name="制冷量",
    ) == "hvac:centrifugal_chiller:performance_spec:制冷量"


def test_strict_arbiter_accepts_split_groups_shape(monkeypatch) -> None:
    monkeypatch.setattr(ck, "_resolve_arbiter_backend", lambda backend_name: object())
    monkeypatch.setattr(ck, "_llm_arbiter_cache_path", lambda *args, **kwargs: _MissingCachePath())
    monkeypatch.setattr(
        ck,
        "_request_json_completion",
        lambda messages, backend, response_format: {
            "merge": False,
            "split_groups": [["air_flow_range"], ["air_leakage_rate"], ["加湿量"]],
            "rationale": "different physical facets",
        },
    )

    groups = ck._llm_adjudicate_cluster(
        ["air_flow_range", "air_leakage_rate", "加湿量", "extra"],
        domain_id="hvac",
        equipment_class_id="ahu",
        knowledge_object_type="performance_spec",
    )

    assert groups == [["air_flow_range", "air_leakage_rate", "加湿量", "extra"]]

    groups = ck._llm_adjudicate_cluster(
        ["air_flow_range", "air_leakage_rate", "加湿量"],
        domain_id="hvac",
        equipment_class_id="ahu",
        knowledge_object_type="performance_spec",
    )

    assert groups == [["air_flow_range"], ["air_leakage_rate"], ["加湿量"]]


def test_phase2_fault_temperature_sensor_cluster_splits() -> None:
    names = ["推力轴承—油温传感器", "润滑油温度过高", "供油温度高温报警/保护", "预启动报警"]

    mapping = _group_with_identical_embeddings(names, "fault_code", "centrifugal_chiller")

    assert len(set(mapping.values())) >= 3
    assert mapping["润滑油温度过高"] == mapping["供油温度高温报警/保护"]
    assert mapping["推力轴承—油温传感器"] != mapping["供油温度高温报警/保护"]


def test_phase2_discharge_pressure_splits_from_water_working_pressure() -> None:
    names = ["排气压力", "水室设计工作压力", "固态启动器冷却水回路工作压力", "排气过热度"]

    mapping = _group_with_identical_embeddings(names, "performance_spec", "screw_chiller")

    assert mapping["排气压力"] != mapping["水室设计工作压力"]
    assert mapping["排气压力"] != mapping["固态启动器冷却水回路工作压力"]
    assert mapping["排气压力"] != mapping["排气过热度"]


def test_phase2_air_flow_cluster_splits_leakage_and_humidification() -> None:
    names = ["air_flow_range", "air_leakage_rate", "加湿量"]

    mapping = _group_with_identical_embeddings(names, "performance_spec", "ahu")

    assert len(set(mapping.values())) == 3


def test_phase2_drain_pipe_size_splits_from_condenser_flow_pressure() -> None:
    names = ["排水管接口尺寸", "蒸发器管径与效率", "冷凝器管径与效率", "冷凝器流量过小 - 压差要求"]

    mapping = _group_with_identical_embeddings(names, "performance_spec", "centrifugal_chiller")

    assert len(set(mapping.values())) == 4


def test_phase2_room_temp_humidity_limits_stay_merged() -> None:
    names = ["Room temperature and humidity limits", "安装环境要求", "安装环境温度要求"]

    mapping = _group_with_identical_embeddings(names, "application_guidance", "centrifugal_chiller")

    assert len(set(mapping.values())) == 1


def test_phase2_capacity_control_splits_flow_lower_bound() -> None:
    names = ["能量调节范围", "最大负荷设定", "热水流量变化下限", "压缩机转换能量"]

    mapping = _group_with_identical_embeddings(names, "parameter_spec", "water_source_heat_pump")

    assert mapping["能量调节范围"] == mapping["最大负荷设定"]
    assert mapping["能量调节范围"] != mapping["热水流量变化下限"]
    assert mapping["能量调节范围"] != mapping["压缩机转换能量"]


class _MissingCachePath:
    def exists(self) -> bool:
        return False

    @property
    def parent(self) -> "_MissingCachePath":
        return self

    def mkdir(self, **kwargs) -> None:
        return None

    def write_text(self, *args, **kwargs) -> None:
        return None


def _group_with_identical_embeddings(
    names: list[str],
    knowledge_object_type: str,
    equipment_class_id: str,
) -> dict[str, str]:
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
