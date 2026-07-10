# engines/scoring/evaluator.py
"""Évaluation des conditions de scoring."""


def obtenir_valeur(dossier: dict, champ: str):
    if "." in champ:
        parties   = champ.split(".", 1)
        sous_dict = dossier.get(parties[0], {})
        if isinstance(sous_dict, dict):
            return sous_dict.get(parties[1])
        return None
    return dossier.get(champ)


def evaluer_condition(condition: dict, dossier: dict) -> bool:
    """
    Évalue une condition de scoring.
    Retourne True si la condition est remplie.
    """
    champ     = condition.get("champ")
    operateur = condition.get("operateur")
    valeur    = condition.get("valeur")

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