# tests/test_decision.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.decision_engine import executer_decision, afficher_rapport_decision
from config import SEUIL_COMPLEMENT
if __name__ == "__main__":

    print("TEST 1 — Score élevé, aucun flag → ACCEPTER")
    r1 = executer_decision(score=82, flags=[], montant_reclame=200)
    afficher_rapport_decision(r1)
    assert r1["decision"] == "accepter", f"Attendu: accepter, obtenu: {r1['decision']}"

    print("TEST 2 — Score moyen, flag mineur → COMPLÉMENT")
    r2 = executer_decision(score=58, flags=["FREQUENCE_ANORMALE"], montant_reclame=800)
    afficher_rapport_decision(r2)
    assert r2["decision"] == "complement_requis"

    print("TEST 3 — Score faible, pas de flag → REFUSER")
    r3 = executer_decision(score=30, flags=[], montant_reclame=150)
    afficher_rapport_decision(r3)
    assert r3["decision"] == "refuser"

    print("TEST 4 — Flag INELIGIBILITE → REFUS IMMÉDIAT")
    r4 = executer_decision(score=75, flags=["INELIGIBILITE"], montant_reclame=500)
    afficher_rapport_decision(r4)
    assert r4["decision"] == "refuser"
    assert r4["flag_bloquant"] == "INELIGIBILITE"

    print("TEST 5 — Flag INCOHERENCE_MEDICALE → COMPLÉMENT + ESCALADE")
    r5 = executer_decision(score=65, flags=["INCOHERENCE_MEDICALE"], montant_reclame=400)
    afficher_rapport_decision(r5)
    assert r5["decision"] == "complement_requis"
    assert r5["necessite_validation_humaine"] == True

    print("TEST 6 — Score 75 mais montant > 5000 → ACCEPTER + ESCALADE")
    r6 = executer_decision(score=75, flags=[], montant_reclame=7500)
    afficher_rapport_decision(r6)
    assert r6["decision"] == "accepter"
    assert r6["necessite_validation_humaine"] == True

    print("TEST 7 — Score zone grise (50) → COMPLÉMENT + ESCALADE")
    r7 = executer_decision(score=50, flags=[], montant_reclame=300)
    afficher_rapport_decision(r7)
    assert r7["necessite_validation_humaine"] == True

