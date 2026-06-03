# agents/capture.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
import time
from pathlib import Path
from datetime import datetime

import fitz          # PyMuPDF
import cv2
import numpy as np
from paddleocr import PaddleOCR
from loguru import logger

from config import (
    UPLOADS_DIR, OCR_LANGUAGE,
    OCR_MIN_DPI, OCR_CONFIDENCE_THRESHOLD
)

# ────────────────────────────────────────────────────────────
# SECTION 1 — INITIALISATION OCR 
# ────────────────────────────────────────────────────────────

_ocr_instance = None

def get_ocr() -> PaddleOCR:
    """
    Retourne l'instance PaddleOCR (singleton).
    Le modèle est chargé une seule fois en mémoire.
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


# ────────────────────────────────────────────────────────────
# SECTION 2 — UTILITAIRES FICHIER
# ────────────────────────────────────────────────────────────

def calculer_hash(chemin_fichier: str) -> str:
    """
    Calcule le hash SHA-256 d'un fichier.
    Utilisé pour détecter les doublons.
    """
    sha256 = hashlib.sha256()
    with open(chemin_fichier, "rb") as f:
        for bloc in iter(lambda: f.read(8192), b""):
            sha256.update(bloc)
    return sha256.hexdigest()


def detecter_type_document(nom_fichier: str) -> str:
    """
    Détecte le type de document à partir du nom de fichier.
    Retourne un code parmi les types définis dans la BDD.
    """
    nom = nom_fichier.lower()
    if any(mot in nom for mot in ["formulaire", "sinistre", "declaration"]):
        return "formulaire_sinistre"
    if any(mot in nom for mot in ["attestation", "assurance"]):
        return "attestation"
    if any(mot in nom for mot in ["contrat", "police", "conditions"]):
        return "contrat"
    if any(mot in nom for mot in ["certificat", "medical", "arret"]):
        return "certificat_medical"
    if any(mot in nom for mot in ["facture", "recu", "note"]):
        return "facture"
    if any(mot in nom for mot in ["identite", "cin", "passeport"]):
        return "piece_identite"
    if any(mot in nom for mot in ["deces", "acte"]):
        return "acte_deces"
    return "autre"


# ────────────────────────────────────────────────────────────
# SECTION 3 — PREPROCESSING IMAGE
# ────────────────────────────────────────────────────────────

def preprocesser_image(image_np: np.ndarray) -> np.ndarray:
    """
    Applique le preprocessing OpenCV pour améliorer la qualité OCR.

    Étapes :
      1. Conversion en niveaux de gris
      2. Débruitage gaussien
      3. Binarisation adaptative (Otsu)
      4. Légère dilatation pour épaissir les caractères
    """
    # Conversion niveaux de gris
    if len(image_np.shape) == 3:
        gris = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    else:
        gris = image_np

    # Débruitage
    debruite = cv2.GaussianBlur(gris, (1, 1), 0)

    # Binarisation Otsu
    _, binaire = cv2.threshold(
        debruite, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binaire


def verifier_qualite_image(image_np: np.ndarray) -> dict:
    """
    Évalue la qualité d'une image avant OCR.
    Retourne un score de qualité et des indicateurs.
    """
    gris = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY) \
        if len(image_np.shape) == 3 else image_np

    # Netteté (variance du Laplacien)
    nettete = cv2.Laplacian(gris, cv2.CV_64F).var()

    # Luminosité moyenne
    luminosite = np.mean(gris)

    # Évaluation
    ok_nettete   = nettete > 100
    ok_luminosite = 50 < luminosite < 220

    score_qualite = (
        (0.5 if ok_nettete   else 0.0) +
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


# ────────────────────────────────────────────────────────────
# SECTION 4 — EXTRACTION OCR PAR PAGE
# ────────────────────────────────────────────────────────────

def ocr_page(image_np: np.ndarray, numero_page: int) -> dict:
    """
    Applique l'OCR sur une image de page.

    Retourne un dict contenant :
        numero_page      : int
        texte_brut       : str  — texte extrait concatené
        lignes           : list — liste des lignes avec scores
        score_confiance  : float — confiance moyenne
        nb_mots          : int
        qualite_image    : dict
    """
    qualite = verifier_qualite_image(image_np)

    if not qualite["acceptable"]:
        logger.warning(
            f"Page {numero_page} : qualité image faible "
            f"(score={qualite['score_qualite']}, "
            f"netteté={qualite['nettete']:.0f})"
        )

    # Preprocessing
    image_traitee = preprocesser_image(image_np)

    # OCR
    ocr = get_ocr()
    resultat = ocr.ocr(image_traitee, cls=True)

    # Extraction du texte et des scores
    lignes        = []
    scores        = []
    texte_complet = []

    if resultat and resultat[0]:
        for ligne in resultat[0]:
            if ligne and len(ligne) >= 2:
                texte  = ligne[1][0]
                confiance = float(ligne[1][1])
                lignes.append({
                    "texte":     texte,
                    "confiance": round(confiance, 3)
                })
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


# ────────────────────────────────────────────────────────────
# SECTION 5 — TRAITEMENT PDF
# ────────────────────────────────────────────────────────────

def traiter_pdf(chemin_pdf: str, dpi: int = None) -> dict:
    """
    Traite un document PDF page par page.

    Paramètres :
        chemin_pdf : chemin vers le fichier PDF
        dpi        : résolution d'extraction (défaut : OCR_MIN_DPI)

    Retourne un dict contenant :
        statut           : str  — succes / erreur
        nb_pages         : int
        pages            : list — résultats OCR par page
        texte_complet    : str  — tout le texte concatené
        score_confiance  : float — confiance moyenne globale
        metadata         : dict — métadonnées du PDF
    """
    dpi = dpi or OCR_MIN_DPI
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

            page = doc[numero_page]

            # Conversion PDF → image numpy
            matrice = fitz.Matrix(dpi / 72, dpi / 72)
            pixmap  = page.get_pixmap(matrix=matrice, colorspace=fitz.csRGB)
            image_np = np.frombuffer(pixmap.samples, dtype=np.uint8)
            image_np = image_np.reshape(pixmap.height, pixmap.width, 3)

            # OCR sur cette page
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
            f"confiance={score_global}, "
            f"durée={duree_ms}ms"
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
                "chemin":     str(chemin_pdf),
                "taille_ko":  round(chemin.stat().st_size / 1024, 1),
                "hash_sha256": calculer_hash(chemin_pdf),
                "dpi_utilise": dpi,
                "date_traitement": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Erreur traitement PDF : {e}")
        return {"statut": "erreur", "message": str(e)}


# ────────────────────────────────────────────────────────────
# SECTION 6 — TRAITEMENT IMAGE SEULE
# ────────────────────────────────────────────────────────────

def traiter_image(chemin_image: str) -> dict:
    """
    Traite une image unique (JPG, PNG, TIFF).
    Retourne le même format que traiter_pdf pour uniformité.
    """
    chemin = Path(chemin_image)
    extensions_ok = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}

    if not chemin.exists():
        return {"statut": "erreur", "message": f"Fichier introuvable : {chemin_image}"}

    if chemin.suffix.lower() not in extensions_ok:
        return {"statut": "erreur", "message": f"Format non supporté : {chemin.suffix}"}

    logger.info(f"Traitement image : {chemin.name}")
    t_debut = time.perf_counter()

    try:
        image_np = cv2.imread(chemin_image)
        if image_np is None:
            return {"statut": "erreur", "message": "Impossible de lire l'image"}

        resultat_page = ocr_page(image_np, numero_page=1)
        duree_ms = round((time.perf_counter() - t_debut) * 1000, 1)

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
                "chemin":      str(chemin_image),
                "taille_ko":   round(chemin.stat().st_size / 1024, 1),
                "hash_sha256": calculer_hash(chemin_image),
                "date_traitement": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Erreur traitement image : {e}")
        return {"statut": "erreur", "message": str(e)}


# ────────────────────────────────────────────────────────────
# SECTION 7 — POINT D'ENTRÉE PRINCIPAL
# ────────────────────────────────────────────────────────────

def executer_capture(chemin_fichier: str) -> dict:
    """
    Point d'entrée de l'Agent Capture.
    Détecte automatiquement le type de fichier et applique
    le traitement approprié (PDF ou image).

    Paramètres :
        chemin_fichier : chemin absolu vers le document

    Retourne un dict standardisé contenant :
        statut           : succes / erreur
        type_document    : type détecté (formulaire_sinistre, etc.)
        texte_complet    : texte brut extrait
        score_confiance  : qualité OCR globale (0-1)
        nb_pages         : nombre de pages
        nb_mots_total    : nombre de mots extraits
        pages            : détail page par page
        metadata         : hash, taille, date, chemin
        confiance_ok     : bool — confiance >= seuil config
    """
    chemin = Path(chemin_fichier)
    extension = chemin.suffix.lower()

    # Routage selon le format
    if extension == ".pdf":
        resultat = traiter_pdf(chemin_fichier)
    elif extension in {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}:
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


# ────────────────────────────────────────────────────────────
# SECTION 8 — TEST
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    # ── Créer un PDF de test minimal si aucun disponible ────
    pdf_test = "data/Document Test Assurance Tunisie Ocr.pdf"

    if not Path(pdf_test).exists():
        logger.info("Création d'un PDF de test...")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 100),
            "FORMULAIRE DE DECLARATION DE SINISTRE\n\n"
            "Nom de l'assuré : Mohamed Ben Salah\n"
            "Numéro CNSS : 123456789\n"
            "Numéro de contrat : STAR-AUTO-2024-00847\n"
            "Date du sinistre : 15/03/2024\n"
            "Type de sinistre : Accident automobile\n"
            "Montant réclamé : 2500,000 TND\n\n"
            "Description : Collision avec un autre véhicule\n"
            "au carrefour de l'Avenue Habib Bourguiba.\n"
            "Dommages matériels uniquement.\n",
            fontsize=11,
            fontname="helv"
        )
        doc.save(pdf_test)
        doc.close()
        logger.info(f"PDF de test créé : {pdf_test}")

    # ── Test de l'agent ──────────────────────────────────────
    print("\n" + "═" * 60)
    print("    TEST — Agent Capture")
    print("═" * 60)

    resultat = executer_capture(pdf_test)

    if resultat["statut"] == "succes":
        print(f"\n Statut          : {resultat['statut'].upper()}")
        print(f" Type document   : {resultat['type_document']}")
        print(f" Pages           : {resultat['nb_pages']}")
        print(f"Mots extraits   : {resultat['nb_mots_total']}")
        print(f" Confiance OCR   : {resultat['score_confiance']}")
        print(f"Confiance OK    : {resultat['confiance_ok']}")
        print(f" Durée           : {resultat['duree_ms']}ms")
        print(f"Hash SHA-256    : {resultat['metadata']['hash_sha256'][:16]}...")
        print(f"\n Texte extrait :\n{'-' * 40}")
        print(resultat["texte_complet"][:500])
        if len(resultat["texte_complet"]) > 500:
            print(f" ({len(resultat['texte_complet'])} caractères au total)")
    else:
        print(f"\n Erreur : {resultat.get('message', 'Inconnue')}")

    print("\n" + "═" * 60)
    print("Résultat complet (structure JSON) :")
    print("═" * 60)
    resultat_affichage = {k: v for k, v in resultat.items() if k != "pages"}
    print(json.dumps(resultat_affichage, ensure_ascii=False, indent=2))