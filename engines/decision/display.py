# engines/decision/display.py
"""Affichage formaté du rapport de décision."""


def afficher_rapport_decision(resultat: dict) -> None:
    icones = {
        "accepter":          "✅ ACCEPTÉ",
        "refuser":           "❌ REFUSÉ",
        "complement_requis": "⚠️ COMPLÉMENT REQUIS"
    }
    print("\n" + "═" * 60)
    print("         RAPPORT DE DÉCISION — SmartClaim")
    print("═" * 60)
    print(f"\n  Décision : {icones.get(resultat['decision'], resultat['decision'].upper())}")
    print(f"  Score    : {resultat['score']}/100")
    print(f"  Seuil    : {resultat['seuil_utilise']}")
    if resultat["flag_bloquant"]:
        print(f"\n  🔴 Flag bloquant : {resultat['flag_bloquant']}")
    if resultat["flags"]:
        print(f"\n  🚩 Flags actifs  : {', '.join(resultat['flags'])}")
    print(f"\n  📋 Motif          : {resultat['motif_principal']}")
    print(f"  💬 Message client : {resultat['message_client']}")
    if resultat["necessite_validation_humaine"]:
        print(f"\n  👤 ESCALADE : {resultat['motif_escalade']}")
    print(f"\n  🕐 Horodatage : {resultat['timestamp']}")
    print("═" * 60 + "\n")