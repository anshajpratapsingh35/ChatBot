import os
import pytest
from app.backend.database.connection import get_db
from app.backend.models.document import Document
from app.backend.services.document_service import document_service
from app.backend.services.rag_service import rag_service
from app.backend.utils.file_storage import FileStorageManager

def test_document_chunking_overlap():
    pages_data = [
        {"page": 1, "text": "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta Iota Kappa Lambda Mu Nu Xi Omicron Pi Rho Sigma Tau Upsilon Phi Chi Psi Omega."},
        {"page": 2, "text": "The Multimodal AI Companion combines RAG, speech synthesis, and vision reasoning into a secure unified platform."}
    ]
    chunks = document_service.chunk_document(pages_data, chunk_size=50, chunk_overlap=15)
    assert len(chunks) > 1
    assert all("chunk_text" in c for c in chunks)
    assert chunks[0]["metadata"]["page_number"] == 1

def test_document_ingestion_and_retrieval():
    sample_text = (
        "Project Antigravity is a multimodal companion system. "
        "The security module enforces file signature checks and rate limiting. "
        "The crisis module provides immediate access to Tele-MANAS and 988 suicide lifelines."
    ).encode("utf-8")

    file_id, file_path, file_hash = FileStorageManager.save_document("sample_policy.txt", sample_text)

    db_gen = get_db()
    db = next(db_gen)
    try:
        doc = Document(
            id=file_id,
            filename="sample_policy.txt",
            mime_type="text/plain",
            file_size_bytes=len(sample_text),
            storage_path=file_path,
            file_hash=file_hash,
            status="processing"
        )
        db.add(doc)
        db.commit()

        # Ingest
        chunks_count = rag_service.ingest_document(db, doc)
        assert chunks_count > 0
        assert doc.status == "ready"

        # Semantic Search Query
        citations = rag_service.retrieve_relevant_chunks(
            db=db,
            query="What lifelines does the crisis module provide?",
            top_k=2,
            threshold=0.1
        )
        assert len(citations) > 0
        assert "sample_policy.txt" in citations[0].document_name

        # Clean up
        rag_service.delete_document(db, doc.id)
        assert db.get(Document, doc.id) is None
    finally:
        db.close()
