# api/auth/schemas.py
"""
Schémas Pydantic du domaine authentification.
Valide automatiquement les données entrantes et sortantes.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class InscriptionRequest(BaseModel):
    """Données requises pour créer un nouveau compte."""
    email:        EmailStr
    mot_de_passe: str      = Field(min_length=6,  description="Minimum 6 caractères")
    nom_complet:  str      = Field(min_length=2,  description="Nom et prénom")
    role:         str      = Field(default="EMPLOYE", description="EMPLOYE, GESTIONNAIRE ou ADMIN")
    employe_id:   Optional[int] = Field(default=None, description="Lien vers la table employes")

    class Config:
        json_schema_extra = {
            "example": {
                "email":        "farah.ben@assurance.tn",
                "mot_de_passe": "monmdp123",
                "nom_complet":  "Farah Ben Ali",
                "role":         "EMPLOYE",
                "employe_id":   None
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