from typing import TypedDict


class ResearchRAGState(TypedDict):
    user_id: int
    session_id: int
    question: str
    chat_history: list[dict]
    uploaded_documents: list[dict]
    retrieval_query: str
    documents: list[dict] 
    answer: str
    retry_count: int
    documents_relevant: bool
    grounded: bool
    can_retry: bool
    sources: list[dict]
