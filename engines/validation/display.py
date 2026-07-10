# engines/validation/display.py
"""Affichage formaté du rapport de validation."""


def afficher_rapport_validation(resultat: dict) -> None:
    print("\n" + "═" * 60)
    print("        RAPPORT DE VALIDATION — SmartClaim")
    print("═" * 60)
    print(f"\n{resultat['resume']}")
    print(f"\n📊 Statistiques :")
    print(f"   Règles évaluées : {resultat['nb_regles_total']}")
    print(f"   Réussies        : {resultat['nb_reussies']}")
    print(f"   Échouées        : {resultat['nb_echouees']}")
    if resultat["echecs_bloquants"]:
        print(f"\n🔴 Règles BLOQUANTES échouées :")
        for d in resultat["details"]:
            if d["id"] in resultat["echecs_bloquants"]:
                print(f"   [{d['id']}] {d['description']}")
                print(f"          → {d['message']}")
    if resultat["echecs_mineurs"]:
        print(f"\n🟡 Règles MINEURES échouées :")
        for d in resultat["details"]:
            if d["id"] in resultat["echecs_mineurs"]:
                print(f"   [{d['id']}] {d['description']}")
    print(f"\n{'✅ PEUT CONTINUER' if resultat['peut_continuer'] else '🛑 ARRÊT'}")
    print("═" * 60 + "\n")