from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import settings


def create_semantic_chunks(
    pages: list[Document],
) -> list[Document]:
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
    chunk_index = 0

    for page in pages:
        if not page.page_content.strip():
            continue

        page_chunks = text_splitter.split_documents(
            [page],
        )

        for chunk in page_chunks:
            chunks.append(
                Document(
                    page_content=chunk.page_content,
                    metadata={
                        **chunk.metadata,
                        "chunk_index": chunk_index,
                    },
                )
            )

            chunk_index += 1

    return chunks
