# engines/database/crud_reclamations.py
"""
Opérations sur les réclamations déposées par les employés.
"""
import sqlite3
from engines.database.connection import get_connection


def creer_reclamation(dossier_id: int, utilisateur_id: int, message: str) -> dict:
    """Enregistre une réclamation d'un employé sur l'un de ses dossiers."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO reclamations (dossier_id, utilisateur_id, message)
            VALUES (?, ?, ?)
        """, (dossier_id, utilisateur_id, message))
        conn.commit()
        return {"succes": True, "reclamation_id": cursor.lastrowid}
    except sqlite3.IntegrityError as e:
        return {"succes": False, "message": str(e)}
    finally:
        conn.close()


def lister_reclamations(statut: str = None) -> list:
    """Liste toutes les réclamations, avec filtre optionnel sur le statut."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        requete = """
            SELECT r.*, d.reference_dossier, u.nom_complet AS auteur
            FROM reclamations r
            JOIN dossiers_sinistres d ON d.dossier_id = r.dossier_id
            JOIN utilisateurs u ON u.utilisateur_id = r.utilisateur_id
        """
        params = []
        if statut:
            requete += " WHERE r.statut = ?"
            params.append(statut)
        requete += " ORDER BY r.created_at DESC"

        rows = conn.execute(requete, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def lister_reclamations_utilisateur(utilisateur_id: int) -> list:
    """Liste les réclamations déposées par un utilisateur donné."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT r.*, d.reference_dossier
            FROM reclamations r
            JOIN dossiers_sinistres d ON d.dossier_id = r.dossier_id
            WHERE r.utilisateur_id = ?
            ORDER BY r.created_at DESC
        """, (utilisateur_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def repondre_reclamation(reclamation_id: int, reponse: str,
                         repondu_par: int) -> dict:
    """Enregistre la réponse d'un gestionnaire et clôt la réclamation."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            UPDATE reclamations
            SET reponse = ?, repondu_par = ?, statut = 'traitee',
                date_reponse = datetime('now')
            WHERE reclamation_id = ?
        """, (reponse, repondu_par, reclamation_id))
        conn.commit()
        if cursor.rowcount == 0:
            return {"succes": False, "message": "Réclamation introuvable"}
        return {"succes": True, "message": "Réponse enregistrée"}
    finally:
        conn.close()