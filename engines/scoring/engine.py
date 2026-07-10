# engines/scoring/engine.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from config import SCORING_RULES, SCORE_BASE, SEUIL_ACCEPTER, SEUIL_COMPLEMENT
from engines.scoring.loader    import charger_regles_scoring
from engines.scoring.evaluator import evaluer_condition


def executer_scoring(
    dossier: dict,
    chemin_regles: str = str(SCORING_RULES)
) -> dict:
    """Calcule le score composite 0-100 d'un dossier."""
    config = charger_regles_scoring(chemin_regles)

    score_base    = config.get("score_base",    SCORE_BASE)
    score_minimum = config.get("score_minimum", 0)
    score_maximum = config.get("score_maximum", 100)
    regles        = config.get("regles",        [])

    score        = score_base
    details      = []
    flags        = []
    nb_penalites = 0
    nb_bonus     = 0

    for regle in regles:
        condition  = regle.get("condition", {})
        declenchee = evaluer_condition(condition, dossier)
        delta      = regle.get("delta_score", 0)
        flag       = regle.get("flag")

        if declenchee:
            score += delta
            if delta < 0:  nb_penalites += 1
            elif delta > 0: nb_bonus    += 1
            if flag:        flags.append(flag)

        details.append({
            "id":            regle["id"],
            "description":   regle["description"],
            "source":        regle.get("source", ""),
            "condition":     f"{condition.get('champ')} {condition.get('operateur')} {condition.get('valeur')}",
            "declenchee":    declenchee,
            "delta_score":   delta if declenchee else 0,
            "flag_genere":   flag if (declenchee and flag) else None,
            "justification": regle.get("justification", "")
        })

    score_final   = max(score_minimum, min(score_maximum, score))
    delta_total   = score_final - score_base
    niveau_risque = (
        "FAIBLE" if score_final >= SEUIL_ACCEPTER else
        "MOYEN"  if score_final >= SEUIL_COMPLEMENT else
        "ELEVE"
    )

    return {
        "score":         score_final,
        "score_base":    score_base,
        "delta_total":   delta_total,
        "flags":         flags,
        "nb_penalites":  nb_penalites,
        "nb_bonus":      nb_bonus,
        "details":       details,
        "niveau_risque": niveau_risque,
        "resume": (
            f"Score : {score_final}/100 — Risque {niveau_risque} — "
            f"{nb_penalites} pénalité(s), {nb_bonus} bonus — "
            f"Flags : {', '.join(flags) if flags else 'aucun'}"
        )
    }