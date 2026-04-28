"""Page generation service."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from pypdf import PdfReader

from packages.db.models import Document, DocumentPage, ProcessingJob, ProcessingStageLog
from packages.storage.manager import StorageManager


class ParserService:
    """Document parsing service for page generation."""

    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager

    def parse_document(self, db: Session, doc_id: str) -> dict:
        """Parse document and generate pages."""
        # Get document
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if not doc:
            raise ValueError(f"Document not found: {doc_id}")

        # Create job
        job_id = f"job_{uuid.uuid4().hex[:16]}"
        job = ProcessingJob(
            job_id=job_id,
            job_type='parse_document',
            target_doc_id=doc_id,
            status='running',
            started_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()

        # Create stage
        stage_id = f"stage_{uuid.uuid4().hex[:16]}"
        stage = ProcessingStageLog(
            stage_id=stage_id,
            job_id=job_id,
            stage_name='parse',
            doc_id=doc_id,
            status='running',
            started_at=datetime.now(timezone.utc)
        )
        db.add(stage)
        db.commit()

        try:
            # Get file path
            file_path = self.storage.get_document_path(doc.storage_path)

            # Parse PDF
            pages_created = self._parse_pdf(db, doc_id, str(file_path))

            # Update document status
            doc.parse_status = 'completed'

            # Update stage
            stage.status = 'success'
            stage.completed_at = datetime.now(timezone.utc)
            elapsed = (stage.completed_at - stage.started_at).total_seconds() * 1000
            stage.elapsed_ms = int(elapsed)

            # Update job
            job.status = 'success'
            job.completed_at = datetime.now(timezone.utc)

            db.commit()

            return {
                'job_id': job_id,
                'doc_id': doc_id,
                'pages_created': pages_created,
                'status': 'success'
            }

        except Exception as e:
            doc.parse_status = 'failed'
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.completed_at = datetime.now(timezone.utc)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            raise

    def _parse_pdf(self, db: Session, doc_id: str, file_path: str) -> int:
        """Parse PDF and create page records."""
        reader = PdfReader(file_path)
        pages_created = 0

        for page_no, page in enumerate(reader.pages, start=1):
            # Extract text
            raw_text = self._strip_unsupported_chars(page.extract_text())
            cleaned_text = self._clean_text(raw_text)

            # Generate page_id
            page_id = f"page_{uuid.uuid4().hex[:16]}"

            # Create page record
            page_record = DocumentPage(
                page_id=page_id,
                doc_id=doc_id,
                page_no=page_no,
                raw_text=raw_text,
                cleaned_text=cleaned_text,
                page_type='text'
            )

            db.add(page_record)
            pages_created += 1

        db.commit()
        return pages_created

    @staticmethod
    def _clean_text(text: str) -> str:
        """Basic text cleaning."""
        if not text:
            return ""
        text = ParserService._strip_unsupported_chars(text)
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        return '\n'.join(lines)

    @staticmethod
    def _strip_unsupported_chars(text: str | None) -> str:
        """Remove characters PostgreSQL text fields cannot store."""

        if not text:
            return ""
        return text.replace("\x00", "")
