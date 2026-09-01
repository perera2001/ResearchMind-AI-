import os
import shutil
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.documents.models import Document
from app.rag.bm25_store import bm25_store
from app.rag.chunker import create_semantic_chunks
from app.rag.pdf_loader import load_pdf_pages
from app.rag.vector_store import vector_store


def save_uploaded_pdf(
    file: UploadFile,
    user_id: int,
    db: Session,
) -> Document:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    existing_document = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.file_name == file.filename,
        )
        .first()
    )

    if existing_document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This PDF is already uploaded",
        )

    user_folder = os.path.join(
        settings.pdf_upload_path,
        str(user_id),
    )

    os.makedirs(
        user_folder,
        exist_ok=True,
    )

    unique_file_name = f"{uuid4()}_{file.filename}"

    file_path = os.path.join(
        user_folder,
        unique_file_name,
    )

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        document = Document(
            user_id=user_id,
            file_name=file.filename,
            file_path=file_path,
            status="processing",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        pages = load_pdf_pages(file_path)

        if not pages:
            document.status = "failed"
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from PDF",
            )

        chunks = create_semantic_chunks(
            pages=pages,
            document_id=document.id,
            user_id=user_id,
            file_name=file.filename,
        )

        vector_store.add_chunks(chunks)
        bm25_store.add_chunks(chunks)

        document.page_count = len(pages)
        document.chunk_count = len(chunks)
        document.status = "processed"

        db.commit()
        db.refresh(document)

        return document

    except HTTPException:
        raise

    except Exception as error:
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(error)}",
        )


def get_user_documents(
    user_id: int,
    db: Session,
):
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


def delete_user_document(
    document_id: int,
    user_id: int,
    db: Session,
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    vector_store.delete_document_chunks(
        user_id=user_id,
        document_id=document_id,
    )

    bm25_store.delete_document_chunks(
        user_id=user_id,
        document_id=document_id,
    )

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
    }