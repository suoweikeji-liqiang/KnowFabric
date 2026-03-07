"""Chunk generation service."""
import uuid
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from packages.db.models import DocumentPage, ContentChunk, ProcessingJob, ProcessingStageLog


class ChunkingService:
    """Chunk generation service."""

    def __init__(self, max_chunk_length: int = 1000):
        self.max_chunk_length = max_chunk_length

    def chunk_document(self, db: Session, doc_id: str) -> dict:
        """Generate chunks for all pages in document."""
        # Get pages
        pages = db.query(DocumentPage).filter(
            DocumentPage.doc_id == doc_id
        ).order_by(DocumentPage.page_no).all()

        if not pages:
            raise ValueError(f"No pages found for document: {doc_id}")

        # Create job
        job_id = f"job_{uuid.uuid4().hex[:16]}"
        job = ProcessingJob(
            job_id=job_id,
            job_type='chunk_document',
            target_doc_id=doc_id,
            status='running',
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        total_chunks = 0

        for page in pages:
            stage_id = f"stage_{uuid.uuid4().hex[:16]}"
            stage = ProcessingStageLog(
                stage_id=stage_id,
                job_id=job_id,
                stage_name='chunk',
                doc_id=doc_id,
                status='running',
                started_at=datetime.utcnow()
            )
            db.add(stage)
            db.commit()

            try:
                chunks_created = self._chunk_page(db, page)
                total_chunks += chunks_created

                stage.status = 'success'
                stage.completed_at = datetime.utcnow()
                elapsed = (stage.completed_at - stage.started_at).total_seconds() * 1000
                stage.elapsed_ms = int(elapsed)

            except Exception as e:
                stage.status = 'failed'
                stage.error_message = str(e)
                stage.completed_at = datetime.utcnow()

            db.commit()

        # Update job
        job.status = 'success'
        job.completed_at = datetime.utcnow()
        db.commit()

        return {
            'job_id': job_id,
            'doc_id': doc_id,
            'chunks_created': total_chunks,
            'status': 'success'
        }

    def _chunk_page(self, db: Session, page: DocumentPage) -> int:
        """Generate chunks for a single page."""
        text = page.cleaned_text
        if not text:
            return 0

        # Simple paragraph-based chunking
        paragraphs = self._split_paragraphs(text)
        chunks_created = 0

        for idx, para in enumerate(paragraphs):
            if not para.strip():
                continue

            chunk_id = f"chunk_{uuid.uuid4().hex[:16]}"
            text_excerpt = para[:200] if len(para) > 200 else para

            chunk = ContentChunk(
                chunk_id=chunk_id,
                doc_id=page.doc_id,
                page_id=page.page_id,
                page_no=page.page_no,
                chunk_index=idx,
                cleaned_text=para,
                text_excerpt=text_excerpt,
                chunk_type='paragraph'
            )

            db.add(chunk)
            chunks_created += 1

        db.commit()
        return chunks_created

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newline or single newline
        paragraphs = text.split('\n\n')

        # Further split if paragraphs are too long
        result = []
        for para in paragraphs:
            if len(para) <= self.max_chunk_length:
                result.append(para)
            else:
                # Split long paragraphs by sentence or length
                sentences = para.split('. ')
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) <= self.max_chunk_length:
                        current += sent + ". "
                    else:
                        if current:
                            result.append(current.strip())
                        current = sent + ". "
                if current:
                    result.append(current.strip())

        return result
