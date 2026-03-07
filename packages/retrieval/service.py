"""Retrieval service for chunk search."""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from packages.db.models import ContentChunk, DocumentPage, Document


class RetrievalService:
    """Chunk retrieval service with full-text search."""

    def search_chunks(
        self,
        db: Session,
        query: str,
        domain: Optional[str] = None,
        doc_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search chunks with traceability."""
        # Build query
        q = db.query(
            ContentChunk,
            DocumentPage,
            Document
        ).join(
            DocumentPage,
            ContentChunk.page_id == DocumentPage.page_id
        ).join(
            Document,
            ContentChunk.doc_id == Document.doc_id
        )

        # Apply filters
        if domain:
            q = q.filter(Document.source_domain == domain)
        if doc_id:
            q = q.filter(ContentChunk.doc_id == doc_id)

        # Simple text search (case-insensitive contains)
        if query:
            search_pattern = f"%{query}%"
            q = q.filter(
                or_(
                    ContentChunk.cleaned_text.ilike(search_pattern),
                    ContentChunk.text_excerpt.ilike(search_pattern)
                )
            )

        # Execute query
        results = q.limit(limit).all()

        # Format results with traceability
        output = []
        for chunk, page, doc in results:
            output.append({
                'chunk_id': chunk.chunk_id,
                'doc_id': chunk.doc_id,
                'page_no': chunk.page_no,
                'evidence_text': chunk.text_excerpt or chunk.cleaned_text[:200],
                'cleaned_text': chunk.cleaned_text,
                'chunk_type': chunk.chunk_type,
                'file_name': doc.file_name,
                'source_domain': doc.source_domain,
                'relevance_score': 1.0  # Placeholder for P0
            })

        return output
