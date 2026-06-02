# =============================================================
# main.py — Point d'entrée de l'application FastAPI
# =============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes import etudiants, stats, invalides
import os

app = FastAPI(
    title="Gestion Étudiants API",
    description="API REST pour la gestion des données étudiants",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes API
app.include_router(etudiants.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(invalides.router, prefix="/api/v1")

# Chemin vers le frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Servir les fichiers statiques (CSS, JS)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Health check
@app.get("/health")
def health():
    return {"status": "ok", "message": "API opérationnelle"}

# Page principale — étudiants
@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Page dashboard
@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


# Page invalides
@app.get("/invalides")
def invalides_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "invalides.html"))

