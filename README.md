# ThreadBot — Chatbot para Tienda de Ropa

Prototipo funcional de chatbot para e-commerce desarrollado con **FastAPI** y **Groq** (llama-3.3-70b-versatile).
Proyecto de prácticas en WinoWin · Semana 1.

---

## Características

- Identidad de tienda: **ThreadCo** (tienda de ropa casual masculina ficticia)
- Catálogo de productos integrado en el system prompt
- **Memoria de sesión por `session_id`** — cada usuario mantiene su propio contexto
- Aislamiento de sesiones verificado (test superado al 100%)

## Stack

| Componente | Tecnología |
|---|---|
| Backend | FastAPI |
| Modelo LLM | Groq · llama-3.3-70b-versatile |
| Variables de entorno | python-dotenv |
| Servidor | Uvicorn |

## Instalación

```bash
# 1. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install fastapi uvicorn groq python-dotenv

# 3. Configurar API key
cp .env.example .env
# Edita .env y añade tu GROQ_API_KEY

# 4. Arrancar el servidor
uvicorn main:app --reload
```

## Uso

```bash
# Enviar mensaje al chatbot
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "usuario1", "message": "Hola, ¿qué vaqueros tenéis?"}'
```

## Tests

```bash
# Test básico
python3 test.py

# Test de memoria independiente por sesión (2 usuarios)
python3 test_memoria.py
```

## Estructura

```
.
├── main.py            # API FastAPI + lógica del chatbot
├── test.py            # Test básico de conectividad
├── test_memoria.py    # Test de aislamiento de sesiones
├── .env.example       # Plantilla de variables de entorno
└── README.md
```

---

**Autor:** Jonathan Neto · Prácticas WinoWin 2026
