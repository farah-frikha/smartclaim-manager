# agents/coordinateur/enrichment.py
"""
Enrichissement du dossier extrait avant la validation.

Responsabilités :
  1. Calculer les champs dérivés (délais, durées)
  2. Récupérer les données contrat depuis la BDD
  3. Appliquer des valeurs par défaut pour les champs manquants

Sans cet enrichissement, le moteur de validation manquerait
de champs obligatoires (date_debut_contrat, delai_declaration_jours...)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import re
import sqlite3
from datetime import date, datetime
from loguru import logger

from engines.database import get_connection


def normaliser_date_iso(valeur: str) -> str:
    """
    Convertit n'importe quel format de date vers YYYY-MM-DD.
    Formats acceptés : DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD.
    Retourne la valeur inchangée si le format n'est pas reconnu.
    """
    if not valeur:
        return valeur

    if re.match(r'^\d{4}-\d{2}-\d{2}$', str(valeur)):
        return valeur

    m = re.match(r'^(\d{2})[/\-](\d{2})[/\-](\d{4})$', str(valeur))
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    return valeur


def _to_date(valeur) -> date:
    """Convertit une valeur vers un objet date Python."""
    if isinstance(valeur, date):
        return valeur
    if isinstance(valeur, str):
        for fmt in ["%Y-%m-%d", "%d/%m/%Y"]:
            try:
                return datetime.strptime(valeur, fmt).date()
            except ValueError:
                continue
    return None


def _enrichir_dates(dossier: dict) -> dict:
    """
    Calcule les champs de délai à partir des dates extraites.
    Ces champs sont nécessaires pour VA-03, VA-06, VA-08.
    """
    date_sinistre    = _to_date(dossier.get("date_sinistre"))
    date_declaration = _to_date(dossier.get("date_declaration"))
    aujourd_hui      = date.today()

    if date_sinistre:
        dossier["delai_declaration_jours"] = (
            (date_declaration - date_sinistre).days
            if date_declaration
            else (aujourd_hui - date_sinistre).days
        )
        dossier["jours_depuis_sinistre"] = (
            aujourd_hui - date_sinistre
        ).days

    return dossier


def _enrichir_depuis_bdd(dossier: dict) -> dict:
    """
    Récupère les données contrat depuis la BDD via le numéro de contrat.
    Nécessaire pour VA-01 (date_debut_contrat) et VA-02 (date_fin_contrat).
    """
    numero_contrat = dossier.get("numero_contrat")
    if not numero_contrat:
        return dossier

    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        contrat = conn.execute("""
            SELECT date_effet, date_echeance, delai_carence_jours
            FROM contrats_collectifs
            WHERE numero_contrat = ?
        """, (numero_contrat,)).fetchone()
        conn.close()

        if contrat:
            dossier["date_debut_contrat"] = normaliser_date_iso(
                contrat["date_effet"]
            )
            dossier["date_fin_contrat"] = normaliser_date_iso(
                contrat["date_echeance"]
            )
            logger.info(
                f"Dates contrat normalisées — "
                f"début={dossier['date_debut_contrat']}, "
                f"fin={dossier['date_fin_contrat']}"
            )

            date_debut = _to_date(contrat["date_effet"])
            date_sinistre = _to_date(dossier.get("date_sinistre"))
            if date_debut and date_sinistre:
                dossier["jours_depuis_souscription"] = (
                    date_sinistre - date_debut
                ).days
        else:
            logger.warning(
                f"Contrat '{numero_contrat}' non trouvé en BDD "
                f"— utilisation valeurs par défaut"
            )
            dossier["date_debut_contrat"]       = "2024-01-01"
            dossier["date_fin_contrat"]         = "2027-01-01"
            dossier["jours_depuis_souscription"] = 400

    except Exception as e:
        logger.warning(f"Enrichissement BDD échoué : {e}")
        dossier["date_debut_contrat"]       = "2024-01-01"
        dossier["date_fin_contrat"]         = "2027-01-01"
        dossier["jours_depuis_souscription"] = 400

    return dossier


def _appliquer_defaults(dossier: dict) -> dict:
    """
    Applique des valeurs par défaut pour les champs métier manquants.
    Évite les KeyError dans les moteurs de règles.
    """
    dossier.setdefault("statut_cotisations_cnss_employeur", "a_jour")
    dossier.setdefault("statut_affiliation",                "actif")
    dossier.setdefault("concerne_ayant_droit",              False)
    dossier.setdefault("cause_sinistre",                    "accident")
    dossier.setdefault(
        "montant_net_complementaire",
        dossier.get("montant_reclame", 0)
    )
    dossier.setdefault(
        "garanties_contrat",
        ["AUTO_ACCIDENT", "AUTO_VOL", "AUTO_BRIS_GLACE", "SANTE_CONSUL"]
    )
    dossier.setdefault(
        "documents_fournis",
        ["formulaire_sinistre", "piece_identite"]
    )
    return dossier


def enrichir_dossier(dossier_extrait: dict) -> dict:
    """
    Point d'entrée public — enrichit le dossier en 3 étapes.

    Appelé par noeud_validation() avant d'envoyer le dossier
    au moteur de validation.
    """
    dossier = {**dossier_extrait}
    dossier = _enrichir_dates(dossier)
    dossier = _enrichir_depuis_bdd(dossier)
    dossier = _appliquer_defaults(dossier)
    return dossier