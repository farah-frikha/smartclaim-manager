# agents/extraction/agent.py
"""
Point d'entrée de l'Agent Extraction.
Orchestre : prompt → LLM → parsing → validation → résultat.
C'est le seul fichier importé par coordinateur.py.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from datetime import datetime
from loguru import logger

from agents.extraction.prompt    import construire_prompt
from agents.extraction.llm_client import appeler_llm
from agents.extraction.parser    import valider_et_normaliser
from agents.extraction.schema    import CHAMPS_CRITIQUES


def executer_extraction(texte_ocr: str) -> dict:
    """
    Point d'entrée public de l'Agent Extraction.

    Reçoit le texte brut produit par l'Agent Capture,
    envoie à Qwen via Ollama, valide et retourne
    un JSON structuré prêt pour l'Agent Validation.

    Retourne :
        statut           : succes / erreur / confiance_faible
        dossier_extrait  : dict  — champs extraits et normalisés
        champs_manquants : list  — champs obligatoires absents
        champs_invalides : list  — champs présents mais invalides
        score_completude : float — 0 à 1
        peut_continuer   : bool
        llm_tentatives   : int
        llm_duree_ms     : float
        timestamp        : str
    """
    if not texte_ocr or not texte_ocr.strip():
        logger.error("Texte OCR vide — impossible d'extraire")
        return {
            "statut":         "erreur",
            "message":        "Texte OCR vide",
            "peut_continuer": False
        }

    logger.info(f"Extraction LLM sur {len(texte_ocr)} caractères...")

    # 1. Construire le prompt
    prompt = construire_prompt(texte_ocr)

    # 2. Appeler le LLM
    resultat_llm = appeler_llm(prompt)

    if not resultat_llm["succes"]:
        return {
            "statut":          "erreur",
            "message":         "Le LLM n'a pas retourné de JSON valide",
            "peut_continuer":  False,
            "llm_tentatives":  resultat_llm["tentatives"],
            "llm_duree_ms":    resultat_llm["duree_ms"],
            "timestamp":       datetime.now().isoformat()
        }

    # 3. Valider et normaliser
    validation = valider_et_normaliser(resultat_llm["json_parse"])

    # 4. Décider si le pipeline peut continuer
    champs_critiques_manquants = [
        c for c in CHAMPS_CRITIQUES
        if c in validation["champs_manquants"]
    ]
    peut_continuer = len(champs_critiques_manquants) == 0

    # 5. Déterminer le statut
    if not peut_continuer:
        statut = "erreur"
        logger.error(f"Champs critiques manquants : {champs_critiques_manquants}")
    elif validation["score_completude"] < 0.6:
        statut = "confiance_faible"
        logger.warning(f"Complétude faible : {validation['score_completude']}")
    else:
        statut = "succes"
        logger.success(
            f"Extraction réussie — "
            f"complétude={validation['score_completude']}, "
            f"LLM={resultat_llm['duree_ms']}ms"
        )

    return {
        "statut":           statut,
        "dossier_extrait":  validation["donnees_validees"],
        "champs_manquants": validation["champs_manquants"],
        "champs_invalides": validation["champs_invalides"],
        "score_completude": validation["score_completude"],
        "peut_continuer":   peut_continuer,
        "llm_tentatives":   resultat_llm["tentatives"],
        "llm_duree_ms":     resultat_llm["duree_ms"],
        "timestamp":        datetime.now().isoformat()
    }