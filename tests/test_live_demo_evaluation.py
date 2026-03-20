"""Tests for the one-shot live demo evaluation runner."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_live_demo_evaluation import (
    default_cover_note_path,
    build_live_demo_evaluation_summary_text,
    default_api_log_path,
    default_live_evaluation_manifest_path,
    default_preflight_report_path,
    run_live_demo_evaluation,
)


def test_default_live_demo_evaluation_paths_use_output_dir() -> None:
    output_dir = "output/demo"
    assert str(default_preflight_report_path(output_dir)) == "output/demo/demo_environment_preflight.json"
    assert str(default_api_log_path(output_dir)) == "output/demo/api_service.log"
    assert str(default_cover_note_path(output_dir)) == "output/demo/EVALUATOR_NOTE.md"
    assert str(default_live_evaluation_manifest_path(output_dir)) == "output/demo/live_demo_evaluation_manifest.json"


def test_run_live_demo_evaluation_orchestrates_full_flow(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, object]] = []

    def fake_preflight(*, output_dir, api_base_url=None, db_checker=None, health_fetcher=None):
        calls.append(("preflight", (str(output_dir), api_base_url)))
        return {
            "summary": {"passed": 7, "failed": 0, "skipped": 1},
            "checks": [],
        }

    def fake_bootstrap(**kwargs):
        calls.append(("bootstrap", kwargs))
        return {
            "ontology_sync": [{"domain_id": "hvac"}, {"domain_id": "drive"}],
            "reports": [{"passed": 6, "failed": 0, "report_path": str(tmp_path / "semantic.json")}],
            "mcp_reports": [{"passed": 4, "failed": 0, "report_path": str(tmp_path / "mcp.json")}],
            "brief_path": str(tmp_path / "brief.md"),
            "brief_language": kwargs.get("brief_language"),
        }

    def fake_start(*, api_base_url, log_path):
        calls.append(("start_api", (api_base_url, str(log_path))))
        return SimpleNamespace(
            log_path=Path(log_path),
            command=["python", "-m", "uvicorn"],
            process=None,
            log_file=None,
        )

    def fake_wait(handle, *, api_base_url, startup_timeout):
        calls.append(("wait_api", (api_base_url, startup_timeout)))
        return {"name": "api_health", "status": "passed", "http_status": 200}

    def fake_api_reports(base_url, output_dir):
        calls.append(("api_reports", (base_url, str(output_dir))))
        return [{"passed": 10, "failed": 0, "report_path": str(tmp_path / "api.json")}]

    def fake_brief(*, report_dir, output_path, language):
        calls.append(("brief", (str(report_dir), str(output_path), language)))
        Path(output_path).write_text("# brief\n", encoding="utf-8")
        return Path(output_path)

    def fake_stop(handle):
        calls.append(("stop_api", handle.command))

    monkeypatch.setattr("scripts.run_live_demo_evaluation.check_demo_environment", fake_preflight)
    monkeypatch.setattr("scripts.run_live_demo_evaluation.bootstrap_v1_demo", fake_bootstrap)
    monkeypatch.setattr("scripts.run_live_demo_evaluation.start_api_service", fake_start)
    monkeypatch.setattr("scripts.run_live_demo_evaluation.wait_for_api_service", fake_wait)
    monkeypatch.setattr("scripts.run_live_demo_evaluation.run_api_smoke_reports", fake_api_reports)
    monkeypatch.setattr("scripts.run_live_demo_evaluation.build_v1_demo_brief", fake_brief)
    monkeypatch.setattr("scripts.run_live_demo_evaluation.stop_api_service", fake_stop)

    manifest = run_live_demo_evaluation(output_dir=tmp_path / "demo", api_base_url="http://127.0.0.1:8000")

    manifest_path = Path(manifest["paths"]["manifest"])
    cover_note_path = Path(manifest["handoff"]["primary_artifacts"]["cover_note"])
    assert manifest["statuses"]["overall"] == "passed"
    assert manifest_path.exists()
    assert cover_note_path.exists()
    disk_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert disk_manifest["statuses"]["api"] == "passed"
    assert disk_manifest["paths"]["manifest"] == str(manifest_path)
    assert disk_manifest["bundle_language"] == "zh"
    assert disk_manifest["handoff"]["ready_for_external_evaluation"] is True
    assert disk_manifest["handoff"]["bundle_language"] == "zh"
    assert disk_manifest["handoff"]["domain_ids"] == ["drive", "hvac"]
    assert disk_manifest["handoff"]["primary_artifacts"]["manifest"] == str(manifest_path)
    assert "KnowFabric 中文评估交付包" in cover_note_path.read_text(encoding="utf-8")
    assert "Live Demo Evaluation Summary" in build_live_demo_evaluation_summary_text(manifest)
    assert [item[0] for item in calls] == ["preflight", "bootstrap", "start_api", "wait_api", "api_reports", "stop_api", "brief"]
