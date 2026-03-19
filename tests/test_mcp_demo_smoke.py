"""Tests for the MCP-level semantic demo smoke runner."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_mcp_demo_smoke import (
    build_mcp_demo_smoke_summary_text,
    default_mcp_smoke_report_path,
    run_mcp_demo_smoke,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_EXAMPLES = REPO_ROOT / "domain_packages/hvac/v2/examples/example_queries.yaml"
DRIVE_EXAMPLES = REPO_ROOT / "domain_packages/drive/v2/examples/example_queries.yaml"


def _fake_fetcher(method: str, params: dict | None = None):
    params = params or {}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}}
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "get_application_guidance"},
                    {"name": "get_maintenance_guidance"},
                    {"name": "get_parameter_profile"},
                    {"name": "get_fault_knowledge"},
                    {"name": "get_operational_guidance"},
                ]
            },
        }

    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    responses = {
        ("get_application_guidance", "ahu_sequence"): {"items": [{"canonical_key": "ahu_zone_group_operating_mode", "review_status": "approved"}]},
        ("get_maintenance_guidance", "ahu"): {"items": [
            {"canonical_key": "ahu_airflow_inspection_and_calibration", "review_status": "approved"},
            {"canonical_key": "ahu_preventive_airflow_maintenance_plan", "review_status": "approved"},
        ]},
        ("get_parameter_profile", "chiller"): {"items": [
            {"canonical_key": "design_chiller_capacity", "review_status": "approved"},
            {"canonical_key": "minimum_chiller_lift_at_minimum_load", "review_status": "approved"},
        ]},
        ("get_parameter_profile", "condenser_water_pump"): {"items": [
            {"canonical_key": "design_condenser_water_pump_speed_by_stage", "review_status": "approved"},
            {"canonical_key": "minimum_condenser_water_pump_speed", "review_status": "approved"},
        ]},
        ("get_parameter_profile", "chilled_water_pump"): {"items": [
            {"canonical_key": "design_primary_chilled_water_pump_speed_by_stage", "review_status": "approved"},
            {"canonical_key": "minimum_primary_chilled_water_pump_speed_by_stage", "review_status": "approved"},
        ]},
        ("get_parameter_profile", "cooling_tower"): {"items": [
            {"canonical_key": "cooling_tower_design_wetbulb_and_approach", "review_status": "approved"},
        ]},
        ("get_fault_knowledge", "A7C1"): {"items": [{"canonical_key": "A7C1", "review_status": "approved"}]},
        ("get_parameter_profile", "p0604"): {"items": [{"canonical_key": "p0604_motor_temperature_alarm_threshold", "review_status": "approved"}]},
        ("get_application_guidance", "pump_fan"): {"items": [{"canonical_key": "pump_fan_application_control", "review_status": "approved"}]},
        ("get_operational_guidance", "variable_frequency_drive"): {"items": [{"canonical_key": "shield_grounding_control_cable_shield_360", "review_status": "approved"}]},
    }
    selector = (
        tool_name,
        str(
            arguments.get("application_type")
            or arguments.get("fault_code")
            or arguments.get("parameter_name")
            or arguments.get("equipment_class_id")
            or arguments.get("guidance_type")
            or ""
        ),
    )
    payload = responses.get(selector, {"items": []})
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": __import__("json").dumps({"success": True, "items": payload["items"]}),
                }
            ]
        },
    }


def test_run_mcp_demo_smoke_passes_for_hvac_and_drive_examples() -> None:
    hvac_report = run_mcp_demo_smoke(HVAC_EXAMPLES, fetcher=_fake_fetcher)
    drive_report = run_mcp_demo_smoke(DRIVE_EXAMPLES, fetcher=_fake_fetcher)

    assert hvac_report["initialize_ok"] is True
    assert hvac_report["tools_list_ok"] is True
    assert hvac_report["summary"] == {"total_examples": 6, "passed": 6, "failed": 0}
    assert drive_report["summary"] == {"total_examples": 4, "passed": 4, "failed": 0}
    assert "MCP Demo Smoke Summary" in build_mcp_demo_smoke_summary_text(hvac_report)


def test_run_mcp_demo_smoke_fails_when_review_status_is_wrong() -> None:
    def bad_fetcher(method: str, params: dict | None = None):
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": 1, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "get_application_guidance"}]}}
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "{\"success\": true, \"items\": [{\"canonical_key\": \"ahu_zone_group_operating_mode\", \"review_status\": \"pending\"}]}",
                    }
                ]
            },
        }

    report = run_mcp_demo_smoke(HVAC_EXAMPLES, fetcher=bad_fetcher)
    assert report["summary"]["failed"] >= 1
    assert report["results"][0]["wrong_review_status_canonical_keys"] == ["ahu_zone_group_operating_mode"]


def test_default_mcp_smoke_report_path_uses_domain_prefix() -> None:
    path = default_mcp_smoke_report_path("domain_packages/drive/v2/examples/example_queries.yaml", "output/demo")
    assert str(path) == "output/demo/drive__example_queries__mcp_smoke_report.json"
