# api/auth/schemas.py
"""
Schémas Pydantic du domaine authentification.
Valide automatiquement les données entrantes et sortantes.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class InscriptionRequest(BaseModel):
    email:        EmailStr
    mot_de_passe: str = Field(min_length=6)
    nom_complet:  str = Field(min_length=2)
    role:         str = Field(default="EMPLOYE")
    numero_cnss:  Optional[str] = Field(
        default=None,
        description="Obligatoire si role=EMPLOYE"
    )
    employe_id:   Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email":        "ahmed@assurance.tn",
                "mot_de_passe": "motdepasse123",
                "nom_complet":  "Ahmed Trabelsi",
                "role":         "EMPLOYE",
                "numero_cnss":  "112233445"
            }
        }

class ConnexionRequest(BaseModel):
    """Données requises pour se connecter."""
    email:        EmailStr
    mot_de_passe: str

    class Config:
        json_schema_extra = {
            "example": {
                "email":        "farah.ben@assurance.tn",
                "mot_de_passe": "monmdp123"
            }
        }


class TokenResponse(BaseModel):
    """Réponse après connexion réussie."""
    access_token: str
    token_type:   str
    utilisateur:  dict


class UtilisateurResponse(BaseModel):
    """Données publiques d'un utilisateur (sans mot de passe)."""
    utilisateur_id:     int
    email:              str
    role:               str
    nom_complet:        str
    actif:              int
    derniere_connexion: Optional[str]
    created_at:         str
class ChangementMotDePasseRequest(BaseModel):
    ancien_mot_de_passe:  str = Field(min_length=1)
    nouveau_mot_de_passe: str = Field(min_length=6)    