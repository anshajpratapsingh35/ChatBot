import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.models.base import Base

if TYPE_CHECKING:
    from app.backend.models.document import Document

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # page_number, heading, etc.

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    embedding: Mapped[Optional["Embedding"]] = relationship(
        "Embedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan"
    )

class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), unique=True, nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_data: Mapped[list] = mapped_column(JSON, nullable=False)  # List[float]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    chunk: Mapped["DocumentChunk"] = relationship("DocumentChunk", back_populates="embedding")
