"""Tests for the external evaluation demo environment preflight."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.check_demo_environment as demo_check
from scripts.demo_bundle_inventory import (
    default_demo_example_query_paths,
    default_demo_fixture_paths,
)


class _FakeVersionInfo:
    def __init__(self, major: int, minor: int, micro: int):
        self.major = major
        self.minor = minor
        self.micro = micro


def _touch_required_demo_files(root: Path) -> None:
    for relative_path in [Path(".env.example"), Path("alembic.ini"), *default_demo_example_query_paths(), *default_demo_fixture_paths()]:
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok\n", encoding="utf-8")


def test_check_demo_environment_passes_with_stubbed_db_and_api(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _touch_required_demo_files(tmp_path)
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql://demo:demo@localhost:5432/knowfabric\n", encoding="utf-8")

    report = demo_check.check_demo_environment(
        output_dir="output/demo",
        api_base_url="http://127.0.0.1:8000",
        db_checker=lambda url: None,
        health_fetcher=lambda base_url: (200, {"service": "api", "status": "healthy"}),
    )

    assert report["summary"] == {"passed": 8, "failed": 0, "skipped": 0}
    assert "Demo Environment Preflight" in demo_check.build_demo_environment_summary_text(report)


def test_ensure_demo_environment_ready_raises_for_missing_config(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _touch_required_demo_files(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(demo_check, "_default_db_checker", lambda url: None)

    try:
        demo_check.ensure_demo_environment_ready(output_dir="output/demo")
    except RuntimeError as exc:
        message = str(exc)
    else:  # pragma: no cover - defensive guard
        raise AssertionError("ensure_demo_environment_ready should fail without DATABASE_URL")

    assert "FAILED config" in message


def test_check_demo_environment_flags_wrong_python_version(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _touch_required_demo_files(tmp_path)
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql://demo:demo@localhost:5432/knowfabric\n", encoding="utf-8")
    monkeypatch.setattr(demo_check.sys, "version_info", _FakeVersionInfo(3, 14, 0))

    report = demo_check.check_demo_environment(
        output_dir="output/demo",
        db_checker=lambda url: None,
    )

    statuses = {item["name"]: item["status"] for item in report["checks"]}
    assert statuses["python"] == "failed"
