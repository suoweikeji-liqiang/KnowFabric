"""API service entry point."""
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.core.models import ChunkSearchResult
from packages.db.session import get_db
from packages.retrieval.service import RetrievalService

# Setup logging
setup_logging(settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="KnowFabric API",
    version="0.1.0",
    description="Industrial Knowledge Injection Platform"
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "KnowFabric API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/api/v1/chunks/search", response_model=dict)
async def search_chunks(
    query: str = Query(..., description="Search query"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    doc_id: Optional[str] = Query(None, description="Filter by document ID"),
    limit: int = Query(20, ge=1, le=100, description="Result limit"),
    db: Session = Depends(get_db)
):
    """
    Search chunks with mandatory traceability.

    All results include:
    - chunk_id: Unique chunk identifier
    - doc_id: Source document ID
    - page_no: Source page number
    - evidence_text: Evidence text snippet
    """
    retrieval = RetrievalService()
    results = retrieval.search_chunks(
        db=db,
        query=query,
        domain=domain,
        doc_id=doc_id,
        limit=limit
    )

    # Validate traceability fields
    for result in results:
        if not all([
            result.get('chunk_id'),
            result.get('doc_id'),
            result.get('page_no') is not None,
            result.get('evidence_text')
        ]):
            raise ValueError("Result missing mandatory traceability fields")

    return {
        "success": True,
        "data": results,
        "metadata": {
            "total": len(results),
            "limit": limit,
            "query": query
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
