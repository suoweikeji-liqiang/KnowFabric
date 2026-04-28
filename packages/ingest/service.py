"""Document ingestion service."""
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from packages.db.models import Document, ProcessingJob, ProcessingStageLog
from packages.storage.manager import StorageManager


class IngestService:
    """Document ingestion service."""

    SUPPORTED_EXTENSIONS = {'.pdf'}

    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager

    def scan_directory(self, directory: str) -> List[str]:
        """Scan directory for supported documents."""
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")

        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            files.extend(dir_path.glob(f"**/*{ext}"))

        return [str(f) for f in files]

    def import_document(
        self,
        db: Session,
        file_path: str,
        source_domain: Optional[str] = None,
        batch_id: Optional[str] = None
    ) -> Optional[str]:
        """Import single document. Returns doc_id or None if duplicate."""
        # Calculate hash
        file_hash = self.storage.calculate_file_hash(file_path)

        # Check for duplicate
        existing = db.query(Document).filter(
            Document.file_hash == file_hash
        ).first()

        if existing:
            return None  # Skip duplicate

        # Generate doc_id
        doc_id = f"doc_{uuid.uuid4().hex[:16]}"

        # Store file
        storage_path = self.storage.store_document(file_path, doc_id)

        # Get file info
        file_stat = os.stat(file_path)
        file_name = Path(file_path).name
        file_ext = Path(file_path).suffix

        # Create document record
        doc = Document(
            doc_id=doc_id,
            file_hash=file_hash,
            storage_path=storage_path,
            file_name=file_name,
            file_ext=file_ext,
            file_size=file_stat.st_size,
            source_domain=source_domain,
            source_batch_id=batch_id,
            parse_status='pending'
        )

        db.add(doc)
        db.commit()

        return doc_id

    def import_batch(
        self,
        db: Session,
        directory: str,
        source_domain: Optional[str] = None
    ) -> dict:
        """Import all documents from directory."""
        # Generate batch ID
        batch_id = f"batch_{uuid.uuid4().hex[:16]}"

        # Create job
        job_id = f"job_{uuid.uuid4().hex[:16]}"
        job = ProcessingJob(
            job_id=job_id,
            job_type='ingest_batch',
            status='running',
            started_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()

        # Scan directory
        files = self.scan_directory(directory)

        imported = []
        skipped = []
        failed = []

        for file_path in files:
            stage_id = f"stage_{uuid.uuid4().hex[:16]}"
            stage = ProcessingStageLog(
                stage_id=stage_id,
                job_id=job_id,
                stage_name='ingest',
                status='running',
                started_at=datetime.now(timezone.utc)
            )
            db.add(stage)
            db.commit()

            try:
                doc_id = self.import_document(
                    db, file_path, source_domain, batch_id
                )

                if doc_id:
                    imported.append(doc_id)
                    stage.doc_id = doc_id
                    stage.status = 'success'
                else:
                    skipped.append(file_path)
                    stage.status = 'skipped'

                stage.completed_at = datetime.now(timezone.utc)
                elapsed = (stage.completed_at - stage.started_at).total_seconds() * 1000
                stage.elapsed_ms = int(elapsed)

            except Exception as e:
                failed.append(file_path)
                stage.status = 'failed'
                stage.error_message = str(e)
                stage.completed_at = datetime.now(timezone.utc)

            db.commit()

        # Update job
        job.status = 'success' if not failed else 'failed'
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {
            'job_id': job_id,
            'batch_id': batch_id,
            'imported': len(imported),
            'skipped': len(skipped),
            'failed': len(failed),
            'doc_ids': imported
        }
