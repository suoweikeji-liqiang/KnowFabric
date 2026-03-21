"""Tests for the read-only admin web bundle loader."""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


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


def test_load_workbench_payload_reads_fixture_catalog_and_coverage_inventory() -> None:
    module = _load_admin_web_module()
    module._load_documents_from_db = lambda: []

    payload = module.load_workbench_payload()
    domains = {item["domain_id"]: item for item in payload["views"]["coverage"]["domains"]}
    drive = domains["drive"]
    soft_starter = next(
        item for item in drive["equipment_classes"] if item["equipment_class_id"] == "soft_starter"
    )
    samples = {item["doc_id"]: item for item in payload["views"]["documents"]["fixture_samples"]}

    assert payload["title"] == "KnowFabric Internal Workbench"
    assert payload["summary"]["fixture_count"] >= 1
    assert "fault_code" in soft_starter["covered_knowledge_objects"]
    assert "commissioning_step" in soft_starter["missing_knowledge_objects"]
    assert "doc_schneider_ats480_manual" in samples
    assert "soft_starter" in samples["doc_schneider_ats480_manual"]["equipment_classes"]


def test_load_review_workspace_reads_local_review_pack_directory(tmp_path: Path) -> None:
    module = _load_admin_web_module()
    review_dir = tmp_path / "review_bundle"
    review_dir.mkdir(parents=True, exist_ok=True)
    pack_path = review_dir / "drive__doc_demo__soft_starter.json"
    pack_path.write_text(
        json.dumps(
            {
                "review_mode": "chunk_backfill_review_pack",
                "domain_id": "drive",
                "doc_id": "doc_demo",
                "doc_name": "Demo Manual.pdf",
                "equipment_class": {
                    "equipment_class_id": "soft_starter",
                    "equipment_class_key": "drive:soft_starter",
                    "label": "Soft Starter",
                },
                "candidate_entries": [
                    {
                        "candidate_id": "cand_1",
                        "domain_id": "drive",
                        "doc_id": "doc_demo",
                        "doc_name": "Demo Manual.pdf",
                        "page_id": "page_1",
                        "page_no": 10,
                        "chunk_id": "chunk_1",
                        "chunk_index": 0,
                        "chunk_type": "fault_code_block",
                        "page_type": "fault_code_reference",
                        "text_excerpt": "fault excerpt",
                        "evidence_text": "fault evidence",
                        "knowledge_object_type": "fault_code",
                        "canonical_key_candidate": "OCF",
                        "structured_payload_candidate": {"fault_code": "OCF"},
                        "confidence_score": 0.9,
                        "review_decision": "pending",
                        "equipment_class_candidate": {
                            "equipment_class_id": "soft_starter",
                            "equipment_class_key": "drive:soft_starter",
                            "label": "Soft Starter",
                        },
                        "curation": {},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = module.load_review_workspace(review_root=review_dir)

    assert payload["available"] is True
    assert payload["workspace_id"] == "default"
    assert payload["pack_count"] == 1
    assert payload["packs"][0]["equipment_class_id"] == "soft_starter"
    assert payload["packs"][0]["status"] == "blocked_pending"


def test_save_review_pack_writes_updated_review_decision(tmp_path: Path) -> None:
    module = _load_admin_web_module()
    review_dir = tmp_path / "review_bundle"
    review_dir.mkdir(parents=True, exist_ok=True)
    pack_path = review_dir / "drive__doc_demo__soft_starter.json"
    payload = {
        "review_mode": "chunk_backfill_review_pack",
        "domain_id": "drive",
        "doc_id": "doc_demo",
        "doc_name": "Demo Manual.pdf",
        "equipment_class": {
            "equipment_class_id": "soft_starter",
            "equipment_class_key": "drive:soft_starter",
            "label": "Soft Starter",
        },
        "candidate_entries": [
            {
                "candidate_id": "cand_1",
                "domain_id": "drive",
                "doc_id": "doc_demo",
                "doc_name": "Demo Manual.pdf",
                "page_id": "page_1",
                "page_no": 10,
                "chunk_id": "chunk_1",
                "chunk_index": 0,
                "chunk_type": "fault_code_block",
                "page_type": "fault_code_reference",
                "text_excerpt": "fault excerpt",
                "evidence_text": "fault evidence",
                "knowledge_object_type": "fault_code",
                "canonical_key_candidate": "OCF",
                "structured_payload_candidate": {"fault_code": "OCF"},
                "confidence_score": 0.9,
                "review_decision": "pending",
                "equipment_class_candidate": {
                    "equipment_class_id": "soft_starter",
                    "equipment_class_key": "drive:soft_starter",
                    "label": "Soft Starter",
                },
                "curation": {
                    "title": "",
                    "summary": "",
                    "structured_payload": {},
                    "applicability": {},
                    "trust_level": "L2",
                },
            }
        ],
    }
    pack_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["candidate_entries"][0]["review_decision"] = "accepted"
    payload["candidate_entries"][0]["curation"]["title"] = "Reviewed OCF"
    payload["candidate_entries"][0]["curation"]["summary"] = "Reviewed fault entry."
    payload["candidate_entries"][0]["curation"]["structured_payload"] = {"fault_code": "OCF"}

    saved = module.save_review_pack(None, pack_path.name, payload, review_root=review_dir)
    persisted = json.loads(pack_path.read_text(encoding="utf-8"))

    assert saved["candidate_entries"][0]["review_decision"] == "accepted"
    assert persisted["candidate_entries"][0]["curation"]["title"] == "Reviewed OCF"


def test_bootstrap_review_pack_fills_missing_curation_fields(tmp_path: Path) -> None:
    module = _load_admin_web_module()
    review_dir = tmp_path / "review_bundle"
    review_dir.mkdir(parents=True, exist_ok=True)
    pack_path = review_dir / "drive__doc_demo__soft_starter.json"
    pack_path.write_text(
        json.dumps(
            {
                "review_mode": "chunk_backfill_review_pack",
                "domain_id": "drive",
                "doc_id": "doc_demo",
                "doc_name": "Demo Manual.pdf",
                "equipment_class": {
                    "equipment_class_id": "soft_starter",
                    "equipment_class_key": "drive:soft_starter",
                    "label": "Soft Starter",
                },
                "candidate_entries": [
                    {
                        "candidate_id": "cand_1",
                        "domain_id": "drive",
                        "doc_id": "doc_demo",
                        "doc_name": "Demo Manual.pdf",
                        "page_id": "page_1",
                        "page_no": 10,
                        "chunk_id": "chunk_1",
                        "chunk_index": 0,
                        "chunk_type": "fault_code_block",
                        "page_type": "fault_code_reference",
                        "text_excerpt": "fault excerpt",
                        "evidence_text": "fault evidence",
                        "knowledge_object_type": "fault_code",
                        "canonical_key_candidate": "OCF",
                        "structured_payload_candidate": {"fault_code": "OCF"},
                        "confidence_score": 0.9,
                        "review_decision": "accepted",
                        "equipment_class_candidate": {
                            "equipment_class_id": "soft_starter",
                            "equipment_class_key": "drive:soft_starter",
                            "label": "Soft Starter",
                        },
                        "curation": {},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    bootstrapped = module.bootstrap_review_pack(None, pack_path.name, review_root=review_dir)

    assert bootstrapped["candidate_entries"][0]["curation"]["title"].startswith("Draft Fault Code")
    assert bootstrapped["candidate_entries"][0]["curation"]["trust_level"] == "L3"


def test_load_apply_workspace_reports_pending_pack_status(tmp_path: Path) -> None:
    module = _load_admin_web_module()
    review_dir = tmp_path / "review_bundle"
    review_dir.mkdir(parents=True, exist_ok=True)
    pack_path = review_dir / "drive__doc_demo__soft_starter.json"
    pack_path.write_text(
        json.dumps(
            {
                "review_mode": "chunk_backfill_review_pack",
                "domain_id": "drive",
                "doc_id": "doc_demo",
                "doc_name": "Demo Manual.pdf",
                "equipment_class": {
                    "equipment_class_id": "soft_starter",
                    "equipment_class_key": "drive:soft_starter",
                    "label": "Soft Starter",
                },
                "candidate_entries": [
                    {
                        "candidate_id": "cand_1",
                        "domain_id": "drive",
                        "doc_id": "doc_demo",
                        "doc_name": "Demo Manual.pdf",
                        "page_id": "page_1",
                        "page_no": 10,
                        "chunk_id": "chunk_1",
                        "chunk_index": 0,
                        "chunk_type": "fault_code_block",
                        "page_type": "fault_code_reference",
                        "text_excerpt": "fault excerpt",
                        "evidence_text": "fault evidence",
                        "knowledge_object_type": "fault_code",
                        "canonical_key_candidate": "OCF",
                        "structured_payload_candidate": {"fault_code": "OCF"},
                        "confidence_score": 0.9,
                        "review_decision": "pending",
                        "equipment_class_candidate": {
                            "equipment_class_id": "soft_starter",
                            "equipment_class_key": "drive:soft_starter",
                            "label": "Soft Starter",
                        },
                        "curation": {},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = module.load_apply_workspace(review_root=review_dir)

    assert payload["available"] is True
    assert payload["workspace_id"] == "default"
    assert payload["summary"]["blocked_pending"] == 1
    assert payload["results"][0]["status"] == "blocked_pending"


def test_load_apply_workspace_includes_latest_apply_artifacts(tmp_path: Path) -> None:
    module = _load_admin_web_module()
    review_dir = tmp_path / "review_bundle"
    review_dir.mkdir(parents=True, exist_ok=True)
    stats_path = review_dir / "bootstrapped_review_pipeline_stats.json"
    summary_path = review_dir / "review_pipeline_summary.txt"
    stats_path.write_text(
        json.dumps({"overall": {"apply_status_counts": {"applied": 1}}}) + "\n",
        encoding="utf-8",
    )
    summary_path.write_text("Apply: 1 applied\n", encoding="utf-8")
    (review_dir / "apply_ready_manifest.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-03-21T00:00:00+00:00",
                "ready_pack_count": 1,
                "summary": {"applied": 1, "failed": 0},
                "paths": {
                    "apply_report": str(review_dir / "review_pack_apply_report.json"),
                    "stats": str(stats_path),
                    "summary_text": str(summary_path),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = module.load_apply_workspace(review_root=review_dir)

    assert payload["latest_apply"]["summary"]["applied"] == 1
    assert payload["latest_apply"]["stats"]["overall"]["apply_status_counts"]["applied"] == 1
    assert "Apply: 1 applied" in payload["latest_apply"]["summary_text"]


def test_run_prepare_bundle_refreshes_review_and_apply_workspace(monkeypatch, tmp_path: Path) -> None:
    module = _load_admin_web_module()
    review_dir = tmp_path / "review_bundle"
    review_dir.mkdir(parents=True, exist_ok=True)

    def fake_prepare(domain_id, output_dir, **kwargs):
        boot_dir = Path(output_dir) / "bootstrapped_review_packs"
        boot_dir.mkdir(parents=True, exist_ok=True)
        pack_path = boot_dir / "drive__doc_demo__soft_starter.json"
        pack_path.write_text(
            json.dumps(
                {
                    "review_mode": "chunk_backfill_review_pack",
                    "domain_id": "drive",
                    "doc_id": "doc_demo",
                    "doc_name": "Demo Manual.pdf",
                    "equipment_class": {
                        "equipment_class_id": "soft_starter",
                        "equipment_class_key": "drive:soft_starter",
                        "label": "Soft Starter",
                    },
                    "candidate_entries": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        readiness_path = Path(output_dir) / "review_pack_readiness_report.json"
        readiness_path.write_text(
            json.dumps(
                {
                    "pack_dir": str(boot_dir),
                    "summary": {"ready": 0, "blocked_pending": 0, "blocked_no_accepted": 1, "blocked_invalid": 0},
                    "results": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        manifest = {
            "paths": {
                "bootstrapped_review_pack_dir": str(boot_dir),
                "readiness_report": str(readiness_path),
            }
        }
        (Path(output_dir) / "prepare_manifest.json").write_text(
            json.dumps(manifest) + "\n",
            encoding="utf-8",
        )
        return manifest

    monkeypatch.setattr(module, "prepare_review_pipeline_bundle", fake_prepare)

    result = module.run_prepare_bundle(
        "drive",
        doc_id="doc_demo",
        equipment_class_id="soft_starter",
        workspace_id="demo_workspace",
        review_root=review_dir,
    )

    assert result["review_workspace"]["available"] is True
    assert result["workspace_id"] == "demo_workspace"
    assert result["review_workspace"]["pack_count"] == 1
    assert result["apply_workspace"]["available"] is True
