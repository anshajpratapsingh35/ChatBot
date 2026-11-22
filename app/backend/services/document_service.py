import os
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from app.backend.core.config import settings
from app.backend.utils.logger import logger

class DocumentService:
    """Handles text extraction and chunking for PDF, DOCX, and TXT files."""

    @staticmethod
    def extract_text_from_pdf(filepath: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF page by page.
        Returns a list of dicts: [{"page": 1, "text": "..."}]
        """
        pages_content = []
        try:
            doc = fitz.open(filepath)
            for page_idx in range(len(doc)):
                page = doc.load_page(page_idx)
                text = page.get_text("text").strip()
                if text:
                    pages_content.append({
                        "page": page_idx + 1,
                        "text": text
                    })
            doc.close()
            logger.info(f"Extracted {len(pages_content)} pages from PDF: {filepath}")
        except Exception as e:
            logger.error(f"Error reading PDF {filepath}: {e}")
            raise ValueError(f"Failed to parse PDF document: {e}")
        return pages_content

    @staticmethod
    def extract_text_from_docx(filepath: str) -> List[Dict[str, Any]]:
        """Extracts text from DOCX paragraphs and tables."""
        pages_content = []
        try:
            doc = DocxDocument(filepath)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        full_text.append(row_text)
            
            combined = "\n\n".join(full_text)
            if combined:
                pages_content.append({"page": 1, "text": combined})
            logger.info(f"Extracted content from DOCX: {filepath}")
        except Exception as e:
            logger.error(f"Error reading DOCX {filepath}: {e}")
            raise ValueError(f"Failed to parse DOCX document: {e}")
        return pages_content

    @staticmethod
    def extract_text_from_txt(filepath: str) -> List[Dict[str, Any]]:
        """Extracts text from TXT files with fallback encoding detection."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except UnicodeDecodeError:
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read().strip()
        except Exception as e:
            logger.error(f"Error reading TXT {filepath}: {e}")
            raise ValueError(f"Failed to parse text document: {e}")

        if content:
            return [{"page": 1, "text": content}]
        return []

    @classmethod
    def parse_document(cls, filepath: str) -> List[Dict[str, Any]]:
        """Dispatcher based on file extension."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf":
            return cls.extract_text_from_pdf(filepath)
        elif ext == ".docx":
            return cls.extract_text_from_docx(filepath)
        elif ext == ".txt":
            return cls.extract_text_from_txt(filepath)
        else:
            raise ValueError(f"Unsupported document extension: {ext}")

    @classmethod
    def chunk_document(
        cls,
        pages_data: List[Dict[str, Any]],
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Recursively splits text into overlapping chunks, tracking page numbers.
        Returns a list of chunks with metadata.
        """
        size = chunk_size or settings.CHUNK_SIZE
        overlap = chunk_overlap or settings.CHUNK_OVERLAP
        chunks = []
        global_chunk_idx = 0

        for page_item in pages_data:
            page_num = page_item["page"]
            text = page_item["text"]

            # Simple sliding window chunker preserving words
            start = 0
            text_len = len(text)

            while start < text_len:
                end = min(start + size, text_len)
                
                # If not at the end of the text, look for sentence boundary or whitespace
                if end < text_len:
                    boundary = text.rfind("\n", start + size // 2, end)
                    if boundary == -1:
                        boundary = text.rfind(". ", start + size // 2, end)
                    if boundary == -1:
                        boundary = text.rfind(" ", start + size // 2, end)
                    if boundary != -1:
                        end = boundary + 1

                chunk_str = text[start:end].strip()
                if chunk_str:
                    chunks.append({
                        "chunk_index": global_chunk_idx,
                        "chunk_text": chunk_str,
                        "char_count": len(chunk_str),
                        "token_count": len(chunk_str.split()),
                        "metadata": {
                            "page_number": page_num
                        }
                    })
                    global_chunk_idx += 1

                if end >= text_len:
                    break
                start = max(start + 1, end - overlap)

        return chunks

document_service = DocumentService()
