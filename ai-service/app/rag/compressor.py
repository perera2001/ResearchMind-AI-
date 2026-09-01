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
Extract the useful evidence from this research paper chunk.

Rules:
- Keep complete sentences only.
- Do not start from the middle of a sentence.
- Do not rewrite as an answer.
- Only keep evidence useful for the question.
- If nothing is useful, return EMPTY.

Question:
{question}

Chunk:
{document["content"]}
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