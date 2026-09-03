from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.documents.service import (
    delete_document_chunks,
    process_uploaded_pdf,
)
from app.graph.workflow import research_rag_graph
from app.internal.schemas import (
    DocumentProcessResponse,
    InternalChatRequest,
    InternalChatResponse,
)


router = APIRouter(
    prefix="/internal",
    tags=["Internal AI"],
)


@router.post(
    "/documents/process",
    response_model=DocumentProcessResponse,
)
def process_document(
    user_id: int = Form(...),
    document_id: int = Form(...),
    file_name: str = Form(...),
    file_path: str = Form(...),
    file: UploadFile = File(...),
):
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    try:
        return process_uploaded_pdf(
            file=file,
            user_id=user_id,
            document_id=document_id,
            file_name=file_name,
            file_path=file_path,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(error)}",
        )


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    user_id: int,
):
    return delete_document_chunks(
        user_id=user_id,
        document_id=document_id,
    )


@router.post(
    "/chat",
    response_model=InternalChatResponse,
)
def chat(request: InternalChatRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    initial_state = {
        "user_id": request.user_id,
        "session_id": 0,
        "question": request.question,
        "chat_history": request.chat_history,
        "uploaded_documents": request.documents,
        "selected_document_ids": [
            document["document_id"]
            for document in request.documents
        ],
        "retrieval_query": request.question,
        "documents": [],
        "answer": "",
        "retry_count": 0,
        "documents_relevant": False,
        "grounded": False,
        "can_retry": True,
        "sources": [],
    }

    try:
        result = research_rag_graph.invoke(initial_state)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(error)}",
        )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "retry_count": result["retry_count"],
        "documents_relevant": result["documents_relevant"],
        "grounded": result["grounded"],
    }
