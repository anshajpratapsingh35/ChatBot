from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.backend.database.connection import get_db
from app.backend.models.document import Document, ConversationDocumentMapping
from app.backend.schemas.document_schema import DocumentUploadResponse, DocumentInfo, DocumentListResponse
from app.backend.services.rag_service import rag_service
from app.backend.core.security import SecurityValidator
from app.backend.utils.file_storage import FileStorageManager
from app.backend.utils.logger import logger

router = APIRouter(prefix="/api/documents", tags=["Documents & RAG"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Uploads and ingests a PDF, DOCX, or TXT document into the RAG pipeline."""
    content = await file.read()
    SecurityValidator.validate_document(file.filename, content, file.content_type)
    
    # Calculate hash to avoid duplicate ingestion
    file_hash = FileStorageManager.calculate_sha256(content)
    existing = db.scalars(select(Document).where(Document.file_hash == file_hash)).first()
    if existing:
        return DocumentUploadResponse(
            message="Document already exists in the knowledge base.",
            document=DocumentInfo.model_validate(existing),
            chunks_created=existing.total_chunks
        )

    # Save to storage
    file_id, file_path, _ = FileStorageManager.save_document(file.filename, content)

    # Record document in DB
    new_doc = Document(
        id=file_id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(content),
        storage_path=file_path,
        file_hash=file_hash,
        status="processing"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Execute ingestion, chunking, and embedding
    try:
        chunks_count = rag_service.ingest_document(db, new_doc)
        db.refresh(new_doc)
        return DocumentUploadResponse(
            message="Document successfully processed and indexed for RAG.",
            document=DocumentInfo.model_validate(new_doc),
            chunks_created=chunks_count
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)):
    """Lists all uploaded documents and processing status."""
    docs = db.scalars(select(Document).order_by(desc(Document.uploaded_at))).all()
    return DocumentListResponse(documents=[DocumentInfo.model_validate(d) for d in docs])

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Deletes a document, its database vectors, and filesystem storage."""
    success = rag_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document and associated vectors deleted successfully.", "id": document_id}

@router.post("/attach/{conversation_id}/{document_id}")
def attach_document_to_conversation(
    conversation_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    """Associates a document specifically with a conversation thread."""
    existing = db.scalars(
        select(ConversationDocumentMapping).where(
            ConversationDocumentMapping.conversation_id == conversation_id,
            ConversationDocumentMapping.document_id == document_id
        )
    ).first()
    if existing:
        return {"message": "Document is already mapped to this conversation."}

    mapping = ConversationDocumentMapping(
        conversation_id=conversation_id,
        document_id=document_id
    )
    db.add(mapping)
    db.commit()
    return {"message": "Document successfully mapped to conversation.", "conversation_id": conversation_id, "document_id": document_id}
