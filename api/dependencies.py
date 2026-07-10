# api/dependencies.py
"""
Dépendances FastAPI partagées par tous les domaines.
HTTPBearer remplace OAuth2PasswordBearer pour que Swagger UI
affiche un simple champ "Value" au lieu du formulaire OAuth2.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# HTTPBearer — dit à Swagger UI d'afficher un champ "Value" simple
# OAuth2PasswordBearer — affichait un formulaire username/password (incorrect)
security = HTTPBearer()


async def get_utilisateur_actuel(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Extrait et valide l'utilisateur depuis le token JWT.
    credentials.credentials contient le token sans le préfixe "Bearer ".
    Swagger UI ajoute "Bearer " automatiquement — vous collez juste le token.
    """
    from api.auth.auth import verifier_token
    token   = credentials.credentials
    payload = verifier_token(token)
    return {
        "utilisateur_id": payload.get("utilisateur_id"),
        "email":          payload.get("email"),
        "role":           payload.get("role"),
        "employe_id":     payload.get("employe_id"),
        "nom_complet":    payload.get("nom_complet"),
    }


def exiger_roles(*roles: str):
    """
    Restreint l'accès à certains rôles.
    Lève HTTP 403 si le rôle n'est pas autorisé.
    """
    async def verificateur(
        utilisateur: dict = Depends(get_utilisateur_actuel)
    ) -> dict:
        if utilisateur["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Accès refusé. "
                    f"Rôles autorisés : {', '.join(roles)}. "
                    f"Votre rôle : {utilisateur['role']}"
                )
            )
        return utilisateur
    return verificateur