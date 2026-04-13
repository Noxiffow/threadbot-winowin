from fastapi import APIRouter, HTTPException, Request
from app.schemas.chat_schemas import ChatIn, ChatOut
from app.services.llm_service import chat_with_bot
from app.services.orders import get_pedido
from app.models.db_models import Alerta, Configuracion, Pedido, Producto, SolicitudFactura
from app.services.database import SessionLocal
from slowapi import Limiter
from slowapi.util import get_remote_address
import httpx

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/chat", response_model=ChatOut)
@limiter.limit("20/minute")
async def chat(request: Request, chat_in: ChatIn):
    if not chat_in.session_id.strip():
        raise HTTPException(
            status_code=400,
            detail="El campo session_id no puede estar vacío"
        )
    if not chat_in.message.strip():
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío"
        )
    if len(chat_in.message) > 500:
        raise HTTPException(status_code=400, detail="Mensaje demasiado largo")
    reply = chat_with_bot(chat_in.session_id, chat_in.message)
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

@router.post("/invoices/request")
def solicitar_factura(session_id: str, pedido_id: int, api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")
    db = SessionLocal()
    try:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        solicitud = SolicitudFactura(
            session_id=session_id,
            email_cliente=pedido.email_cliente,
            pedido_id=pedido_id,
            procesada=False
        )
        db.add(solicitud)
        db.commit()
        try:
            webhook_url = "https://n8n-production-6d70.up.railway.app/webhook-test/invoice-request"
            payload = {
                "pedido_id": pedido.id,
                "nombre_cliente": pedido.nombre_cliente,
                "email_cliente": pedido.email_cliente,
                "total": pedido.total_cents / 100
            }
            httpx.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error webhook n8n: {e}")
            pass
        return {"ok": True, "mensaje": "Solicitud de factura registrada correctamente"}
    finally:
        db.close()

@router.post("/orders/{pedido_id}/status")
def actualizar_estado_pedido(pedido_id: int, estado: str, api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")
    estados_validos = ["pendiente", "confirmado", "enviado", "entregado", "cancelado"]
    if estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado no válido. Opciones: {estados_validos}")
    db = SessionLocal()
    try:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        pedido.estado = estado
        db.commit()
        db.refresh(pedido)
        mensajes = {
            "confirmado": "Tu pedido ha sido confirmado y está siendo preparado.",
            "enviado": "Tu pedido está en camino. Recibirás tu entrega en los próximos días.",
            "entregado": "Tu pedido ha sido entregado. ¡Esperamos que lo disfrutes!",
            "cancelado": "Tu pedido ha sido cancelado. Si tienes dudas, contáctanos.",
            "pendiente": "Tu pedido está pendiente de confirmación."
        }
        try:
            webhook_url = "https://n8n-production-6d70.up.railway.app/webhook-test/order-status"
            payload = {
                "pedido_id": pedido.id,
                "nombre_cliente": pedido.nombre_cliente,
                "email_cliente": pedido.email_cliente,
                "estado": estado,
                "mensaje": mensajes.get(estado, "Estado actualizado.")
            }
            httpx.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error webhook n8n: {e}")
            pass
        return {"ok": True, "pedido_id": pedido.id, "estado": pedido.estado}
    finally:
        db.close()

@router.get("/products")
def listar_productos():
    db = SessionLocal()
    try:
        productos = db.query(Producto).filter(
            Producto.activo == True
        ).all()
        return [
            {
                "id": p.id,
                "nombre": p.nombre,
                "precio": p.precio_cents / 100,
                "stock": p.stock,
                "tallas": p.tallas,
                "categoria": p.categoria
            }
            for p in productos
        ]
    finally:
        db.close()

@router.post("/products/{producto_id}/stock")
def actualizar_stock(producto_id: int, stock: int, api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")
    db = SessionLocal()
    try:
        producto = db.query(Producto).filter(Producto.id == producto_id).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if stock < 0:
            raise HTTPException(status_code=400, detail="El stock no puede ser negativo")
        producto.stock = stock
        db.commit()
        return {"ok": True, "producto_id": producto_id, "stock": stock}
    finally:
        db.close()

@router.get("/orders-admin")
def listar_pedidos_admin(api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")
    db = SessionLocal()
    try:
        pedidos = db.query(Pedido).order_by(Pedido.id.desc()).limit(50).all()
        return [
            {
                "id": p.id,
                "nombre_cliente": p.nombre_cliente,
                "email_cliente": p.email_cliente,
                "estado": p.estado,
                "total": p.total_cents / 100,
                "fecha": str(p.fecha_creacion)
            }
            for p in pedidos
        ]
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
            webhook_url = "https://n8n-production-6d70.up.railway.app/webhook/order-confirmed"
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

@router.get("/config")
def obtener_config(api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")
    db = SessionLocal()
    try:
        configs = db.query(Configuracion).all()
        return {c.clave: {"valor": c.valor, "descripcion": c.descripcion} for c in configs}
    finally:
        db.close()

@router.post("/config/{clave}")
def actualizar_config(clave: str, valor: str, api_key: str = ""):
    if api_key != "threadbot-internal-key":
        raise HTTPException(status_code=401, detail="No autorizado")
    db = SessionLocal()
    try:
        config = db.query(Configuracion).filter(Configuracion.clave == clave).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        config.valor = valor
        db.commit()
        return {"ok": True, "clave": clave, "valor": valor}
    finally:
        db.close()