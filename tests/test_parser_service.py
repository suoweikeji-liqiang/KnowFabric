"""Tests for PDF parser text sanitization."""

from packages.parser.service import ParserService


def test_parser_clean_text_removes_nul_characters() -> None:
    assert ParserService._clean_text("line 1\x00\n\nline 2\x00") == "line 1\nline 2"
