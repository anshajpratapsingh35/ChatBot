from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.backend.core.config import settings
from app.backend.models.document import Document, ConversationDocumentMapping
from app.backend.models.chunk import DocumentChunk, Embedding
from app.backend.services.document_service import document_service
from app.backend.services.provider_service import provider_service
from app.backend.schemas.chat_schema import CitationItem
from app.backend.utils.file_storage import FileStorageManager
from app.backend.utils.logger import logger

class RAGService:
    """Manages document ingestion, chunking, vector indexing, and semantic retrieval."""

    @staticmethod
    def ingest_document(db: Session, document: Document) -> int:
        """
        Parses document, chunks it, generates embeddings, and saves to database.
        Returns total chunks created.
        """
        try:
            pages = document_service.parse_document(document.storage_path)
            if not pages:
                document.status = "failed"
                db.commit()
                raise ValueError("No extractable text found in document.")

            chunks_data = document_service.chunk_document(pages)
            if not chunks_data:
                document.status = "failed"
                db.commit()
                raise ValueError("Document could not be partitioned into meaningful chunks.")

            chunk_texts = [c["chunk_text"] for c in chunks_data]
            logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
            vectors = provider_service.generate_embeddings(chunk_texts)

            for idx, c in enumerate(chunks_data):
                chunk_record = DocumentChunk(
                    document_id=document.id,
                    chunk_index=c["chunk_index"],
                    chunk_text=c["chunk_text"],
                    char_count=c["char_count"],
                    token_count=c["token_count"],
                    chunk_metadata=c["metadata"]
                )
                db.add(chunk_record)
                db.flush()  # to get chunk_record.id

                embedding_record = Embedding(
                    chunk_id=chunk_record.id,
                    dimensions=len(vectors[idx]),
                    vector_data=vectors[idx]
                )
                db.add(embedding_record)

            document.total_chunks = len(chunks_data)
            document.status = "ready"
            db.commit()
            logger.info(f"Successfully ingested document '{document.filename}' with {len(chunks_data)} chunks.")
            return len(chunks_data)
        except Exception as e:
            db.rollback()
            document.status = "failed"
            db.commit()
            logger.error(f"Failed to ingest document {document.id}: {e}")
            raise e

    @staticmethod
    def retrieve_relevant_chunks(
        db: Session,
        query: str,
        conversation_id: Optional[str] = None,
        top_k: int = None,
        threshold: float = None
    ) -> List[CitationItem]:
        """
        Retrieves the most semantically relevant chunks for a user query.
        """
        limit = top_k or settings.TOP_K_CHUNKS
        min_similarity = threshold or settings.SIMILARITY_THRESHOLD

        # 1. Determine scoped documents
        doc_query = select(Document.id, Document.filename).where(Document.status == "ready")
        if conversation_id:
            # Check if this conversation has specific documents mapped
            mappings = db.scalars(
                select(ConversationDocumentMapping.document_id)
                .where(ConversationDocumentMapping.conversation_id == conversation_id)
            ).all()
            if mappings:
                doc_query = doc_query.where(Document.id.in_(mappings))

        active_docs = db.execute(doc_query).all()
        if not active_docs:
            return []

        doc_dict = {row[0]: row[1] for row in active_docs}
        target_doc_ids = list(doc_dict.keys())

        # 2. Fetch chunks and their embeddings
        chunks_with_embeddings = db.query(DocumentChunk, Embedding).\
            join(Embedding, DocumentChunk.id == Embedding.chunk_id).\
            filter(DocumentChunk.document_id.in_(target_doc_ids)).all()

        if not chunks_with_embeddings:
            return []

        # 3. Generate query embedding
        query_vectors = provider_service.generate_embeddings([query])
        if not query_vectors or not query_vectors[0]:
            return []
        q_vec = np.array(query_vectors[0], dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm

        # 4. Compute cosine similarities
        ranked_results = []
        for chunk, embedding in chunks_with_embeddings:
            v = np.array(embedding.vector_data, dtype=np.float32)
            v_norm = np.linalg.norm(v)
            if v_norm == 0:
                continue
            v = v / v_norm
            similarity = float(np.dot(q_vec, v))

            if similarity >= min_similarity:
                page_num = (chunk.chunk_metadata or {}).get("page_number", 1)
                ranked_results.append((similarity, chunk, doc_dict.get(chunk.document_id, "Unknown Doc"), page_num))

        # Sort descending by similarity score
        ranked_results.sort(key=lambda x: x[0], reverse=True)

        citations = []
        for sim, chunk, doc_name, page_num in ranked_results[:limit]:
            citations.append(CitationItem(
                document_id=chunk.document_id,
                document_name=doc_name,
                page_number=page_num,
                chunk_index=chunk.chunk_index,
                snippet=chunk.chunk_text[:300] + ("..." if len(chunk.chunk_text) > 300 else ""),
                similarity=round(sim, 3)
            ))

        return citations

    @staticmethod
    def format_context_for_prompt(citations: List[CitationItem], db: Session) -> str:
        """Formats the retrieved citations into a grounded context string for the LLM."""
        if not citations:
            return ""

        context_blocks = []
        for item in citations:
            chunk = db.get(DocumentChunk, item.chunk_index) # or query by chunk index / id
            # Retrieve exact chunk text
            chunk_rec = db.scalars(
                select(DocumentChunk).where(
                    DocumentChunk.document_id == item.document_id,
                    DocumentChunk.chunk_index == item.chunk_index
                )
            ).first()
            content = chunk_rec.chunk_text if chunk_rec else item.snippet
            context_blocks.append(
                f"[Source: {item.document_name}, Page: {item.page_number}]\n{content}"
            )
        return "\n\n---\n\n".join(context_blocks)

    @staticmethod
    def delete_document(db: Session, document_id: str) -> bool:
        """Deletes a document, its database chunks/embeddings, and disk file."""
        doc = db.get(Document, document_id)
        if not doc:
            return False
        
        # Remove from disk
        FileStorageManager.delete_file(doc.storage_path)
        
        # Remove from DB (cascades to chunks, embeddings, mappings)
        db.delete(doc)
        db.commit()
        logger.info(f"Deleted document {document_id} and all associated vectors.")
        return True

rag_service = RAGService()
