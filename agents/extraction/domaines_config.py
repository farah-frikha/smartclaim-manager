# agents/extraction/domaines_config.py
"""
Registre central des configurations d'extraction par domaine.
Seul endroit à modifier pour ajouter un domaine.
"""

CONFIG_DOMAINES = {
    "AUTO": {
        "fichier_prompt":   "extraction_prompt.txt",
        "champs_critiques": ["nom_assure", "numero_contrat", "date_sinistre", "type_sinistre"],
        "utilise_types_sinistres": True,
    },
    "CNAM_SOINS": {
        "fichier_prompt":   "extraction_cnam_soins.txt",
        "champs_critiques": ["nom_victime", "numero_immatriculation", "type_prestation"],
        "utilise_types_sinistres": False,
    },
}

DOMAINE_DEFAUT = "AUTO"


def get_config_domaine(domaine: str) -> dict:
    """Retourne la config du domaine, ou celle du domaine par défaut."""
    return CONFIG_DOMAINES.get(domaine, CONFIG_DOMAINES[DOMAINE_DEFAUT])