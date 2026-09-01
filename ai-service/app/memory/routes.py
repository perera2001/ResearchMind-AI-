from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.graph.workflow import research_rag_graph
from app.memory.conversation_memory import add_message, get_memory, set_memory
from app.memory.models import ChatMessage, ChatSession
from app.memory.schemas import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionDetailResponse,
    ChatSessionResponse,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if request.session_id is None:
        session = ChatSession(
            user_id=current_user.id,
            title=request.question[:80],
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        session_id = session.id

    else:
        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id,
            )
            .first()
        )

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )

        session_id = session.id

    db.add(
        ChatMessage(
            session_id=session_id,
            user_id=current_user.id,
            role="user",
            content=request.question,
        )
    )

    db.commit()

    memory_messages = get_memory(session_id)

    if not memory_messages:
        db_messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == current_user.id,
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        memory_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in db_messages
        ]

        set_memory(
            session_id=session_id,
            messages=memory_messages,
        )

    initial_state = {
        "user_id": current_user.id,
        "session_id": session_id,
        "question": request.question,
        "chat_history": memory_messages,
        "retrieval_query": request.question,
        "documents": [],
        "answer": "",
        "retry_count": 0,
        "documents_relevant": False,
        "grounded": False,
        "can_retry": True,
        "sources": [],
    }

    result = research_rag_graph.invoke(initial_state)

    db.add(
        ChatMessage(
            session_id=session_id,
            user_id=current_user.id,
            role="assistant",
            content=result["answer"],
        )
    )

    db.commit()

    add_message(
        session_id=session_id,
        role="user",
        content=request.question,
    )

    add_message(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
    )

    return {
        "session_id": session_id,
        "answer": result["answer"],
        "sources": result["sources"],
        "retry_count": result["retry_count"],
        "documents_relevant": result["documents_relevant"],
        "grounded": result["grounded"],
    }


@router.get(
    "/sessions",
    response_model=List[ChatSessionResponse],
)
def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

    return sessions


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
)
def get_chat_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return {
        "session": session,
        "messages": messages,
    }


@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id,
        )
        .delete()
    )

    db.delete(session)
    db.commit()

    return {
        "message": "Chat session deleted successfully",
    }