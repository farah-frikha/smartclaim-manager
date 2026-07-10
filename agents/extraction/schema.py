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