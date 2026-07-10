# agents/extraction/prompt.py
"""
Chargement et construction du prompt few-shot pour l'extraction LLM.
Le template est stocké dans prompts/extraction_prompt.txt
pour être modifiable sans toucher au code.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from loguru import logger
from config import PROMPTS_DIR
from agents.extraction.schema import TYPES_SINISTRES_VALIDES

# Cache du template — lu une seule fois depuis le disque
_cache_template: str = None


def charger_prompt_template() -> str:
    """
    Charge le template depuis prompts/extraction_prompt.txt.
    Utilise un cache module-level pour éviter les I/O répétées.
    """
    global _cache_template
    if _cache_template is not None:
        return _cache_template

    chemin = PROMPTS_DIR / "extraction_prompt.txt"
    try:
        with open(chemin, encoding="utf-8") as f:
            _cache_template = f.read()
        logger.info(f"Prompt chargé depuis {chemin}")
        return _cache_template
    except FileNotFoundError:
        logger.error(f"Prompt introuvable : {chemin}")
        raise


def construire_prompt(texte_ocr: str) -> str:
    """
    Construit le prompt final en injectant le texte OCR
    et la liste des types de sinistres valides.
    Tronque le texte à 6000 caractères pour respecter
    la limite de contexte du LLM.
    """
    template      = charger_prompt_template()
    texte_tronque = texte_ocr[:6000] if len(texte_ocr) > 6000 else texte_ocr

    return template.format(
        texte_ocr     = texte_tronque,
        types_valides = ", ".join(TYPES_SINISTRES_VALIDES)
    )