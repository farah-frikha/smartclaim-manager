# api/dossiers/routes.py
"""
Endpoints du domaine dossiers.
Cœur du système — orchestre le pipeline IA complet.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from loguru import logger

from api.dependencies       import get_utilisateur_actuel, exiger_roles
from api.dossiers.schemas   import (
    UploadResponse,
    CorrectionChampsRequest
)
from agents.coordinateur    import traiter_dossier
from engines.database       import (
    lister_dossiers,
    lister_dossiers_par_employe,
    lire_dossier_complet,
    get_connection,
    log_audit
)
from config import UPLOADS_DIR

router = APIRouter(
    prefix="/dossiers",
    tags=["Dossiers"]
)

EXTENSIONS_AUTORISEES = {".pdf", ".jpg", ".jpeg", ".png"}
TAILLE_MAX_OCTETS     = 10 * 1024 * 1024  # 10 Mo


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Déposer un document de sinistre",
    description="Upload PDF/image → déclenche le pipeline IA complet"
)
async def upload_dossier(
    fichier:      UploadFile = File(...),
    utilisateur:  dict       = Depends(get_utilisateur_actuel)
):
    """
    1. Valide le fichier (format + taille)
    2. Sauvegarde sur le disque
    3. Lance le pipeline LangGraph complet
    4. Retourne la décision préliminaire
    """
    # ── Validation format ────────────────────────────────────
    extension = Path(fichier.filename).suffix.lower()
    if extension not in EXTENSIONS_AUTORISEES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Format '{extension}' non supporté. "
                f"Formats acceptés : PDF, JPG, PNG"
            )
        )

    # ── Validation taille ────────────────────────────────────
    contenu = await fichier.read()
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise HTTPException(
            status_code=413,
            detail="Fichier trop volumineux. Taille maximale : 10 Mo"
        )

    # ── Sauvegarde disque ────────────────────────────────────
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    horodatage  = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_fichier = f"{horodatage}_{utilisateur['utilisateur_id']}_{fichier.filename}"
    chemin      = UPLOADS_DIR / nom_fichier

    with open(chemin, "wb") as f:
        f.write(contenu)

    logger.info(
        f"Fichier reçu : {nom_fichier} "
        f"({len(contenu)/1024:.1f} Ko) "
        f"— utilisateur : {utilisateur['email']}"
    )

    # ── Pipeline IA ──────────────────────────────────────────
    try:
        resultat = traiter_dossier(
            str(chemin),
            employe_id=utilisateur.get("employe_id") or 1
        )
    except Exception as e:
        logger.error(f"Erreur pipeline : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement : {str(e)}"
        )

   # ── Réponse ──────────────────────────────────────────────
    decision = resultat.get("resultat_decision") or {}
    scoring  = resultat.get("resultat_scoring")  or {}
    etape_arret = resultat.get("etape_arret")
    if not etape_arret:
        statut = "traite"
    elif etape_arret == "validation":
        statut = "validation_bloquee"
    else:
        statut = "erreur"

    return UploadResponse(
        reference_dossier = resultat.get("reference_dossier", "N/A"),
        dossier_id        = resultat.get("dossier_id", 0),
        statut            = statut,
        decision          = decision.get("decision"),
        score             = scoring.get("score"),
        duree_totale_ms   = resultat.get("duree_totale_ms", 0),
        message           = decision.get("message_client", "Traitement terminé")
    )


@router.get(
    "",
    summary="Lister tous les dossiers",
    description="Réservé aux GESTIONNAIRE et ADMIN"
)
def liste_tous_dossiers(
    statut:      str  = Query(None, description="Filtrer par statut"),
    limite:      int  = Query(50,   description="Nombre maximum de résultats"),
    utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))
):
    """Retourne tous les dossiers avec filtre optionnel sur le statut."""
    return lister_dossiers(statut=statut, limite=limite)


@router.get(
    "/mes-dossiers",
    summary="Mes dossiers personnels",
    description="L'employé voit uniquement ses propres dossiers"
)
def mes_dossiers(
    utilisateur: dict = Depends(get_utilisateur_actuel)
):
    """
    Retourne uniquement les dossiers de l'employé connecté.
    Isolation stricte — un employé ne voit jamais les dossiers d'un autre.
    """
    employe_id = utilisateur.get("employe_id")
    if not employe_id:
        return []
    return lister_dossiers_par_employe(employe_id)


@router.get(
    "/{dossier_id}",
    summary="Détail complet d'un dossier",
)
def detail_dossier(
    dossier_id:  int,
    utilisateur: dict = Depends(get_utilisateur_actuel)
):
    """
    Retourne toutes les données d'un dossier.
    Contrôle d'accès :
      - EMPLOYE : uniquement ses propres dossiers
      - GESTIONNAIRE / ADMIN : tous les dossiers
    """
    dossier = lire_dossier_complet(dossier_id)

    if "erreur" in dossier:
        raise HTTPException(status_code=404, detail=dossier["erreur"])

    if utilisateur["role"] == "EMPLOYE":
        if dossier["dossier"].get("employe_id") != utilisateur.get("employe_id"):
            raise HTTPException(
                status_code=403,
                detail="Accès refusé — ce dossier ne vous appartient pas"
            )

    return dossier


@router.put(
    "/{dossier_id}/champs",
    summary="Corriger un champ extrait",
    description="Permet au gestionnaire de corriger une extraction LLM incorrecte"
)
def corriger_champ(
    dossier_id:  int,
    correction:  CorrectionChampsRequest,
    utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))
):
    """
    Modifie la valeur normalisée d'un champ extrait par le LLM.
    Marque le champ comme validé manuellement.
    Trace la correction dans audit_logs.
    """
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT extraction_id FROM champs_extraits
            WHERE dossier_id = ? AND nom_champ = ?
        """, (dossier_id, correction.nom_champ)).fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Champ '{correction.nom_champ}' introuvable "
                    f"pour le dossier {dossier_id}"
                )
            )

        conn.execute("""
            UPDATE champs_extraits
            SET valeur_normalisee   = ?,
                valide_manuellement = 1
            WHERE dossier_id = ? AND nom_champ = ?
        """, (correction.valeur_corrigee, dossier_id, correction.nom_champ))

        log_audit(conn, dossier_id, "gestionnaire", "CHAMP_CORRIGE", {
            "champ":           correction.nom_champ,
            "nouvelle_valeur": correction.valeur_corrigee,
            "motif":           correction.motif_correction,
            "corrige_par":     utilisateur["email"]
        })

        conn.commit()
        logger.info(
            f"Champ corrigé — dossier={dossier_id}, "
            f"champ={correction.nom_champ}, "
            f"par={utilisateur['email']}"
        )

        return {
            "message":         "Champ mis à jour avec succès",
            "champ":           correction.nom_champ,
            "nouvelle_valeur": correction.valeur_corrigee
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur correction champ : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get(
    "/{dossier_id}/rapport",
    summary="Rapport complet d'un dossier",
    description="Retourne toutes les données pour générer un rapport PDF"
)
def rapport_dossier(
    dossier_id:  int,
    utilisateur: dict = Depends(get_utilisateur_actuel)
):
    """
    Retourne le rapport structuré complet.
    Même contrôle d'accès que GET /{dossier_id}.
    """
    dossier = lire_dossier_complet(dossier_id)

    if "erreur" in dossier:
        raise HTTPException(status_code=404, detail=dossier["erreur"])

    if utilisateur["role"] == "EMPLOYE":
        if dossier["dossier"].get("employe_id") != utilisateur.get("employe_id"):
            raise HTTPException(status_code=403, detail="Accès refusé")

    return {
        "reference":     dossier["dossier"]["reference_dossier"],
        "date_rapport":  datetime.now().isoformat(),
        "assure":        dossier["champs"].get("nom_assure"),
        "contrat":       dossier["champs"].get("numero_contrat"),
        "date_sinistre": dossier["champs"].get("date_sinistre"),
        "montant":       dossier["champs"].get("montant_reclame"),
        "decision":      dossier["decision"],
        "score":         dossier["score"],
        "validation":    dossier["validation"],
        "audit":         dossier["audit_logs"]
    }