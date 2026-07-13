# test_extraction_cnam.py
"""
Test isolé de l'extraction CNAM_SOINS.
Vérifie que le prompt et le schéma fonctionnent sur le texte OCR réel,
sans toucher au pipeline.
"""
import json
from pathlib import Path
from agents.extraction.llm_client import appeler_llm
from config import PROMPTS_DIR

# Texte OCR réel extrait par OCR.space de votre formulaire
TEXTE_OCR = """République Tunisienne
Ministère des Affaires, de la Solidarité
Caisse Nationale d'Assurance Maladie
الصندوق الوطني للتأمين على المرض CNAM
DEMANDE DE PRISE EN CHARGE DE SOINS ET D'APPAREILLAGE
Régime de réparation des préjudices resultant des Accidents du Travail
LA VICTIME
Nom et Prénom
1236700 2105
Date et heure de l'Accident ou de la Maladie
L'EMPLOYEUR
Nom ou raison sociale
Je soussigné (e) Frikha Farah
Titulaire de la CIN 231 25156
demande en ma qualité de Stagiaire
la prise en charge par la C.N.A.M des frais de
Soins auprès de Rowaida Clinic
Consultation médicale auprès de Dr Rowaida
Exécution d'ordonnance auprès de
Hospitalisation à
Appareillages"""


def charger_prompt_cnam():
    """Charge le prompt CNAM_SOINS."""
    chemin = PROMPTS_DIR / "extraction_cnam_soins.txt"
    return chemin.read_text(encoding="utf-8")


def main():
    print("=" * 60)
    print("TEST EXTRACTION CNAM_SOINS (isolé)")
    print("=" * 60)

    # Construire le prompt avec le texte OCR
    template = charger_prompt_cnam()
    prompt = template.replace("{texte_ocr}", TEXTE_OCR)

    print("\nAppel du LLM...\n")
    reponse = appeler_llm(prompt)

    print("Réponse brute du LLM :")
    print("-" * 60)
    print(reponse)
    print("-" * 60)

    # Tenter de parser le JSON
    try:
        # Nettoyer d'éventuels artefacts markdown
        texte = reponse.strip()
        if texte.startswith("```"):
            texte = texte.split("```")[1]
            if texte.startswith("json"):
                texte = texte[4:]
        debut = texte.find("{")
        fin = texte.rfind("}") + 1
        donnees = json.loads(texte[debut:fin])

        print("\n JSON parsé avec succès :\n")
        for champ, valeur in donnees.items():
            print(f"  {champ:25} : {valeur}")

    except Exception as e:
        print(f"\n Erreur de parsing JSON : {e}")


if __name__ == "__main__":
    main()