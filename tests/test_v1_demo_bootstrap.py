"""Tests for the v1 demo bootstrap orchestrator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.bootstrap_v1_demo import (
    bootstrap_v1_demo,
    default_demo_fixture_paths,
)


def test_default_demo_fixture_paths_include_hvac_and_drive_demo_inputs() -> None:
    paths = [str(path) for path in default_demo_fixture_paths()]
    assert "tests/fixtures/manual_validation/hvac_demo_ahu_authority.json" in paths
    assert "tests/fixtures/manual_validation/drive_vfd_faults.json" in paths
    assert len(paths) >= 9


def test_bootstrap_v1_demo_orchestrates_steps(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, object]] = []

    def fake_preflight(output_dir, api_base_url):
        calls.append(("preflight", (str(output_dir), api_base_url)))
        return {"summary": {"failed": 0}}

    def fake_upgrade(config_path):
        calls.append(("upgrade", str(config_path)))

    def fake_sync():
        calls.append(("sync", None))
        return [{"domain_id": "hvac"}, {"domain_id": "drive"}]

    def fake_seed():
        calls.append(("seed", None))
        return [{"fixture_path": "a"}, {"fixture_path": "b"}]

    def fake_reports(output_dir):
        calls.append(("reports", str(output_dir)))
        return [
            {"report_path": str(tmp_path / "hvac.json"), "passed": 6, "failed": 0},
            {"report_path": str(tmp_path / "drive.json"), "passed": 4, "failed": 0},
        ]

    def fake_mcp(output_dir):
        calls.append(("mcp", str(output_dir)))
        return [
            {"report_path": str(tmp_path / "hvac_mcp.json"), "passed": 6, "failed": 0},
            {"report_path": str(tmp_path / "drive_mcp.json"), "passed": 4, "failed": 0},
        ]

    def fake_api(base_url, output_dir):
        calls.append(("api", (base_url, str(output_dir))))
        return [
            {"report_path": str(tmp_path / "hvac_api.json"), "passed": 6, "failed": 0},
            {"report_path": str(tmp_path / "drive_api.json"), "passed": 4, "failed": 0},
        ]

    def fake_brief(report_paths, report_dir, output_path, language):
        calls.append(("brief", (list(report_paths), str(report_dir), str(output_path), language)))
        return Path(output_path)

    monkeypatch.setattr("scripts.bootstrap_v1_demo.ensure_demo_environment_ready", fake_preflight)
    monkeypatch.setattr("scripts.bootstrap_v1_demo.upgrade_database", fake_upgrade)
    monkeypatch.setattr("scripts.bootstrap_v1_demo.sync_demo_ontologies", fake_sync)
    monkeypatch.setattr("scripts.bootstrap_v1_demo.seed_demo_knowledge", fake_seed)
    monkeypatch.setattr("scripts.bootstrap_v1_demo.run_demo_reports", fake_reports)
    monkeypatch.setattr("scripts.bootstrap_v1_demo.run_mcp_smoke_reports", fake_mcp)
    monkeypatch.setattr("scripts.bootstrap_v1_demo.run_api_smoke_reports", fake_api)
    monkeypatch.setattr("scripts.bootstrap_v1_demo.build_v1_demo_brief", fake_brief)

    result = bootstrap_v1_demo(
        output_dir=tmp_path / "demo",
        brief_path=tmp_path / "demo" / "brief.md",
        config_path="alembic.ini",
        api_base_url="http://127.0.0.1:8000",
    )

    assert result["brief_path"] == str(tmp_path / "demo" / "brief.md")
    assert result["preflight"] == {"summary": {"failed": 0}}
    assert result["brief_language"] == "zh"
    assert len(result["mcp_reports"]) == 2
    assert len(result["api_reports"]) == 2
    assert [item[0] for item in calls] == ["preflight", "upgrade", "sync", "seed", "reports", "mcp", "api", "brief"]
