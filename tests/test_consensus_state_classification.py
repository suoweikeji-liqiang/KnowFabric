"""Consensus-state classification tests for value disagreement vs over-merge."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.cross_source_merger import (
    _compute_consensus_state,
    classify_conflicting_layers,
)
from packages.core.semantic_contract_v2 import ConsensusState
from scripts.retag_consensus_state import retag_consensus_states


def _layer(name: str, value: str, publisher: str = "A", **payload) -> dict:
    structured_payload = {"parameter_name": name, **payload}
    return {
        "publisher": publisher,
        "source_name": name,
        "structured_payload": structured_payload,
        "value_summary": value,
    }


def test_same_facet_different_values_returns_value_disagreement():
    layers = [
        _layer("油温高报警", "80℃", "Gree", unit="℃", summary="oil system 油温高报警"),
        _layer("油温高报警", "75℃", "McQuay", unit="℃", summary="oil system 油温高报警"),
    ]

    assert classify_conflicting_layers(layers) == ConsensusState.VALUE_DISAGREEMENT.value
    state, _summary = _compute_consensus_state(layers)
    assert state == ConsensusState.VALUE_DISAGREEMENT.value


def test_different_subsystem_returns_over_merge():
    layers = [
        _layer("油压差报警", "100kPa", "A", unit="kPa", summary="oil system 油压差报警"),
        _layer("水压差报警", "100kPa", "B", unit="kPa", summary="water system 水压差报警"),
    ]

    assert classify_conflicting_layers(layers) == ConsensusState.OVER_MERGE.value


def test_different_refrigerant_returns_over_merge():
    layers = [
        _layer("排气压力 R22", "1.8MPa", "A", unit="MPa", summary="R22 discharge pressure"),
        _layer("排气压力 R134a", "1.8MPa", "B", unit="MPa", summary="R134a discharge pressure"),
    ]

    assert classify_conflicting_layers(layers) == ConsensusState.OVER_MERGE.value


def test_partial_facet_missing_returns_partial_conflict():
    layers = [
        _layer("系统参数", "100V", "A", unit="V", summary="electrical system"),
        _layer("系统参数", "120V", "B", unit="V"),
    ]

    assert classify_conflicting_layers(layers) == ConsensusState.PARTIAL_CONFLICT.value


def test_agreed_values_still_return_agreed():
    layers = [
        _layer("油温高报警", "80℃", "A", unit="℃"),
        _layer("油温高报警", "80℃", "B", unit="℃"),
    ]

    state, summary = _compute_consensus_state(layers)
    assert state == ConsensusState.AGREED.value
    assert summary is None


def test_retag_report_is_idempotent():
    rows = [
        {"knowledge_object_id": "ko_a", "consensus_state": "material_conflict", "authority_summary_json": {"layers": [
            _layer("油温高报警", "80℃", "A", unit="℃", summary="oil system"),
            _layer("油温高报警", "75℃", "B", unit="℃", summary="oil system"),
        ]}},
        {"knowledge_object_id": "ko_b", "consensus_state": "value_disagreement", "authority_summary_json": {"layers": [
            _layer("油温高报警", "80℃", "A", unit="℃", summary="oil system"),
            _layer("油温高报警", "75℃", "B", unit="℃", summary="oil system"),
        ]}},
    ]

    first = retag_consensus_states(rows, apply=False)
    second = retag_consensus_states(first["rows"], apply=False)

    assert first["counts"] == second["counts"]
    assert [row["new_state"] for row in first["rows"]] == [row["new_state"] for row in second["rows"]]
