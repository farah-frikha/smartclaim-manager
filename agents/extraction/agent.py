# agents/extraction/agent.py
"""
Point d'entrée de l'Agent Extraction.
Orchestre : prompt → LLM → parsing → validation → résultat.
Supporte plusieurs domaines via le paramètre 'domaine'.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from datetime import datetime
from loguru import logger

from agents.extraction.prompt         import construire_prompt
from agents.extraction.llm_client     import appeler_llm
from agents.extraction.parser         import valider_et_normaliser
from agents.extraction.domaines_config import get_config_domaine


def executer_extraction(texte_ocr: str, domaine: str = "AUTO") -> dict:
    """
    Point d'entrée public de l'Agent Extraction.

    Reçoit le texte brut produit par l'Agent Capture,
    envoie à Qwen via Ollama, valide et retourne
    un JSON structuré prêt pour l'Agent Validation.

    Le paramètre 'domaine' sélectionne le prompt et les champs
    critiques. Par défaut "AUTO" — le comportement existant est préservé.

    Retourne :
        statut           : succes / erreur / confiance_faible
        dossier_extrait  : dict  — champs extraits et normalisés
        champs_manquants : list  — champs obligatoires absents
        champs_invalides : list  — champs présents mais invalides
        score_completude : float — 0 à 1
        peut_continuer   : bool
        domaine          : str   — domaine utilisé
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

    config = get_config_domaine(domaine)

    logger.info(
        f"Extraction LLM sur {len(texte_ocr)} caractères (domaine={domaine})..."
    )

    # 1. Construire le prompt selon le domaine
    prompt = construire_prompt(texte_ocr, domaine=domaine)

    # 2. Appeler le LLM
    resultat_llm = appeler_llm(prompt)

    if not resultat_llm["succes"]:
        return {
            "statut":          "erreur",
            "message":         "Le LLM n'a pas retourné de JSON valide",
            "peut_continuer":  False,
            "domaine":         domaine,
            "llm_tentatives":  resultat_llm["tentatives"],
            "llm_duree_ms":    resultat_llm["duree_ms"],
            "timestamp":       datetime.now().isoformat()
        }

    # 3. Valider et normaliser
    validation = valider_et_normaliser(resultat_llm["json_parse"], domaine=domaine)
    # 4. Décider si le pipeline peut continuer (champs critiques du domaine)
    champs_critiques = config["champs_critiques"]
    champs_critiques_manquants = [
        c for c in champs_critiques
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
        "domaine":          domaine,
        "llm_tentatives":   resultat_llm["tentatives"],
        "llm_duree_ms":     resultat_llm["duree_ms"],
        "timestamp":        datetime.now().isoformat()
    }