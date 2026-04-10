from fastapi import HTTPException
from app.core.config import groq_client
from app.core.prompts import get_system_prompt
from app.services.session import get_or_create_session, append_message
from app.services.orders import crear_pedido
import re
import httpx


def extraer_datos_pedido(historial: list) -> dict | None:
    texto = " ".join([m["content"] for m in historial])

    # Extraer email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', texto)
    if not email_match:
        return None

    # Extraer nombre
    nombre = "Cliente ThreadCo"
    nombre_patterns = [
        r'(?:me llamo|soy|mi nombre es|nombre[:\s]+)\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de|da|dos|del|las|los|van|von)?\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
        r'(?:me llamo|soy|mi nombre es|nombre[:\s]+)\s*([A-ZÁÉÍÓÚÑ][^\n,\.]{2,50})',
    ]
    for msg in historial:
        if msg["role"] == "user":
            txt = msg["content"].strip()
            for pattern in nombre_patterns:
                match = re.search(pattern, txt, re.IGNORECASE)
                if match:
                    nombre = match.group(1).strip()
                    break
            if nombre != "Cliente ThreadCo":
                break
            # Mensaje que es solo un nombre (2-5 palabras, primera capitalizada)
            palabras = txt.split()
            palabras_excluidas = ['cancelar', 'confirmar', 'factura', 'pedido',
                                   'quiero', 'necesito', 'gracias', 'hola',
                                   'adiós', 'por', 'favor', 'sí', 'no']
            if (2 <= len(palabras) <= 5 and
                palabras[0][0].isupper() and
                len(txt) < 60 and
                not any(p in txt.lower() for p in palabras_excluidas)):
                nombre = txt
                break

    # Extraer dirección
    direccion = "Ver conversación"
    # Buscar mensajes del usuario que parezcan direcciones
    for msg in historial:
        if msg["role"] == "user":
            txt = msg["content"].strip()
            if re.search(r'(?:calle|avenida|av\.|plaza|camino|carretera)', txt, re.IGNORECASE):
                if len(txt) < 150:
                    direccion = txt
                    break

    # Extraer producto y talla
    productos_map = {
        "camiseta blanca": ("Camiseta básica blanca", 1500),
        "camiseta básica blanca": ("Camiseta básica blanca", 1500),
        "camiseta negra": ("Camiseta básica negra", 1500),
        "camiseta básica negra": ("Camiseta básica negra", 1500),
        "sudadera": ("Sudadera gris con capucha", 3500),
        "vaqueros": ("Vaqueros slim fit azul", 4500),
        "chaqueta bomber": ("Chaqueta bomber negra", 7500),
        "chaqueta": ("Chaqueta bomber negra", 7500),
        "shorts cargo": ("Shorts cargo beige", 3000),
        "shorts": ("Shorts cargo beige", 3000),
    }

    producto_nombre = "Producto"
    precio_cents = 0
    for key, (nombre_prod, precio) in productos_map.items():
        if key in texto.lower():
            producto_nombre = nombre_prod
            precio_cents = precio
            break

    talla = "M"
    for t in ["XL", "28", "30", "32", "34", "S", "M", "L"]:
        if f"talla {t}".lower() in texto.lower() or f" {t} " in texto:
            talla = t
            break

    return {
        "tiene_datos": True,
        "email": email_match.group(0),
        "nombre": nombre,
        "direccion": direccion,
        "producto": producto_nombre,
        "talla": talla,
        "precio_cents": precio_cents
    }


