# tests/test_scoring.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.scoring_engine import executer_scoring, afficher_rapport_scoring
from config import SEUIL_COMPLEMENT

dossier_penalise = {
    "nb_soins_12m":                  12,
    "depassement_tarif_cnss":        True,
    "jours_depuis_souscription":     20,
    "nb_arrets_24m":                 4,
    "delai_declaration_jours":       5,
    "dossier_complet_premiere_fois": False,
    "coherence_cnss_facture":        False,
}

dossier_propre = {
    "nb_soins_12m":                  3,
    "depassement_tarif_cnss":        False,
    "jours_depuis_souscription":     1900,
    "nb_arrets_24m":                 1,
    "delai_declaration_jours":       2,
    "dossier_complet_premiere_fois": True,
    "coherence_cnss_facture":        True,
}

dossier_critique = {
    "nb_soins_12m":                  15,
    "depassement_tarif_cnss":        True,
    "sinistre_hors_contrat":         True,
    "jours_depuis_souscription":     10,
    "incoherence_duree_arret":       True,
    "nb_arrets_24m":                 5,
    "depassement_salaire_cnss":      True,
    "delai_declaration_jours":       5,
    "dossier_complet_premiere_fois": False,
    "coherence_cnss_facture":        False,
}

print("TEST 1 — Dossier avec pénalités")
r1 = executer_scoring(dossier_penalise)
afficher_rapport_scoring(r1)

print("TEST 2 — Dossier propre sans anomalie")
r2 = executer_scoring(dossier_propre)
afficher_rapport_scoring(r2)

print("TEST 3 — Dossier critique")
r3 = executer_scoring(dossier_critique)
afficher_rapport_scoring(r3)

cas = [
    ("Dossier pénalisé",  r1, lambda r: r["score"] < 100 and len(r["flags"]) > 0),
    ("Dossier propre",    r2, lambda r: r["score"] >= 70),
    ("Dossier critique",  r3, lambda r: r["score"] < 40),
]

