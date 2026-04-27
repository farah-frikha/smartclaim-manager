# ============================================================
# MOTEUR DE VALIDATION COMPLET
# SmartClaim Manager — Agent Validation
# ============================================================

import json
from datetime import datetime, date
from typing import Union

# ────────────────────────────────────────────────────────────
# SECTION 1 — CHARGEMENT DES RÈGLES
# ────────────────────────────────────────────────────────────

def charger_regles_validation(chemin: str = "regles_validation_agent.json") -> list:

    try:
        with open(chemin, encoding="utf-8") as f:
            data = json.load(f)
            regles = data["rules"]
        print(f" {len(regles)} règles chargées depuis {chemin}")
        return regles
    except FileNotFoundError:
        print("  Fichier JSON non trouvé — utilisation des règles par défaut")

# ────────────────────────────────────────────────────────────
# SECTION 2 — FONCTIONS UTILITAIRES
# ────────────────────────────────────────────────────────────

def vers_date(valeur) -> Union[date, None]:
    """
    Convertit une valeur en objet date Python.
    Accepte : date, datetime, str (plusieurs formats).
    Retourne None si la conversion échoue.
    """
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
    """
    Applique un opérateur de comparaison entre deux valeurs.
    Supporte : >=, <=, >, <, ==, !=
    """
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
    """
    Récupère une valeur depuis le dossier.
    Supporte la notation pointée : 'adresse.ville'
    """
    if "." in champ:
        parties = champ.split(".", 1)
        sous_dict = dossier.get(parties[0], {})
        if isinstance(sous_dict, dict):
            return sous_dict.get(parties[1])
        return None
    return dossier.get(champ)


# ────────────────────────────────────────────────────────────
# SECTION 3 — ÉVALUATEURS PAR TYPE DE RÈGLE
# ────────────────────────────────────────────────────────────

def evaluer_comparaison_dates(regle: dict, dossier: dict) -> tuple:
    """
    Type : comparaison_dates
    """
    val_1 = vers_date(obtenir_valeur(dossier, regle["champ_1"]))
    val_2 = vers_date(obtenir_valeur(dossier, regle["champ_2"]))

    if val_1 is None:
        return False, f"Champ '{regle['champ_1']}' absent ou format de date invalide"
    if val_2 is None:
        return False, f"Champ '{regle['champ_2']}' absent ou format de date invalide"

    ok = comparer(val_1, regle["operateur"], val_2)
    message = "" if ok else (
        f"{regle['message_echec']} "
        f"({regle['champ_1']}={val_1} {regle['operateur']} {regle['champ_2']}={val_2})"
    )
    return ok, message


def evaluer_comparaison_valeur(regle: dict, dossier: dict) -> tuple:
    """
    Type : comparaison_valeur
    Exemple : delai_declaration_jours <= 5
    """
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
    """
    Type : appartenance_liste
    Exemple : type_sinistre dans garanties_contrat
    """
    val_1 = obtenir_valeur(dossier, regle["champ_1"])
    liste = obtenir_valeur(dossier, regle["champ_2"])

    if val_1 is None:
        return False, f"Champ '{regle['champ_1']}' absent du dossier"
    if not isinstance(liste, list) or len(liste) == 0:
        return False, f"Liste '{regle['champ_2']}' absente ou vide dans le dossier"

    ok = val_1 in liste
    message = "" if ok else (
        f"{regle['message_echec']} "
        f"('{val_1}' absent de {liste})"
    )
    return ok, message


def evaluer_presence_documents(regle: dict, dossier: dict) -> tuple:
    """
    Type : presence_documents
    Exemple : documents_fournis contient formulaire_sinistre ET piece_identite
    """
    docs_fournis = obtenir_valeur(dossier, "documents_fournis") or []
    docs_requis  = regle.get("documents_requis", [])

    manquants = [doc for doc in docs_requis if doc not in docs_fournis]
    ok = len(manquants) == 0
    message = "" if ok else (
        f"{regle['message_echec']} : {', '.join(manquants)}"
    )
    return ok, message


def evaluer_comparaison_enum(regle: dict, dossier: dict) -> tuple:
    """
    Type : comparaison_enum
    Supporte : valeurs_acceptees (liste blanche) ET valeurs_refusees (liste noire)
    """
    val = obtenir_valeur(dossier, regle["champ_1"])

    if val is None:
        # Si le champ est absent et que la règle est optionnelle, on passe
        return True, ""

    if "valeurs_acceptees" in regle:
        ok = val in regle["valeurs_acceptees"]
        message = "" if ok else (
            f"{regle['message_echec']} (valeur='{val}')"
        )
        return ok, message

    if "valeurs_refusees" in regle:
        ok = val not in regle["valeurs_refusees"]
        message = "" if ok else (
            f"{regle['message_echec']} (valeur='{val}')"
        )
        return ok, message

    return True, ""


def evaluer_condition_si_alors(regle: dict, dossier: dict) -> tuple:
    """
    Type : condition_si_alors
    Exemple : SI type_sinistre == PREV_ARRET ALORS certificat_medical présent
    La vérification ne s'applique que si la condition est vraie.
    """
    condition = regle["condition"]
    val_condition = obtenir_valeur(dossier, condition["champ"])

    # Si la condition n'est pas remplie, la règle ne s'applique pas → OK
    if val_condition != condition["valeur"]:
        return True, ""

    # La condition est remplie → vérifier la contrainte
    verification = regle["verification"]

    # Cas 1 : vérification par valeur exacte
    if "valeur" in verification:
        val_verif = obtenir_valeur(dossier, verification["champ"])
        ok = val_verif == verification["valeur"]
        message = "" if ok else regle["message_echec"]
        return ok, message

    # Cas 2 : vérification par présence dans une liste
    if "contient" in verification:
        liste = obtenir_valeur(dossier, verification["champ"]) or []
        ok = verification["contient"] in liste
        message = "" if ok else regle["message_echec"]
        return ok, message

    return True, ""


