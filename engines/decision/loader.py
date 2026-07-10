# engines/decision/loader.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

import json
from loguru import logger
from config import DECISION_RULES, SEUIL_ACCEPTER, SEUIL_COMPLEMENT

_cache_regles = {}


def _config_defaut() -> dict:
    return {
        "seuils": {"accepter": SEUIL_ACCEPTER, "complement": SEUIL_COMPLEMENT},
        "flags_refus_immediat": ["INELIGIBILITE", "DEPASSEMENT_SALAIRE", "SINISTRE_HORS_CONTRAT"],
        "flags_complement_obligatoire": ["DECLARATION_TARDIVE_AT", "INCOHERENCE_MEDICALE", "DOCUMENT_ETRANGER", "FREQUENCE_ANORMALE"],
        "escalade_humaine": {
            "montant_seuil": 5000, "score_zone_grise_min": 45,
            "score_zone_grise_max": 55,
            "flags_escalade": ["INCOHERENCE_MEDICALE", "DOCUMENT_ETRANGER"]
        },
        "messages": {
            "accepter":         {"client": "Votre dossier a été accepté. Vous serez contacté sous 48h.", "interne": "Dossier validé automatiquement."},
            "complement_requis": {"client": "Votre dossier nécessite des informations complémentaires.", "interne": "Score intermédiaire ou flag nécessitant vérification."},
            "refuser":          {"client": "Votre dossier ne peut pas être pris en charge.", "interne": "Refus automatique — score insuffisant ou anomalie bloquante."}
        }
    }


def charger_regles_decision(chemin: str = str(DECISION_RULES)) -> dict:
    if chemin in _cache_regles:
        return _cache_regles[chemin]
    try:
        with open(chemin, encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"Règles de décision chargées depuis {chemin}")
        _cache_regles[chemin] = config
        return config
    except FileNotFoundError:
        logger.warning(f"Fichier JSON non trouvé : {chemin} — valeurs par défaut")
        return _config_defaut()
    except json.JSONDecodeError as e:
        logger.error(f"Erreur JSON dans {chemin} : {e}")
        return _config_defaut()