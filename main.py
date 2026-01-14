from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# CORS (нужно для Mini App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== API =====

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "API is running"}

# Пример API ручки (потом расширим)
@app.get("/api/routes")
def get_routes():
    return [
        {"id": 1, "route": "КА-12", "address": "ул. Ленина, 1"},
        {"id": 2, "route": "КА-7", "address": "пр. Мира, 15"}
    ]

# ===== MINI APP =====
# ВАЖНО: монтируем ПОСЛЕ API
app.mount(
    "/",
    StaticFiles(directory="mini_app", html=True),
    name="mini_app"
)
