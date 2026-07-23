import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends

from api.reclamations.schemas import ReclamationRequest, ReponseRequest
from api.dependencies import get_utilisateur_actuel, exiger_roles
from engines.database import (
    creer_reclamation,
    lister_reclamations,
    lister_reclamations_utilisateur,
    repondre_reclamation,
)

router = APIRouter(prefix="/reclamations", tags=["Réclamations"])


@router.post("", summary="Déposer une réclamation")
def deposer(donnees: ReclamationRequest,
            utilisateur: dict = Depends(get_utilisateur_actuel)):
    if not donnees.message.strip():
        raise HTTPException(status_code=400, detail="Le message est vide")

    resultat = creer_reclamation(
        donnees.dossier_id,
        utilisateur["utilisateur_id"],
        donnees.message.strip(),
    )
    if not resultat["succes"]:
        raise HTTPException(status_code=400, detail=resultat["message"])
    return resultat


@router.get("/mes-reclamations", summary="Mes réclamations")
def mes_reclamations(utilisateur: dict = Depends(get_utilisateur_actuel)):
    return lister_reclamations_utilisateur(utilisateur["utilisateur_id"])


@router.get("", summary="Toutes les réclamations")
def toutes(statut: str | None = None,
           utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))):
    return lister_reclamations(statut)


@router.put("/{reclamation_id}/reponse", summary="Répondre à une réclamation")
def repondre(reclamation_id: int,
             donnees: ReponseRequest,
             utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))):
    if not donnees.reponse.strip():
        raise HTTPException(status_code=400, detail="La réponse est vide")

    resultat = repondre_reclamation(
        reclamation_id, donnees.reponse.strip(), utilisateur["utilisateur_id"]
    )
    if not resultat["succes"]:
        raise HTTPException(status_code=404, detail=resultat["message"])
    return resultat