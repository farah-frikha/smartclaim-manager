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
    authentifier_utilisateur,
    creer_token_acces
)
from api.auth.schemas import (
    InscriptionRequest,
    ConnexionRequest,
    TokenResponse,
    UtilisateurResponse
)
from api.dependencies import get_utilisateur_actuel, exiger_roles
from engines.database import (
    creer_utilisateur,
    mettre_a_jour_derniere_connexion,
    lister_utilisateurs
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
def inscription(donnees: InscriptionRequest):
    """
    Crée un nouvel utilisateur dans la base.
    Hash le mot de passe avant de le stocker — jamais en clair.
    """
    roles_valides = ["EMPLOYE", "GESTIONNAIRE", "ADMIN"]
    if donnees.role not in roles_valides:
        raise HTTPException(
            status_code=400,
            detail=f"Rôle invalide. Rôles acceptés : {roles_valides}"
        )

    hash_pwd = hash_mot_de_passe(donnees.mot_de_passe)

    resultat = creer_utilisateur(
        email            = donnees.email,
        mot_de_passe_hash = hash_pwd,
        role             = donnees.role,
        nom_complet      = donnees.nom_complet,
        employe_id       = donnees.employe_id
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