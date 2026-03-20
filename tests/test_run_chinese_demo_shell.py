"""Tests for the one-shot Chinese demo shell launcher."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_chinese_demo_shell import run_chinese_demo_shell


def test_run_chinese_demo_shell_refreshes_bundle_and_launches_server(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, object]] = []

    def fake_refresh(**kwargs):
        calls.append(("refresh", kwargs))
        return {"statuses": {"overall": "passed"}}

    def fake_run(command, cwd, env, check):
        calls.append(("run", {"command": command, "cwd": str(cwd), "env": env, "check": check}))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("scripts.run_chinese_demo_shell.run_live_demo_evaluation", fake_refresh)
    monkeypatch.setattr("scripts.run_chinese_demo_shell.subprocess.run", fake_run)

    code = run_chinese_demo_shell(
        output_dir=tmp_path / "demo",
        host="127.0.0.1",
        port=4173,
        bundle_language="zh",
    )

    assert code == 0
    assert calls[0][0] == "refresh"
    assert calls[1][0] == "run"
    run_call = calls[1][1]
    assert run_call["env"]["DEMO_ARTIFACT_DIR"] == str(tmp_path / "demo")
    assert run_call["env"]["ADMIN_WEB_PORT"] == "4173"


def test_run_chinese_demo_shell_can_skip_refresh(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, object]] = []

    def fake_run(command, cwd, env, check):
        calls.append(("run", {"command": command, "cwd": str(cwd), "env": env, "check": check}))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("scripts.run_chinese_demo_shell.subprocess.run", fake_run)

    code = run_chinese_demo_shell(
        output_dir=tmp_path / "demo",
        skip_refresh=True,
    )

    assert code == 0
    assert [item[0] for item in calls] == ["run"]
