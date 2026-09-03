from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


class BM25Store:
    def __init__(self):
        self.documents = []
        self.tokenized_documents = []
        self.bm25 = None

    def add_chunks(self, chunks: list[Document]):
        for chunk in chunks:
            self.documents.append(
                Document(
                    page_content=chunk.page_content,
                    metadata=dict(chunk.metadata),
                )
            )

        self._rebuild_index()

    def delete_document_chunks(
        self,
        user_id: int,
        document_id: int,
    ):
        self.documents = [
            document
            for document in self.documents
            if not (
                document.metadata["user_id"] == user_id
                and document.metadata["document_id"] == document_id
            )
        ]

        self._rebuild_index()

    def _rebuild_index(self):
        self.tokenized_documents = [
            document.page_content.lower().split()
            for document in self.documents
        ]

        if self.tokenized_documents:
            self.bm25 = BM25Okapi(
                self.tokenized_documents,
            )
        else:
            self.bm25 = None

    def search(
        self,
        query: str,
        user_id: int,
        top_k: int,
        document_ids: list[int] | None = None,
    ) -> list[dict]:
        if self.bm25 is None:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        scored_documents = []

        for index, score in enumerate(scores):
            document = self.documents[index]

            if document.metadata["user_id"] != user_id:
                continue

            if (
                document_ids
                and document.metadata["document_id"] not in document_ids
            ):
                continue

            scored_documents.append(
                {
                    "content": document.page_content,
                    "metadata": document.metadata,
                    "score": float(score),
                }
            )

        scored_documents.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return scored_documents[:top_k]


bm25_store = BM25Store()
