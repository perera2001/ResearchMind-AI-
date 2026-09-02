import json

from langchain_openai import ChatOpenAI

from app.agent.schemas import (
    AuthorExtraction,
    GroundednessGrade,
    RelevanceGrade,
    RouteDecision,
)
from app.agent.research_agent import run_research_agent
from app.agent.tools import search_research_papers
from app.config import settings


llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0,
)


def is_author_question(question: str) -> bool:
    normalized_question = question.lower()

    return (
        "author" in normalized_question
        or "authors" in normalized_question
        or "who wrote" in normalized_question
        or "written by" in normalized_question
    )


def build_unique_sources(documents: list[dict]) -> list[dict]:
    sources = []
    seen_sources = set()

    for document in documents:
        key = (
            document["source"],
            document["page_number"],
            document["document_id"],
        )

        if key in seen_sources:
            continue

        seen_sources.add(key)
        sources.append(
            {
                "source": document["source"],
                "page_number": document["page_number"],
                "document_id": document["document_id"],
            }
        )

    return sources


def route_question_node(state: dict) -> dict:
    question = state["question"].lower()

    paper_words = [
        "paper",
        "research",
        "document",
        "pdf",
        "study",
        "article",
    ]

    vague_follow_up_words = [
        "that",
        "it",
        "above",
        "previous",
        "explain that",
        "explain this",
        "simplify",
        "simple words",
    ]

    if any(word in question for word in paper_words):
        return {
            "documents_relevant": True,
        }

    if state["chat_history"] and any(word in question for word in vague_follow_up_words):
        return {
            "documents_relevant": False,
        }

    structured_llm = llm.with_structured_output(
        RouteDecision,
    )

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
    chat_history_text = "\n".join(
        [
            f'{message["role"]}: {message["content"]}'
            for message in state["chat_history"][-6:]
        ]
    )

    response = llm.invoke(
        f"""
You are ResearchMind AI.

Answer the current message using the chat history if needed.

Rules:
- If the user says "that", "this", or "it", use the previous assistant answer.
- Do not ask what they mean if the chat history clearly shows it.
- Keep the answer short and simple.

Chat history:
{chat_history_text}

Current message:
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
    if is_author_question(state["question"]):
        from app.rag.pdf_loader import load_single_pdf_page
        from app.rag.vector_store import vector_store

        document_metadatas = state.get("uploaded_documents", [])

        if not document_metadatas:
            document_metadatas = vector_store.get_user_document_metadata(
                user_id=state["user_id"],
            )

        documents = []

        for metadata in document_metadatas:
            file_path = metadata.get("file_path")

            if not file_path:
                continue

            try:
                page_text = load_single_pdf_page(
                    file_path=file_path,
                    page_number=1,
                )
            except (FileNotFoundError, RuntimeError, ValueError):
                continue

            if not page_text.strip():
                continue

            documents.append(
                {
                    "content": page_text,
                    "source": metadata.get(
                        "source",
                        metadata.get("file_name"),
                    ),
                    "page_number": 1,
                    "document_id": metadata["document_id"],
                    "score": 1.0,
                }
            )

    else:
        tool_result = search_research_papers.invoke(
            {
                "query": state["retrieval_query"],
                "user_id": state["user_id"],
            }
        )

        documents = json.loads(tool_result)

    unique_documents = []
    seen_documents = set()

    for document in documents:
        key = (
            document["source"],
            document["page_number"],
            document["document_id"],
            document["content"][:100],
        )

        if key in seen_documents:
            continue

        seen_documents.add(key)
        unique_documents.append(document)

    return {
        "documents": unique_documents,
        "sources": build_unique_sources(unique_documents),
    }
def grade_documents_node(state: dict) -> dict:
    if not state["documents"]:
        return {
            "documents_relevant": False,
        }

    if is_author_question(state["question"]):
        return {
            "documents_relevant": True,
        }

    context = "\n\n".join(
        [
            document["content"]
            for document in state["documents"][:5]
        ]
    )

    structured_llm = llm.with_structured_output(
        RelevanceGrade,
    )

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
    if is_author_question(state["question"]):
        raw_first_pages = "\n\n".join(
            [
                (
                    f'Source: {document["source"]}\n'
                    f'{document["content"]}'
                )
                for document in state["documents"]
            ]
        )

        structured_llm = llm.with_structured_output(
            AuthorExtraction,
        )

        result = structured_llm.invoke(
            f"""
Extract every author name exactly as written in the raw first page text.

Strict rules:
- Use only the raw first page text below.
- Find the author block between the paper title and the Abstract or Keywords section.
- Include every author in that block and preserve their original order.
- Preserve every initial exactly. Never shorten or remove initials.
- Join parts of the same author name when they continue across line breaks.
- Do not guess or correct names.
- Do not include email addresses.
- Do not include affiliations, departments, universities, degrees, or job titles.
- Do not use chat history or any previous answer.
- Return the authors only in the structured authors list.

Raw first page text:
{raw_first_pages}
"""
        )

        if not result.authors:
            return {
                "answer": "I could not find enough evidence in your uploaded research papers to identify the authors.",
                "documents": state["documents"],
                "sources": [],
            }

        return {
            "answer": f'The authors are: {", ".join(result.authors)}.',
            "documents": state["documents"],
            "sources": build_unique_sources(state["documents"]),
        }

    answer, tool_documents = run_research_agent(
        question=state["question"],
        user_id=state["user_id"],
        chat_history=state["chat_history"],
        documents=state["documents"],
    )

    documents = []
    seen_documents = set()

    for document in state["documents"] + tool_documents:
        key = (
            document["source"],
            document["page_number"],
            document["document_id"],
            document["content"][:100],
        )

        if key in seen_documents:
            continue

        seen_documents.add(key)
        documents.append(document)

    return {
        "answer": answer,
        "documents": documents,
        "sources": build_unique_sources(documents),
    }
def check_groundedness_node(state: dict) -> dict:
    if is_author_question(state["question"]):
        if (
            state["documents"]
            and state["answer"].startswith("The authors are:")
        ):
            return {
                "grounded": True,
            }

        return {
            "grounded": False,
        }

    if not state["documents"]:
        return {
            "grounded": False,
        }

    if (
        "I could not find enough evidence"
        in state["answer"]
    ):
        return {
            "grounded": False,
        }

    context = "\n\n".join(
        [
            document["content"]
            for document in state["documents"][:5]
        ]
    )

    structured_llm = llm.with_structured_output(
        GroundednessGrade,
    )

    result = structured_llm.invoke(
        f"""
Check whether the answer is supported by the research paper context.

Important rules:
- Mark grounded=true if the main meaning of the answer is supported by the context.
- The answer does not need to copy the exact same words.
- Minor wording differences are okay.
- Do not be too strict.
- Mark grounded=false only if the answer adds facts that are not in the context.

Question:
{state["question"]}

Research paper context:
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
         "sources": [],
    }
