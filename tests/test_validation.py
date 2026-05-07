# tests/test_validation.py
import sys
sys.path.insert(0, ".")

from engines.validation_engine import executer_validation, afficher_rapport_validation

# Dossier de test fictif
dossier_test = {
    "date_sinistre":          "2024-01-10",
    "date_declaration":       "2024-01-12",
    "delai_declaration_jours": 2,
    "type_sinistre":          "SANTE_HOSPI",
    "garanties_contrat":      ["SANTE_HOSPI", "PREV_ARRET"],
    "statut_cotisations_cnss": "ok",
    "documents_fournis":      ["formulaire_sinistre", "piece_identite", "certificat_medical"],
    "montant_reclame":        1500.0,
}

resultat = executer_validation(dossier_test)
afficher_rapport_validation(resultat)