# ────────────────────────────────────────────────────────────
# SECTION 4 — ÉVALUATEUR PRINCIPAL
# ────────────────────────────────────────────────────────────

def evaluer_regle(regle: dict, dossier: dict) -> tuple:
    """
    Dispatche l'évaluation vers le bon évaluateur
    selon le type de règle.
    Retourne (ok: bool, message: str)
    """
    type_regle = regle.get("type", "")

    evaluateurs = {
        "comparaison_dates":    evaluer_comparaison_dates,
        "comparaison_valeur":   evaluer_comparaison_valeur,
        "appartenance_liste":   evaluer_appartenance_liste,
        "presence_documents":   evaluer_presence_documents,
        "comparaison_enum":     evaluer_comparaison_enum,
        "condition_si_alors":   evaluer_condition_si_alors,
    }

    if type_regle not in evaluateurs:
        return False, f"Type de règle inconnu : '{type_regle}'"

    try:
        return evaluateurs[type_regle](regle, dossier)
    except Exception as e:
        return False, f"Erreur lors de l'évaluation de {regle['id']} : {str(e)}"


# ────────────────────────────────────────────────────────────
# SECTION 5 — MOTEUR PRINCIPAL
# ────────────────────────────────────────────────────────────

def executer_validation(
    dossier: dict,
    chemin_regles: str = "validation_rules.json"
) -> dict:
    """
    Exécute toutes les règles de validation sur un dossier.

    Paramètres :
        dossier       : dict contenant les champs extraits du sinistre
        chemin_regles : chemin vers le fichier JSON de règles

    Retourne un dict contenant :
        valide          : bool — True si toutes les règles obligatoires passent
        peut_continuer  : bool — False si au moins une règle obligatoire échoue
        nb_regles_total : int
        nb_reussies     : int
        nb_echouees     : int
        echecs_bloquants: list — IDs des règles obligatoires échouées
        echecs_mineurs  : list — IDs des règles non-obligatoires échouées
        details         : list — détail complet de chaque règle évaluée
        resume          : str  — message lisible récapitulatif
    """
    regles = charger_regles_validation(chemin_regles)

    details         = []
    echecs_bloquants = []
    echecs_mineurs   = []

    for regle in regles:
        ok, message = evaluer_regle(regle, dossier)

        details.append({
            "id":           regle["id"],
            "description":  regle["description"],
            "source":       regle.get("source", ""),
            "obligatoire":  regle.get("obligatoire", True),
            "resultat":     "PASS" if ok else "FAIL",
            "message":      message
        })

        if not ok:
            if regle.get("obligatoire", True):
                echecs_bloquants.append(regle["id"])
            else:
                echecs_mineurs.append(regle["id"])

    valide         = len(echecs_bloquants) == 0
    nb_reussies    = sum(1 for d in details if d["resultat"] == "PASS")
    nb_echouees    = len(details) - nb_reussies

    # Message récapitulatif lisible
    if valide and len(echecs_mineurs) == 0:
        resume = f"✅ Dossier valide — {nb_reussies}/{len(regles)} règles passées"
    elif valide and len(echecs_mineurs) > 0:
        resume = (
            f"⚠️  Dossier valide avec avertissements — "
            f"{nb_reussies}/{len(regles)} règles passées, "
            f"anomalies mineures : {', '.join(echecs_mineurs)}"
        )
    else:
        resume = (
            f"❌ Dossier invalide — "
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


# ────────────────────────────────────────────────────────────
# SECTION 6 — AFFICHAGE FORMATÉ (utile pour Colab)
# ────────────────────────────────────────────────────────────

def afficher_rapport_validation(resultat: dict) -> None:
    """
    Affiche un rapport lisible du résultat de validation.
    Conçu pour être lisible dans un notebook Colab.
    """
    print("\n" + "═" * 60)
    print("        RAPPORT DE VALIDATION — SmartClaim")
    print("═" * 60)

    print(f"\n{resultat['resume']}")
    print(f"\n📊 Statistiques :")
    print(f"   Règles évaluées : {resultat['nb_regles_total']}")
    print(f"   Réussies        : {resultat['nb_reussies']}")
    print(f"   Échouées        : {resultat['nb_echouees']}")

    if resultat["echecs_bloquants"]:
        print(f"\n🔴 Règles BLOQUANTES échouées :")
        for detail in resultat["details"]:
            if detail["id"] in resultat["echecs_bloquants"]:
                print(f"   [{detail['id']}] {detail['description']}")
                print(f"          → {detail['message']}")
                print(f"          📖 Source : {detail['source']}")

    if resultat["echecs_mineurs"]:
        print(f"\n🟡 Règles MINEURES échouées (non bloquantes) :")
        for detail in resultat["details"]:
            if detail["id"] in resultat["echecs_mineurs"]:
                print(f"   [{detail['id']}] {detail['description']}")
                print(f"          → {detail['message']}")

    print(f"\n{'✅ PEUT CONTINUER vers Scoring' if resultat['peut_continuer'] else '🛑 ARRÊT — Refus immédiat'}")
    print("═" * 60 + "\n")