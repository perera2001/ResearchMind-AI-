conversation_memory = {}


def get_memory(session_id: int) -> list[dict]:
    return conversation_memory.get(
        session_id,
        [],
    )


def add_message(
    session_id: int,
    role: str,
    content: str,
):
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []

    conversation_memory[session_id].append(
        {
            "role": role,
            "content": content,
        }
    )


def set_memory(
    session_id: int,
    messages: list[dict],
):
    conversation_memory[session_id] = messages