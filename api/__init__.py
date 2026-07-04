# api/regles/schemas.py
"""
Schémas Pydantic du domaine règles métier.
"""
from pydantic import BaseModel, Field


class ModifierReglesRequest(BaseModel):
    """
    Requête de modification d'un fichier de règles JSON.
    Chaque modification est tracée dans audit_logs.
    """
    contenu: dict = Field(
        description="Contenu JSON complet du fichier de règles"
    )
    motif: str = Field(
        description="Raison de la modification — tracée dans l'audit"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contenu": {"regles": []},
                "motif":   "Ajustement seuil VA-03 de 5 à 7 jours"
            }
        }