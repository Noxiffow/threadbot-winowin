from fastapi import APIRouter, HTTPException
from app.schemas.chat_schemas import ChatIn, ChatOut
from app.services.llm_service import chat_with_bot
from app.services.orders import get_pedido
from app.models.db_models import Alerta, Pedido
from app.services.database import SessionLocal

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

@router.get("/alerts/pending")
def alertas_pendientes(api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")

    db = SessionLocal()
    try:
        alertas = db.query(Alerta).filter(Alerta.enviada == False).all()
        return {
            "total": len(alertas),
            "alertas": [
                {
                    "id": a.id,
                    "tipo": a.tipo,
                    "producto_id": a.producto_id,
                    "mensaje": a.mensaje,
                    "fecha": str(a.fecha)
                }
                for a in alertas
            ]
        }
    finally:
        db.close()

@router.post("/alerts/{alerta_id}/mark-sent")
def marcar_alerta_enviada(alerta_id: int, api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")

    db = SessionLocal()
    try:
        alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()

        if not alerta:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")

        alerta.enviada = True
        db.commit()
        db.refresh(alerta)

        return {
            "ok": True,
            "id": alerta.id,
            "enviada": alerta.enviada
        }
    finally:
        db.close()

@router.post("/orders/{pedido_id}/confirm")
def confirmar_pedido(pedido_id: int, api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")
    db = SessionLocal()
    try:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        pedido.estado = "confirmado"
        db.commit()
        db.refresh(pedido)

        # Notificar a n8n
        try:
            import httpx
            webhook_url = "http://localhost:5678/webhook/order-confirmed"
            payload = {
                "pedido_id": pedido.id,
                "estado": pedido.estado,
                "nombre_cliente": pedido.nombre_cliente,
                "email_cliente": pedido.email_cliente,
                "direccion": pedido.direccion,
                "total": pedido.total_cents / 100
            }
            httpx.post(webhook_url, json=payload, timeout=5)
        except Exception:
            pass

        return {
            "ok": True,
            "pedido_id": pedido.id,
            "estado": pedido.estado,
            "nombre_cliente": pedido.nombre_cliente,
            "email_cliente": pedido.email_cliente,
            "direccion": pedido.direccion,
            "total": pedido.total_cents / 100
        }
    finally:
        db.close()