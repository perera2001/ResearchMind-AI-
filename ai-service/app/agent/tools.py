import json

from langchain.tools import tool

from app.rag.compressor import compress_documents
from app.rag.hybrid_retriever import hybrid_search
from app.rag.multi_query import generate_search_queries


@tool
def search_research_papers(query: str, user_id: int) -> str:
    """
    Search uploaded research papers using multi-query hybrid retrieval.
    """

    queries = generate_search_queries(query)

    all_results = {}

    for search_query in queries:
        results = hybrid_search(
            query=search_query,
            user_id=user_id,
        )

        for result in results:
            key = (
                result["metadata"]["document_id"],
                result["metadata"]["page_number"],
                result["content"][:100],
            )

            if key not in all_results:
                all_results[key] = result

    documents = list(all_results.values())

    documents.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    compressed_documents = compress_documents(
        question=query,
        documents=documents,
    )

    response = []

    for document in compressed_documents:
        metadata = document["metadata"]

        response.append(
            {
                "content": document["content"],
                "source": metadata["file_name"],
                "page_number": metadata["page_number"],
                "document_id": metadata["document_id"],
                "score": document["score"],
            }
        )

    return json.dumps(response)