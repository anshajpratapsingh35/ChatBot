from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ChunkInfo(BaseModel):
    id: str
    chunk_index: int
    char_count: int
    token_count: int
    snippet: str

class DocumentInfo(BaseModel):
    id: str
    filename: str
    mime_type: str
    file_size_bytes: int
    total_chunks: int
    status: str
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentInfo
    chunks_created: int

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
