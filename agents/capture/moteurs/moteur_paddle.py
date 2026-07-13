# agents/capture/moteurs/moteur_paddle.py
"""
Implémentation MoteurOCR pour PaddleOCR.
Encapsule votre logique PaddleOCR existante dans le contrat commun.
Moteur local — respecte la contrainte on-premise.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np
from paddleocr import PaddleOCR
from loguru import logger

from config import OCR_LANGUAGE
from agents.capture.preprocessing import preprocesser_image, verifier_qualite_image
from agents.capture.moteurs.base import MoteurOCR


class MoteurPaddle(MoteurOCR):
    """Moteur OCR local basé sur PaddleOCR."""

    def __init__(self):
        # Singleton interne : le modèle n'est chargé qu'une fois
        self._ocr = None

    @property
    def nom(self) -> str:
        return "paddle"

    def _get_ocr(self) -> PaddleOCR:
        """Charge le modèle PaddleOCR une seule fois (lazy loading)."""
        if self._ocr is None:
            logger.info("Chargement du modèle PaddleOCR...")
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=OCR_LANGUAGE,
                show_log=False
            )
            logger.success("Modèle PaddleOCR chargé")
        return self._ocr

    def lire_page(self, image_np: np.ndarray, numero_page: int) -> dict:
        qualite = verifier_qualite_image(image_np)
        if not qualite["acceptable"]:
            logger.warning(
                f"Page {numero_page} : qualité image faible "
                f"(score={qualite['score_qualite']})"
            )

        image_traitee = preprocesser_image(image_np)
        resultat = self._get_ocr().ocr(image_traitee, cls=True)

        lignes, scores, texte_complet = [], [], []
        if resultat and resultat[0]:
            for ligne in resultat[0]:
                if ligne and len(ligne) >= 2:
                    texte = ligne[1][0]
                    confiance = float(ligne[1][1])
                    lignes.append({"texte": texte, "confiance": round(confiance, 3)})
                    scores.append(confiance)
                    texte_complet.append(texte)

        score_moyen = round(sum(scores) / len(scores), 3) if scores else 0.0
        texte_brut = "\n".join(texte_complet)

        return {
            "numero_page":     numero_page,
            "texte_brut":      texte_brut,
            "lignes":          lignes,
            "score_confiance": score_moyen,
            "nb_mots":         len(texte_brut.split()),
            "qualite_image":   qualite,
            "langue_detectee": OCR_LANGUAGE,
        }