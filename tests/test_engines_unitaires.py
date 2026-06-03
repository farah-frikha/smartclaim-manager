import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engines.validation_engine import executer_validation
from engines.scoring_engine     import executer_scoring
from engines.decision_engine    import executer_decision

# ═══════════════════════════════════════════════════════════
# FIXTURES — dossiers de base réutilisables
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def dossier_valide_base():
    """Dossier minimal valide — référence pour tous les tests."""
    return {
        "date_sinistre":                     "2024-03-15",
        "date_debut_contrat":                "2023-01-01",
        "date_fin_contrat":                  "2025-12-31",
        "delai_declaration_jours":           3,
        "jours_depuis_sinistre":             10,
        "jours_depuis_souscription":         438,
        "type_sinistre":                     "SANTE_CONSUL",
        "garanties_contrat":                 ["SANTE_CONSUL", "SANTE_HOSPIT", "PREV_ARRET"],
        "documents_fournis":                 ["formulaire_sinistre", "piece_identite"],
        "statut_cotisations_cnss_employeur": "a_jour",
        "statut_affiliation":                "actif",
        "concerne_ayant_droit":              False,
        "ayant_droit_declare":               False,
        "cause_sinistre":                    "accident",
        "montant_net_complementaire":        90.0,
        # Scoring fields
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
        "montant_reclame":                   150.0,
    }


# ═══════════════════════════════════════════════════════════
# TESTS — AGENT VALIDATION
# ═══════════════════════════════════════════════════════════

class TestValidationEngine:

    def test_dossier_valide_complet(self, dossier_valide_base):
        """CAS NOMINAL — tout correct → doit passer."""
        r = executer_validation(dossier_valide_base)
        assert r["valide"]           is True,  f"Attendu valide=True, obtenu: {r['resume']}"
        assert r["peut_continuer"]   is True
        assert r["nb_echouees"]      == 0
        assert len(r["echecs_bloquants"]) == 0

    def test_sinistre_avant_debut_contrat(self, dossier_valide_base):
        """VA-01 — sinistre antérieur à la souscription → refus."""
        d = {**dossier_valide_base, "date_sinistre": "2022-06-01"}
        r = executer_validation(d)
        assert r["valide"] is False
        assert "VA-01" in r["echecs_bloquants"]

    def test_sinistre_apres_fin_contrat(self, dossier_valide_base):
        """VA-02 — sinistre après expiration → refus."""
        d = {**dossier_valide_base, "date_sinistre": "2026-05-01"}
        r = executer_validation(d)
        assert r["valide"] is False
        assert "VA-02" in r["echecs_bloquants"]

    def test_type_sinistre_non_couvert(self, dossier_valide_base):
        """VA-04 — type de sinistre absent des garanties → refus."""
        d = {**dossier_valide_base, "type_sinistre": "PREV_DECES"}
        r = executer_validation(d)
        assert r["valide"] is False
        assert "VA-04" in r["echecs_bloquants"]

    def test_documents_manquants(self, dossier_valide_base):
        """VA-05 — document obligatoire absent → refus."""
        d = {**dossier_valide_base, "documents_fournis": ["formulaire_sinistre"]}
        r = executer_validation(d)
        assert r["valide"] is False
        assert "VA-05" in r["echecs_bloquants"]

    def test_employeur_cnss_retard(self, dossier_valide_base):
        """VA-07 — employeur en retard CNSS → refus."""
        d = {**dossier_valide_base, "statut_cotisations_cnss_employeur": "en_retard"}
        r = executer_validation(d)
        assert r["valide"] is False
        assert "VA-07" in r["echecs_bloquants"]

    def test_declaration_tardive_mineure(self, dossier_valide_base):
        """VA-03 — délai > 5 jours → échec mineur, dossier continue."""
        d = {**dossier_valide_base, "delai_declaration_jours": 8}
        r = executer_validation(d)
        # VA-03 est non obligatoire → valide mais avec avertissement
        assert r["peut_continuer"] is True
        assert "VA-03" in r["echecs_mineurs"]

    def test_structure_retour_complete(self, dossier_valide_base):
        """Vérifie que tous les champs attendus sont présents."""
        r = executer_validation(dossier_valide_base)
        champs_requis = [
            "valide", "peut_continuer", "nb_regles_total",
            "nb_reussies", "nb_echouees",
            "echecs_bloquants", "echecs_mineurs",
            "details", "resume"
        ]
        for champ in champs_requis:
            assert champ in r, f"Champ manquant dans le retour : '{champ}'"


# ═══════════════════════════════════════════════════════════
# TESTS — AGENT SCORING
# ═══════════════════════════════════════════════════════════

