"""Tests for backfilling inventory metadata onto Document rows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.backfill_document_inventory_metadata import (
    apply_inventory_metadata,
    fields_from_inventory_row,
    latest_inventory_csv,
)


@dataclass
class DocumentStub:
    file_name: str = "manual.pdf"
    text_quality: str | None = None
    page_count: int | None = None
    sample_text_chars_first_3_pages: int | None = None
    inventory_source_path: str | None = None


def test_latest_inventory_csv_skips_runs_without_source_inventory(tmp_path: Path) -> None:
    older = tmp_path / "20260507T083207Z"
    newer_without_inventory = tmp_path / "20260514T091154Z"
    older.mkdir()
    newer_without_inventory.mkdir()
    expected = older / "source_inventory.csv"
    expected.write_text("path,file_name\n/tmp/a.pdf,a.pdf\n", encoding="utf-8")

    assert latest_inventory_csv(tmp_path) == expected


def test_fields_from_inventory_row_coerces_numeric_values() -> None:
    row = {
        "path": "/Volumes/TSD302/manual.pdf",
        "text_quality": "good_text",
        "page_count": "83.0",
        "sample_text_chars_first_3_pages": "12345",
    }

    fields = fields_from_inventory_row(row)

    assert fields == {
        "text_quality": "good_text",
        "page_count": 83,
        "sample_text_chars_first_3_pages": 12345,
        "inventory_source_path": "/Volumes/TSD302/manual.pdf",
    }


def test_apply_inventory_metadata_updates_only_inventory_fields() -> None:
    doc = DocumentStub()
    row = {
        "path": "/Volumes/TSD302/manual.pdf",
        "text_quality": "partial_text",
        "page_count": "14",
        "sample_text_chars_first_3_pages": "",
    }

    filled = apply_inventory_metadata(doc, row)

    assert filled == ["text_quality", "page_count", "inventory_source_path"]
    assert doc.text_quality == "partial_text"
    assert doc.page_count == 14
    assert doc.sample_text_chars_first_3_pages is None
    assert doc.inventory_source_path == "/Volumes/TSD302/manual.pdf"
