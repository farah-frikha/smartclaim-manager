# engines/database/crud_documents.py
"""
CRUD pour les tables liées aux documents physiques.
Tables concernées : documents, pages_ocr, champs_extraits, erreurs_extraction.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from loguru import logger

from engines.database.connection import get_connection


def log_audit(conn: sqlite3.Connection, dossier_id: int,
              agent: str, action: str, details: dict = None) -> None:
    """
    Insère une ligne dans audit_logs.
    Appelée après chaque action significative pour la traçabilité CGA.
    Utilise la connexion existante — ne crée pas de nouvelle connexion.
    """
    conn.execute("""
        INSERT INTO audit_logs
            (dossier_id, agent_nom, action, details, date_action)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (
        dossier_id,
        agent,
        action,
        json.dumps(details, ensure_ascii=False) if details else None
    ))


def generer_reference_dossier() -> str:
    """
    Génère une référence unique pour un dossier.
    Format : SC-YYYY-HHMMSSRND (ex: SC-2026-163239857)
    """
    import random
    ts   = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"SC-{datetime.now().year}-{ts[-6:]}{rand}"


def sauvegarder_document(dossier_id: int,
                          resultat_capture: dict) -> int:
    """
    Insère le document reçu dans la table documents.
    Insère chaque page OCR dans pages_ocr.
    Retourne le document_id créé.
    Appelé par noeud_capture() dans coordinateur.py.
    """
    conn = get_connection()
    try:
        meta = resultat_capture.get("metadata", {})

        cursor = conn.execute("""
            INSERT INTO documents (
                dossier_id, nom_fichier_original, type_document,
                format_fichier, taille_octets, hash_sha256,
                chemin_stockage, date_reception, statut_traitement
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'ocr_termine')
        """, (
            dossier_id,
            resultat_capture.get("nom_fichier", "inconnu"),
            resultat_capture.get("type_document", "autre"),
            Path(resultat_capture.get("nom_fichier", "")).suffix.lstrip(".") or "pdf",
            int(meta.get("taille_ko", 0) * 1024),
            meta.get("hash_sha256"),
            meta.get("chemin", "")
        ))
        document_id = cursor.lastrowid

        for page in resultat_capture.get("pages", []):
            conn.execute("""
                INSERT INTO pages_ocr (
                    document_id, numero_page, texte_brut,
                    score_confiance_ocr, langue_detectee, date_traitement
                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                document_id,
                page.get("numero_page", 1),
                page.get("texte_brut", ""),
                page.get("score_confiance", 0.0),
                page.get("langue_detectee", "fr")
            ))

        log_audit(conn, dossier_id, "capture", "DOCUMENT_RECU", {
            "nom_fichier": resultat_capture.get("nom_fichier"),
            "nb_pages":    resultat_capture.get("nb_pages"),
            "confiance":   resultat_capture.get("score_confiance")
        })

        conn.commit()
        logger.success(f"Document sauvegardé — document_id={document_id}")
        return document_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_document : {e}")
        raise
    finally:
        conn.close()


def sauvegarder_extraction(dossier_id: int,
                            document_id: int,
                            resultat_extraction: dict) -> bool:
    """
    Insère chaque champ extrait dans champs_extraits.
    Insère les erreurs éventuelles dans erreurs_extraction.
    Appelé par noeud_extraction() dans coordinateur.py.
    """
    conn = get_connection()
    try:
        dossier    = resultat_extraction.get("dossier_extrait", {})
        completude = resultat_extraction.get("score_completude", 0)

        for nom_champ, valeur in dossier.items():
            conn.execute("""
                INSERT INTO champs_extraits (
                    dossier_id, document_id, nom_champ,
                    valeur_extraite, valeur_normalisee,
                    score_confiance_llm, date_extraction
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                dossier_id,
                document_id,
                nom_champ,
                str(valeur) if valeur is not None else None,
                str(valeur) if valeur is not None else None,
                completude
            ))

        for champ in resultat_extraction.get("champs_manquants", []):
            conn.execute("""
                INSERT INTO erreurs_extraction (
                    document_id, type_erreur,
                    champ_concerne, message_erreur
                ) VALUES (?, 'champ_manquant', ?, ?)
            """, (
                document_id,
                champ,
                f"Champ obligatoire '{champ}' absent du document"
            ))

        log_audit(conn, dossier_id, "extraction", "CHAMPS_EXTRAITS", {
            "completude":   completude,
            "nb_champs":    len(dossier),
            "manquants":    resultat_extraction.get("champs_manquants"),
            "llm_duree_ms": resultat_extraction.get("llm_duree_ms")
        })

        conn.commit()
        logger.success(
            f"Extraction sauvegardée — "
            f"{len(dossier)} champs, complétude={completude}"
        )
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_extraction : {e}")
        return False
    finally:
        conn.close()


