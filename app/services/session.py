sessions: dict[str, list] = {}

def get_or_create_session(session_id: str) -> list:
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]

def append_message(session_id: str, role: str, content: str):
    sessions[session_id].append({"role": role, "content": content})
