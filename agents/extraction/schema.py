# agents/extraction/schema.py
"""
Schéma des champs attendus et types de sinistres valides.
Ce fichier définit le contrat de données entre l'extraction LLM
et le moteur de validation.
"""

SCHEMA_EXTRACTION = {
    "nom_assure":       {"type": str,   "obligatoire": True},
    "prenom_assure":    {"type": str,   "obligatoire": False},
    "numero_cnss":      {"type": str,   "obligatoire": True},
    "numero_contrat":   {"type": str,   "obligatoire": True},
    "date_sinistre":    {"type": str,   "obligatoire": True},
    "type_sinistre":    {"type": str,   "obligatoire": True},
    "montant_reclame":  {"type": float, "obligatoire": True},
    "description":      {"type": str,   "obligatoire": False},
    "date_declaration": {"type": str,   "obligatoire": False},
    "numero_dossier":   {"type": str,   "obligatoire": False},
}

TYPES_SINISTRES_VALIDES = [
    "SANTE_CONSUL",
    "SANTE_HOSPIT",
    "PREV_ARRET",
    "PREV_INVALIDITE",
    "PREV_DECES",
    "AT_ACCIDENT",
    "AUTO_ACCIDENT",
    "AUTO_VOL",
    "AUTO_BRIS_GLACE",
    "AUTRE"
]

# Champs dont l'absence bloque le pipeline
CHAMPS_CRITIQUES = [
    "nom_assure",
    "numero_contrat",
    "date_sinistre",
    "type_sinistre"
]
# --- Schéma du domaine CNAM_SOINS ---
SCHEMA_CNAM_SOINS = {
    "nom_victime":            {"type": str,   "obligatoire": True},
    "prenom_victime":         {"type": str,   "obligatoire": False},
    "numero_immatriculation": {"type": str,   "obligatoire": True},
    "numero_cin":             {"type": str,   "obligatoire": False},
    "qualite_demandeur":      {"type": str,   "obligatoire": False},
    "date_accident":          {"type": str,   "obligatoire": False},
    "nom_employeur":          {"type": str,   "obligatoire": False},
    "type_prestation":        {"type": str,   "obligatoire": True},
    "prestataire_soins":      {"type": str,   "obligatoire": False},
    "date_demande":           {"type": str,   "obligatoire": False},
}

# Registre : chaque domaine pointe vers son schéma
SCHEMAS_PAR_DOMAINE = {
    "AUTO":       SCHEMA_EXTRACTION,
    "CNAM_SOINS": SCHEMA_CNAM_SOINS,
}


def get_schema(domaine: str = "AUTO") -> dict:
    """Retourne le schéma d'extraction du domaine (auto par défaut)."""
    return SCHEMAS_PAR_DOMAINE.get(domaine, SCHEMA_EXTRACTION)