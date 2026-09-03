from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class RetrievedDocument(BaseModel):
    content: str
    source: str
    page_number: int
    document_id: int
    score: float = 0.0