from fastapi import HTTPException
from app.core.config import groq_client
from app.core.prompts import get_system_prompt
from app.services.session import get_or_create_session, append_message
from app.services.orders import crear_pedido
import re
import httpx

def extraer_datos_pedido(historial: list) -> dict | None:
    """
    Analiza el historial buscando los 4 datos del pedido:
    producto, talla, nombre, dirección, email
    Devuelve None si no están todos.
    """
    texto = " ".join([m["content"] for m in historial]).lower()

    productos = ["camiseta blanca", "camiseta negra", "sudadera",
                 "vaqueros", "chaqueta bomber", "shorts cargo"]
    tallas = ["s", "m", "l", "xl", "28", "30", "32", "34"]

    tiene_producto = any(p in texto for p in productos)
    tiene_talla = any(f"talla {t}" in texto or f" {t} " in texto for t in tallas)
    tiene_email = bool(re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', texto))
    tiene_direccion = any(p in texto for p in ["calle", "avenida", "plaza", "ctra", "camino"])
    tiene_nombre = len([m for m in historial if m["role"] == "user"]) >= 4

    if all([tiene_producto, tiene_talla, tiene_email, tiene_direccion, tiene_nombre]):
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', texto)
        return {
            "tiene_datos": True,
            "email": email_match.group(0) if email_match else ""
        }
    return None

def chat_with_bot(session_id: str, user_message: str) -> str:
    try:
        history = get_or_create_session(session_id)
        append_message(session_id, "user", user_message)

        # Detectar confirmación de pedido
        if user_message.strip().upper() == "CONFIRMAR":
            datos = extraer_datos_pedido(history)
            if datos and datos["tiene_datos"]:
                try:
                    pedido = crear_pedido(
                        session_id=session_id,
                        nombre_cliente="Cliente ThreadCo",
                        email_cliente=datos["email"],
                        direccion="Ver conversación",
                        items=[{"nombre_producto": "Producto", "talla": "", "cantidad": 1}]
                    )

                    # Notificar a n8n
                    try:
                        httpx.post(
                            "http://localhost:5678/webhook/order-confirmed",
                            json={
                                "pedido_id": pedido.id,
                                "estado": "confirmado",
                                "nombre_cliente": pedido.nombre_cliente,
                                "email_cliente": pedido.email_cliente,
                                "direccion": pedido.direccion,
                                "total": pedido.total_cents / 100
                            },
                            timeout=5
                        )
                    except Exception:
                        pass

                    reply = f"✅ ¡Pedido confirmado! Tu número de pedido es el #{pedido.id}. Recibirás un email de confirmación en breve. ¡Gracias por comprar en ThreadCo!"
                    append_message(session_id, "assistant", reply)
                    return reply
                except Exception:
                    pass

        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": get_system_prompt()}] + history
        )
        reply = resp.choices[0].message.content
        append_message(session_id, "assistant", reply)
        return reply

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="El servicio de IA no está disponible. Inténtalo de nuevo."
        )
