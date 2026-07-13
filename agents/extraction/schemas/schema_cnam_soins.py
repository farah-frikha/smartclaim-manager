# agents/extraction/schemas/schema_cnam_soins.py
"""
Schéma d'extraction pour le domaine CNAM_SOINS.
Demande de prise en charge de soins et d'appareillage (formulaire CNAM AT.016).
"""

SCHEMA_CNAM_SOINS = {
    "domaine": "CNAM_SOINS",
    "champs": {
        "nom_victime":          {"type": "str",  "critique": True},
        "prenom_victime":       {"type": "str",  "critique": False},
        "numero_immatriculation": {"type": "str", "critique": True},
        "numero_cin":           {"type": "str",  "critique": False},
        "qualite_demandeur":    {"type": "str",  "critique": False},
        "date_accident":        {"type": "date", "critique": False},
        "nom_employeur":        {"type": "str",  "critique": False},
        "type_prestation":      {"type": "str",  "critique": True},
        "prestataire_soins":    {"type": "str",  "critique": False},
        "date_demande":         {"type": "date", "critique": False},
    },
}

# Champs critiques : leur absence bloque le traitement
CHAMPS_CRITIQUES_CNAM_SOINS = [
    nom for nom, info in SCHEMA_CNAM_SOINS["champs"].items()
    if info["critique"]
]