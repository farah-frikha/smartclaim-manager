# agents/capture/ocr.py
"""
Singleton PaddleOCR et extraction OCR page par page.
Ce fichier est le seul à dépendre de paddleocr.
Changer d'OCR = modifier uniquement ce fichier.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import numpy as np
from paddleocr import PaddleOCR
from loguru import logger

from config import OCR_LANGUAGE, OCR_CONFIDENCE_THRESHOLD
from agents.capture.preprocessing import preprocesser_image, verifier_qualite_image

# Singleton — chargé une seule fois en mémoire
_ocr_instance = None


def get_ocr() -> PaddleOCR:
    """
    Retourne l'instance PaddleOCR (singleton).
    Le modèle (~300 Mo) est chargé une seule fois.
    Les appels suivants retournent l'instance existante.
    """
    global _ocr_instance
    if _ocr_instance is None:
        logger.info("Chargement du modèle PaddleOCR...")
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang=OCR_LANGUAGE,
            show_log=False
        )
        logger.success("Modèle PaddleOCR chargé")
    return _ocr_instance


def ocr_page(image_np: np.ndarray, numero_page: int) -> dict:
    """
    Applique l'OCR sur une image de page numpy.

    Pipeline :
      1. Évalue la qualité de l'image (netteté, luminosité)
      2. Applique le preprocessing OpenCV
      3. Lance PaddleOCR
      4. Agrège le texte et calcule la confiance moyenne

    Retourne :
        numero_page      : int
        texte_brut       : str   — texte extrait concatené
        lignes           : list  — liste des lignes avec scores
        score_confiance  : float — confiance moyenne
        nb_mots          : int
        qualite_image    : dict
        langue_detectee  : str
    """
    qualite = verifier_qualite_image(image_np)

    if not qualite["acceptable"]:
        logger.warning(
            f"Page {numero_page} : qualité image faible "
            f"(score={qualite['score_qualite']}, "
            f"netteté={qualite['nettete']:.0f})"
        )

    image_traitee = preprocesser_image(image_np)

    ocr     = get_ocr()
    resultat = ocr.ocr(image_traitee, cls=True)

    lignes        = []
    scores        = []
    texte_complet = []

    if resultat and resultat[0]:
        for ligne in resultat[0]:
            if ligne and len(ligne) >= 2:
                texte     = ligne[1][0]
                confiance = float(ligne[1][1])
                lignes.append({"texte": texte, "confiance": round(confiance, 3)})
                scores.append(confiance)
                texte_complet.append(texte)

    score_moyen = round(sum(scores) / len(scores), 3) if scores else 0.0
    texte_brut  = "\n".join(texte_complet)

    return {
        "numero_page":     numero_page,
        "texte_brut":      texte_brut,
        "lignes":          lignes,
        "score_confiance": score_moyen,
        "nb_mots":         len(texte_brut.split()),
        "qualite_image":   qualite,
        "langue_detectee": OCR_LANGUAGE
    }