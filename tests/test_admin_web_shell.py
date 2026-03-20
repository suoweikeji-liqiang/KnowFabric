"""Tests for the read-only admin web bundle loader."""

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ADMIN_WEB_MAIN = REPO_ROOT / "apps" / "admin-web" / "main.py"


def _load_admin_web_module():
    spec = importlib.util.spec_from_file_location("admin_web_main", ADMIN_WEB_MAIN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_demo_bundle_reads_manifest_notes_and_domain_queries(tmp_path: Path) -> None:
    module = _load_admin_web_module()
    bundle_dir = tmp_path / "demo"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    (bundle_dir / "live_demo_evaluation_manifest.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-03-20T00:00:00+00:00",
                "bundle_language": "zh",
                "statuses": {"overall": "passed"},
                "counts": {"semantic_checks_passed": 10, "mcp_checks_passed": 10, "api_checks_passed": 10},
                "handoff": {
                    "primary_artifacts": {"cover_note": str(bundle_dir / "EVALUATOR_NOTE.md")},
                },
                "paths": {
                    "brief": str(bundle_dir / "v1_demo_brief.md"),
                    "preflight_report": str(bundle_dir / "demo_environment_preflight.json"),
                    "api_log": str(bundle_dir / "api_service.log"),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "EVALUATOR_NOTE.md").write_text("# note\n", encoding="utf-8")
    (bundle_dir / "v1_demo_brief.md").write_text("# brief\n", encoding="utf-8")
    (bundle_dir / "hvac__example_queries__semantic_demo_report.json").write_text(
        json.dumps(
            {
                "example_file": "domain_packages/hvac/v2/examples/example_queries.yaml",
                "summary": {"failed": 0},
                "results": [
                    {
                        "id": "ahu_demo",
                        "description": "demo",
                        "query": "demo query",
                        "query_type": "application_guidance",
                        "status": "passed",
                        "found_canonical_keys": ["ahu_zone_group_operating_mode"],
                        "found_items": [
                            {
                                "canonical_key": "ahu_zone_group_operating_mode",
                                "title": "AHU 分区组运行模式指导",
                                "summary": "中文摘要",
                                "display_language": "zh",
                            }
                        ],
                        "request": {"equipment_class_id": "ahu"},
                    },
                    {
                        "id": "chiller_demo",
                        "description": "demo chiller",
                        "query": "demo chiller query",
                        "query_type": "parameter_profile",
                        "status": "passed",
                        "found_canonical_keys": ["design_chiller_capacity"],
                        "found_items": [
                            {
                                "canonical_key": "design_chiller_capacity",
                                "title": "ASHRAE 冷水机组设计容量",
                                "summary": "冷站核心参数摘要",
                                "display_language": "zh",
                            }
                        ],
                        "request": {"equipment_class_id": "chiller"},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "drive__example_queries__semantic_demo_report.json").write_text(
        json.dumps(
            {
                "example_file": "domain_packages/drive/v2/examples/example_queries.yaml",
                "summary": {"failed": 0},
                "results": [
                    {
                        "id": "drive_demo",
                        "description": "drive demo",
                        "query": "drive query",
                        "query_type": "fault_knowledge",
                        "status": "passed",
                        "found_canonical_keys": ["A7C1"],
                        "found_items": [
                            {
                                "canonical_key": "A7C1",
                                "title": "ABB A7C1 现场总线适配器 A 通讯警告",
                                "summary": "drive 摘要",
                                "display_language": "zh",
                            }
                        ],
                        "request": {"equipment_class_id": "variable_frequency_drive"},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = module.load_demo_bundle(bundle_dir)
    domains = {item["domain_id"]: item for item in payload["domains"]}

    assert payload["bundle_language"] == "zh"
    assert payload["cover_note_text"] == "# note\n"
    assert payload["brief_text"] == "# brief\n"
    assert domains["hvac"]["label"] == "HVAC"
    assert domains["hvac"]["queries"][0]["title"] == "AHU 分区组运行模式指导"
    assert payload["scenario"]["title"] == "冷站控制知识演示"
    assert payload["scenario"]["primary_cards"][0]["equipment_class_id"] == "chiller"
    assert payload["scenario"]["downstream_cards"][0]["equipment_class_id"] == "ahu"
    assert payload["scenario"]["extension_domains"][0]["domain_id"] == "drive"
