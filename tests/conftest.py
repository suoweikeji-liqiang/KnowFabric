"""Shared test configuration."""

from __future__ import annotations

from pathlib import Path


def pytest_configure() -> None:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "sw_base_model_ontology.yaml"
    import os

    os.environ.setdefault("SW_BASE_MODEL_ONTOLOGY_PATH", str(fixture_path))
