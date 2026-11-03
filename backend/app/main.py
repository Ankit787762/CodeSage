# ============================================================
# PART 1 — IMPORTS
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.routes import router

# ============================================================
# PART 2 — CREATE APP
# ============================================================

app = FastAPI(title="CodeSage")


# ============================================================
# PART 3 — CORS (allow the React frontend)
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PART 4 — ADD ROUTES
# ============================================================

app.include_router(router)


# ============================================================
# PART 5 — HEALTH CHECK
# ============================================================


@app.get("/health")
def health():

    return {"status": "ok", "model": config.GROQ_MODEL}
