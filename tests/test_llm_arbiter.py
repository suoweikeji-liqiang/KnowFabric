"""Tests for scoped LLM final adjudication of embedding clusters."""

from __future__ import annotations

import pytest

from packages.compiler import canonical_key as ck


def test_llm_arbiter_split_refines_cluster(monkeypatch) -> None:
    calls = []

    def fake_adjudicate(cluster, **kwargs):
        calls.append((cluster, kwargs))
        return [["A", "C"], ["B"]]

    monkeypatch.setattr(ck, "_llm_adjudicate_cluster", fake_adjudicate)

    clusters = ck._apply_llm_arbiter(
        [["A", "B", "C"]],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        publisher_hints={"A": "Gree", "B": "Trane", "C": "Gree"},
    )

    assert clusters == [["A", "C"], ["B"]]
    assert len(calls) == 1


def test_llm_arbiter_keep_preserves_cluster(monkeypatch) -> None:
    monkeypatch.setattr(ck, "_llm_adjudicate_cluster", lambda cluster, **kwargs: [cluster])

    clusters = ck._apply_llm_arbiter(
        [["Oil Temperature", "油温"]],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        publisher_hints={"Oil Temperature": "Trane", "油温": "Gree"},
    )

    assert clusters == [["Oil Temperature", "油温"]]


def test_llm_arbiter_exception_falls_back_to_original_cluster(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise RuntimeError("backend down")

    monkeypatch.setattr(ck, "_llm_adjudicate_cluster", fail)

    clusters = ck._apply_llm_arbiter(
        [["A", "B"]],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        publisher_hints={"A": "Gree", "B": "Trane"},
    )

    assert clusters == [["A", "B"]]


def test_llm_arbiter_skips_clusters_larger_than_eight(monkeypatch) -> None:
    def should_not_call(*args, **kwargs):
        raise AssertionError("LLM should not be called")

    monkeypatch.setattr(ck, "_llm_adjudicate_cluster", should_not_call)
    cluster = [f"name_{idx}" for idx in range(9)]
    publishers = {name: ("Gree" if idx % 2 else "Trane") for idx, name in enumerate(cluster)}

    assert ck._apply_llm_arbiter(
        [cluster],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        publisher_hints=publishers,
    ) == [cluster]


def test_llm_arbiter_skips_single_publisher_cluster(monkeypatch) -> None:
    def should_not_call(*args, **kwargs):
        raise AssertionError("LLM should not be called")

    monkeypatch.setattr(ck, "_llm_adjudicate_cluster", should_not_call)

    assert ck._apply_llm_arbiter(
        [["A", "B"]],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        publisher_hints={"A": "Gree", "B": "Gree"},
    ) == [["A", "B"]]


def test_llm_arbiter_repair_detector_flags_known_bad_control_mix() -> None:
    groups = [[
        "Active Current Limit Setpoint。value=100%",
        "热气旁通启动点电流值。满负荷时电流的40%",
    ]]

    assert ck._arbiter_needs_repair(groups)
