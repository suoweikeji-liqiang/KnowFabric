"""Tests for section-aware HVAC doc-level extraction helpers."""

from types import SimpleNamespace

from scripts.run_hvac_doclevel_extraction_batch import split_rows_into_sections


def _row(chunk_id: str, page_no: int, text: str):
    chunk = SimpleNamespace(
        chunk_id=chunk_id,
        page_no=page_no,
        chunk_index=int(chunk_id.rsplit("_", 1)[-1]),
        cleaned_text=text,
        text_excerpt=text[:120],
    )
    page = SimpleNamespace(page_no=page_no)
    doc = SimpleNamespace(doc_id="doc_test", file_name="test.pdf")
    return chunk, page, doc


def test_split_rows_into_sections_starts_new_section_at_clause_heading():
    rows = [
        _row("chunk_1", 1, "1. Scope\nThis standard covers HVAC systems."),
        _row("chunk_2", 2, "1.1 Application\nSmall details."),
        _row("chunk_3", 3, "5.20.4.15 Chiller stage up logic\nWhen load rises, stage up."),
        _row("chunk_4", 4, "The sequence shall increase active chillers."),
    ]

    sections = split_rows_into_sections(rows, max_tokens=200, min_tokens_before_heading=5)

    assert [section["section_id"] for section in sections] == ["section_001", "section_002", "section_003"]
    assert sections[2]["title"].startswith("5.20.4.15")
    assert [row[0].chunk_id for row in sections[2]["rows"]] == ["chunk_3", "chunk_4"]


def test_split_rows_into_sections_respects_token_limit_without_heading():
    rows = [
        _row("chunk_1", 1, "alpha " * 120),
        _row("chunk_2", 2, "beta " * 120),
        _row("chunk_3", 3, "gamma " * 120),
    ]

    sections = split_rows_into_sections(rows, max_tokens=90, min_tokens_before_heading=999)

    assert len(sections) == 3
    assert [section["page_start"] for section in sections] == [1, 2, 3]
