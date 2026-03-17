import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database import SessionLocal
from app.models.db_models import Producto

productos = [
    Producto(
        nombre="Camiseta básica blanca",
        precio_cents=1500,
        stock=50,
        categoria="camisetas",
        tallas="S,M,L,XL",
        activo=True
    ),
    Producto(
        nombre="Camiseta básica negra",
        precio_cents=1500,
        stock=50,
        categoria="camisetas",
        tallas="S,M,L,XL",
        activo=True
    ),
    Producto(
        nombre="Sudadera gris con capucha",
        precio_cents=3500,
        stock=30,
        categoria="sudaderas",
        tallas="M,L,XL",
        activo=True
    ),
    Producto(
        nombre="Vaqueros slim fit azul",
        precio_cents=4500,
        stock=25,
        categoria="pantalones",
        tallas="28,30,32,34",
        activo=True
    ),
    Producto(
        nombre="Chaqueta bomber negra",
        precio_cents=7500,
        stock=15,
        categoria="chaquetas",
        tallas="M,L,XL",
        activo=True
    ),
    Producto(
        nombre="Shorts cargo beige",
        precio_cents=3000,
        stock=20,
        categoria="pantalones",
        tallas="S,M,L",
        activo=True
    ),
]

db = SessionLocal()
try:
    existentes = db.query(Producto).count()
    if existentes > 0:
        print(f"Ya hay {existentes} productos en la BD. No se insertan duplicados.")
    else:
        db.add_all(productos)
        db.commit()
        print(f"{len(productos)} productos insertados correctamente.")
finally:
    db.close()
