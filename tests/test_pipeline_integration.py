# tests/test_pipeline_integration.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engines.validation_engine import executer_validation
from engines.scoring_engine     import executer_scoring
from engines.decision_engine    import executer_decision


def executer_pipeline_complet(dossier: dict) -> dict:
    """
    Exécute le pipeline complet V → S → D sur un dossier.
    Retourne un dict unifié avec les résultats des 3 agents.
    """
    # Étape 1 : Validation
    r_validation = executer_validation(dossier)

    if not r_validation["peut_continuer"]:
        return {
            "etape_arret":  "validation",
            "validation":   r_validation,
            "scoring":      None,
            "decision":     executer_decision(
                                score=0,
                                flags=r_validation["echecs_bloquants"],
                                montant_reclame=dossier.get("montant_reclame", 0)
                            ),
            "pipeline_complet": False
        }

    # Étape 2 : Scoring
    r_scoring = executer_scoring(dossier)

    # Étape 3 : Décision
    r_decision = executer_decision(
        score=r_scoring["score"],
        flags=r_scoring["flags"],
        montant_reclame=dossier.get("montant_reclame", 0)
    )

    return {
        "etape_arret":      None,
        "validation":       r_validation,
        "scoring":          r_scoring,
        "decision":         r_decision,
        "pipeline_complet": True
    }


# ── Dossier de base ─────────────────────────────────────────
BASE = {
    "date_sinistre":                     "2024-03-15",
    "date_debut_contrat":                "2023-01-01",
    "date_fin_contrat":                  "2025-12-31",
    "delai_declaration_jours":           3,
    "jours_depuis_sinistre":             10,
    "jours_depuis_souscription":         438,
    "type_sinistre":                     "SANTE_CONSUL",
    "garanties_contrat":                 ["SANTE_CONSUL", "SANTE_HOSPIT"],
    "documents_fournis":                 ["formulaire_sinistre", "piece_identite"],
    "statut_cotisations_cnss_employeur": "a_jour",
    "statut_affiliation":                "actif",
    "concerne_ayant_droit":              False,
    "cause_sinistre":                    "accident",
    "montant_net_complementaire":        90.0,
    "montant_reclame":                   150.0,
    "nb_soins_12m":                      3,
    "depassement_tarif_cnss":            False,
    "sinistre_hors_contrat":             False,
    "incoherence_duree_arret":           False,
    "nb_arrets_24m":                     0,
    "depassement_salaire_cnss":          False,
    "delai_declaration_at_jours":        2,
    "document_etranger_non_legalise":    False,
    "dossier_complet_premiere_fois":     True,
    "anciennete_contrat_jours":          1500,
    "coherence_cnss_facture":            True,
}


class TestPipelineIntegration:

    def test_scenario_1_dossier_ideal(self):
        """
        SCÉNARIO 1 — Dossier idéal
        Validation OK → Score élevé → ACCEPTER
        """
        r = executer_pipeline_complet(BASE)
        assert r["pipeline_complet"]             is True
        assert r["validation"]["valide"]          is True
        assert r["scoring"]["score"]              >= 70
        assert r["decision"]["decision"]          == "accepter"
        assert r["decision"]["necessite_validation_humaine"] is False

    def test_scenario_2_blocage_validation(self):
        """
        SCÉNARIO 2 — Blocage dès la validation
        Type sinistre non couvert → court-circuit → REFUSER
        Pipeline s'arrête à la validation
        """
        d = {**BASE, "type_sinistre": "PREV_DECES"}
        r = executer_pipeline_complet(d)
        assert r["pipeline_complet"]    is False
        assert r["etape_arret"]         == "validation"
        assert r["scoring"]             is None
        assert r["decision"]["decision"] == "refuser"

    def test_scenario_3_score_insuffisant(self):
        """
        SCÉNARIO 3 — Validation OK mais score bas
        Cumul d'anomalies → REFUSER
        """
        d = {
            **BASE,
            "nb_soins_12m":           15,
            "depassement_tarif_cnss": True,
            "nb_arrets_24m":          5,
            "coherence_cnss_facture": False,
        }
        r = executer_pipeline_complet(d)
        assert r["pipeline_complet"]             is True
        assert r["validation"]["valide"]          is True
        assert r["scoring"]["score"]              < 70
        assert r["decision"]["decision"]          in ["refuser", "complement_requis"]

    def test_scenario_4_complement_requis(self):
        """
        SCÉNARIO 4 — Score intermédiaire
        Validation OK, anomalies mineures → COMPLÉMENT REQUIS
        """
        d = {
            **BASE,
            "nb_soins_12m":    12,
            "delai_declaration_jours": 6,
        }
        r = executer_pipeline_complet(d)
        assert r["pipeline_complet"] is True
        assert r["decision"]["decision"] in ["complement_requis", "refuser"]

    def test_scenario_5_escalade_montant(self):
        """
        SCÉNARIO 5 — Dossier valide mais montant élevé
        Score OK → ACCEPTER mais escalade humaine obligatoire
        """
        d = {**BASE, "montant_reclame": 8000}
        r = executer_pipeline_complet(d)
        assert r["pipeline_complet"]                          is True
        assert r["decision"]["necessite_validation_humaine"]  is True

    def test_scenario_6_flag_bloquant_bon_score(self):
        """
        SCÉNARIO 6 — Flag INELIGIBILITE malgré score 85
        Le flag override le score → REFUSER immédiatement
        """
        d = {**BASE, "sinistre_hors_contrat": True}
        r = executer_pipeline_complet(d)
        # sinistre_hors_contrat génère INELIGIBILITE dans scoring
        assert r["decision"]["decision"] == "refuser"

    def test_coherence_flags_scoring_decision(self):
        """
        COHÉRENCE — Les flags du scoring arrivent bien dans la décision.
        """
        d = {**BASE, "depassement_salaire_cnss": True}
        r = executer_pipeline_complet(d)
        flags_scoring  = set(r["scoring"]["flags"])
        flags_decision = set(r["decision"]["flags"])
        assert flags_scoring == flags_decision, (
            f"Incohérence flags : scoring={flags_scoring}, décision={flags_decision}"
        )

    def test_pas_de_score_negatif_ni_superieur_100(self):
        """
        INVARIANT — Le score doit toujours rester entre 0 et 100.
        """
        d = {
            **BASE,
            "nb_soins_12m":              20,
            "depassement_tarif_cnss":    True,
            "sinistre_hors_contrat":     True,
            "depassement_salaire_cnss":  True,
            "incoherence_duree_arret":   True,
            "dossier_complet_premiere_fois": False,
        }
        r = executer_pipeline_complet(d)
        if r["scoring"]:
            assert 0 <= r["scoring"]["score"] <= 100