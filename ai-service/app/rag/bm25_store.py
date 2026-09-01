from rank_bm25 import BM25Okapi


class BM25Store:
    def __init__(self):
        self.documents = []
        self.tokenized_documents = []
        self.bm25 = None

    def add_chunks(self, chunks: list[dict]):
        for chunk in chunks:
            self.documents.append(
                {
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                }
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
                document["metadata"]["user_id"] == user_id
                and document["metadata"]["document_id"] == document_id
            )
        ]

        self._rebuild_index()

    def _rebuild_index(self):
        self.tokenized_documents = [
            document["content"].lower().split()
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
    ) -> list[dict]:
        if self.bm25 is None:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        scored_documents = []

        for index, score in enumerate(scores):
            document = self.documents[index]

            if document["metadata"]["user_id"] != user_id:
                continue

            scored_documents.append(
                {
                    "content": document["content"],
                    "metadata": document["metadata"],
                    "score": float(score),
                }
            )

        scored_documents.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return scored_documents[:top_k]


bm25_store = BM25Store()