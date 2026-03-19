"""Tests for the API-level semantic demo smoke runner."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_api_demo_smoke import (
    build_api_demo_smoke_summary_text,
    default_api_smoke_report_path,
    run_api_demo_smoke,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_EXAMPLES = REPO_ROOT / "domain_packages/hvac/v2/examples/example_queries.yaml"
DRIVE_EXAMPLES = REPO_ROOT / "domain_packages/drive/v2/examples/example_queries.yaml"


def _fake_fetcher(path: str, params: dict | None = None):
    params = params or {}
    if path == "/health":
        return 200, {"status": "healthy", "service": "api", "version": "0.1.0"}

    responses = {
        (
            "/api/v2/domains/hvac/equipment-classes/ahu/application-guidance",
            "ahu_sequence",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "ahu"},
                "items": [
                    {
                        "canonical_key": "ahu_zone_group_operating_mode",
                        "review_status": "approved",
                    }
                ],
            },
            "metadata": {"query_type": "application_guidance"},
        },
        (
            "/api/v2/domains/hvac/equipment-classes/ahu/maintenance-guidance",
            "",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "ahu"},
                "items": [
                    {
                        "canonical_key": "ahu_airflow_inspection_and_calibration",
                        "review_status": "approved",
                    },
                    {
                        "canonical_key": "ahu_preventive_airflow_maintenance_plan",
                        "review_status": "approved",
                    },
                ],
            },
            "metadata": {"query_type": "maintenance_guidance"},
        },
        (
            "/api/v2/domains/hvac/equipment-classes/chiller/parameter-profiles",
            "",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "chiller"},
                "items": [
                    {
                        "canonical_key": "design_chiller_capacity",
                        "review_status": "approved",
                    },
                    {
                        "canonical_key": "minimum_chiller_lift_at_minimum_load",
                        "review_status": "approved",
                    },
                ],
            },
            "metadata": {"query_type": "parameter_profile"},
        },
        (
            "/api/v2/domains/hvac/equipment-classes/condenser_water_pump/parameter-profiles",
            "",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "condenser_water_pump"},
                "items": [
                    {
                        "canonical_key": "design_condenser_water_pump_speed_by_stage",
                        "review_status": "approved",
                    },
                    {
                        "canonical_key": "minimum_condenser_water_pump_speed",
                        "review_status": "approved",
                    },
                ],
            },
            "metadata": {"query_type": "parameter_profile"},
        },
        (
            "/api/v2/domains/hvac/equipment-classes/chilled_water_pump/parameter-profiles",
            "",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "chilled_water_pump"},
                "items": [
                    {
                        "canonical_key": "design_primary_chilled_water_pump_speed_by_stage",
                        "review_status": "approved",
                    },
                    {
                        "canonical_key": "minimum_primary_chilled_water_pump_speed_by_stage",
                        "review_status": "approved",
                    },
                ],
            },
            "metadata": {"query_type": "parameter_profile"},
        },
        (
            "/api/v2/domains/hvac/equipment-classes/cooling_tower/parameter-profiles",
            "",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "cooling_tower"},
                "items": [
                    {
                        "canonical_key": "cooling_tower_design_wetbulb_and_approach",
                        "review_status": "approved",
                    }
                ],
            },
            "metadata": {"query_type": "parameter_profile"},
        },
        (
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/fault-knowledge",
            "A7C1",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "variable_frequency_drive"},
                "items": [
                    {
                        "canonical_key": "A7C1",
                        "review_status": "approved",
                    }
                ],
            },
            "metadata": {"query_type": "fault_knowledge"},
        },
        (
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/parameter-profiles",
            "p0604",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "variable_frequency_drive"},
                "items": [
                    {
                        "canonical_key": "p0604_motor_temperature_alarm_threshold",
                        "review_status": "approved",
                    }
                ],
            },
            "metadata": {"query_type": "parameter_profile"},
        },
        (
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/application-guidance",
            "pump_fan",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "variable_frequency_drive"},
                "items": [
                    {
                        "canonical_key": "pump_fan_application_control",
                        "review_status": "approved",
                    }
                ],
            },
            "metadata": {"query_type": "application_guidance"},
        },
        (
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/operational-guidance",
            "wiring_guidance",
        ): {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "variable_frequency_drive"},
                "items": [
                    {
                        "canonical_key": "shield_grounding_control_cable_shield_360",
                        "review_status": "approved",
                    }
                ],
            },
            "metadata": {"query_type": "operational_guidance"},
        },
    }

    selector = (
        path,
        str(
            params.get("fault_code")
            or params.get("parameter_name")
            or params.get("application_type")
            or params.get("guidance_type")
            or ""
        ),
    )
    payload = responses.get(selector)
    if payload is None:
        return 404, {"success": False, "detail": "not found"}
    return 200, payload


def test_run_api_demo_smoke_passes_for_hvac_and_drive_examples() -> None:
    hvac_report = run_api_demo_smoke(HVAC_EXAMPLES, base_url="http://testserver", fetcher=_fake_fetcher)
    drive_report = run_api_demo_smoke(DRIVE_EXAMPLES, base_url="http://testserver", fetcher=_fake_fetcher)

    assert hvac_report["health"]["status"] == "passed"
    assert hvac_report["summary"] == {"total_examples": 6, "passed": 6, "failed": 0}
    assert drive_report["health"]["status"] == "passed"
    assert drive_report["summary"] == {"total_examples": 4, "passed": 4, "failed": 0}
    assert "API Demo Smoke Summary" in build_api_demo_smoke_summary_text(hvac_report)


def test_run_api_demo_smoke_fails_when_review_status_does_not_match() -> None:
    def bad_fetcher(path: str, params: dict | None = None):
        if path == "/health":
            return 200, {"status": "healthy"}
        return 200, {
            "success": True,
            "data": {
                "equipment_class": {"equipment_class_id": "ahu"},
                "items": [
                    {
                        "canonical_key": "ahu_zone_group_operating_mode",
                        "review_status": "pending",
                    }
                ],
            },
            "metadata": {"query_type": "application_guidance"},
        }

    report = run_api_demo_smoke(HVAC_EXAMPLES, base_url="http://testserver", fetcher=bad_fetcher)

    assert report["summary"]["failed"] >= 1
    first = report["results"][0]
    assert first["wrong_review_status_canonical_keys"] == ["ahu_zone_group_operating_mode"]


def test_default_api_smoke_report_path_uses_domain_prefix() -> None:
    path = default_api_smoke_report_path("domain_packages/hvac/v2/examples/example_queries.yaml", "output/demo")
    assert str(path) == "output/demo/hvac__example_queries__api_smoke_report.json"
