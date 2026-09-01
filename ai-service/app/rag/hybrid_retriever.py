from app.config import settings
from app.rag.bm25_store import bm25_store
from app.rag.vector_store import vector_store


def hybrid_search(
    query: str,
    user_id: int,
) -> list[dict]:
    vector_results = vector_store.search(
        query=query,
        user_id=user_id,
        top_k=settings.retrieval_top_k,
    )

    bm25_results = bm25_store.search(
        query=query,
        user_id=user_id,
        top_k=settings.retrieval_top_k,
    )

    merged = {}

    for result in vector_results:
        key = (
            result["metadata"]["document_id"],
            result["metadata"]["page_number"],
            result["content"][:80],
        )

        merged[key] = {
            **result,
            "score": result["score"] * 0.6,
        }

    for result in bm25_results:
        key = (
            result["metadata"]["document_id"],
            result["metadata"]["page_number"],
            result["content"][:80],
        )

        if key in merged:
            merged[key]["score"] += result["score"] * 0.4
        else:
            merged[key] = {
                **result,
                "score": result["score"] * 0.4,
            }

    results = list(merged.values())

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[: settings.retrieval_top_k]