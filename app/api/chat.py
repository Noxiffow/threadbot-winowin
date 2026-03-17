from fastapi import APIRouter, HTTPException
from app.schemas.chat_schemas import ChatIn, ChatOut
from app.services.llm_service import chat_with_bot
from app.services.orders import get_pedido

router = APIRouter()

@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    if not body.session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="El campo session_id no puede estar vacío"
        )
    if not body.message.strip():
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío"
        )
    reply = chat_with_bot(body.session_id, body.message)
    return ChatOut(reply=reply)

@router.get("/orders/{pedido_id}")
def consultar_pedido(pedido_id: int):
    pedido = get_pedido(pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )
    return {
        "id": pedido.id,
        "estado": pedido.estado,
        "nombre_cliente": pedido.nombre_cliente,
        "email_cliente": pedido.email_cliente,
        "total": pedido.total_cents / 100
    }
