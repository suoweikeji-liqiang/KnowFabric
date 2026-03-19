#!/usr/bin/env python3
"""Bootstrap selected PDF pages into Document/Page/Chunk rows."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal


def _slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def _doc_id_from_path(path: Path, domain_id: str) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    return f"doc_{domain_id}_{digest}"


def _page_id(doc_id: str, page_no: int) -> str:
    return f"{doc_id}_page_{page_no}"


def _chunk_id(doc_id: str, page_no: int) -> str:
    return f"{doc_id}_chunk_{page_no}"


def _file_hash(path: Path) -> str:
    digest = hashlib.sha1(path.read_bytes()).hexdigest()
    return digest


def _sanitize_pdf_text(text: str) -> str:
    return text.replace("\x00", "").strip()


def seed_pdf_pages_as_chunks(
    pdf_path: str | Path,
    *,
    domain_id: str,
    page_numbers: list[int],
    page_type: str,
    chunk_type: str,
    doc_id: str | None = None,
) -> tuple[str, int]:
    """Seed selected PDF pages as one page and one chunk each."""

    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(source)
    reader = PdfReader(str(source))
    resolved_doc_id = doc_id or _doc_id_from_path(source, domain_id)
    session = SessionLocal()
    try:
        session.merge(
            Document(
                doc_id=resolved_doc_id,
                file_hash=_file_hash(source),
                storage_path=str(source),
                file_name=source.name,
                file_ext=source.suffix.lstrip(".") or "pdf",
                mime_type="application/pdf",
                file_size=source.stat().st_size,
                source_domain=domain_id,
                parse_status="complete",
                is_active=True,
            )
        )
        session.flush()
        seeded_pages = 0
        for page_no in page_numbers:
            if page_no < 1 or page_no > len(reader.pages):
                raise ValueError(f"Page number out of range: {page_no}")
            page = reader.pages[page_no - 1]
            text = _sanitize_pdf_text(page.extract_text() or "")
            if not text:
                raise ValueError(f"No extractable text on page {page_no}")
            page_id = _page_id(resolved_doc_id, page_no)
            chunk_id = _chunk_id(resolved_doc_id, page_no)
            session.merge(
                DocumentPage(
                    page_id=page_id,
                    doc_id=resolved_doc_id,
                    page_no=page_no,
                    raw_text=text,
                    cleaned_text=text,
                    page_type=page_type,
                )
            )
            session.flush()
            session.merge(
                ContentChunk(
                    chunk_id=chunk_id,
                    doc_id=resolved_doc_id,
                    page_id=page_id,
                    page_no=page_no,
                    chunk_index=0,
                    raw_text=text,
                    cleaned_text=text,
                    text_excerpt=text[:512],
                    chunk_type=chunk_type,
                    evidence_anchor=f'{{"source_page": {page_no}}}',
                )
            )
            seeded_pages += 1
        session.commit()
        return resolved_doc_id, seeded_pages
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", help="Path to a PDF file")
    parser.add_argument("--domain-id", required=True, help="Domain scope such as 'hvac' or 'drive'")
    parser.add_argument("--page", dest="pages", action="append", type=int, required=True, help="1-based page number to seed")
    parser.add_argument("--page-type", required=True, help="Document page_type to write")
    parser.add_argument("--chunk-type", required=True, help="Chunk chunk_type to write")
    parser.add_argument("--doc-id", help="Optional explicit doc_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    doc_id, seeded = seed_pdf_pages_as_chunks(
        args.pdf_path,
        domain_id=args.domain_id,
        page_numbers=args.pages,
        page_type=args.page_type,
        chunk_type=args.chunk_type,
        doc_id=args.doc_id,
    )
    print(f"Seeded {seeded} page(s) into {doc_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"PDF page bootstrap failed: {exc}")
        raise SystemExit(1)
