# api/dossiers/schemas.py
"""
Schémas Pydantic du domaine dossiers.
"""
from pydantic import BaseModel, Field
from typing import Optional


class UploadResponse(BaseModel):
    """Réponse retournée après traitement complet d'un dossier."""
    reference_dossier: str
    dossier_id:        int
    statut:            str
    decision:          Optional[str]
    score:             Optional[int]
    duree_totale_ms:   int
    message:           str


class CorrectionChampsRequest(BaseModel):
    """
    Requête de correction manuelle d'un champ extrait.
    Le gestionnaire corrige une valeur extraite incorrectement par le LLM.
    """
    nom_champ:        str
    valeur_corrigee:  str
    motif_correction: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nom_champ":        "montant_reclame",
                "valeur_corrigee":  "1500.00",
                "motif_correction": "Montant lu incorrectement sur la facture"
            }
        }


class DossierListeResponse(BaseModel):
    """Représentation condensée d'un dossier pour les listes."""
    dossier_id:        int
    reference_dossier: str
    statut_global:     str
    domaine:           Optional[str] = "AUTO"
    montant_reclame:   Optional[float]
    date_sinistre:     Optional[str]
    created_at:        str