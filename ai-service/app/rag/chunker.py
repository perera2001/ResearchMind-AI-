from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

from app.config import settings


def create_semantic_chunks(
    pages: list[dict],
    document_id: int,
    user_id: int,
    file_name: str,
) -> list[dict]:
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )

    text_splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=90,
    )

    chunks = []

    for page in pages:
        page_chunks = text_splitter.create_documents(
            texts=[page["text"]],
            metadatas=[
                {
                    "user_id": user_id,
                    "document_id": document_id,
                    "file_name": file_name,
                    "page_number": page["page_number"],
                }
            ],
        )

        for chunk_index, chunk in enumerate(page_chunks):
            chunks.append(
                {
                    "id": f"user_{user_id}_doc_{document_id}_page_{page['page_number']}_chunk_{chunk_index}",
                    "content": chunk.page_content,
                    "metadata": chunk.metadata,
                }
            )

    return chunks