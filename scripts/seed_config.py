import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.db_models import Configuracion
from app.services.database import SessionLocal

configuraciones_por_defecto = [
    {
        "clave": "nombre_tienda",
        "valor": "ThreadCo",
        "descripcion": "Nombre de la tienda que usa el bot",
    },
    {
        "clave": "saludo_bienvenida",
        "valor": "¡Bienvenido a ThreadCo! ¿En qué puedo ayudarte?",
        "descripcion": "Mensaje de bienvenida del chatbot",
    },
    {
        "clave": "tono_bot",
        "valor": "amable y profesional",
        "descripcion": "Tono y personalidad del asistente",
    },
    {
        "clave": "producto_destacado",
        "valor": "",
        "descripcion": "Producto que el bot menciona primero (dejar vacío para ninguno)",
    },
    {
        "clave": "oferta_activa",
        "valor": "",
        "descripcion": "Mensaje de oferta que el bot menciona (dejar vacío para ninguna)",
    },
    {
        "clave": "bot_activo",
        "valor": "true",
        "descripcion": "Si el bot está activo o en mantenimiento",
    },
]

db = SessionLocal()
try:
    insertadas = 0
    for conf in configuraciones_por_defecto:
        existente = db.query(Configuracion).filter(Configuracion.clave == conf["clave"]).first()
        if existente:
            continue
        db.add(
            Configuracion(
                clave=conf["clave"],
                valor=conf["valor"],
                descripcion=conf["descripcion"],
            )
        )
        insertadas += 1

    if insertadas:
        db.commit()
    print(f"Configuraciones insertadas: {insertadas}")
finally:
    db.close()
