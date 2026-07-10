# engines/database/crud_utilisateurs.py
"""
CRUD pour la table utilisateurs.
Responsabilité unique : gestion des comptes et de l'authentification.
Ce module est utilisé uniquement par la couche API (api/auth/).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import sqlite3
from loguru import logger

from engines.database.connection import get_connection


def creer_utilisateur(email: str, mot_de_passe_hash: str,
                       role: str, nom_complet: str,
                       employe_id: int = None) -> dict:
    """
    Crée un nouvel utilisateur.
    Le mot de passe doit être hashé AVANT d'appeler cette fonction.
    Retourne {succes, utilisateur_id, message}.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO utilisateurs (
                email, mot_de_passe_hash, role,
                nom_complet, employe_id
            ) VALUES (?, ?, ?, ?, ?)
        """, (email, mot_de_passe_hash, role, nom_complet, employe_id))
        conn.commit()

        utilisateur_id = cursor.lastrowid
        logger.success(
            f"Utilisateur créé — id={utilisateur_id}, "
            f"email={email}, role={role}"
        )
        return {
            "succes": True,
            "utilisateur_id": utilisateur_id,
            "message": "Utilisateur créé avec succès"
        }

    except sqlite3.IntegrityError:
        logger.warning(f"Email déjà utilisé : {email}")
        return {
            "succes": False,
            "utilisateur_id": None,
            "message": "Cet email est déjà utilisé"
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur creer_utilisateur : {e}")
        return {"succes": False, "utilisateur_id": None, "message": str(e)}
    finally:
        conn.close()


def obtenir_utilisateur_par_email(email: str) -> dict:
    """Récupère un utilisateur actif par son email. Retourne None si absent."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("""
            SELECT * FROM utilisateurs
            WHERE email = ? AND actif = 1
        """, (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def obtenir_utilisateur_par_id(utilisateur_id: int) -> dict:
    """Récupère un utilisateur par son id. Retourne None si absent."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("""
            SELECT * FROM utilisateurs
            WHERE utilisateur_id = ?
        """, (utilisateur_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def mettre_a_jour_derniere_connexion(utilisateur_id: int) -> None:
    """Met à jour l'horodatage de dernière connexion après login."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE utilisateurs
            SET derniere_connexion = datetime('now')
            WHERE utilisateur_id = ?
        """, (utilisateur_id,))
        conn.commit()
    finally:
        conn.close()


def lister_utilisateurs(role: str = None) -> list:
    """
    Liste les utilisateurs avec filtre optionnel par rôle.
    Utilisé par le Portail Responsable — gestion des utilisateurs.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        if role:
            rows = conn.execute("""
                SELECT utilisateur_id, email, role, nom_complet,
                       actif, derniere_connexion, created_at
                FROM utilisateurs
                WHERE role = ?
                ORDER BY created_at DESC
            """, (role,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT utilisateur_id, email, role, nom_complet,
                       actif, derniere_connexion, created_at
                FROM utilisateurs
                ORDER BY created_at DESC
            """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def desactiver_utilisateur(utilisateur_id: int) -> bool:
    """Désactive un utilisateur sans le supprimer (soft delete)."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE utilisateurs
            SET actif = 0, updated_at = datetime('now')
            WHERE utilisateur_id = ?
        """, (utilisateur_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Erreur desactiver_utilisateur : {e}")
        return False
    finally:
        conn.close()
def creer_employe_et_utilisateur(
    email: str,
    mot_de_passe_hash: str,
    nom_complet: str,
    numero_cnss: str,
    employeur_id: int = 1
) -> dict:
    """
    Crée un employé ET son compte utilisateur en une seule transaction.

    Utilisé quand role=EMPLOYE lors de l'inscription — garantit
    qu'un compte EMPLOYE a toujours un employe_id valide.
    """
    conn = get_connection()
    try:
        parties = nom_complet.strip().split(" ", 1)
        prenom  = parties[0]
        nom     = parties[1] if len(parties) > 1 else parties[0]

        cursor = conn.execute("""
            INSERT INTO employes (
                employeur_id, numero_cnss, nom, prenom
            ) VALUES (?, ?, ?, ?)
        """, (employeur_id, numero_cnss, nom, prenom))
        employe_id = cursor.lastrowid

        cursor = conn.execute("""
            INSERT INTO utilisateurs (
                email, mot_de_passe_hash, role,
                nom_complet, employe_id
            ) VALUES (?, ?, 'EMPLOYE', ?, ?)
        """, (email, mot_de_passe_hash, nom_complet, employe_id))
        utilisateur_id = cursor.lastrowid

        conn.commit()
        logger.success(
            f"Employé + utilisateur créés — "
            f"employe_id={employe_id}, utilisateur_id={utilisateur_id}"
        )

        return {
            "succes":         True,
            "utilisateur_id": utilisateur_id,
            "employe_id":     employe_id,
            "message":        "Compte employé créé avec succès"
        }

    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Erreur intégrité : {e}")
        return {
            "succes": False, "utilisateur_id": None, "employe_id": None,
            "message": "Cet email ou ce numéro CNSS est déjà utilisé"
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur creer_employe_et_utilisateur : {e}")
        return {
            "succes": False, "utilisateur_id": None, "employe_id": None,
            "message": str(e)
        }
    finally:
        conn.close()