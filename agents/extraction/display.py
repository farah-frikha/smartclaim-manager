# agents/extraction/display.py
"""
Affichage formaté des résultats d'extraction.
Utilisé pour le debug et les tests — pas en production.
"""


def afficher_rapport_extraction(resultat: dict) -> None:
    """Affiche un rapport lisible du résultat d'extraction."""
    print("\n" + "═" * 60)
    print("      RAPPORT D'EXTRACTION — SmartClaim")
    print("═" * 60)
    print(f"\nStatut         : {resultat['statut'].upper()}")
    print(f"Complétude     : {resultat.get('score_completude', 0):.0%}")
    print(f"Peut continuer : {' OUI' if resultat.get('peut_continuer') else ' NON'}")
    print(f"Durée LLM      : {resultat.get('llm_duree_ms', 0)}ms")
    print(f"Tentatives     : {resultat.get('llm_tentatives', 0)}")

    dossier = resultat.get("dossier_extrait", {})
    if dossier:
        print(f"\n Champs extraits :")
        for champ, valeur in dossier.items():
            icone = "oui" if valeur is not None else "echec"
            print(f"  {icone} {champ:<22} : {valeur}")

    manquants = resultat.get("champs_manquants", [])
    if manquants:
        print(f"\n  Champs manquants : {', '.join(manquants)}")

    invalides = resultat.get("champs_invalides", [])
    if invalides:
        print(f" Champs invalides  : {', '.join(invalides)}")

    print("═" * 60 + "\n")