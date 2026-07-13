# agents/capture/ocr.py
"""
Point d'entrée OCR du pipeline.
Délègue au moteur configuré via la factory.
Le pipeline appelle ocr_page() sans savoir quel moteur est derrière —
c'est tout l'intérêt de l'abstraction.
"""
import numpy as np
from agents.capture.moteurs.factory import obtenir_moteur_ocr


def ocr_page(image_np: np.ndarray, numero_page: int) -> dict:
    """
    Applique l'OCR sur une image de page via le moteur configuré.
    Conserve la même signature qu'avant : aucun autre fichier
    du pipeline n'a besoin d'être modifié.
    """
    moteur = obtenir_moteur_ocr()
    return moteur.lire_page(image_np, numero_page)