def cancelar_pedido_por_id(pedido_id: int, email_verificacion: str) -> dict:
    from app.services.database import SessionLocal
    from app.models.db_models import Pedido, LineaPedido, Producto

    db = SessionLocal()
    try:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            return {"ok": False, "mensaje": "No encontré ningún pedido con ese número."}

        if pedido.email_cliente.lower().strip() != email_verificacion.lower().strip():
            return {"ok": False, "mensaje": "El email no coincide con el registrado para ese pedido. No es posible cancelarlo."}

        if pedido.estado in ["enviado", "entregado"]:
            return {"ok": False, "mensaje": f"Lo sentimos, el pedido #{pedido_id} ya está {pedido.estado} y no puede cancelarse."}

        if pedido.estado == "cancelado":
            return {"ok": False, "mensaje": f"El pedido #{pedido_id} ya estaba cancelado."}

        lineas = db.query(LineaPedido).filter(LineaPedido.pedido_id == pedido_id).all()
        for linea in lineas:
            producto = db.query(Producto).filter(Producto.id == linea.producto_id).first()
            if producto:
                producto.stock += linea.cantidad

        pedido.estado = "cancelado"
        db.commit()

        try:
            webhook_url = "https://n8n-production-6d70.up.railway.app/webhook/order-status"
            payload = {
                "pedido_id": pedido.id,
                "nombre_cliente": pedido.nombre_cliente,
                "email_cliente": pedido.email_cliente,
                "estado": "cancelado",
                "mensaje": "Tu pedido ha sido cancelado correctamente. Si tienes alguna duda, no dudes en contactarnos."
            }
            httpx.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error webhook cancelacion: {e}")
            pass

        return {"ok": True, "mensaje": f"Tu pedido #{pedido_id} ha sido cancelado correctamente."}
    finally:
        db.close()


cancelaciones_pendientes: dict[str, dict] = {}
esperando_numero_pedido: dict[str, bool] = {}


def chat_with_bot(session_id: str, user_message: str) -> str:
    try:
        history = get_or_create_session(session_id)
        append_message(session_id, "user", user_message)

        # Si estamos esperando el número de pedido
        if session_id in esperando_numero_pedido:
            numero_match = re.search(r'\d+', user_message)
            if numero_match:
                pedido_id = int(numero_match.group(0))
                del esperando_numero_pedido[session_id]
                cancelaciones_pendientes[session_id] = {"pedido_id": pedido_id}
                reply = f"Para verificar tu identidad, indícame el email con el que realizaste el pedido #{pedido_id}."
                append_message(session_id, "assistant", reply)
                return reply

        # Si hay cancelación pendiente de email
        if session_id in cancelaciones_pendientes:
            pedido_id = cancelaciones_pendientes[session_id]["pedido_id"]
            del cancelaciones_pendientes[session_id]
            resultado = cancelar_pedido_por_id(pedido_id, user_message.strip())
            reply = resultado["mensaje"]
            append_message(session_id, "assistant", reply)
            return reply

        # Detectar intención de cancelar sin número
        if any(word in user_message.lower() for word in ['cancelar', 'cancelación', 'anular', 'deseo cancelar', 'quiero cancelar']):
            if not re.search(r'\d+', user_message):
                esperando_numero_pedido[session_id] = True
                reply = "¿Cuál es el número de pedido que quieres cancelar? Lo encontrarás en el email de confirmación."
                append_message(session_id, "assistant", reply)
                return reply

        # Detectar cancelación con número incluido
        cancelar_match = re.search(r'cancelar?\s+(?:el\s+)?(?:pedido\s+)?#?(\d+)', user_message.lower())
        if not cancelar_match:
            cancelar_match = re.search(r'(?:pedido\s+(?:es\s+el\s+|numero\s+|número\s+|el\s+)?#?)(\d+)', user_message.lower())

        if cancelar_match:
            pedido_id = int(cancelar_match.group(1))
            cancelaciones_pendientes[session_id] = {"pedido_id": pedido_id}
            reply = f"Para verificar tu identidad, indícame el email con el que realizaste el pedido #{pedido_id}."
            append_message(session_id, "assistant", reply)
            return reply

        # Detectar confirmación de pedido
        if user_message.strip().upper() == "CONFIRMAR":
            datos = extraer_datos_pedido(history)
            if datos and datos["tiene_datos"]:
                try:
                    pedido = crear_pedido(
                        session_id=session_id,
                        nombre_cliente=datos["nombre"],
                        email_cliente=datos["email"],
                        direccion=datos["direccion"],
                        items=[{
                            "nombre_producto": datos["producto"],
                            "talla": datos["talla"],
                            "cantidad": 1
                        }]
                    )

                    # Confirmar el pedido automáticamente
                    try:
                        httpx.post(
                            f"https://threadbot-winowin-production.up.railway.app/orders/{pedido.id}/confirm",
                            params={"api_key": "threadbot-internal-key"},
                            timeout=5
                        )
                    except Exception:
                        pass

                    # Notificar a n8n
                    try:
                        httpx.post(
                            "https://n8n-production-6d70.up.railway.app/webhook/order-confirmed",
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
