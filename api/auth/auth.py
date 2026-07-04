# api/auth/auth.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES


def hash_mot_de_passe(mot_de_passe: str) -> str:
    """
    Hash un mot de passe avec bcrypt.
    Tronque à 72 bytes — limite native de bcrypt.
    """
    password_bytes = mot_de_passe.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond au hash stocké.
    """
    password_bytes = mot_de_passe.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hash_stocke.encode("utf-8"))


def creer_token_acces(donnees: dict) -> str:
    """
    Génère un token JWT signé.
    """
    a_encoder = donnees.copy()
    expiration = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    a_encoder.update({"exp": expiration})
    return jwt.encode(a_encoder, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verifier_token(token: str) -> dict:
    """
    Décode et vérifie un token JWT.
    Lève HTTP 401 si invalide ou expiré.
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré — veuillez vous reconnecter",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authentifier_utilisateur(email: str, mot_de_passe: str) -> Optional[dict]:
    """
    Vérifie les identifiants contre la base de données.
    Import local pour éviter la circularité des imports.
    """
    from engines.database import obtenir_utilisateur_par_email
    utilisateur = obtenir_utilisateur_par_email(email)
    if not utilisateur:
        return None
    if not verifier_mot_de_passe(mot_de_passe, utilisateur["mot_de_passe_hash"]):
        return None
    return utilisateur