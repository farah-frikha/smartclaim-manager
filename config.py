# config.py
import os
from pathlib import Path

# Racine du projet
BASE_DIR = Path(__file__).parent

# Dossiers
RULES_DIR    = BASE_DIR / "rules"
DATA_DIR     = BASE_DIR / "data"
PROMPTS_DIR  = BASE_DIR / "prompts"
UPLOADS_DIR  = DATA_DIR / "uploads"
CONTRATS_DIR = DATA_DIR / "contrats"
TESTS_DIR    = DATA_DIR / "dossiers_test"

# Base de données
DB_PATH = DATA_DIR / "smartclaim.db"

# Fichiers de règles
VALIDATION_RULES = RULES_DIR / "regles_validation_agent.json"
SCORING_RULES    = RULES_DIR / "regles_scoring.json"
DECISION_RULES   = RULES_DIR / "regles_decision.json"
COORDINATION_RULES = RULES_DIR / "regles_coordinateur.json"

# LLM
OLLAMA_MODEL   = "qwen2.5:7b-instruct"
OLLAMA_URL     = "http://localhost:11434"
LLM_MAX_TOKENS = 1000
LLM_TEMPERATURE = 0.0  

# OCR
OCR_LANGUAGE   = "fr"
OCR_MIN_DPI    = 300
OCR_CONFIDENCE_THRESHOLD = 0.6

# Scoring
SCORE_BASE     = 100
SEUIL_ACCEPTER = 70
SEUIL_COMPLEMENT = 40

# Streamlit
APP_TITLE = "SmartClaim Manager"
APP_PORT  = 8501
# Authentification JWT
JWT_SECRET_KEY = "smartclaim-secret-key-a-changer-en-production-2026"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 480  # 8 heures