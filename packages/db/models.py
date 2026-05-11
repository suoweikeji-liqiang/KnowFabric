"""Database models for KnowFabric."""
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from packages.db.session import Base


class Document(Base):
    """Raw document layer - primary truth source."""
    __tablename__ = "document"

    doc_id = Column(String(64), primary_key=True)
    file_hash = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(1024), nullable=False)
    file_name = Column(String(512), nullable=False)
    file_ext = Column(String(32))
    mime_type = Column(String(128))
    file_size = Column(Integer)
    source_domain = Column(String(64), index=True)
    source_batch_id = Column(String(64))
    parse_status = Column(String(32), default="pending")
    is_active = Column(Boolean, default=True, nullable=False)
    authority_level = Column(String(32), nullable=True, default="unspecified")
    publisher = Column(String(128), nullable=True)
    standard_id = Column(String(128), nullable=True)
    publication_year = Column(Integer, nullable=True)
    revision = Column(String(64), nullable=True)
    regulatory_scope = Column(String(32), nullable=True)
    vendor_brand = Column(String(128), nullable=True)
    vendor_model_family = Column(String(128), nullable=True)
    applies_to_equipment_classes_json = Column(JSON, nullable=True)
    language = Column(String(16), nullable=True, default="en")
    authority_metadata_json = Column(JSON, nullable=True)
    is_redistributable = Column(Boolean, default=False, nullable=False)
    authority_review_status = Column(String(32), nullable=True, default="auto_suggested")
    import_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DocumentPage(Base):
    """Page layer - traceability anchor."""
    __tablename__ = "document_page"

    page_id = Column(String(64), primary_key=True)
    doc_id = Column(String(64), ForeignKey("document.doc_id"), nullable=False, index=True)
    page_no = Column(Integer, nullable=False)
    raw_text = Column(Text)
    cleaned_text = Column(Text, nullable=False)
    page_image_path = Column(String(1024))
    page_type = Column(String(32))
    has_table = Column(Boolean, default=False)
    has_diagram = Column(Boolean, default=False)
    ocr_status = Column(String(32))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_page_doc_page_no", "doc_id", "page_no"),
    )


class ContentChunk(Base):
    """Chunk layer - retrieval truth source."""
    __tablename__ = "content_chunk"

    chunk_id = Column(String(64), primary_key=True)
    doc_id = Column(String(64), ForeignKey("document.doc_id"), nullable=False, index=True)
    page_id = Column(String(64), ForeignKey("document_page.page_id"), nullable=False, index=True)
    page_no = Column(Integer, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    raw_text = Column(Text)
    cleaned_text = Column(Text, nullable=False)
    text_excerpt = Column(String(512))
    chunk_type = Column(String(32), nullable=False)
    standard_clause = Column(String(64), nullable=True)
    clause_path = Column(JSON, nullable=True)
    evidence_anchor = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_chunk_doc_page", "doc_id", "page_no"),
    )


class ProcessingJob(Base):
    """Job tracking for processing tasks."""
    __tablename__ = "processing_job"

    job_id = Column(String(64), primary_key=True)
    job_type = Column(String(64), nullable=False, index=True)
    target_doc_id = Column(String(64), ForeignKey("document.doc_id"), index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ProcessingStageLog(Base):
    """Stage-level logging for processing jobs."""
    __tablename__ = "processing_stage_log"

    stage_id = Column(String(64), primary_key=True)
    job_id = Column(String(64), ForeignKey("processing_job.job_id"), nullable=False, index=True)
    stage_name = Column(String(64), nullable=False)
    doc_id = Column(String(64), ForeignKey("document.doc_id"), index=True)
    status = Column(String(32), nullable=False, default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    elapsed_ms = Column(Integer)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_stage_job_doc", "job_id", "doc_id"),
    )
