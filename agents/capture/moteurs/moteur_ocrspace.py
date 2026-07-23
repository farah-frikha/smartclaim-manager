# agents/capture/moteurs/moteur_ocrspace.py
"""
Implémentation MoteurOCR pour l'API OCR.space.
Moteur cloud — meilleure reconnaissance de l'arabe selon le benchmark.

⚠️ Contrainte de souveraineté : ce moteur envoie les images à un
service tiers. À réserver au développement ou à documenter
explicitement en production (voir documentation technique).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import io
import numpy as np
import cv2
import requests
from loguru import logger

from config import OCRSPACE_API_KEY, OCRSPACE_ENGINE, OCRSPACE_LANGUAGE
from agents.capture.moteurs.base import MoteurOCR

OCRSPACE_URL = "https://api.ocr.space/parse/image"


class MoteurOcrSpace(MoteurOCR):
    """Moteur OCR cloud basé sur l'API OCR.space."""

    @property
    def nom(self) -> str:
        return "ocrspace"

    def lire_page(self, image_np: np.ndarray, numero_page: int) -> dict:
        # Redimensionner si trop grande (limite OCR.space free : 1.5 Mo)
        image_np = self._reduire_si_besoin(image_np)

        # Encoder en JPEG compressé pour l'envoi
        succes, buffer = cv2.imencode(
            ".jpg", image_np, [cv2.IMWRITE_JPEG_QUALITY, 85]
        )
        if not succes:
            logger.error(f"Page {numero_page} : échec encodage image")
            return self._resultat_vide(numero_page)

        fichier = io.BytesIO(buffer.tobytes())
        taille_ko = len(buffer.tobytes()) / 1024
        logger.info(f"Page {numero_page} : taille envoyée = {taille_ko:.0f} Ko")

        try:
            reponse = requests.post(
                OCRSPACE_URL,
                files={"filename": ("page.jpg", fichier, "image/jpeg")},
                data={
                    "apikey":            OCRSPACE_API_KEY,
                    "language":          OCRSPACE_LANGUAGE,
                    "OCREngine":         OCRSPACE_ENGINE,
                    "isOverlayRequired": False,
                    "scale":             True,
                    "detectOrientation": True,
                },
                timeout=60,
            )
            reponse.raise_for_status()
            donnees = reponse.json()

        except requests.RequestException as e:
            logger.error(f"Page {numero_page} : erreur API OCR.space — {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Réponse OCR.space : {e.response.text[:500]}")
            return self._resultat_vide(numero_page)

        # Vérifier les erreurs applicatives de l'API
        if donnees.get("IsErroredOnProcessing"):
            message = donnees.get("ErrorMessage", ["Erreur inconnue"])
            logger.error(f"Page {numero_page} : OCR.space a échoué — {message}")
            return self._resultat_vide(numero_page)

        resultats = donnees.get("ParsedResults", [])
        if not resultats:
            return self._resultat_vide(numero_page)

        texte_brut = resultats[0].get("ParsedText", "").strip()

        lignes = [
            {"texte": l, "confiance": None}
            for l in texte_brut.split("\n") if l.strip()
        ]

        score_confiance = 0.9 if texte_brut else 0.0

        return {
            "numero_page":     numero_page,
            "texte_brut":      texte_brut,
            "lignes":          lignes,
            "score_confiance": score_confiance,
            "nb_mots":         len(texte_brut.split()),
            "langue_detectee": OCRSPACE_LANGUAGE,
        }

    def _reduire_si_besoin(self, image_np, largeur_max=1600):
        """Réduit la largeur si l'image dépasse largeur_max (préserve le ratio)."""
        h, w = image_np.shape[:2]
        if w > largeur_max:
            ratio = largeur_max / w
            image_np = cv2.resize(image_np, (largeur_max, int(h * ratio)),
                                  interpolation=cv2.INTER_AREA)
            logger.info(f"Image réduite de {w}px à {largeur_max}px de large")
        return image_np

    def _resultat_vide(self, numero_page: int) -> dict:
        """Résultat par défaut en cas d'échec, au format normalisé."""
        return {
            "numero_page":     numero_page,
            "texte_brut":      "",
            "lignes":          [],
            "score_confiance": 0.0,
            "nb_mots":         0,
            "langue_detectee": OCRSPACE_LANGUAGE,
        }