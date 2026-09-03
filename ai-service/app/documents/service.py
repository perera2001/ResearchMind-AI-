import os
import shutil
import tempfile

from fastapi import UploadFile

from app.rag.bm25_store import bm25_store
from app.rag.chunker import create_semantic_chunks
from app.rag.pdf_loader import load_pdf_pages
from app.rag.vector_store import vector_store


def process_uploaded_pdf(
    file: UploadFile,
    user_id: int,
    document_id: int,
    file_name: str,
    file_path: str,
) -> dict:
    temporary_file_path = ""

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temporary_file:
            shutil.copyfileobj(file.file, temporary_file)
            temporary_file_path = temporary_file.name

        pages = load_pdf_pages(
            file_path=temporary_file_path,
            metadata_file_path=file_path,
            user_id=user_id,
            document_id=document_id,
            file_name=file_name,
        )

        if not pages or not any(
            page.page_content.strip()
            for page in pages
        ):
            raise ValueError("Could not extract text from PDF")

        chunks = create_semantic_chunks(pages=pages)

        vector_store.add_chunks(chunks)
        bm25_store.add_chunks(chunks)

        return {
            "status": "processed",
            "page_count": len(pages),
            "chunk_count": len(chunks),
        }

    except Exception:
        vector_store.delete_document_chunks(
            user_id=user_id,
            document_id=document_id,
        )
        bm25_store.delete_document_chunks(
            user_id=user_id,
            document_id=document_id,
        )
        raise

    finally:
        if temporary_file_path and os.path.exists(temporary_file_path):
            os.remove(temporary_file_path)


def delete_document_chunks(
    user_id: int,
    document_id: int,
) -> dict:
    vector_store.delete_document_chunks(
        user_id=user_id,
        document_id=document_id,
    )
    bm25_store.delete_document_chunks(
        user_id=user_id,
        document_id=document_id,
    )

    return {
        "message": "Document chunks deleted successfully",
    }
