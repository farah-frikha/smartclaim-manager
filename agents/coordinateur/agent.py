# agents/coordinateur/agent.py
"""
Point d'entrée public du système SmartClaim.
C'est la seule fonction importée par l'API et les tests.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import time
from loguru import logger

from engines.database import init_db
from agents.coordinateur.graph import construire_graphe
from agents.coordinateur.state import EtatDossier


def traiter_dossier(chemin_fichier: str, employe_id: int = 1) -> dict:
    logger.info("=" * 60)
    logger.info(f"SMARTCLAIM — Nouveau dossier : {chemin_fichier}")
    logger.info("=" * 60)

    init_db()
    t_debut = time.perf_counter()

    etat_initial: EtatDossier = {
        "chemin_fichier":      chemin_fichier,
        "employe_id":          employe_id,
        "dossier_id":          None,
        "document_id":         None,
        "reference_dossier":   None,
        "resultat_capture":    None,
        "resultat_extraction": None,
        "resultat_validation": None,
        "resultat_scoring":    None,
        "resultat_decision":   None,
        "etape_actuelle":      "debut",
        "etape_arret":         None,
        "erreurs":             [],
        "peut_continuer":      True,
        "score_id":            None,
        "temps_debut":         t_debut,
    }

    graphe     = construire_graphe()
    etat_final = graphe.invoke(etat_initial)

    duree_totale = round((time.perf_counter() - t_debut) * 1000)

    decision = etat_final.get("resultat_decision") or {}
    logger.info("=" * 60)
    logger.info(
        f"PIPELINE TERMINÉ en {duree_totale}ms — "
        f"Décision : {(decision.get('decision') or 'N/A').upper()}"
    )
    logger.info("=" * 60)
    logger.info("=" * 60)
    logger.info(
        f"PIPELINE TERMINÉ en {duree_totale}ms — "
        f"Décision : {decision.get('decision', 'N/A').upper()}"
    )
    logger.info("=" * 60)

    return {
        "reference_dossier":   etat_final.get("reference_dossier"),
        "dossier_id":          etat_final.get("dossier_id"),
        "etape_arret":         etat_final.get("etape_arret"),
        "resultat_capture":    etat_final.get("resultat_capture"),
        "resultat_extraction": etat_final.get("resultat_extraction"),
        "resultat_validation": etat_final.get("resultat_validation"),
        "resultat_scoring":    etat_final.get("resultat_scoring"),
        "resultat_decision":   etat_final.get("resultat_decision"),
        "duree_totale_ms":     duree_totale,
        "erreurs":             etat_final.get("erreurs", []),
    }