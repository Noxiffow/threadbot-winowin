from fastapi import HTTPException
from app.services.database import SessionLocal
from app.models.db_models import Pedido, LineaPedido, Producto

def crear_pedido(
    session_id: str,
    nombre_cliente: str,
    email_cliente: str,
    direccion: str,
    items: list[dict]
) -> Pedido:
    """
    Crea un pedido en la BD.
    items es una lista de dicts con:
    { "nombre_producto": str, "talla": str, "cantidad": int }
    """
    db = SessionLocal()
    try:
        total_cents = 0
        lineas = []

        for item in items:
            producto = db.query(Producto).filter(
                Producto.nombre.ilike(f"%{item['nombre_producto']}%"),
                Producto.activo == True
            ).first()

            if producto:
                # Verificar stock suficiente
                if producto.stock <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No hay stock disponible para {producto.nombre}"
                    )
                # Descontar stock
                producto.stock -= item.get("cantidad", 1)
                linea = LineaPedido(
                    producto_id=producto.id,
                    cantidad=item.get("cantidad", 1),
                    precio_unidad_cents=producto.precio_cents,
                    talla=item.get("talla", "")
                )
                lineas.append(linea)
                total_cents += producto.precio_cents * item.get("cantidad", 1)

        pedido = Pedido(
            session_id=session_id,
            nombre_cliente=nombre_cliente,
            email_cliente=email_cliente,
            direccion=direccion,
            estado="pendiente",
            total_cents=total_cents
        )

        db.add(pedido)
        db.flush()

        for linea in lineas:
            linea.pedido_id = pedido.id
            db.add(linea)

        db.commit()
        db.refresh(pedido)
        return pedido

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_pedido(pedido_id: int) -> Pedido | None:
    db = SessionLocal()
    try:
        return db.query(Pedido).filter(Pedido.id == pedido_id).first()
    finally:
        db.close()
