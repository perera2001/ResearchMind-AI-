from langchain_openai import ChatOpenAI

from app.config import settings


llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0,
)


def compress_documents(
    question: str,
    documents: list[dict],
) -> list[dict]:
    compressed_documents = []

    for document in documents[:6]:
        prompt = f"""
Keep only the sentences from this research paper chunk
that are useful for answering the question.

Question:
{question}

Chunk:
{document["content"]}

Return only the useful text.
If nothing is useful, return EMPTY.
"""

        response = llm.invoke(prompt)
        compressed_text = response.content.strip()

        if compressed_text and compressed_text.upper() != "EMPTY":
            compressed_documents.append(
                {
                    **document,
                    "content": compressed_text,
                }
            )

    return compressed_documents