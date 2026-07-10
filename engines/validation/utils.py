# engines/validation/utils.py
"""
Fonctions utilitaires pures pour le moteur de validation.
Pas de dépendances externes — testables unitairement.
"""
from datetime import datetime, date
from typing import Union


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
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(valeur.strip(), fmt).date()
            except ValueError:
                continue
    return None


def comparer(valeur_1, operateur: str, valeur_2) -> bool:
    """Applique un opérateur de comparaison entre deux valeurs."""
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
        parties   = champ.split(".", 1)
        sous_dict = dossier.get(parties[0], {})
        if isinstance(sous_dict, dict):
            return sous_dict.get(parties[1])
        return None
    return dossier.get(champ)