#!/usr/bin/env python3
"""Shared inventory for the external evaluation demo bundle."""

from __future__ import annotations

from pathlib import Path

DEFAULT_DOMAINS = ("hvac", "drive")
DEFAULT_FIXTURE_PATHS = (
    "tests/fixtures/manual_validation/hvac_demo_ahu_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_chiller_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_condenser_water_pump_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_chilled_water_pump_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_cooling_tower_authority.json",
    "tests/fixtures/manual_validation/drive_vfd_faults.json",
    "tests/fixtures/manual_validation/drive_parameter_profiles.json",
    "tests/fixtures/manual_validation/drive_application_guidance.json",
    "tests/fixtures/manual_validation/drive_commissioning_guidance.json",
)
DEFAULT_EXAMPLE_QUERY_FILES = (
    "domain_packages/hvac/v2/examples/example_queries.yaml",
    "domain_packages/drive/v2/examples/example_queries.yaml",
)


def default_demo_fixture_paths() -> list[Path]:
    """Return committed fixture paths required for the read-only demo bundle."""

    return [Path(path) for path in DEFAULT_FIXTURE_PATHS]


def default_demo_example_query_paths() -> list[Path]:
    """Return committed semantic example query files for the demo bundle."""

    return [Path(path) for path in DEFAULT_EXAMPLE_QUERY_FILES]
