# api/auth/routes.py
"""
Endpoints du domaine authentification.
Gère la création de comptes, la connexion et la gestion des utilisateurs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from fastapi import APIRouter, HTTPException, status, Depends

from api.auth.auth    import (
    hash_mot_de_passe,
    verifier_mot_de_passe,
    authentifier_utilisateur,
    creer_token_acces
)
from api.auth.schemas import (
    InscriptionRequest,
    ConnexionRequest,
    TokenResponse,
    ChangementMotDePasseRequest,
    UtilisateurResponse ,
    ChangementStatutRequest
)
from api.dependencies import get_utilisateur_actuel, exiger_roles
from engines.database import (
    creer_utilisateur,
    mettre_a_jour_derniere_connexion,
    lister_utilisateurs ,
    obtenir_utilisateur_par_id ,
    get_connection ,
    changer_statut_utilisateur
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentification"]

)



@router.post(
    "/register",
    summary="Créer un compte utilisateur",
    description="Crée un nouveau compte. En production, réservé à l'ADMIN."
)
def inscription(donnees: InscriptionRequest , utilisateur: dict = Depends(exiger_roles("ADMIN"))):
    roles_valides = ["EMPLOYE", "GESTIONNAIRE", "ADMIN"]
    if donnees.role not in roles_valides:
        raise HTTPException(
            status_code=400,
            detail=f"Rôle invalide. Rôles acceptés : {roles_valides}"
        )

    hash_pwd = hash_mot_de_passe(donnees.mot_de_passe)

    if donnees.role == "EMPLOYE":
        if not donnees.numero_cnss:
            raise HTTPException(
                status_code=400,
                detail="numero_cnss obligatoire pour un compte EMPLOYE"
            )

        from engines.database import creer_employe_et_utilisateur
        resultat = creer_employe_et_utilisateur(
            email=donnees.email,
            mot_de_passe_hash=hash_pwd,
            nom_complet=donnees.nom_complet,
            numero_cnss=donnees.numero_cnss,
        )
    else:
        resultat = creer_utilisateur(
            email=donnees.email,
            mot_de_passe_hash=hash_pwd,
            role=donnees.role,
            nom_complet=donnees.nom_complet,
            employe_id=None
        )

    if not resultat["succes"]:
        raise HTTPException(status_code=400, detail=resultat["message"])

    return {
        "message":        "Compte créé avec succès",
        "utilisateur_id": resultat["utilisateur_id"]
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Se connecter",
    description="Retourne un token JWT valable 8 heures"
)
def connexion(donnees: ConnexionRequest):
    """
    Vérifie email + mot de passe.
    Retourne un token JWT à inclure dans toutes les requêtes suivantes.
    Le token doit être envoyé dans l'en-tête : Authorization: Bearer <token>
    """
    utilisateur = authentifier_utilisateur(donnees.email, donnees.mot_de_passe)

    if not utilisateur:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    mettre_a_jour_derniere_connexion(utilisateur["utilisateur_id"])

    token = creer_token_acces({
        "utilisateur_id": utilisateur["utilisateur_id"],
        "email":          utilisateur["email"],
        "role":           utilisateur["role"],
        "employe_id":     utilisateur["employe_id"],
        "nom_complet":    utilisateur["nom_complet"],
    })

    return TokenResponse(
        access_token = token,
        token_type   = "bearer",
        utilisateur  = {
            "utilisateur_id": utilisateur["utilisateur_id"],
            "email":          utilisateur["email"],
            "role":           utilisateur["role"],
            "nom_complet":    utilisateur["nom_complet"],
        }
    )


@router.get(
    "/me",
    summary="Mon profil",
    description="Retourne les informations de l'utilisateur connecté"
)
def mon_profil(utilisateur: dict = Depends(get_utilisateur_actuel)):
    """Retourne les informations extraites du token JWT."""
    return utilisateur


@router.get(
    "/utilisateurs",
    summary="Liste des utilisateurs",
    description="Réservé aux GESTIONNAIRE et ADMIN"
)
def liste_utilisateurs(
    utilisateur: dict = Depends(exiger_roles("GESTIONNAIRE", "ADMIN"))
):
    """Retourne la liste de tous les utilisateurs du système."""
    return lister_utilisateurs()
@router.put(
    "/mot-de-passe",
    summary="Changer son mot de passe",
    description="Permet à l'utilisateur connecté de modifier son mot de passe."
)
def changer_mot_de_passe(
    donnees: ChangementMotDePasseRequest,
    utilisateur: dict = Depends(get_utilisateur_actuel)
):
    # Récupérer l'utilisateur complet avec son hash actuel
    user_complet = obtenir_utilisateur_par_id(utilisateur["utilisateur_id"])
    if not user_complet:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Vérifier l'ancien mot de passe
    if not verifier_mot_de_passe(
        donnees.ancien_mot_de_passe,
        user_complet["mot_de_passe_hash"]
    ):
        raise HTTPException(
            status_code=400,
            detail="Mot de passe actuel incorrect"
        )

    # Hasher et sauvegarder le nouveau
    nouveau_hash = hash_mot_de_passe(donnees.nouveau_mot_de_passe)
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE utilisateurs
            SET mot_de_passe_hash = ?, updated_at = datetime('now')
            WHERE utilisateur_id = ?
        """, (nouveau_hash, utilisateur["utilisateur_id"]))
        conn.commit()
    finally:
        conn.close()

    return {"message": "Mot de passe modifié avec succès"}
@router.put(
    "/utilisateurs/{utilisateur_id}/statut",
    summary="Activer ou désactiver un compte",
    description="Réservé à l'ADMIN. La désactivation empêche la connexion "
                "sans supprimer les données de l'utilisateur."
)
def modifier_statut_utilisateur(
    utilisateur_id: int,
    donnees: ChangementStatutRequest,
    utilisateur: dict = Depends(exiger_roles("ADMIN"))
):
    # Un administrateur ne peut pas désactiver son propre compte
    if utilisateur_id == utilisateur["utilisateur_id"] and not donnees.actif:
        raise HTTPException(
            status_code=400,
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )

    resultat = changer_statut_utilisateur(utilisateur_id, donnees.actif)

    if not resultat["succes"]:
        raise HTTPException(status_code=404, detail=resultat["message"])

    return resultat
