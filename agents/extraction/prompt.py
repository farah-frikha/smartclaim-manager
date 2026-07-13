# agents/extraction/prompt.py
"""
Chargement et construction du prompt few-shot pour l'extraction LLM.
Les templates sont dans prompts/, un par domaine, modifiables sans code.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))
from loguru import logger
from config import PROMPTS_DIR
from agents.extraction.schema import TYPES_SINISTRES_VALIDES
from agents.extraction.domaines_config import get_config_domaine

# Cache des templates par fichier — lus une seule fois
_cache_templates: dict = {}


def charger_prompt_template(fichier_prompt: str) -> str:
    """
    Charge un template de prompt depuis prompts/<fichier_prompt>.
    Cache par fichier pour éviter les I/O répétées.
    """
    if fichier_prompt in _cache_templates:
        return _cache_templates[fichier_prompt]

    chemin = PROMPTS_DIR / fichier_prompt
    try:
        with open(chemin, encoding="utf-8") as f:
            contenu = f.read()
        _cache_templates[fichier_prompt] = contenu
        logger.info(f"Prompt chargé depuis {chemin}")
        return contenu
    except FileNotFoundError:
        logger.error(f"Prompt introuvable : {chemin}")
        raise


def construire_prompt(texte_ocr: str, domaine: str = "AUTO") -> str:
    """
    Construit le prompt final selon le domaine.
    Injecte le texte OCR (et les types de sinistres pour le domaine auto).
    Tronque le texte à 6000 caractères.
    """
    config        = get_config_domaine(domaine)
    template      = charger_prompt_template(config["fichier_prompt"])
    texte_tronque = texte_ocr[:6000] if len(texte_ocr) > 6000 else texte_ocr

    if config["utilise_types_sinistres"]:
        # Domaine auto : le template attend {texte_ocr} et {types_valides}
        return template.format(
            texte_ocr     = texte_tronque,
            types_valides = ", ".join(TYPES_SINISTRES_VALIDES)
        )
    else:
        # Autres domaines : seul {texte_ocr} est injecté.
        # On remplace manuellement pour ne pas interférer avec les {{ }}
        # du JSON d'exemple dans le prompt.
        return template.replace("{texte_ocr}", texte_tronque)