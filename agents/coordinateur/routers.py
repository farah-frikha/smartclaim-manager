# agents/coordinateur/routers.py
"""
Fonctions de routage conditionnel du graphe LangGraph.
Chaque routeur décide quel nœud exécuter après le nœud courant.
"""
from loguru import logger
from agents.coordinateur.state import EtatDossier


def router_apres_capture(etat: EtatDossier) -> str:
    """Après capture : continuer vers extraction ou terminer en erreur."""
    if not etat.get("peut_continuer"):
        return "erreur"
    if not etat["resultat_capture"].get("confiance_ok"):
        logger.warning("Confiance OCR faible — pipeline continue avec avertissement")
    return "extraction"


def router_apres_extraction(etat: EtatDossier) -> str:
    """Après extraction : continuer si champs critiques présents."""
    if not etat.get("peut_continuer"):
        return "erreur"
    return "validation"


def router_apres_validation(etat: EtatDossier) -> str:
    """
    Après validation — implémente le FAIL-FAST.
    Si une règle obligatoire échoue, court-circuit vers
    decision_directe sans passer par le scoring.
    """
    if not etat.get("peut_continuer"):
        logger.warning(
            "Validation bloquante — court-circuit vers décision directe"
        )
        return "decision_directe"
    return "scoring"


def router_apres_scoring(etat: EtatDossier) -> str:
    """Après scoring : toujours vers décision sauf erreur."""
    if not etat.get("peut_continuer"):
        return "erreur"
    return "decision"