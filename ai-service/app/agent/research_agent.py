import json

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI

from app.agent.tools import search_research_papers
from app.config import settings


research_agent = create_agent(
    model=ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    ),
    tools=[search_research_papers],
    system_prompt="""
You are the ResearchMind AI research agent.

Rules:
- Answer only the current question.
- Use only evidence from the user's uploaded research papers.
- Use the supplied research context first.
- Call search_research_papers only when more research-paper context is needed.
- When calling the tool, always use the user_id supplied in the request.
- Never use outside knowledge for research-paper claims.
- If the available evidence is insufficient, say that you could not find enough evidence.
- Preserve the meaning of author names and other details exactly as supported by the evidence.
- For an authors question, list every author name exactly as written and exclude emails and affiliations.
- For a main-problem question, prioritize evidence from the abstract, introduction, problem statement, or motivation.
- Do not include a sources list in the answer because sources are returned separately by the API.
- Keep the answer short, clear, and meaningful.
""",
)


def run_research_agent(
    question: str,
    user_id: int,
    chat_history: list[dict],
    documents: list[dict],
) -> tuple[str, list[dict]]:
    chat_history_text = "\n".join(
        [
            f'{message["role"]}: {message["content"]}'
            for message in chat_history[-6:]
        ]
    )

    context = "\n\n".join(
        [
            (
                f'Source: {document["source"]}, '
                f'Page: {document["page_number"]}, '
                f'Document ID: {document["document_id"]}\n'
                f'{document["content"]}'
            )
            for document in documents[:5]
        ]
    )

    result = research_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
User ID for tool calls: {user_id}

Chat history is only for understanding follow-up questions:
{chat_history_text}

Current question:
{question}

Already retrieved research-paper context:
{context}
""",
                }
            ]
        }
    )

    tool_documents = []

    for message in result["messages"]:
        if not isinstance(message, ToolMessage):
            continue

        if message.name != search_research_papers.name:
            continue

        try:
            parsed_documents = json.loads(message.content)

        except (json.JSONDecodeError, TypeError):
            continue

        if isinstance(parsed_documents, list):
            tool_documents.extend(parsed_documents)

    answer = result["messages"][-1].content

    if not isinstance(answer, str):
        answer = str(answer)

    return answer.strip(), tool_documents
