# engines/validation/domaines.py
"""
Associe chaque domaine métier à son fichier de règles de validation.
Ajouter un domaine = ajouter une entrée ici.
"""
from config import VALIDATION_RULES, VALIDATION_RULES_CNAM_SOINS

REGLES_PAR_DOMAINE = {
    "AUTO":       VALIDATION_RULES,
    "CNAM_SOINS": VALIDATION_RULES_CNAM_SOINS,
}


def get_regles_domaine(domaine: str = "AUTO"):
    """Retourne le chemin du fichier de règles du domaine (auto par défaut)."""
    return REGLES_PAR_DOMAINE.get(domaine, VALIDATION_RULES)