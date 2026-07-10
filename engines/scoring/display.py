# engines/scoring/display.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
from config import SEUIL_COMPLEMENT


def afficher_rapport_scoring(resultat: dict) -> None:
    print("\n" + "═" * 60)
    print("         RAPPORT DE SCORING — SmartClaim")
    print("═" * 60)
    print(f"\n{resultat['resume']}")
    print(f"\n📊 Détail :")
    print(f"   Score de base : {resultat['score_base']}/100")
    print(f"   Delta total   : {resultat['delta_total']:+d} pts")
    print(f"   Score final   : {resultat['score']}/100")
    print(f"   Niveau risque : {resultat['niveau_risque']}")
    declenchees = [d for d in resultat["details"] if d["declenchee"]]
    if declenchees:
        print(f"\n⚡ Règles déclenchées ({len(declenchees)}) :")
        for d in declenchees:
            signe = "🔴" if d["delta_score"] < 0 else "🟢"
            print(f"   {signe} [{d['id']}] {d['description']}")
            print(f"          Delta : {d['delta_score']:+d} pts")
    if resultat["flags"]:
        print(f"\n🚩 Flags : {', '.join(resultat['flags'])}")
    print(f"\n{'✅ PEUT CONTINUER' if resultat['score'] >= SEUIL_COMPLEMENT else '🛑 Score insuffisant'}")
    print("═" * 60 + "\n")