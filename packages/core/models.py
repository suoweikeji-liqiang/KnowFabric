"""Response models for API."""
from pydantic import BaseModel, Field
from typing import Optional


class ChunkSearchResult(BaseModel):
    """Chunk search result with mandatory traceability fields."""

    # Mandatory traceability fields
    chunk_id: str = Field(..., description="Unique chunk identifier")
    doc_id: str = Field(..., description="Source document ID")
    page_no: int = Field(..., description="Source page number")
    evidence_text: str = Field(..., description="Evidence text snippet")

    # Content fields
    cleaned_text: str = Field(..., description="Full chunk text")
    chunk_type: str = Field(..., description="Chunk type")

    # Metadata fields
    file_name: Optional[str] = Field(None, description="Source file name")
    source_domain: Optional[str] = Field(None, description="Source domain")
    relevance_score: Optional[float] = Field(None, description="Relevance score")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_abc123",
                "doc_id": "doc_xyz789",
                "page_no": 5,
                "evidence_text": "Temperature range: 15-30°C",
                "cleaned_text": "The system operates within a temperature range of 15-30°C...",
                "chunk_type": "paragraph",
                "file_name": "hvac_manual.pdf",
                "source_domain": "hvac",
                "relevance_score": 0.95
            }
        }
