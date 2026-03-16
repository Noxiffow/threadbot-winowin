from fastapi import APIRouter
from app.schemas.chat_schemas import ChatIn, ChatOut
from app.services.llm_service import chat_with_bot

router = APIRouter()

@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    reply = chat_with_bot(body.session_id, body.message)
    return ChatOut(reply=reply)
