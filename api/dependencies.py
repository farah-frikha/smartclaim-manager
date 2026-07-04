# api/dependencies.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_utilisateur_actuel(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """
    Extrait et valide l'utilisateur depuis le token JWT.
    Import local de verifier_token pour éviter la circularité.
    """
    from api.auth.auth import verifier_token   # ← import local ici
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