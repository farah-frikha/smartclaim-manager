# engines/validation/loader.py
"""
Chargement et cache des règles de validation depuis le fichier JSON.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

import json
from loguru import logger
from config import VALIDATION_RULES

_cache_regles = {}


def charger_regles_validation(chemin: str = str(VALIDATION_RULES)) -> list:
    """
    Charge les règles depuis le fichier JSON avec cache.
    Le fichier n'est lu qu'une seule fois — les appels suivants
    retournent la valeur en mémoire.
    """
    if chemin in _cache_regles:
        return _cache_regles[chemin]
    try:
        with open(chemin, encoding="utf-8") as f:
            data = json.load(f)
        regles = data["rules"] if isinstance(data, dict) else data
        logger.info(f"{len(regles)} règles chargées depuis {chemin}")
        _cache_regles[chemin] = regles
        return regles
    except FileNotFoundError:
        logger.warning(f"Fichier JSON non trouvé : {chemin}")
        return []
    except KeyError:
        logger.warning(f"Clé 'rules' absente dans {chemin}")
        return []