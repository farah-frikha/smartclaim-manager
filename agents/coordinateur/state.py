# agents/coordinateur/state.py
"""
Définition de l'état partagé entre tous les agents du pipeline.
EtatDossier est le contrat de données LangGraph.
Chaque nœud reçoit cet état, le lit, l'enrichit et le retourne.
"""
from typing import TypedDict, Optional


class EtatDossier(TypedDict):
    """
    État partagé entre tous les nœuds du graphe LangGraph.

    Règle : chaque nœud retourne {**etat, "champ_modifie": valeur}
    pour préserver les champs des nœuds précédents.
    """
    # ── Entrée ────────────────────────────────────────────────
    chemin_fichier:       str
    employe_id:           Optional[int]
    dossier_id:           Optional[int]
    document_id:          Optional[int]
    reference_dossier:    Optional[str]

    # ── Résultats par agent ───────────────────────────────────
    resultat_capture:     Optional[dict]
    resultat_extraction:  Optional[dict]
    resultat_validation:  Optional[dict]
    resultat_scoring:     Optional[dict]
    resultat_decision:    Optional[dict]

    # ── Contrôle de flux ─────────────────────────────────────
    etape_actuelle:       Optional[str]
    etape_arret:          Optional[str]
    erreurs:              Optional[list]
    peut_continuer:       Optional[bool]

    # ── Métriques ─────────────────────────────────────────────
    score_id:             Optional[int]
    temps_debut:          Optional[float]