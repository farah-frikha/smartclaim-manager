# engines/validation_engine.py
import json
from datetime import datetime, date
from typing import Union
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import VALIDATION_RULES

# SECTION 1 — CHARGEMENT DES RÈGLES

def charger_regles_validation(chemin: str = str(VALIDATION_RULES)) -> list:

    try:
        with open(chemin, encoding="utf-8") as f:
            data = json.load(f)
            regles = data["rules"] if isinstance(data, dict) else data
        print(f" {len(regles)} règles chargées depuis {chemin}")
        return regles
    except FileNotFoundError:
        print(f"  Fichier JSON non trouvé : {chemin}")
        return []
    except KeyError:
        print(f"  Clé 'rules' absente dans {chemin}")
        return []

# SECTION 2 — FONCTIONS UTILITAIRES

def vers_date(valeur) -> Union[date, None]:
    if valeur is None:
        return None
    if isinstance(valeur, datetime):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    if isinstance(valeur, str):
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(valeur.strip(), fmt).date()
            except ValueError:
                continue
    return None


def comparer(valeur_1, operateur: str, valeur_2) -> bool:
    try:
        if operateur == ">=": return valeur_1 >= valeur_2
        if operateur == "<=": return valeur_1 <= valeur_2
        if operateur == ">":  return valeur_1 > valeur_2
        if operateur == "<":  return valeur_1 < valeur_2
        if operateur == "==": return valeur_1 == valeur_2
        if operateur == "!=": return valeur_1 != valeur_2
    except TypeError:
        return False
    return False


def obtenir_valeur(dossier: dict, champ: str):
    if "." in champ:
        parties = champ.split(".", 1)
        sous_dict = dossier.get(parties[0], {})
        if isinstance(sous_dict, dict):
            return sous_dict.get(parties[1])
        return None
    return dossier.get(champ)

# SECTION 3 — ÉVALUATEURS PAR TYPE DE RÈGLE

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
    message = "" if ok else (
        f"{regle['message_echec']} ('{val_1}' absent de {liste})"
    )
    return ok, message


def evaluer_presence_documents(regle: dict, dossier: dict) -> tuple:
    docs_fournis = obtenir_valeur(dossier, "documents_fournis") or []
    docs_requis  = regle.get("documents_requis", [])

    manquants = [doc for doc in docs_requis if doc not in docs_fournis]
    ok = len(manquants) == 0
    message = "" if ok else f"{regle['message_echec']} : {', '.join(manquants)}"
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
    condition = regle["condition"]
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
        ok = verification["contient"] in liste
        return ok, "" if ok else regle["message_echec"]

    return True, ""

# SECTION 4 — ÉVALUATEUR PRINCIPAL

def evaluer_regle(regle: dict, dossier: dict) -> tuple:
    type_regle = regle.get("type", "")

    evaluateurs = {
        "comparaison_dates":   evaluer_comparaison_dates,
        "comparaison_valeur":  evaluer_comparaison_valeur,
        "appartenance_liste":  evaluer_appartenance_liste,
        "presence_documents":  evaluer_presence_documents,
        "comparaison_enum":    evaluer_comparaison_enum,
        "condition_si_alors":  evaluer_condition_si_alors,
    }

    if type_regle not in evaluateurs:
        return False, f"Type de règle inconnu : '{type_regle}'"

    try:
        return evaluateurs[type_regle](regle, dossier)
    except Exception as e:
        return False, f"Erreur lors de l'évaluation de {regle['id']} : {str(e)}"

# SECTION 5 — MOTEUR PRINCIPAL ← CORRIGÉ

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
            "valide": False,
            "peut_continuer": False,
            "nb_regles_total": 0,
            "nb_reussies": 0,
            "nb_echouees": 0,
            "echecs_bloquants": ["ERREUR_CHARGEMENT_REGLES"],
            "echecs_mineurs": [],
            "details": [],
            "resume": " Impossible de charger les règles de validation"
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

    if valide and len(echecs_mineurs) == 0:
        resume = f" Dossier valide — {nb_reussies}/{len(regles)} règles passées"
    elif valide and len(echecs_mineurs) > 0:
        resume = (
            f"  Dossier valide avec avertissements — "
            f"{nb_reussies}/{len(regles)} règles passées, "
            f"anomalies mineures : {', '.join(echecs_mineurs)}"
        )
    else:
        resume = (
            f" Dossier invalide — "
            f"Règles bloquantes échouées : {', '.join(echecs_bloquants)}"
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

# SECTION 6 — AFFICHAGE

def afficher_rapport_validation(resultat: dict) -> None:
    print("\n" + "═" * 60)
    print("        RAPPORT DE VALIDATION — SmartClaim")
    print("═" * 60)
    print(f"\n{resultat['resume']}")
    print(f"\n Statistiques :")
    print(f"   Règles évaluées : {resultat['nb_regles_total']}")
    print(f"   Réussies        : {resultat['nb_reussies']}")
    print(f"   Échouées        : {resultat['nb_echouees']}")

    if resultat["echecs_bloquants"]:
        print(f"\n Règles BLOQUANTES échouées :")
        for detail in resultat["details"]:
            if detail["id"] in resultat["echecs_bloquants"]:
                print(f"   [{detail['id']}] {detail['description']}")
                print(f"          → {detail['message']}")
                print(f"          Source : {detail['source']}")

    if resultat["echecs_mineurs"]:
        print(f"\n Règles MINEURES échouées :")
        for detail in resultat["details"]:
            if detail["id"] in resultat["echecs_mineurs"]:
                print(f"   [{detail['id']}] {detail['description']}")
                print(f"          → {detail['message']}")

    print(f"\n{' PEUT CONTINUER' if resultat['peut_continuer'] else ' ARRÊT — Refus immédiat'}")
    print("═" * 60 + "\n")
