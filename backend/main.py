# =============================================================
# main.py — Point d'entrée de l'application FastAPI
# =============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import etudiants, stats

# Création de l'instance FastAPI avec métadonnées
app = FastAPI(
    title="Gestion Étudiants API",
    description="API REST pour la gestion des données étudiants",
    version="1.0.0"
)

# -------------------------------------------------------------
# Middleware CORS
# Permet au frontend (HTML/JS) d'appeler l'API sans blocage
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Autoriser toutes les origines
    allow_credentials=True,
    allow_methods=["*"],       # GET, POST, PUT, PATCH, DELETE
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Enregistrement des routeurs
# Chaque routeur gère un groupe de routes
# -------------------------------------------------------------
app.include_router(etudiants.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")


# -------------------------------------------------------------
# Route : GET /health
# Vérification que le serveur est bien démarré
# -------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "message": "API opérationnelle"}


# -------------------------------------------------------------
# Route : GET /
# Page d'accueil de l'API
# -------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API Gestion Étudiants"}