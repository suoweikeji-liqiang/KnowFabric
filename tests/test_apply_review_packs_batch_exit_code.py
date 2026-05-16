"""CLI exit-code tests for review-pack batch apply."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import apply_review_packs_batch


def test_main_returns_nonzero_when_any_pack_failed(monkeypatch, tmp_path):
    def fake_apply_review_packs_in_directory(*_args, **_kwargs):
        return {
            "summary": {
                "applied": 0,
                "skipped_pending": 0,
                "skipped_no_accepted": 0,
                "failed": 1,
            },
            "report_path": str(tmp_path / "report.json"),
        }

    monkeypatch.setattr(
        apply_review_packs_batch,
        "apply_review_packs_in_directory",
        fake_apply_review_packs_in_directory,
    )

    assert apply_review_packs_batch.main([str(tmp_path)]) == 1


def test_main_returns_zero_when_no_pack_failed(monkeypatch, tmp_path):
    def fake_apply_review_packs_in_directory(*_args, **_kwargs):
        return {
            "summary": {
                "applied": 1,
                "skipped_pending": 0,
                "skipped_no_accepted": 0,
                "failed": 0,
            },
            "report_path": str(tmp_path / "report.json"),
        }

    monkeypatch.setattr(
        apply_review_packs_batch,
        "apply_review_packs_in_directory",
        fake_apply_review_packs_in_directory,
    )

    assert apply_review_packs_batch.main([str(tmp_path)]) == 0
