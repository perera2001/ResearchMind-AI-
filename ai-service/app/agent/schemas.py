from pydantic import BaseModel


class RouteDecision(BaseModel):
    needs_retrieval: bool
    reason: str


class RelevanceGrade(BaseModel):
    documents_relevant: bool
    reason: str


class GroundednessGrade(BaseModel):
    grounded: bool
    reason: str