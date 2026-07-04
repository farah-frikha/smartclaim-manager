# api/dashboard/schemas.py
"""
Schémas Pydantic du domaine dashboard.
"""
from pydantic import BaseModel
from typing import Optional, List


class StatsGlobalesResponse(BaseModel):
    """Statistiques globales du système."""
    total_dossiers:     int
    acceptes:           int
    refuses:            int
    complement_requis:  int
    en_cours:           int
    taux_acceptation:   float
    score_moyen:        Optional[float]


class ActiviteJour(BaseModel):
    """Activité d'un jour donné."""
    jour: str
    nb:   int