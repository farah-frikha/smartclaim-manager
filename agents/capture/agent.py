# agents/capture/agent.py
"""
Point d'entrée de l'Agent Capture.
Détecte le format, route vers le bon handler,
enrichit le résultat avec le type de document.
C'est le seul fichier importé par coordinateur.py.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from pathlib import Path
from loguru import logger

from config import OCR_CONFIDENCE_THRESHOLD
from agents.capture.pdf_handler   import traiter_pdf
from agents.capture.image_handler import traiter_image, EXTENSIONS_IMAGE
from agents.capture.file_utils    import detecter_type_document


def executer_capture(chemin_fichier: str) -> dict:
    """
    Point d'entrée public de l'Agent Capture.

    Reçoit un chemin de fichier, détecte le format,
    route vers traiter_pdf() ou traiter_image(),
    enrichit le résultat avec le type de document détecté.

    Retourne :
        statut          : succes / erreur
        type_document   : formulaire_sinistre, contrat, etc.
        texte_complet   : texte brut extrait par OCR
        score_confiance : qualité OCR globale (0 à 1)
        confiance_ok    : bool — confiance >= seuil config
        nb_pages        : nombre de pages traitées
        nb_mots_total   : nombre de mots extraits
        pages           : détail page par page
        metadata        : hash, taille, date, chemin
    """
    chemin    = Path(chemin_fichier)
    extension = chemin.suffix.lower()

    # Routage selon le format
    if extension == ".pdf":
        resultat = traiter_pdf(chemin_fichier)
    elif extension in EXTENSIONS_IMAGE:
        resultat = traiter_image(chemin_fichier)
    else:
        logger.error(f"Format non supporté : {extension}")
        return {
            "statut":  "erreur",
            "message": f"Format '{extension}' non supporté. "
                       f"Formats acceptés : PDF, JPG, PNG, TIFF"
        }

    # Enrichissement si succès
    if resultat["statut"] == "succes":
        resultat["type_document"] = detecter_type_document(chemin.name)
        resultat["confiance_ok"]  = (
            resultat["score_confiance"] >= OCR_CONFIDENCE_THRESHOLD
        )

        if not resultat["confiance_ok"]:
            logger.warning(
                f"Confiance OCR faible : {resultat['score_confiance']} "
                f"< seuil {OCR_CONFIDENCE_THRESHOLD}. "
                f"Vérification manuelle recommandée."
            )

    return resultat