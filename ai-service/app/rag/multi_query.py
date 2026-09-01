from langchain_openai import ChatOpenAI

from app.config import settings


llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0,
)


def generate_search_queries(question: str) -> list[str]:
    prompt = f"""
Generate 3 different search queries for finding information
inside research paper chunks.

Original question:
{question}

Return only the queries.
One query per line.
"""

    response = llm.invoke(prompt)

    queries = [
        line.strip("- ").strip()
        for line in response.content.split("\n")
        if line.strip()
    ]

    queries.insert(
        0,
        question,
    )

    return queries[:4]