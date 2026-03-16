from fastapi import FastAPI
from app.api import chat, health

app = FastAPI(title="ThreadBot", version="2.0")

app.include_router(health.router)
app.include_router(chat.router)
