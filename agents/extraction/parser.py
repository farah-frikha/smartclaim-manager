# agents/extraction/parser.py
"""
Nettoyage, normalisation et validation des données extraites par le LLM.
Fonctions pures — pas de dépendances externes (ni LLM, ni BDD).
Testables unitairement avec de simples assertions.
"""
import re
from loguru import logger

from agents.extraction.schema import (
    SCHEMA_EXTRACTION,
    TYPES_SINISTRES_VALIDES
)


def nettoyer_json(reponse_llm: str) -> str:
    """
    Nettoie la réponse brute du LLM pour extraire le JSON pur.
    Supprime les blocs markdown ```json ... ``` que le modèle
    ajoute parfois malgré les instructions du prompt.
    Extrait le premier objet JSON { ... } trouvé.
    """
    texte = reponse_llm.strip()
    texte = re.sub(r"```json\s*", "", texte)
    texte = re.sub(r"```\s*",     "", texte)

    match = re.search(r'\{.*\}', texte, re.DOTALL)
    if match:
        return match.group(0).strip()
    return texte


def normaliser_date(valeur) -> str:
    """
    Convertit une date vers le format YYYY-MM-DD.
    Accepte : YYYY-MM-DD (inchangé), DD/MM/YYYY, DD-MM-YYYY.
    Retourne None si la valeur est absente.
    """
    if valeur is None:
        return None
    if isinstance(valeur, str):
        if re.match(r'^\d{4}-\d{2}-\d{2}$', valeur):
            return valeur
        match = re.match(r'^(\d{2})[/\-](\d{2})[/\-](\d{4})$', valeur)
        if match:
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return valeur

def valider_et_normaliser(donnees: dict, domaine: str = "AUTO") -> dict:
    """
    Valide et normalise le JSON extrait par le LLM, selon le domaine.

    Charge le schéma du domaine (auto par défaut), vérifie les champs
    obligatoires, normalise montants et dates, et calcule la complétude.
    """
    from agents.extraction.schema import get_schema, TYPES_SINISTRES_VALIDES

    schema = get_schema(domaine)

    donnees_validees = {}
    champs_manquants = []
    champs_invalides = []

    for champ, config in schema.items():
        valeur = donnees.get(champ)

        if valeur is None:
            if config["obligatoire"]:
                champs_manquants.append(champ)
            donnees_validees[champ] = None
            continue

        try:
            if config["type"] == float:
                if isinstance(valeur, str):
                    valeur_nettoyee = re.sub(r'[^\d.,]', '', valeur)
                    valeur_nettoyee = valeur_nettoyee.replace(',', '.')
                    valeur = float(valeur_nettoyee)
                else:
                    valeur = float(valeur)

            elif config["type"] == str:
                valeur = str(valeur).strip()
                if valeur == "" or valeur.lower() == "null":
                    valeur = None
                    if config["obligatoire"]:
                        champs_manquants.append(champ)

            donnees_validees[champ] = valeur

        except (ValueError, TypeError):
            champs_invalides.append(champ)
            donnees_validees[champ] = None

    # Normalisation des dates — selon les champs date présents dans le schéma
    champs_dates = [c for c, cfg in schema.items() if "date" in c.lower()]
    for champ_date in champs_dates:
        if donnees_validees.get(champ_date):
            donnees_validees[champ_date] = normaliser_date(
                donnees_validees[champ_date]
            )

    # Validation type_sinistre — uniquement pour le domaine auto
    if domaine == "AUTO":
        type_sin = donnees_validees.get("type_sinistre")
        if type_sin and type_sin not in TYPES_SINISTRES_VALIDES:
            logger.warning(f"Type sinistre non reconnu : '{type_sin}' → 'AUTRE'")
            donnees_validees["type_sinistre"] = "AUTRE"

    # Score de complétude
    champs_renseignes = sum(
        1 for v in donnees_validees.values() if v is not None
    )
    score_completude = round(champs_renseignes / len(schema), 2)

    return {
        "donnees_validees": donnees_validees,
        "champs_manquants": champs_manquants,
        "champs_invalides": champs_invalides,
        "score_completude": score_completude
    }