class TestScoringEngine:

    def test_dossier_propre_score_eleve(self, dossier_valide_base):
        """Dossier sans anomalie → score ≥ 70."""
        r = executer_scoring(dossier_valide_base)
        assert r["score"] >= 70, f"Score attendu ≥ 70, obtenu : {r['score']}"
        assert len(r["flags"]) == 0
        assert r["niveau_risque"] == "FAIBLE"

    def test_penalite_frequence_anormale(self, dossier_valide_base):
        """SS-01 — nb_soins_12m > 10 → pénalité et flag."""
        d = {**dossier_valide_base, "nb_soins_12m": 15}
        r = executer_scoring(d)
        assert "FREQUENCE_ANORMALE" in r["flags"]
        assert r["score"] < 100

    def test_penalite_depassement_salaire(self, dossier_valide_base):
        """SP-03 — dépassement salaire CNSS → forte pénalité."""
        d = {**dossier_valide_base, "depassement_salaire_cnss": True}
        r = executer_scoring(d)
        assert "DEPASSEMENT_SALAIRE" in r["flags"]
        assert r["delta_total"] <= -50

    def test_bonus_dossier_complet(self, dossier_valide_base):
        """SC-01 — dossier complet du premier coup → bonus."""
        d = {**dossier_valide_base, "dossier_complet_premiere_fois": True}
        r = executer_scoring(d)
        assert r["nb_bonus"] >= 1

    def test_cumul_penalites_score_negatif(self, dossier_valide_base):
        """Cumul de pénalités → score clampé à 0 minimum."""
        d = {
            **dossier_valide_base,
            "nb_soins_12m":              15,   # -20
            "depassement_tarif_cnss":    True,  # -25
            "sinistre_hors_contrat":     True,  # -40
            "depassement_salaire_cnss":  True,  # -50
            "incoherence_duree_arret":   True,  # -30
        }
        r = executer_scoring(d)
        assert r["score"] >= 0,   "Score ne peut pas être négatif"
        assert r["score"] <= 100, "Score ne peut pas dépasser 100"
        assert r["niveau_risque"] == "ELEVE"

    def test_structure_retour_complete(self, dossier_valide_base):
        """Vérifie que tous les champs attendus sont présents."""
        r = executer_scoring(dossier_valide_base)
        champs_requis = [
            "score", "score_base", "delta_total", "flags",
            "nb_penalites", "nb_bonus", "details",
            "niveau_risque", "resume"
        ]
        for champ in champs_requis:
            assert champ in r, f"Champ manquant : '{champ}'"


# ═══════════════════════════════════════════════════════════
# TESTS — AGENT DÉCISION
# ═══════════════════════════════════════════════════════════

class TestDecisionEngine:

    def test_score_eleve_accepter(self):
        """RD-01 — score ≥ 70 sans flag → accepter."""
        r = executer_decision(score=85, flags=[], montant_reclame=200)
        assert r["decision"] == "accepter"
        assert r["necessite_validation_humaine"] is False

    def test_score_moyen_complement(self):
        """RD-02 — 40 ≤ score < 70 → complement_requis."""
        r = executer_decision(score=55, flags=[], montant_reclame=200)
        assert r["decision"] == "complement_requis"

    def test_score_faible_refuser(self):
        """RD-03 — score < 40 → refuser."""
        r = executer_decision(score=25, flags=[], montant_reclame=200)
        assert r["decision"] == "refuser"

    def test_flag_bloquant_override_score(self):
        """RD-04 — flag INELIGIBILITE avec score 90 → refus immédiat."""
        r = executer_decision(score=90, flags=["INELIGIBILITE"], montant_reclame=200)
        assert r["decision"]      == "refuser"
        assert r["flag_bloquant"] == "INELIGIBILITE"

    def test_flag_complement_override_score(self):
        """RD-10 — flag INCOHERENCE_MEDICALE → complement + escalade."""
        r = executer_decision(score=80, flags=["INCOHERENCE_MEDICALE"], montant_reclame=200)
        assert r["decision"]                     == "complement_requis"
        assert r["necessite_validation_humaine"] is True

    def test_montant_eleve_escalade(self):
        """RD-08 — montant > 5000 TND → escalade obligatoire."""
        r = executer_decision(score=75, flags=[], montant_reclame=8000)
        assert r["necessite_validation_humaine"] is True
        assert r["decision"] == "accepter"

    def test_zone_grise_escalade(self):
        """RD-09 — score dans zone grise [45-55] → escalade recommandée."""
        r = executer_decision(score=50, flags=[], montant_reclame=300)
        assert r["necessite_validation_humaine"] is True

    def test_messages_presents(self):
        """Les messages client et interne ne doivent pas être vides."""
        r = executer_decision(score=75, flags=[], montant_reclame=200)
        assert r["message_client"]  != ""
        assert r["message_interne"] != ""
        assert r["timestamp"]       != ""

    def test_structure_retour_complete(self):
        """Vérifie que tous les champs attendus sont présents."""
        r = executer_decision(score=75, flags=[], montant_reclame=200)
        champs_requis = [
            "decision", "score", "flags", "motif_principal",
            "flag_bloquant", "necessite_validation_humaine",
            "motif_escalade", "message_client", "message_interne",
            "seuil_utilise", "timestamp", "resume"
        ]
        for champ in champs_requis:
            assert champ in r, f"Champ manquant : '{champ}'"