# engines/scoring_engine.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config import SCORING_RULES, SCORE_BASE, SEUIL_ACCEPTER, SEUIL_COMPLEMENT

# SECTION 1 — CHARGEMENT DES RÈGLES

def charger_regles_scoring(chemin: str = str(SCORING_RULES)) -> dict:
    try:
        with open(chemin, encoding="utf-8") as f:
            config = json.load(f)
        nb = len(config.get("regles", []))
        print(f"{nb} règles de scoring chargées depuis {chemin}")
        return config
    except FileNotFoundError:
        print(f"Fichier JSON non trouvé : {chemin}")
        return {"score_base": SCORE_BASE, "score_minimum": 0,
                "score_maximum": 100, "regles": []}
    except json.JSONDecodeError as e:
        print(f"Erreur JSON dans {chemin} : {e}")
        return {"score_base": SCORE_BASE, "score_minimum": 0,
                "score_maximum": 100, "regles": []}


# SECTION 2 — ÉVALUATEUR DE CONDITION

def obtenir_valeur(dossier: dict, champ: str):

    if "." in champ:
        parties = champ.split(".", 1)
        sous_dict = dossier.get(parties[0], {})
        if isinstance(sous_dict, dict):
            return sous_dict.get(parties[1])
        return None
    return dossier.get(champ)


def evaluer_condition(condition: dict, dossier: dict) -> bool:

    champ    = condition.get("champ")
    operateur = condition.get("operateur")
    valeur   = condition.get("valeur")

    val_dossier = obtenir_valeur(dossier, champ)

    if val_dossier is None:
        return False

    try:
        if isinstance(valeur, (int, float)):
            val_num = float(val_dossier)
            if operateur == ">":  return val_num > valeur
            if operateur == ">=": return val_num >= valeur
            if operateur == "<":  return val_num < valeur
            if operateur == "<=": return val_num <= valeur
            if operateur == "==": return val_num == valeur
            if operateur == "!=": return val_num != valeur

        if operateur == "==": return val_dossier == valeur
        if operateur == "!=": return val_dossier != valeur

    except (TypeError, ValueError):
        return False

    return False


# SECTION 3 — MOTEUR PRINCIPAL

def executer_scoring(
    dossier: dict,
    chemin_regles: str = str(SCORING_RULES)
) -> dict:
   
    config = charger_regles_scoring(chemin_regles)

    score_base    = config.get("score_base", SCORE_BASE)
    score_minimum = config.get("score_minimum", 0)
    score_maximum = config.get("score_maximum", 100)
    regles        = config.get("regles", [])

    score       = score_base
    details     = []
    flags       = []
    nb_penalites = 0
    nb_bonus     = 0

    for regle in regles:
        condition = regle.get("condition", {})
        declenchee = evaluer_condition(condition, dossier)

        delta = regle.get("delta_score", 0)
        flag  = regle.get("flag")

        if declenchee:
            score += delta
            if delta < 0:
                nb_penalites += 1
            elif delta > 0:
                nb_bonus += 1
            if flag:
                flags.append(flag)

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

    score_final = max(score_minimum, min(score_maximum, score))
    delta_total = score_final - score_base

    if score_final >= SEUIL_ACCEPTER:
        niveau_risque = "FAIBLE"
    elif score_final >= SEUIL_COMPLEMENT:
        niveau_risque = "MOYEN"
    else:
        niveau_risque = "ELEVE"

    # Message récapitulatif
    resume = (
        f"Score : {score_final}/100 — "
        f"Risque {niveau_risque} — "
        f"{nb_penalites} pénalité(s), {nb_bonus} bonus — "
        f"Flags : {', '.join(flags) if flags else 'aucun'}"
    )

    return {
        "score":          score_final,
        "score_base":     score_base,
        "delta_total":    delta_total,
        "flags":          flags,
        "nb_penalites":   nb_penalites,
        "nb_bonus":       nb_bonus,
        "details":        details,
        "niveau_risque":  niveau_risque,
        "resume":         resume
    }


# SECTION 4 — AFFICHAGE

def afficher_rapport_scoring(resultat: dict) -> None:
    print("         RAPPORT DE SCORING — SmartClaim")
    print(f"\n{resultat['resume']}")

    print(f"\n Détail du calcul :")
    print(f"   Score de base    : {resultat['score_base']}/100")
    print(f"   Delta total      : {resultat['delta_total']:+d} points")
    print(f"   Score final      : {resultat['score']}/100")
    print(f"   Niveau de risque : {resultat['niveau_risque']}")

    # Règles déclenchées uniquement
    regles_declenchees = [d for d in resultat["details"] if d["declenchee"]]

    if regles_declenchees:
        print(f"\n Règles déclenchées ({len(regles_declenchees)}) :")
        for detail in regles_declenchees:
            print(f" [{detail['id']}] {detail['description']}")
            print(f"          Delta : {detail['delta_score']:+d} pts")
            if detail["flag_genere"]:
                print(f"          Flag  : {detail['flag_genere']}")
            if detail["justification"]:
                print(f"          Note  : {detail['justification']}")
    else:
        print("\n   Aucune règle déclenchée — score de base conservé")

    if resultat["flags"]:
        print(f"\n Flags actifs : {', '.join(resultat['flags'])}")

    print(f"\n{'PEUT CONTINUER vers Décision' if resultat['score'] >= SEUIL_COMPLEMENT else ' Score insuffisant'}")


