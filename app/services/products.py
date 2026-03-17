from app.services.database import SessionLocal
from app.models.db_models import Producto

def get_catalogo_texto() -> str:
    """
    Lee los productos activos de la BD y los devuelve
    como texto para inyectar en el system prompt.
    """
    db = SessionLocal()
    try:
        productos = db.query(Producto).filter(
            Producto.activo == True
        ).all()

        if not productos:
            return "No hay productos disponibles en este momento."

        lineas = []
        for p in productos:
            lineas.append(
                f"- {p.nombre} | "
                f"Tallas: {p.tallas} | "
                f"Precio: {p.precio_cents / 100:.0f}€ | "
                f"Stock: {p.stock} unidades"
            )
        return "\n".join(lineas)
    finally:
        db.close()
