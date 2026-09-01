from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.documents.schemas import DocumentResponse
from app.documents.service import (
    delete_user_document,
    get_user_documents,
    save_uploaded_pdf,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
)
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return save_uploaded_pdf(
        file=file,
        user_id=current_user.id,
        db=db,
    )


@router.get(
    "",
    response_model=List[DocumentResponse],
)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_documents(
        user_id=current_user.id,
        db=db,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_user_document(
        document_id=document_id,
        user_id=current_user.id,
        db=db,
    )