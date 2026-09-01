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

        self.tokenized_documents = [
            document["content"].lower().split()
            for document in self.documents
        ]

        if self.tokenized_documents:
            self.bm25 = BM25Okapi(
                self.tokenized_documents,
            )

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