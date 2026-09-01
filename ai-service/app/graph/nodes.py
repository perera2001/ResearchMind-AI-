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
    question = state["question"].lower()

    if (
        "author" in question
        or "authors" in question
        or "who wrote" in question
        or "written by" in question
    ):
        from app.database import SessionLocal
        from app.documents.models import Document
        from app.rag.pdf_loader import load_single_pdf_page

        db = SessionLocal()

        try:
            user_documents = (
                db.query(Document)
                .filter(Document.user_id == state["user_id"])
                .all()
            )

            documents = []

            for user_document in user_documents:
                page_text = load_single_pdf_page(
                    file_path=user_document.file_path,
                    page_number=1,
                )

                if page_text.strip():
                    documents.append(
                        {
                            "content": page_text,
                            "source": user_document.file_name,
                            "page_number": 1,
                            "document_id": user_document.id,
                            "score": 1.0,
                        }
                    )

        finally:
            db.close()

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

    unique_sources = []
    seen_sources = set()

    for document in unique_documents:
        key = (
            document["source"],
            document["page_number"],
            document["document_id"],
        )

        if key in seen_sources:
            continue

        seen_sources.add(key)

        unique_sources.append(
            {
                "source": document["source"],
                "page_number": document["page_number"],
                "document_id": document["document_id"],
            }
        )

    return {
        "documents": unique_documents,
        "sources": unique_sources,
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
    question = state["question"].lower()

    context = "\n\n".join(
        [
            f'Source: {document["source"]}, Page: {document["page_number"]}\n{document["content"]}'
            for document in state["documents"][:5]
        ]
    )

    if (
        "author" in question
        or "authors" in question
        or "who wrote" in question
        or "written by" in question
    ):
        response = llm.invoke(
            f"""
You are ResearchMind AI.

The user is asking for the authors of the research paper.

Use only the raw first page text below.

Rules:
- Extract every author name exactly as written.
- Do not shorten initials.
- Do not include emails.
- Do not include department names.
- Do not include university names.
- Do not answer a previous question.
- Return only this format:
The authors are: author 1, author 2, author 3.

Question:
{state["question"]}

Raw first page text:
{context}
"""
        )

        return {
            "answer": response.content,
        }

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

Rules:
- Answer only the current question.
- Do not answer previous questions from chat history.
- Do not include authors unless the user asks for authors.
- Identify the central research problem only if the user asks about the problem.
- Prefer problem statements, abstract, introduction, and motivation evidence.
- Start with a complete sentence.
- Give a clear direct answer.
- If the context contains multiple possible answers, mention the most important one first.
- If the context does not contain enough evidence, say you cannot find enough evidence.
- Keep the answer short but meaningful.

Chat history is only for understanding follow-up questions:
{chat_history_text}

Current question:
{state["question"]}

Research paper context:
{context}
"""
    )

    return {
        "answer": response.content,
    }
def check_groundedness_node(state: dict) -> dict:
    question = state["question"].lower()

    if (
        "author" in question
        or "authors" in question
        or "who wrote" in question
        or "written by" in question
    ):
        if state["documents"] and state["answer"]:
            return {
                "grounded": True,
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