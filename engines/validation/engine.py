# engines/validation/engine.py
"""
Moteur principal de validation — orchestre le chargement et l'évaluation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from config import VALIDATION_RULES
from engines.validation.loader     import charger_regles_validation
from engines.validation.evaluators import evaluer_regle


def executer_validation(
    dossier: dict,
    chemin_regles: str = str(VALIDATION_RULES)
) -> dict:
    """
    Exécute toutes les règles de validation sur un dossier.
    Retourne un dict avec valide, peut_continuer, details, resume.
    """
    regles = charger_regles_validation(chemin_regles)

    if not regles:
        return {
            "valide": False, "peut_continuer": False,
            "nb_regles_total": 0, "nb_reussies": 0, "nb_echouees": 0,
            "echecs_bloquants": ["ERREUR_CHARGEMENT_REGLES"],
            "echecs_mineurs": [], "details": [],
            "resume": "❌ Impossible de charger les règles de validation"
        }

    details          = []
    echecs_bloquants = []
    echecs_mineurs   = []

    for regle in regles:
        ok, message = evaluer_regle(regle, dossier)
        details.append({
            "id":          regle["id"],
            "description": regle["description"],
            "source":      regle.get("source", ""),
            "obligatoire": regle.get("obligatoire", True),
            "resultat":    "PASS" if ok else "FAIL",
            "message":     message
        })
        if not ok:
            if regle.get("obligatoire", True):
                echecs_bloquants.append(regle["id"])
            else:
                echecs_mineurs.append(regle["id"])

    valide      = len(echecs_bloquants) == 0
    nb_reussies = sum(1 for d in details if d["resultat"] == "PASS")
    nb_echouees = len(details) - nb_reussies

    if valide and not echecs_mineurs:
        resume = f"✅ Dossier valide — {nb_reussies}/{len(regles)} règles passées"
    elif valide:
        resume = (
            f"⚠️ Dossier valide avec avertissements — "
            f"{nb_reussies}/{len(regles)} règles, "
            f"anomalies : {', '.join(echecs_mineurs)}"
        )
    else:
        resume = (
            f"❌ Dossier invalide — "
            f"Règles bloquantes : {', '.join(echecs_bloquants)}"
        )

    return {
        "valide":           valide,
        "peut_continuer":   valide,
        "nb_regles_total":  len(regles),
        "nb_reussies":      nb_reussies,
        "nb_echouees":      nb_echouees,
        "echecs_bloquants": echecs_bloquants,
        "echecs_mineurs":   echecs_mineurs,
        "details":          details,
        "resume":           resume
    }