# agents/capture/moteurs/factory.py
"""
Factory de moteurs OCR.
Retourne l'implémentation correspondant à la configuration OCR_ENGINE.
C'est le seul endroit qui connaît toutes les implémentations ;
le reste du pipeline ne connaît que l'interface MoteurOCR.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from loguru import logger
from config import OCR_ENGINE
from agents.capture.moteurs.base import MoteurOCR

# Cache : une seule instance par moteur (évite les rechargements)
_instance_moteur = None


def obtenir_moteur_ocr() -> MoteurOCR:
    """
    Retourne l'instance du moteur OCR configuré (singleton).
    Le moteur est choisi via OCR_ENGINE dans config.py / .env.
    """
    global _instance_moteur
    if _instance_moteur is not None:
        return _instance_moteur

    moteur_choisi = OCR_ENGINE.lower().strip()

    if moteur_choisi == "paddle":
        from agents.capture.moteurs.moteur_paddle import MoteurPaddle
        _instance_moteur = MoteurPaddle()
    elif moteur_choisi == "ocrspace":
        from agents.capture.moteurs.moteur_ocrspace import MoteurOcrSpace
        _instance_moteur = MoteurOcrSpace()
    else:
        raise ValueError(
            f"Moteur OCR inconnu : '{OCR_ENGINE}'. "
            f"Valeurs acceptées : 'paddle', 'ocrspace'."
        )

    logger.info(f"Moteur OCR sélectionné : {_instance_moteur.nom}")
    return _instance_moteur