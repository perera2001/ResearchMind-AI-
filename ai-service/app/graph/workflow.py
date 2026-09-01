from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.graph.nodes import (
    check_groundedness_node,
    direct_answer_node,
    fallback_answer_node,
    generate_answer_node,
    generate_query_node,
    grade_documents_node,
    retrieve_documents_node,
    rewrite_query_node,
    route_question_node,
)
from app.graph.state import ResearchRAGState


def route_after_question(state: ResearchRAGState) -> str:
    if state["documents_relevant"]:
        return "generate_query"

    return "direct_answer"


def route_after_document_grade(state: ResearchRAGState) -> str:
    if state["documents_relevant"]:
        return "generate_answer"

    if state["retry_count"] < settings.max_retry_count:
        return "rewrite_query"

    return "fallback_answer"


def route_after_groundedness(state: ResearchRAGState) -> str:
    if state["grounded"]:
        return END

    if state["retry_count"] < settings.max_retry_count:
        return "rewrite_query"

    return "fallback_answer"


workflow = StateGraph(ResearchRAGState)

workflow.add_node("route_question", route_question_node)
workflow.add_node("direct_answer", direct_answer_node)
workflow.add_node("generate_query", generate_query_node)
workflow.add_node("retrieve_documents", retrieve_documents_node)
workflow.add_node("grade_documents", grade_documents_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("check_groundedness", check_groundedness_node)
workflow.add_node("rewrite_query", rewrite_query_node)
workflow.add_node("fallback_answer", fallback_answer_node)

workflow.add_edge(START, "route_question")

workflow.add_conditional_edges(
    "route_question",
    route_after_question,
)

workflow.add_edge("direct_answer", END)
workflow.add_edge("generate_query", "retrieve_documents")
workflow.add_edge("retrieve_documents", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    route_after_document_grade,
)

workflow.add_edge("generate_answer", "check_groundedness")

workflow.add_conditional_edges(
    "check_groundedness",
    route_after_groundedness,
)

workflow.add_edge("rewrite_query", "retrieve_documents")
workflow.add_edge("fallback_answer", END)

research_rag_graph = workflow.compile()