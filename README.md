# ThreadBot — Chatbot para Tienda de Ropa

Chatbot conversacional con IA para atención al cliente de una tienda de ropa. Desarrollado con FastAPI y Groq (llama-3.3-70b-versatile).
Proyecto de prácticas en WinoWin · 2026.

---

## Estado del proyecto

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Planificación y diseño | ✅ Completada |
| 2 | Backend base (FastAPI + Groq) | 🔵 En curso |
| 3 | Base de datos (PostgreSQL) | ⬜ Pendiente |
| 4 | Automatizaciones n8n | ⬜ Pendiente |
| 5 | Interfaz web (frontend) | ⬜ Pendiente |
| 6 | Pruebas y ajustes | ⬜ Pendiente |
| 7 | Despliegue en Railway | ⬜ Pendiente |

---

## Stack

| Componente | Tecnología |
|------------|------------|
| Backend | FastAPI + Python |
| Modelo LLM | Groq · llama-3.3-70b-versatile |
| Base de datos | PostgreSQL (Railway) |
| Automatizaciones | n8n (Docker) |
| Frontend | HTML + CSS + JS |
| Despliegue | Railway |

---

## Estructura del proyecto

```
threadbot/
├── app/
│   ├── main.py               # Punto de entrada FastAPI
│   ├── core/
│   │   ├── config.py         # Variables de entorno y settings
│   │   └── prompts.py        # System prompts
│   ├── api/
│   │   ├── chat.py           # Endpoint /chat
│   │   └── health.py         # Endpoint /health
│   ├── services/
│   │   ├── llm_service.py    # Conexión con Groq
│   │   ├── session.py        # Gestión de memoria de sesión
│   │   ├── products.py       # Lógica de catálogo y stock
│   │   └── orders.py         # Lógica de pedidos
│   ├── models/
│   │   └── db_models.py      # Modelos SQLAlchemy
│   └── schemas/
│       └── chat_schemas.py   # Pydantic request/response
├── n8n/                      # Flujos exportados como JSON
├── frontend/                 # Chat widget HTML/CSS/JS
├── migrations/               # Alembic
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile
└── railway.toml
```

---

## Instalación

```bash
# 1. Crear entorno virtual
uv venv
source .venv/bin/activate

# 2. Instalar dependencias
uv pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env y añade GROQ_API_KEY y DATABASE_URL

# 4. Arrancar el servidor
uvicorn app.main:app --reload
```

---

## Variables de entorno

```
GROQ_API_KEY=
DATABASE_URL=
SECRET_KEY=
```

---

**Autor:** Jonathan Neto · Prácticas WinoWin 2026
