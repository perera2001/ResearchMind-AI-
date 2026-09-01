from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: int | None = None


class ChatResponse(BaseModel):
    session_id: int
    answer: str
    sources: list[dict]
    retry_count: int
    documents_relevant: bool
    grounded: bool


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionDetailResponse(BaseModel):
    session: ChatSessionResponse
    messages: list[ChatMessageResponse]