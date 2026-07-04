# api/regles/schemas.py
from pydantic import BaseModel, Field


class ModifierReglesRequest(BaseModel):
    contenu: dict = Field(description="Contenu JSON complet du fichier de règles")
    motif:   str  = Field(description="Raison de la modification")