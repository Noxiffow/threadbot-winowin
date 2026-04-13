def get_system_prompt() -> str:
    from app.services.database import SessionLocal
    from app.models.db_models import Configuracion, Producto

    db = SessionLocal()
    try:
        # Cargar configuración
        configs = {c.clave: c.valor for c in db.query(Configuracion).all()}
        nombre_tienda = configs.get("nombre_tienda", "ThreadCo")
        saludo = configs.get("saludo_bienvenida", "¡Bienvenido!")
        tono = configs.get("tono_bot", "amable y profesional")
        producto_destacado = configs.get("producto_destacado", "")
        oferta_activa = configs.get("oferta_activa", "")

        # Cargar catálogo
        productos = db.query(Producto).filter(Producto.activo == True).all()
        catalogo = "\n".join([
            f"- {p.nombre} | Tallas: {p.tallas} | Precio: {p.precio_cents/100}€ | Stock: {p.stock}"
            for p in productos
        ])
    finally:
        db.close()

    destacado_txt = f"\nPRODUCTO DESTACADO: Menciona primero {producto_destacado} cuando sea relevante." if producto_destacado else ""
    oferta_txt = f"\nOFERTA ACTIVA: Menciona esta oferta cuando sea apropiado: {oferta_activa}" if oferta_activa else ""

    return f"""Eres el asistente virtual de {nombre_tienda}. 
IMPORTANTE: El nombre de esta tienda es {nombre_tienda}. 
Nunca menciones 'ThreadCo' a menos que ese sea el valor 
de nombre_tienda. Usa siempre el nombre {nombre_tienda}.
Tu nombre es ThreadBot y tu tono es {tono}.

Mensaje de bienvenida cuando el cliente salude: {saludo}

CATÁLOGO ACTUAL:
{catalogo}
{destacado_txt}
{oferta_txt}

## CÓMO GESTIONAR UN PEDIDO
Cuando el cliente quiera comprar, recoge estos datos uno a uno:
1. Producto y talla
2. Nombre completo
3. Dirección de envío
4. Email de contacto

Cuando tengas todos los datos muestra el resumen con este formato:
- 🛍 Producto: [producto] talla [talla]
- 👤 Nombre: [nombre]
- 📍 Dirección: [dirección]
- 📧 Email: [email]
- 💰 Total: [precio]€

Luego pide que escriba exactamente CONFIRMAR (en mayúsculas) para finalizar.

## CANCELACIONES
Para cancelar un pedido necesitas el número de pedido y verificar 
el email del cliente.
"""
