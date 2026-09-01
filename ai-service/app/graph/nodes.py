import json

from langchain_openai import ChatOpenAI

from app.agent.schemas import (
    GroundednessGrade,
    RelevanceGrade,
    RouteDecision,
)
from app.agent.tools import search_research_papers
from app.config import settings


llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0,
)


def route_question_node(state: dict) -> dict:
    structured_llm = llm.with_structured_output(RouteDecision)

    result = structured_llm.invoke(
        f"""
Decide if the user question needs information from uploaded research papers.

Question:
{state["question"]}
"""
    )

    return {
        "documents_relevant": result.needs_retrieval,
    }


def direct_answer_node(state: dict) -> dict:
    response = llm.invoke(
        f"""
Answer this message shortly.

Message:
{state["question"]}
"""
    )

    return {
        "answer": response.content,
        "grounded": True,
        "sources": [],
    }


def generate_query_node(state: dict) -> dict:
    chat_history_text = "\n".join(
        [
            f'{message["role"]}: {message["content"]}'
            for message in state["chat_history"][-6:]
        ]
    )

    response = llm.invoke(
        f"""
Create one clear search query for research paper retrieval.

Chat history:
{chat_history_text}

User question:
{state["question"]}

Return only the search query.
"""
    )

    return {
        "retrieval_query": response.content.strip(),
    }


def retrieve_documents_node(state: dict) -> dict:
    tool_result = search_research_papers.invoke(
        {
            "query": state["retrieval_query"],
            "user_id": state["user_id"],
        }
    )

    documents = json.loads(tool_result)

    return {
        "documents": documents,
        "sources": [
            {
                "source": document["source"],
                "page_number": document["page_number"],
                "document_id": document["document_id"],
            }
            for document in documents
        ],
    }


def grade_documents_node(state: dict) -> dict:
    if not state["documents"]:
        return {
            "documents_relevant": False,
        }

    context = "\n\n".join(
        [
            document["content"]
            for document in state["documents"][:5]
        ]
    )

    structured_llm = llm.with_structured_output(RelevanceGrade)

    result = structured_llm.invoke(
        f"""
Check if the documents are relevant to the question.

Question:
{state["question"]}

Documents:
{context}
"""
    )

    return {
        "documents_relevant": result.documents_relevant,
    }


def generate_answer_node(state: dict) -> dict:
    context = "\n\n".join(
        [
            f'Source: {document["source"]}, Page: {document["page_number"]}\n{document["content"]}'
            for document in state["documents"][:5]
        ]
    )

    chat_history_text = "\n".join(
        [
            f'{message["role"]}: {message["content"]}'
            for message in state["chat_history"][-6:]
        ]
    )

    response = llm.invoke(
        f"""
You are ResearchMind AI.

Answer using only the provided research paper context.
If the context does not contain the answer, say you cannot find enough evidence.

Chat history:
{chat_history_text}

Question:
{state["question"]}

Context:
{context}
"""
    )

    return {
        "answer": response.content,
    }


def check_groundedness_node(state: dict) -> dict:
    context = "\n\n".join(
        [
            document["content"]
            for document in state["documents"][:5]
        ]
    )

    structured_llm = llm.with_structured_output(GroundednessGrade)

    result = structured_llm.invoke(
        f"""
Check if the answer is grounded in the context.

Question:
{state["question"]}

Context:
{context}

Answer:
{state["answer"]}
"""
    )

    return {
        "grounded": result.grounded,
    }


def rewrite_query_node(state: dict) -> dict:
    response = llm.invoke(
        f"""
Rewrite the search query to find better research paper evidence.

Original question:
{state["question"]}

Current query:
{state["retrieval_query"]}

Return only improved query.
"""
    )

    retry_count = state["retry_count"] + 1

    return {
        "retrieval_query": response.content.strip(),
        "retry_count": retry_count,
        "can_retry": retry_count < settings.max_retry_count,
    }


def fallback_answer_node(state: dict) -> dict:
    return {
        "answer": "I could not find enough evidence in your uploaded research papers to answer this confidently.",
        "grounded": False,
    }