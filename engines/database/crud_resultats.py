# engines/database/crud_resultats.py
"""
CRUD pour les résultats du pipeline IA.
Tables concernées : resultats_validation, scores, details_scoring,
                    decisions, flags_sinistres.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import json
import sqlite3
from loguru import logger

from engines.database.connection  import get_connection
from engines.database.crud_documents import log_audit


def sauvegarder_validation(dossier_id: int,
                            resultat_validation: dict) -> bool:
    """
    Insère chaque résultat de règle dans resultats_validation.
    Met à jour statut_global du dossier.
    Appelé par noeud_validation() dans coordinateur.py.
    """
    conn = get_connection()
    try:
        for detail in resultat_validation.get("details", []):
            conn.execute("""
                INSERT INTO resultats_validation (
                    dossier_id, regle_id, regle_description,
                    source_legale, resultat, message
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dossier_id,
                detail.get("id"),
                detail.get("description"),
                detail.get("source"),
                detail.get("resultat"),
                detail.get("message")
            ))

        nouveau_statut = "valide" if resultat_validation["valide"] else "invalide"
        conn.execute("""
            UPDATE dossiers_sinistres
            SET statut_global = ?, updated_at = datetime('now')
            WHERE dossier_id = ?
        """, (nouveau_statut, dossier_id))

        log_audit(conn, dossier_id, "validation", "VALIDATION_TERMINEE", {
            "valide":           resultat_validation["valide"],
            "nb_regles":        resultat_validation["nb_regles_total"],
            "echecs_bloquants": resultat_validation["echecs_bloquants"],
            "echecs_mineurs":   resultat_validation["echecs_mineurs"]
        })

        conn.commit()
        logger.success(
            f"Validation sauvegardée — "
            f"valide={resultat_validation['valide']}, "
            f"dossier_id={dossier_id}"
        )
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_validation : {e}")
        return False
    finally:
        conn.close()


def sauvegarder_scoring(dossier_id: int,
                         resultat_scoring: dict) -> int:
    """
    Insère le score dans scores.
    Insère chaque règle déclenchée dans details_scoring.
    Insère les flags dans flags_sinistres.
    Retourne le score_id créé.
    Appelé par noeud_scoring() dans coordinateur.py.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO scores (
                dossier_id, score_base, score_final,
                nb_regles_appliquees, nb_penalites,
                nb_bonus, flags_actifs
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dossier_id,
            resultat_scoring.get("score_base", 100),
            resultat_scoring.get("score", 0),
            len(resultat_scoring.get("details", [])),
            resultat_scoring.get("nb_penalites", 0),
            resultat_scoring.get("nb_bonus", 0),
            json.dumps(resultat_scoring.get("flags", []))
        ))
        score_id = cursor.lastrowid

        for detail in resultat_scoring.get("details", []):
            if detail.get("declenchee"):
                conn.execute("""
                    INSERT INTO details_scoring (
                        score_id, regle_id, condition_evaluee,
                        condition_remplie, delta_score,
                        flag_genere, justification
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    score_id,
                    detail.get("id"),
                    detail.get("condition"),
                    1 if detail.get("declenchee") else 0,
                    detail.get("delta_score", 0),
                    detail.get("flag_genere"),
                    detail.get("justification")
                ))

        for flag in resultat_scoring.get("flags", []):
            conn.execute("""
                INSERT INTO flags_sinistres (
                    dossier_id, code_flag,
                    niveau_severite, agent_source
                ) VALUES (?, ?, 'avertissement', 'scoring')
            """, (dossier_id, flag))

        log_audit(conn, dossier_id, "scoring", "SCORE_CALCULE", {
            "score_final":   resultat_scoring.get("score"),
            "niveau_risque": resultat_scoring.get("niveau_risque"),
            "flags":         resultat_scoring.get("flags")
        })

        conn.commit()
        logger.success(
            f"Scoring sauvegardé — "
            f"score={resultat_scoring.get('score')}, "
            f"score_id={score_id}"
        )
        return score_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_scoring : {e}")
        raise
    finally:
        conn.close()


def sauvegarder_decision(dossier_id: int,
                          score_id: int,
                          resultat_decision: dict) -> int:
    """
    Insère la décision dans decisions.
    Met à jour statut_global du dossier avec la décision finale.
    Retourne le decision_id créé.
    Appelé par noeud_decision() dans coordinateur.py.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO decisions (
                dossier_id, score_id, decision,
                motif_principal, message_client,
                seuil_utilise, flag_bloquant,
                necessite_validation_humaine
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dossier_id,
            score_id,
            resultat_decision.get("decision"),
            resultat_decision.get("motif_principal"),
            resultat_decision.get("message_client"),
            resultat_decision.get("seuil_utilise"),
            resultat_decision.get("flag_bloquant"),
            1 if resultat_decision.get("necessite_validation_humaine") else 0
        ))
        decision_id = cursor.lastrowid

        statut_map = {
            "accepter":         "accepte",
            "refuser":          "refuse",
            "complement_requis": "complement_requis"
        }
        statut_final = statut_map.get(
            resultat_decision.get("decision"), "en_traitement"
        )
        conn.execute("""
            UPDATE dossiers_sinistres
            SET statut_global = ?, updated_at = datetime('now')
            WHERE dossier_id = ?
        """, (statut_final, dossier_id))

        log_audit(conn, dossier_id, "decision", "DECISION_RENDUE", {
            "decision": resultat_decision.get("decision"),
            "motif":    resultat_decision.get("motif_principal"),
            "escalade": resultat_decision.get("necessite_validation_humaine")
        })

        conn.commit()
        logger.success(
            f"Décision sauvegardée — "
            f"{resultat_decision.get('decision').upper()}, "
            f"decision_id={decision_id}"
        )
        return decision_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_decision : {e}")
        raise
    finally:
        conn.close()