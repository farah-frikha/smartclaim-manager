# engines/scoring/loader.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

import json
from loguru import logger
from config import SCORING_RULES, SCORE_BASE

_cache_regles = {}


def charger_regles_scoring(chemin: str = str(SCORING_RULES)) -> dict:
    if chemin in _cache_regles:
        return _cache_regles[chemin]
    try:
        with open(chemin, encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"{len(config.get('regles', []))} règles scoring chargées")
        _cache_regles[chemin] = config
        return config
    except FileNotFoundError:
        logger.warning(f"Fichier JSON non trouvé : {chemin}")
        return {"score_base": SCORE_BASE, "score_minimum": 0,
                "score_maximum": 100, "regles": []}
    except json.JSONDecodeError as e:
        logger.error(f"Erreur JSON dans {chemin} : {e}")
        return {"score_base": SCORE_BASE, "score_minimum": 0,
                "score_maximum": 100, "regles": []}