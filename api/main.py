# api/main.py
"""
Point d'entrée unique de l'API SmartClaim.
Branche les 4 routers de domaine sur l'application FastAPI.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from engines.database import init_db

from api.auth.routes      import router as auth_router
from api.dossiers.routes  import router as dossiers_router
from api.dashboard.routes import router as dashboard_router
from api.regles.routes    import router as regles_router

# ── Création de l'application ────────────────────────────────
app = FastAPI(
    title       = "SmartClaim Manager API",
    description = (
        "Système multi-agent de traitement automatisé "
        "des sinistres assurance groupe tunisienne. "
        "Stack : PaddleOCR · Qwen2.5-7B · LangGraph · SQLite"
    ),
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc"
)

# ── Middleware CORS ───────────────────────────────────────────
# Autorise les requêtes depuis le frontend Next.js (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Initialisation au démarrage ───────────────────────────────
@app.on_event("startup")
def startup():
    """Appelé une seule fois au lancement du serveur."""
    init_db()
    print("SmartClaim API démarrée — BDD initialisée")
    print(" Documentation : http://localhost:8000/docs")

# ── Branchement des routers ───────────────────────────────────
app.include_router(auth_router)
app.include_router(dossiers_router)
app.include_router(dashboard_router)
app.include_router(regles_router)

# ── Routes de santé ───────────────────────────────────────────
@app.get("/", tags=["Santé"])
def racine():
    """Point d'entrée racine — vérifie que l'API répond."""
    return {
        "service":       "SmartClaim Manager API",
        "version":       "1.0.0",
        "statut":        "actif",
        "documentation": "http://localhost:8000/docs"
    }


@app.get("/health", tags=["Santé"])
def sante():
    """Endpoint de healthcheck — utilisé par les outils de monitoring."""
    return {"statut": "ok"}