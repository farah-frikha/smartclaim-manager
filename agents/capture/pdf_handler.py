# agents/capture/pdf_handler.py
"""
Traitement des fichiers PDF via PyMuPDF.
Ce fichier est le seul à dépendre de fitz (PyMuPDF).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import time
import numpy as np
from pathlib import Path
from datetime import datetime

import fitz
from loguru import logger

from config import OCR_MIN_DPI
from agents.capture.ocr       import ocr_page
from agents.capture.file_utils import calculer_hash


def traiter_pdf(chemin_pdf: str, dpi: int = None) -> dict:
    """
    Traite un document PDF page par page.

    Pipeline :
      1. Ouvre le PDF avec PyMuPDF
      2. Convertit chaque page en image numpy (DPI configurable)
      3. Applique ocr_page() sur chaque image
      4. Concatène les textes avec séparateurs de pages

    Paramètres :
        chemin_pdf : chemin absolu vers le fichier PDF
        dpi        : résolution d'extraction (défaut : OCR_MIN_DPI=300)

    Retourne le résultat standardisé ou {"statut": "erreur"}.
    """
    dpi    = dpi or OCR_MIN_DPI
    chemin = Path(chemin_pdf)

    if not chemin.exists():
        logger.error(f"Fichier introuvable : {chemin_pdf}")
        return {"statut": "erreur", "message": f"Fichier introuvable : {chemin_pdf}"}

    if chemin.suffix.lower() != ".pdf":
        logger.error(f"Format non supporté : {chemin.suffix}")
        return {"statut": "erreur", "message": "Seuls les fichiers PDF sont acceptés"}

    logger.info(f"Traitement PDF : {chemin.name}")
    t_debut = time.perf_counter()

    try:
        doc      = fitz.open(chemin_pdf)
        nb_pages = len(doc)
        pages_resultats = []
        tous_textes     = []
        tous_scores     = []

        for numero_page in range(nb_pages):
            logger.info(f"  OCR page {numero_page + 1}/{nb_pages}...")

            page    = doc[numero_page]
            matrice = fitz.Matrix(dpi / 72, dpi / 72)
            pixmap  = page.get_pixmap(matrix=matrice, colorspace=fitz.csRGB)

            image_np = np.frombuffer(pixmap.samples, dtype=np.uint8)
            image_np = image_np.reshape(pixmap.height, pixmap.width, 3)

            resultat_page = ocr_page(image_np, numero_page + 1)
            pages_resultats.append(resultat_page)

            if resultat_page["texte_brut"]:
                tous_textes.append(resultat_page["texte_brut"])
            tous_scores.append(resultat_page["score_confiance"])

        doc.close()

        score_global  = round(sum(tous_scores) / len(tous_scores), 3) \
            if tous_scores else 0.0
        texte_complet = "\n\n--- PAGE ---\n\n".join(tous_textes)
        duree_ms      = round((time.perf_counter() - t_debut) * 1000, 1)

        logger.success(
            f"PDF traité : {nb_pages} page(s), "
            f"{len(texte_complet.split())} mots, "
            f"confiance={score_global}, durée={duree_ms}ms"
        )

        return {
            "statut":          "succes",
            "nom_fichier":     chemin.name,
            "nb_pages":        nb_pages,
            "pages":           pages_resultats,
            "texte_complet":   texte_complet,
            "score_confiance": score_global,
            "nb_mots_total":   len(texte_complet.split()),
            "duree_ms":        duree_ms,
            "metadata": {
                "chemin":          str(chemin_pdf),
                "taille_ko":       round(chemin.stat().st_size / 1024, 1),
                "hash_sha256":     calculer_hash(chemin_pdf),
                "dpi_utilise":     dpi,
                "date_traitement": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Erreur traitement PDF : {e}")
        return {"statut": "erreur", "message": str(e)}