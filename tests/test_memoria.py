import requests

URL = "http://127.0.0.1:8000/chat"

def send(session_id: str, message: str) -> str:
    r = requests.post(URL, json={"session_id": session_id, "message": message})
    if r.status_code == 200:
        return r.json()["reply"]
    return f"[Error {r.status_code}]"

def bloque(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print('='*60)

bloque("TEST DE MEMORIA INDEPENDIENTE POR SESIÓN")

# ── USUARIO 1: Ana ──────────────────────────────────────────
bloque("USUARIO 1 — sesión: usuario_ana")

msg = "Hola, me llamo Ana."
print(f"\n> Ana: {msg}")
print(f"< Bot: {send('usuario_ana', msg)}")

msg = "¿Cuánto cuestan los vaqueros?"
print(f"\n> Ana: {msg}")
print(f"< Bot: {send('usuario_ana', msg)}")

# ── USUARIO 2: Carlos ───────────────────────────────────────
bloque("USUARIO 2 — sesión: usuario_carlos")

msg = "Buenas, soy Carlos."
print(f"\n> Carlos: {msg}")
print(f"< Bot: {send('usuario_carlos', msg)}")

msg = "¿Tenéis sudaderas?"
print(f"\n> Carlos: {msg}")
print(f"< Bot: {send('usuario_carlos', msg)}")

# ── VERIFICACIÓN DE MEMORIA ─────────────────────────────────
bloque("VERIFICACIÓN DE MEMORIA INDEPENDIENTE")

msg = "¿Recuerdas cómo me llamo?"
print(f"\n> Ana: {msg}")
print(f"< Bot: {send('usuario_ana', msg)}")

msg = "¿Recuerdas mi nombre?"
print(f"\n> Carlos: {msg}")
print(f"< Bot: {send('usuario_carlos', msg)}")

msg = "¿Sabes cómo se llama el otro usuario que está hablando contigo?"
print(f"\n> Ana: {msg}")
print(f"< Bot: {send('usuario_ana', msg)}")

bloque("FIN DEL TEST")
