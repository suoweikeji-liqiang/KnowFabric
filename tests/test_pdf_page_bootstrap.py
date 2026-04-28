"""Tests for bootstrapping PDF pages into Document/Page/Chunk rows."""

import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import OntologyAliasV2, OntologyMappingV2
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.bootstrap_pdf_pages_to_chunks import _sanitize_pdf_text, seed_pdf_pages_as_chunks
from scripts.generate_chunk_backfill_candidates import generate_chunk_backfill_candidates
from scripts.prepare_pdf_review_bundle import PageGroupSpec, prepare_pdf_review_bundle

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        engine,
        tables=[
            Document.__table__,
            DocumentPage.__table__,
            ContentChunk.__table__,
            OntologyAliasV2.__table__,
            OntologyMappingV2.__table__,
        ],
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_ontology(session_factory) -> None:
    db = session_factory()
    try:
        for root in (HVAC_V2_ROOT, DRIVE_V2_ROOT):
            bundle = load_domain_package_v2(root)
            db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
            mapping_rows = build_ontology_mapping_rows(bundle)
            if mapping_rows:
                db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.commit()
    finally:
        db.close()


def _write_simple_pdf(path: Path, page_texts: list[str]) -> None:
    objects = []
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    kids = " ".join(f"{3 + index} 0 R" for index in range(len(page_texts)))
    objects.append(f"2 0 obj\n<< /Type /Pages /Count {len(page_texts)} /Kids [{kids}] >>\nendobj\n")
    page_object_numbers = []
    font_object_number = 3 + len(page_texts)
    content_start = font_object_number + 1
    for index, _ in enumerate(page_texts):
        page_object_number = 3 + index
        content_object_number = content_start + index
        page_object_numbers.append(page_object_number)
        objects.append(
            f"{page_object_number} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_object_number} 0 R >> >> "
            f"/Contents {content_object_number} 0 R >>\n"
            f"endobj\n"
        )
    objects.append(f"{font_object_number} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    for index, text in enumerate(page_texts):
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_object_number = content_start + index
        stream = f"BT\n/F1 18 Tf\n72 720 Td\n({escaped}) Tj\nET\n"
        objects.append(
            f"{content_object_number} 0 obj\n"
            f"<< /Length {len(stream.encode('utf-8'))} >>\n"
            f"stream\n{stream}endstream\nendobj\n"
        )

    header = "%PDF-1.4\n"
    offsets = [0]
    body = ""
    for obj in objects:
        offsets.append(len(header.encode("utf-8")) + len(body.encode("utf-8")))
        body += obj
    xref_start = len(header.encode("utf-8")) + len(body.encode("utf-8"))
    xref = [f"xref\n0 {len(objects) + 1}\n", "0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n")
    trailer = f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref_start}\n%%EOF\n"
    path.write_bytes((header + body + "".join(xref) + trailer).encode("utf-8"))


def test_seed_pdf_pages_as_chunks_writes_document_page_and_chunk(monkeypatch) -> None:
    """Selected PDF pages should become Document/Page/Chunk rows with extracted text."""

    session_factory = _build_session_factory()
    monkeypatch.setattr("scripts.bootstrap_pdf_pages_to_chunks.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "sample.pdf"
        _write_simple_pdf(pdf_path, ["AHU system mode hierarchy occupied cooldown"])
        doc_id, seeded = seed_pdf_pages_as_chunks(
            pdf_path,
            domain_id="hvac",
            page_numbers=[1],
            page_type="application_guide",
            chunk_type="guidance_block",
            doc_id="doc_pdf_seed_001",
        )

    db = session_factory()
    try:
        assert doc_id == "doc_pdf_seed_001"
        assert seeded == 1
        assert db.query(Document).count() == 1
        assert db.query(DocumentPage).one().page_type == "application_guide"
        assert "AHU system mode hierarchy" in db.query(ContentChunk).one().cleaned_text
    finally:
        db.close()


def test_sanitize_pdf_text_removes_nul_characters() -> None:
    """PDF bootstrap should strip NUL characters before persistence."""

    assert _sanitize_pdf_text("AHU\x00 maintenance\x00") == "AHU maintenance"


def test_seeded_pdf_pages_can_feed_candidate_generation(monkeypatch) -> None:
    """Bootstrapped PDF pages should enter the current candidate pipeline."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.bootstrap_pdf_pages_to_chunks.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "sample.pdf"
        _write_simple_pdf(pdf_path, ["AHU system mode hierarchy occupied cooldown setup warmup setback unoccupied"])
        doc_id, _ = seed_pdf_pages_as_chunks(
            pdf_path,
            domain_id="hvac",
            page_numbers=[1],
            page_type="application_guide",
            chunk_type="guidance_block",
            doc_id="doc_pdf_seed_ahu",
        )
        payload = generate_chunk_backfill_candidates(
            "hvac",
            doc_id=doc_id,
            equipment_class_id="ahu",
        )

    assert len(payload["candidate_entries"]) == 1
    assert payload["candidate_entries"][0]["knowledge_object_type"] == "application_guidance"


def test_prepare_pdf_review_bundle_handles_mixed_page_types(monkeypatch) -> None:
    """Mixed page types from one PDF should seed once and prepare one review bundle."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.bootstrap_pdf_pages_to_chunks.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = Path(tmp_dir) / "authority_sample.pdf"
        bundle_dir = Path(tmp_dir) / "review_bundle"
        _write_simple_pdf(
            pdf_path,
            [
                "Air handling unit application sequence occupied cooldown setup warmup setback unoccupied supply air.",
                "Air handling unit maintenance procedure inspect filters clean coils replace belts regularly.",
            ],
        )
        manifest = prepare_pdf_review_bundle(
            pdf_path,
            "hvac",
            bundle_dir,
            page_groups=[
                PageGroupSpec(page_numbers=(1,), page_type="application_guide"),
                PageGroupSpec(page_numbers=(2,), page_type="maintenance_guide"),
            ],
            equipment_class_id="ahu",
        )
        candidates = json.loads(Path(manifest["paths"]["candidates"]).read_text(encoding="utf-8"))
        assert Path(manifest["paths"]["pdf_review_bundle_manifest"]).exists()

    assert manifest["seeded_pages"] == 2
    assert manifest["counts"]["review_packs"] == 1
    assert {entry["page_type"] for entry in candidates["candidate_entries"]} == {
        "application_guide",
        "maintenance_guide",
    }
    assert {entry["knowledge_object_type"] for entry in candidates["candidate_entries"]} == {
        "application_guidance",
        "maintenance_procedure",
    }


if __name__ == "__main__":
    class _MonkeyPatch:
        def __init__(self) -> None:
            self._patches = []

        def setattr(self, target: str, value) -> None:
            module_name, attr_name = target.rsplit(".", 1)
            module = __import__(module_name, fromlist=[attr_name])
            original = getattr(module, attr_name)
            setattr(module, attr_name, value)
            self._patches.append((module, attr_name, original))

        def undo(self) -> None:
            while self._patches:
                module, attr_name, original = self._patches.pop()
                setattr(module, attr_name, original)

    monkeypatch = _MonkeyPatch()
    test_seed_pdf_pages_as_chunks_writes_document_page_and_chunk(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_seeded_pdf_pages_can_feed_candidate_generation(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_prepare_pdf_review_bundle_handles_mixed_page_types(monkeypatch)
    monkeypatch.undo()
    print("PDF page bootstrap checks passed")
