import chromadb
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import settings


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
        )

        self.collection = self.client.get_or_create_collection(
            name="researchmind_chunks",
        )

        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )

    def add_chunks(self, chunks: list[Document]):
        if not chunks:
            return

        texts = [
            chunk.page_content
            for chunk in chunks
        ]

        metadatas = [
            chunk.metadata
            for chunk in chunks
        ]

        ids = [
            (
                f'user_{chunk.metadata["user_id"]}'
                f'_doc_{chunk.metadata["document_id"]}'
                f'_page_{chunk.metadata["page_number"]}'
                f'_chunk_{chunk.metadata["chunk_index"]}'
            )
            for chunk in chunks
        ]

        embeddings = self.embeddings.embed_documents(
            texts,
        )

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def search(
        self,
        query: str,
        user_id: int,
        top_k: int,
    ) -> list[dict]:
        query_embedding = self.embeddings.embed_query(
            query,
        )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={
                "user_id": user_id,
            },
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        retrieved = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):
            retrieved.append(
                {
                    "content": document,
                    "metadata": metadata,
                    "score": float(1 - distance),
                }
            )

        return retrieved

    def get_user_page_chunks(
        self,
        user_id: int,
        page_number: int = 1,
    ) -> list[dict]:
        results = self.collection.get(
            where={
                "$and": [
                    {"user_id": user_id},
                    {"page_number": page_number},
                ]
            }
        )

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        chunks = []

        for document, metadata in zip(
            documents,
            metadatas,
        ):
            chunks.append(
                {
                    "content": document,
                    "metadata": metadata,
                    "score": 1.0,
                }
            )

        return chunks

    def get_user_document_metadata(
        self,
        user_id: int,
    ) -> list[dict]:
        results = self.collection.get(
            where={
                "user_id": user_id,
            },
            include=["metadatas"],
        )

        unique_documents = []
        seen_document_ids = set()

        for metadata in results.get("metadatas", []):
            if not metadata.get("file_path"):
                continue

            document_id = metadata["document_id"]

            if document_id in seen_document_ids:
                continue

            seen_document_ids.add(document_id)
            unique_documents.append(metadata)

        return unique_documents

    def delete_document_chunks(
        self,
        user_id: int,
        document_id: int,
    ):
        self.collection.delete(
            where={
                "$and": [
                    {"user_id": user_id},
                    {"document_id": document_id},
                ]
            }
        )


vector_store = VectorStore()
