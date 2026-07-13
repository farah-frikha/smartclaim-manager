# engines/validation/evaluators.py
"""
Les 6 évaluateurs de règles de validation.
Chaque fonction évalue un type de règle et retourne (bool, str).
Fonctions pures — pas d'effets de bord.
"""
from engines.validation.utils import vers_date, comparer, obtenir_valeur


def evaluer_comparaison_dates(regle: dict, dossier: dict) -> tuple:
    val_1 = vers_date(obtenir_valeur(dossier, regle["champ_1"]))
    val_2 = vers_date(obtenir_valeur(dossier, regle["champ_2"]))
    if val_1 is None:
        return False, f"Champ '{regle['champ_1']}' absent ou format invalide"
    if val_2 is None:
        return False, f"Champ '{regle['champ_2']}' absent ou format invalide"
    ok = comparer(val_1, regle["operateur"], val_2)
    message = "" if ok else (
        f"{regle['message_echec']} "
        f"({regle['champ_1']}={val_1} {regle['operateur']} {regle['champ_2']}={val_2})"
    )
    return ok, message


def evaluer_comparaison_valeur(regle: dict, dossier: dict) -> tuple:
    val_1 = obtenir_valeur(dossier, regle["champ_1"])
    val_2 = regle["valeur"]
    if val_1 is None:
        return False, f"Champ '{regle['champ_1']}' absent du dossier"
    try:
        val_1_num = float(val_1)
        val_2_num = float(val_2)
    except (TypeError, ValueError):
        return False, f"Valeur non numérique pour '{regle['champ_1']}' : {val_1}"
    ok = comparer(val_1_num, regle["operateur"], val_2_num)
    message = "" if ok else (
        f"{regle['message_echec']} "
        f"(valeur={val_1_num}, seuil={regle['operateur']}{val_2_num})"
    )
    return ok, message


def evaluer_appartenance_liste(regle: dict, dossier: dict) -> tuple:
    val_1 = obtenir_valeur(dossier, regle["champ_1"])
    liste = obtenir_valeur(dossier, regle["champ_2"])
    if val_1 is None:
        return False, f"Champ '{regle['champ_1']}' absent du dossier"
    if not isinstance(liste, list) or len(liste) == 0:
        return False, f"Liste '{regle['champ_2']}' absente ou vide"
    ok = val_1 in liste
    message = "" if ok else f"{regle['message_echec']} ('{val_1}' absent de {liste})"
    return ok, message


def evaluer_presence_documents(regle: dict, dossier: dict) -> tuple:
    docs_fournis = obtenir_valeur(dossier, "documents_fournis") or []
    docs_requis  = regle.get("documents_requis", [])
    manquants    = [doc for doc in docs_requis if doc not in docs_fournis]
    ok           = len(manquants) == 0
    message      = "" if ok else f"{regle['message_echec']} : {', '.join(manquants)}"
    return ok, message


def evaluer_comparaison_enum(regle: dict, dossier: dict) -> tuple:
    val = obtenir_valeur(dossier, regle["champ_1"])
    if val is None:
        return True, ""
    if "valeurs_acceptees" in regle:
        ok = val in regle["valeurs_acceptees"]
        return ok, "" if ok else f"{regle['message_echec']} (valeur='{val}')"
    if "valeurs_refusees" in regle:
        ok = val not in regle["valeurs_refusees"]
        return ok, "" if ok else f"{regle['message_echec']} (valeur='{val}')"
    return True, ""


def evaluer_condition_si_alors(regle: dict, dossier: dict) -> tuple:
    condition     = regle["condition"]
    val_condition = obtenir_valeur(dossier, condition["champ"])
    if val_condition != condition["valeur"]:
        return True, ""
    verification = regle["verification"]
    if "valeur" in verification:
        val_verif = obtenir_valeur(dossier, verification["champ"])
        ok = val_verif == verification["valeur"]
        return ok, "" if ok else regle["message_echec"]
    if "contient" in verification:
        liste = obtenir_valeur(dossier, verification["champ"]) or []
        ok    = verification["contient"] in liste
        return ok, "" if ok else regle["message_echec"]
    return True, ""

def evaluer_presence_champ(regle: dict, dossier: dict) -> tuple:
    """
    Vérifie qu'un champ est présent et non vide dans le dossier.
    Type générique, utile pour les règles de complétude de tout domaine.
    """
    val = obtenir_valeur(dossier, regle["champ_1"])

    vide = (
        val is None
        or (isinstance(val, str) and val.strip() == "")
        or (isinstance(val, list) and len(val) == 0)
    )

    ok = not vide
    message = "" if ok else f"{regle['message_echec']} (champ '{regle['champ_1']}' absent)"
    return ok, message
# Dispatch table — mappe type → évaluateur
EVALUATEURS = {
    "comparaison_dates":   evaluer_comparaison_dates,
    "comparaison_valeur":  evaluer_comparaison_valeur,
    "appartenance_liste":  evaluer_appartenance_liste,
    "presence_documents":  evaluer_presence_documents,
    "presence_champ":      evaluer_presence_champ,
    "comparaison_enum":    evaluer_comparaison_enum,
    "condition_si_alors":  evaluer_condition_si_alors,
}


def evaluer_regle(regle: dict, dossier: dict) -> tuple:
    """Dispatch vers le bon évaluateur selon le type de règle."""
    type_regle = regle.get("type", "")
    if type_regle not in EVALUATEURS:
        return False, f"Type de règle inconnu : '{type_regle}'"
    try:
        return EVALUATEURS[type_regle](regle, dossier)
    except Exception as e:
        return False, f"Erreur évaluation {regle['id']} : {str(e)}"