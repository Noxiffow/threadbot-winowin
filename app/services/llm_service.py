from app.core.config import groq_client
from app.core.prompts import SYSTEM_PROMPT
from app.services.session import get_or_create_session, append_message

def chat_with_bot(session_id: str, user_message: str) -> str:
    history = get_or_create_session(session_id)
    append_message(session_id, "user", user_message)

    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history
    )

    reply = resp.choices[0].message.content
    append_message(session_id, "assistant", reply)
    return reply
