# api/regles/routes.py
"""
Endpoints du domaine règles métier.
Permet de lire et modifier les fichiers JSON de règles
sans toucher au code Python.
Réservé aux ADMIN pour la modification.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import json
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from api.dependencies     import exiger_roles
from api.regles.schemas   import ModifierReglesRequest
from engines.database     import get_connection, log_audit
from config import (
    VALIDATION_RULES,
    SCORING_RULES,
    DECISION_RULES,
    COORDINATION_RULES
)

router = APIRouter(
    prefix="/regles",
    tags=["Règles métier"]
)

# Mapping type de règles → chemin du fichier JSON
FICHIERS_REGLES = {
    "validation":   VALIDATION_RULES,
    "scoring":      SCORING_RULES,
    "decision":     DECISION_RULES,
    "coordinateur": COORDINATION_RULES,
}


@router.get(
    "/{type_regles}",
    summary="Lire les règles d'un type",
    description="Retourne le contenu JSON des règles demandées"
)
def lire_regles(
    type_regles: str,
    utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))
):
    """
    Retourne le contenu du fichier JSON de règles.
    Types valides : validation, scoring, decision, coordinateur
    """
    if type_regles not in FICHIERS_REGLES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Type '{type_regles}' invalide. "
                f"Types valides : {list(FICHIERS_REGLES.keys())}"
            )
        )

    chemin = FICHIERS_REGLES[type_regles]
    try:
        with open(chemin, encoding="utf-8") as f:
            contenu = json.load(f)
        return {
            "type":    type_regles,
            "fichier": str(chemin),
            "contenu": contenu
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Fichier introuvable : {chemin}"
        )


@router.put(
    "/{type_regles}",
    summary="Modifier les règles d'un type",
    description="Écrase le fichier JSON — réservé aux ADMIN uniquement"
)
def modifier_regles(
    type_regles: str,
    requete:     ModifierReglesRequest,
    utilisateur: dict = Depends(exiger_roles("ADMIN"))
):
    """
    Remplace le contenu du fichier JSON de règles.
    Crée automatiquement un backup avant modification.
    Invalide le cache des engines pour que les nouvelles règles
    soient prises en compte immédiatement.
    Toute modification est tracée dans audit_logs.
    """
    if type_regles not in FICHIERS_REGLES:
        raise HTTPException(
            status_code=400,
            detail=f"Type '{type_regles}' invalide."
        )

    chemin = FICHIERS_REGLES[type_regles]

    # ── Backup de l'ancienne version ─────────────────────────
    chemin_backup = str(chemin) + ".backup"
    try:
        with open(chemin, encoding="utf-8") as f:
            ancien_contenu = f.read()
        with open(chemin_backup, "w", encoding="utf-8") as f:
            f.write(ancien_contenu)
    except FileNotFoundError:
        pass

    # ── Écriture du nouveau contenu ──────────────────────────
    try:
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(requete.contenu, f, ensure_ascii=False, indent=2)

        # Invalider le cache des engines
        import engines.validation_engine as ve
        import engines.scoring_engine    as se
        import engines.decision_engine   as de
        ve._cache_regles.clear()
        se._cache_regles.clear()
        de._cache_regles.clear()

        # Tracer dans audit_logs
        conn = get_connection()
        log_audit(conn, None, "admin", "REGLES_MODIFIEES", {
            "type_regles": type_regles,
            "modifie_par": utilisateur["email"],
            "motif":       requete.motif
        })
        conn.commit()
        conn.close()

        logger.warning(
            f"Règles '{type_regles}' modifiées "
            f"par {utilisateur['email']} — {requete.motif}"
        )

        return {
            "message":     f"Règles '{type_regles}' mises à jour avec succès",
            "backup":      chemin_backup,
            "modifie_par": utilisateur["email"],
            "motif":       requete.motif
        }

    except Exception as e:
        logger.error(f"Erreur modification règles : {e}")
        raise HTTPException(status_code=500, detail=str(e))