def lire_dossier_complet(dossier_id: int) -> dict:
    """
    Lit toutes les données d'un dossier depuis la BDD.
    Agrège dossier + champs + validation + score + décision + audit.
    Utilisé par l'API GET /dossiers/{id} et le Portail Employé.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        dossier = conn.execute("""
            SELECT * FROM dossiers_sinistres
            WHERE dossier_id = ?
        """, (dossier_id,)).fetchone()

        if not dossier:
            return {"erreur": f"Dossier {dossier_id} introuvable"}

        champs = conn.execute("""
            SELECT nom_champ, valeur_normalisee
            FROM champs_extraits WHERE dossier_id = ?
        """, (dossier_id,)).fetchall()

        validation = conn.execute("""
            SELECT regle_id, resultat, message
            FROM resultats_validation WHERE dossier_id = ?
        """, (dossier_id,)).fetchall()

        score = conn.execute("""
            SELECT * FROM scores WHERE dossier_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (dossier_id,)).fetchone()

        decision = conn.execute("""
            SELECT * FROM decisions WHERE dossier_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (dossier_id,)).fetchone()

        logs = conn.execute("""
            SELECT agent_nom, action, details, date_action
            FROM audit_logs WHERE dossier_id = ?
            ORDER BY date_action ASC
        """, (dossier_id,)).fetchall()

        return {
            "dossier":    dict(dossier),
            "champs":     {r["nom_champ"]: r["valeur_normalisee"] for r in champs},
            "validation": [dict(r) for r in validation],
            "score":      dict(score) if score else None,
            "decision":   dict(decision) if decision else None,
            "audit_logs": [dict(r) for r in logs]
        }

    finally:
        conn.close()


def lister_dossiers(statut: str = None, domaine: str = None, limite: int = 100) -> list:
    """
    Liste les dossiers, avec filtres optionnels par statut et par domaine.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        requete = """
            SELECT dossier_id, reference_dossier,
                   statut_global, domaine, montant_reclame,
                   date_sinistre, created_at
            FROM dossiers_sinistres
        """
        conditions = []
        params = []

        if statut:
            conditions.append("statut_global = ?")
            params.append(statut)

        if domaine:
            conditions.append("domaine = ?")
            params.append(domaine)

        if conditions:
            requete += " WHERE " + " AND ".join(conditions)

        requete += " ORDER BY created_at DESC LIMIT ?"
        params.append(limite)

        rows = conn.execute(requete, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()        

def lister_dossiers_par_employe(employe_id: int,
                                 limite: int = 50) -> list:
    """
    Liste les dossiers d'un employé spécifique.
    Utilisé par le Portail Employé — historique personnel.
    Isolation stricte : un employé ne voit que ses dossiers.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT dossier_id, reference_dossier,
                   statut_global,domaine , montant_reclame,
                   date_sinistre, created_at
            FROM dossiers_sinistres
            WHERE employe_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (employe_id, limite)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()