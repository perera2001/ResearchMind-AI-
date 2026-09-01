from pydantic import BaseModel
from langchain_openai import ChatOpenAI

from app.config import settings


class SelfQueryDecision(BaseModel):
    search_query: str
    document_name: str | None = None
    page_number: int | None = None


llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0,
)


def create_self_query(question: str) -> SelfQueryDecision:
    structured_llm = llm.with_structured_output(
        SelfQueryDecision,
    )

    prompt = f"""
Convert the user question into a search query and optional metadata filters.

If user mentions a specific PDF name, set document_name.
If user mentions a specific page, set page_number.

Question:
{question}
"""

    return structured_llm.invoke(prompt)