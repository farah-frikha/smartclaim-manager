# agents/capture/image_handler.py
"""
Traitement des fichiers image (JPG, PNG, TIFF) via OpenCV.
Retourne le même format que pdf_handler pour uniformité du pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import time
from pathlib import Path
from datetime import datetime

import cv2
from loguru import logger

from agents.capture.ocr        import ocr_page
from agents.capture.file_utils import calculer_hash

EXTENSIONS_IMAGE = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}


def traiter_image(chemin_image: str) -> dict:
    """
    Traite une image unique.
    Retourne le même format que traiter_pdf() pour
    que executer_capture() puisse les traiter uniformément.
    """
    chemin = Path(chemin_image)

    if not chemin.exists():
        return {"statut": "erreur", "message": f"Fichier introuvable : {chemin_image}"}

    if chemin.suffix.lower() not in EXTENSIONS_IMAGE:
        return {"statut": "erreur", "message": f"Format non supporté : {chemin.suffix}"}

    logger.info(f"Traitement image : {chemin.name}")
    t_debut = time.perf_counter()

    try:
        image_np = cv2.imread(chemin_image)
        if image_np is None:
            return {"statut": "erreur", "message": "Impossible de lire l'image"}

        resultat_page = ocr_page(image_np, numero_page=1)
        duree_ms      = round((time.perf_counter() - t_debut) * 1000, 1)

        logger.success(
            f"Image traitée : {len(resultat_page['texte_brut'].split())} mots, "
            f"confiance={resultat_page['score_confiance']}, "
            f"durée={duree_ms}ms"
        )

        return {
            "statut":          "succes",
            "nom_fichier":     chemin.name,
            "nb_pages":        1,
            "pages":           [resultat_page],
            "texte_complet":   resultat_page["texte_brut"],
            "score_confiance": resultat_page["score_confiance"],
            "nb_mots_total":   len(resultat_page["texte_brut"].split()),
            "duree_ms":        duree_ms,
            "metadata": {
                "chemin":          str(chemin_image),
                "taille_ko":       round(chemin.stat().st_size / 1024, 1),
                "hash_sha256":     calculer_hash(chemin_image),
                "date_traitement": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Erreur traitement image : {e}")
        return {"statut": "erreur", "message": str(e)}