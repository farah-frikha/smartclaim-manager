# agents/capture/preprocessing.py
"""
Preprocessing d'images avec OpenCV avant l'OCR.
Fonctions pures — entrée numpy array, sortie numpy array.
Testables unitairement avec des images synthétiques.
"""
import numpy as np
import cv2


def preprocesser_image(image_np: np.ndarray) -> np.ndarray:
    """
    Applique le preprocessing OpenCV pour améliorer la qualité OCR.

    Étapes :
      1. Conversion en niveaux de gris
      2. Débruitage gaussien léger
      3. Binarisation adaptative Otsu
         (calcule automatiquement le seuil optimal)

    L'image résultante est en noir et blanc — format optimal
    pour PaddleOCR sur des documents texte.
    """
    if len(image_np.shape) == 3:
        gris = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    else:
        gris = image_np

    debruite = cv2.GaussianBlur(gris, (1, 1), 0)

    _, binaire = cv2.threshold(
        debruite, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binaire


def verifier_qualite_image(image_np: np.ndarray) -> dict:
    """
    Évalue la qualité d'une image avant OCR.

    Métriques calculées :
      - Netteté : variance du Laplacien (> 100 = net)
      - Luminosité : moyenne des pixels (50-220 = acceptable)

    Retourne :
        score_qualite : float — 0.0 à 1.0
        nettete       : float
        luminosite    : float
        ok_nettete    : bool
        ok_luminosite : bool
        acceptable    : bool — True si score >= 0.5
    """
    gris = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY) \
        if len(image_np.shape) == 3 else image_np

    nettete   = cv2.Laplacian(gris, cv2.CV_64F).var()
    luminosite = np.mean(gris)

    ok_nettete    = nettete > 100
    ok_luminosite = 50 < luminosite < 220

    score_qualite = (
        (0.5 if ok_nettete    else 0.0) +
        (0.5 if ok_luminosite else 0.0)
    )

    return {
        "score_qualite":  round(score_qualite, 2),
        "nettete":        round(float(nettete), 2),
        "luminosite":     round(float(luminosite), 2),
        "ok_nettete":     ok_nettete,
        "ok_luminosite":  ok_luminosite,
        "acceptable":     score_qualite >= 0.5
    }