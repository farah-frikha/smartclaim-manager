# api/dashboard/routes.py
"""
Endpoints du domaine dashboard.
Statistiques, performances pipeline et journal d'audit.
Réservé aux GESTIONNAIRE et ADMIN.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import sqlite3
from fastapi import APIRouter, Depends, Query
from api.dependencies import exiger_roles
from engines.database import get_connection

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/stats",
    summary="Statistiques globales",
    description="Vue d'ensemble des dossiers traités"
)
def statistiques_globales(
    utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))
):
    """
    Retourne les indicateurs clés du système :
    total dossiers, taux d'acceptation, score moyen,
    activité des 7 derniers jours.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        stats = conn.execute("""
            SELECT
                COUNT(*)                                        AS total,
                SUM(CASE WHEN statut_global = 'accepte'
                         THEN 1 ELSE 0 END)                    AS acceptes,
                SUM(CASE WHEN statut_global = 'refuse'
                         THEN 1 ELSE 0 END)                    AS refuses,
                SUM(CASE WHEN statut_global = 'complement_requis'
                         THEN 1 ELSE 0 END)                    AS complement,
                SUM(CASE WHEN statut_global NOT IN
                    ('accepte', 'refuse', 'complement_requis')
                         THEN 1 ELSE 0 END)                    AS en_cours
            FROM dossiers_sinistres
        """).fetchone()

        score_moy = conn.execute("""
            SELECT ROUND(AVG(score_final), 1) AS score_moyen
            FROM scores
        """).fetchone()

        activite = conn.execute("""
            SELECT DATE(created_at) AS jour, COUNT(*) AS nb
            FROM dossiers_sinistres
            WHERE created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY jour
        """).fetchall()

        total = stats["total"] or 0
        return {
            "total_dossiers":    total,
            "acceptes":          stats["acceptes"]   or 0,
            "refuses":           stats["refuses"]    or 0,
            "complement_requis": stats["complement"] or 0,
            "en_cours":          stats["en_cours"]   or 0,
            "taux_acceptation":  round(
                (stats["acceptes"] or 0) / total * 100, 1
            ) if total > 0 else 0.0,
            "score_moyen":       score_moy["score_moyen"],
            "activite_7_jours":  [dict(r) for r in activite]
        }
    finally:
        conn.close()


@router.get(
    "/audit",
    summary="Journal d'audit complet",
    description="Historique de toutes les actions du système"
)
def journal_audit(
    limite:      int  = Query(100, description="Nombre d'entrées à retourner"),
    utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))
):
    """
    Retourne le journal d'audit.
    Chaque action de chaque agent est tracée : capture, extraction,
    validation, scoring, décision, corrections manuelles.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        logs = conn.execute("""
            SELECT
                a.audit_id,
                a.dossier_id,
                d.reference_dossier,
                a.agent_nom,
                a.action,
                a.details,
                a.date_action
            FROM audit_logs a
            LEFT JOIN dossiers_sinistres d
                   ON a.dossier_id = d.dossier_id
            ORDER BY a.date_action DESC
            LIMIT ?
        """, (limite,)).fetchall()
        return [dict(r) for r in logs]
    finally:
        conn.close()


@router.get(
    "/performances",
    summary="Métriques de performance pipeline",
    description="Analyse les performances du pipeline IA"
)
def performances_pipeline(
    utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))
):
    """
    Retourne les métriques de performance :
    répartition des décisions, escalades humaines,
    distribution des scores par niveau de risque.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        decisions = conn.execute("""
            SELECT decision, COUNT(*) AS nb
            FROM decisions
            GROUP BY decision
        """).fetchall()

        escalades = conn.execute("""
            SELECT COUNT(*) AS nb
            FROM decisions
            WHERE necessite_validation_humaine = 1
        """).fetchone()

        scores_par_niveau = conn.execute("""
            SELECT
                CASE
                    WHEN score_final >= 70 THEN 'FAIBLE'
                    WHEN score_final >= 40 THEN 'MOYEN'
                    ELSE 'ELEVE'
                END                           AS niveau_risque,
                COUNT(*)                      AS nb_dossiers,
                ROUND(AVG(score_final), 1)    AS score_moyen
            FROM scores
            GROUP BY niveau_risque
        """).fetchall()

        return {
            "decisions":          [dict(r) for r in decisions],
            "escalades_humaines": escalades["nb"] if escalades else 0,
            "scores_par_niveau":  [dict(r) for r in scores_par_niveau]
        }
    finally:
        conn.close()