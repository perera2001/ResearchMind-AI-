from pydantic import BaseModel, Field


class DocumentProcessResponse(BaseModel):
    status: str
    page_count: int
    chunk_count: int


class InternalChatRequest(BaseModel):
    user_id: int
    question: str
    chat_history: list[dict] = Field(default_factory=list)
    documents: list[dict] = Field(default_factory=list)


class InternalChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    retry_count: int
    documents_relevant: bool
    grounded: bool
