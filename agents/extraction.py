# agents/extraction.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
import time
from datetime import datetime

import ollama
from loguru import logger

from config import (
    OLLAMA_MODEL, OLLAMA_URL,
    LLM_MAX_TOKENS, LLM_TEMPERATURE,
    PROMPTS_DIR
)

# ────────────────────────────────────────────────────────────
# SECTION 1 — SCHÉMA DES CHAMPS ATTENDUS
# ────────────────────────────────────────────────────────────

SCHEMA_EXTRACTION = {
    "nom_assure":        {"type": str,   "obligatoire": True},
    "prenom_assure":     {"type": str,   "obligatoire": False},
    "numero_cnss":       {"type": str,   "obligatoire": True},
    "numero_contrat":    {"type": str,   "obligatoire": True},
    "date_sinistre":     {"type": str,   "obligatoire": True},
    "type_sinistre":     {"type": str,   "obligatoire": True},
    "montant_reclame":   {"type": float, "obligatoire": True},
    "description":       {"type": str,   "obligatoire": False},
    "date_declaration":  {"type": str,   "obligatoire": False},
    "numero_dossier":    {"type": str,   "obligatoire": False},
}

TYPES_SINISTRES_VALIDES = [
    "SANTE_CONSUL",
    "SANTE_HOSPIT",
    "PREV_ARRET",
    "PREV_INVALIDITE",
    "PREV_DECES",
    "AT_ACCIDENT",
    "AUTO_ACCIDENT",
    "AUTO_VOL",
    "AUTO_BRIS_GLACE",
    "AUTRE"
]


# ────────────────────────────────────────────────────────────
# SECTION 2 — PROMPT FEW-SHOT
# ────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """Tu es un assistant spécialisé dans l'extraction d'informations depuis des documents d'assurance groupe tunisienne.

Voici le texte extrait d'un document d'assurance :
---
{texte_ocr}
---

Extrais exactement les informations suivantes et retourne UNIQUEMENT un objet JSON valide.
N'ajoute aucun texte avant ou après le JSON. Pas de markdown, pas de backticks.

Champs à extraire :
- nom_assure : nom de famille de l'assuré (string)
- prenom_assure : prénom de l'assuré (string ou null)
- numero_cnss : numéro CNSS/sécurité sociale (string)
- numero_contrat : numéro de police ou contrat d'assurance (string)
- date_sinistre : date du sinistre au format YYYY-MM-DD (string)
- type_sinistre : UN SEUL parmi {types_valides} (string)
- montant_reclame : montant total réclamé en TND, nombre décimal (float)
- description : brève description du sinistre (string ou null)
- date_declaration : date de déclaration au format YYYY-MM-DD (string ou null)
- numero_dossier : numéro de dossier interne si présent (string ou null)

Règles IMPORTANTES :
1. Si une information est absente, mets null (jamais de chaîne vide)
2. Les dates DOIVENT être au format YYYY-MM-DD
3. Les montants sont des nombres (pas de texte, pas de symbole TND)
4. Le type_sinistre DOIT être exactement l'un des codes fournis
5. Ne jamais inventer une information absente du texte

EXEMPLES :

Exemple 1 — Accident auto :
Texte : "Mohamed Ben Salah, CNSS 145789632, contrat STAR-AUTO-2024-00847, accident le 15/03/2026, montant 2800 TND"
JSON :
{{"nom_assure": "Ben Salah", "prenom_assure": "Mohamed", "numero_cnss": "145789632", "numero_contrat": "STAR-AUTO-2024-00847", "date_sinistre": "2026-03-15", "type_sinistre": "AUTO_ACCIDENT", "montant_reclame": 2800.0, "description": "Accident automobile", "date_declaration": null, "numero_dossier": null}}

Exemple 2 — Arrêt de travail :
Texte : "Fatma Trabelsi, N° affiliation 987654321, police COMAR-PREV-2023-00123, arrêt maladie du 10/01/2026 au 20/01/2026, indemnité 450 TND"
JSON :
{{"nom_assure": "Trabelsi", "prenom_assure": "Fatma", "numero_cnss": "987654321", "numero_contrat": "COMAR-PREV-2023-00123", "date_sinistre": "2026-01-10", "type_sinistre": "PREV_ARRET", "montant_reclame": 450.0, "description": "Arrêt maladie 10 jours", "date_declaration": null, "numero_dossier": null}}

Exemple 3 — Consultation médicale :
Texte : "Sami Gharbi, CNSS 112233445, contrat GAT-SANTE-2025-00789, consultation médecin généraliste le 05/04/2026, facture 90 TND"
JSON :
{{"nom_assure": "Gharbi", "prenom_assure": "Sami", "numero_cnss": "112233445", "numero_contrat": "GAT-SANTE-2025-00789", "date_sinistre": "2026-04-05", "type_sinistre": "SANTE_CONSUL", "montant_reclame": 90.0, "description": "Consultation médecin généraliste", "date_declaration": null, "numero_dossier": null}}

Maintenant extrais les informations du document fourni :"""


def construire_prompt(texte_ocr: str) -> str:
    """
    Construit le prompt final en injectant le texte OCR
    et la liste des types de sinistres valides.
    """
    # Tronquer si trop long (limite contexte LLM)
    texte_tronque = texte_ocr[:6000] if len(texte_ocr) > 6000 else texte_ocr

    return PROMPT_TEMPLATE.format(
        texte_ocr=texte_tronque,
        types_valides=", ".join(TYPES_SINISTRES_VALIDES)
    )


# ────────────────────────────────────────────────────────────
# SECTION 3 — NETTOYAGE ET VALIDATION JSON
# ────────────────────────────────────────────────────────────

def nettoyer_json(reponse_llm: str) -> str:
    """
    Nettoie la réponse du LLM pour extraire le JSON pur.
    Gère les cas où le modèle ajoute du texte ou des backticks.
    """
    texte = reponse_llm.strip()

    # Supprimer les blocs markdown ```json ... ```
    texte = re.sub(r"```json\s*", "", texte)
    texte = re.sub(r"```\s*", "", texte)

    # Extraire le premier objet JSON valide { ... }
    match = re.search(r'\{.*\}', texte, re.DOTALL)
    if match:
        return match.group(0).strip()

    return texte


def normaliser_date(valeur) -> str:
    """
    Normalise une date vers le format YYYY-MM-DD.
    Accepte DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD.
    """
    if valeur is None:
        return None
    if isinstance(valeur, str):
        # Déjà au bon format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', valeur):
            return valeur
        # Format DD/MM/YYYY ou DD-MM-YYYY
        match = re.match(r'^(\d{2})[/\-](\d{2})[/\-](\d{4})$', valeur)
        if match:
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return valeur


def valider_et_normaliser(donnees: dict) -> dict:
    """
    Valide et normalise le JSON extrait par le LLM.

    Retourne un dict avec :
        donnees_validees : dict — champs validés et normalisés
        champs_manquants : list — champs obligatoires absents
        champs_invalides : list — champs présents mais invalides
        score_completude : float — % de champs renseignés
    """
    donnees_validees = {}
    champs_manquants = []
    champs_invalides = []

    for champ, config in SCHEMA_EXTRACTION.items():
        valeur = donnees.get(champ)

        # Champ absent ou null
        if valeur is None:
            if config["obligatoire"]:
                champs_manquants.append(champ)
            donnees_validees[champ] = None
            continue

        # Normalisation selon le type
        try:
            if config["type"] == float:
                # Nettoyer les montants : "2 800 TND" → 2800.0
                if isinstance(valeur, str):
                    valeur_nettoyee = re.sub(r'[^\d.,]', '', valeur)
                    valeur_nettoyee = valeur_nettoyee.replace(',', '.')
                    valeur = float(valeur_nettoyee)
                else:
                    valeur = float(valeur)

            elif config["type"] == str:
                valeur = str(valeur).strip()
                if valeur == "" or valeur.lower() == "null":
                    valeur = None
                    if config["obligatoire"]:
                        champs_manquants.append(champ)

            donnees_validees[champ] = valeur

        except (ValueError, TypeError):
            champs_invalides.append(champ)
            donnees_validees[champ] = None

    # Normalisation des dates
    for champ_date in ["date_sinistre", "date_declaration"]:
        if donnees_validees.get(champ_date):
            donnees_validees[champ_date] = normaliser_date(
                donnees_validees[champ_date]
            )

    # Validation type sinistre
    type_sin = donnees_validees.get("type_sinistre")
    if type_sin and type_sin not in TYPES_SINISTRES_VALIDES:
        logger.warning(
            f"Type sinistre non reconnu : '{type_sin}' → 'AUTRE'"
        )
        donnees_validees["type_sinistre"] = "AUTRE"

    # Score de complétude
    champs_renseignes = sum(
        1 for v in donnees_validees.values() if v is not None
    )
    score_completude = round(
        champs_renseignes / len(SCHEMA_EXTRACTION), 2
    )

    return {
        "donnees_validees": donnees_validees,
        "champs_manquants": champs_manquants,
        "champs_invalides": champs_invalides,
        "score_completude": score_completude
    }


# ────────────────────────────────────────────────────────────
# SECTION 4 — APPEL LLM AVEC RETRY
# ────────────────────────────────────────────────────────────

def appeler_llm(prompt: str, max_retries: int = 3) -> dict:
    """
    Envoie le prompt à Qwen via Ollama avec mécanisme de retry.

    Retourne un dict contenant :
        succes      : bool
        reponse_brute : str
        json_parse  : dict | None
        tentatives  : int
        duree_ms    : float
    """
    t_debut = time.perf_counter()

    for tentative in range(1, max_retries + 1):
        try:
            logger.info(
                f"Appel LLM (tentative {tentative}/{max_retries})..."
            )

            reponse = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                }
            )

            reponse_brute = reponse["message"]["content"]
            json_nettoye  = nettoyer_json(reponse_brute)

            # Tentative de parsing JSON
            json_parse = json.loads(json_nettoye)

            duree_ms = round(
                (time.perf_counter() - t_debut) * 1000, 1
            )
            logger.success(
                f"LLM répondu en {duree_ms}ms "
                f"(tentative {tentative})"
            )

            return {
                "succes":        True,
                "reponse_brute": reponse_brute,
                "json_parse":    json_parse,
                "tentatives":    tentative,
                "duree_ms":      duree_ms
            }

        except json.JSONDecodeError as e:
            logger.warning(
                f"Tentative {tentative} : JSON invalide — {e}"
            )
            if tentative == max_retries:
                logger.error("Toutes les tentatives ont échoué")

        except Exception as e:
            logger.error(f"Tentative {tentative} : erreur LLM — {e}")
            if tentative == max_retries:
                break

    duree_ms = round((time.perf_counter() - t_debut) * 1000, 1)
    return {
        "succes":        False,
        "reponse_brute": "",
        "json_parse":    None,
        "tentatives":    max_retries,
        "duree_ms":      duree_ms
    }


# ────────────────────────────────────────────────────────────
# SECTION 5 — POINT D'ENTRÉE PRINCIPAL
# ────────────────────────────────────────────────────────────

def executer_extraction(texte_ocr: str) -> dict:
    """
    Point d'entrée de l'Agent Extraction.

    Reçoit le texte brut de l'Agent Capture,
    envoie à Qwen via Ollama, valide et retourne
    un JSON structuré prêt pour l'Agent Validation.

    Paramètres :
        texte_ocr : str — texte brut produit par capture.py

    Retourne un dict contenant :
        statut           : succes / erreur / confiance_faible
        dossier_extrait  : dict — champs extraits et normalisés
        champs_manquants : list — champs obligatoires absents
        champs_invalides : list — champs présents mais invalides
        score_completude : float — 0 à 1
        peut_continuer   : bool — True si champs critiques présents
        llm_tentatives   : int
        llm_duree_ms     : float
        timestamp        : str
    """
    if not texte_ocr or not texte_ocr.strip():
        logger.error("Texte OCR vide — impossible d'extraire")
        return {
            "statut":          "erreur",
            "message":         "Texte OCR vide",
            "peut_continuer":  False
        }

    logger.info(
        f"Extraction LLM sur {len(texte_ocr)} caractères..."
    )

    # Construction du prompt
    prompt = construire_prompt(texte_ocr)

    # Appel LLM
    resultat_llm = appeler_llm(prompt)

    if not resultat_llm["succes"]:
        return {
            "statut":          "erreur",
            "message":         "Le LLM n'a pas retourné de JSON valide",
            "peut_continuer":  False,
            "llm_tentatives":  resultat_llm["tentatives"],
            "llm_duree_ms":    resultat_llm["duree_ms"],
            "timestamp":       datetime.now().isoformat()
        }

    # Validation et normalisation
    validation = valider_et_normaliser(resultat_llm["json_parse"])

    # Décision de continuité
    champs_critiques = ["nom_assure", "numero_contrat",
                        "date_sinistre", "type_sinistre"]
    champs_critiques_manquants = [
        c for c in champs_critiques
        if c in validation["champs_manquants"]
    ]
    peut_continuer = len(champs_critiques_manquants) == 0

    # Statut final
    if not peut_continuer:
        statut = "erreur"
        logger.error(
            f"Champs critiques manquants : "
            f"{champs_critiques_manquants}"
        )
    elif validation["score_completude"] < 0.6:
        statut = "confiance_faible"
        logger.warning(
            f"Complétude faible : "
            f"{validation['score_completude']}"
        )
    else:
        statut = "succes"
        logger.success(
            f"Extraction réussie — "
            f"complétude={validation['score_completude']}, "
            f"LLM={resultat_llm['duree_ms']}ms"
        )

    return {
        "statut":           statut,
        "dossier_extrait":  validation["donnees_validees"],
        "champs_manquants": validation["champs_manquants"],
        "champs_invalides": validation["champs_invalides"],
        "score_completude": validation["score_completude"],
        "peut_continuer":   peut_continuer,
        "llm_tentatives":   resultat_llm["tentatives"],
        "llm_duree_ms":     resultat_llm["duree_ms"],
        "timestamp":        datetime.now().isoformat()
    }


# ────────────────────────────────────────────────────────────
# SECTION 6 — AFFICHAGE
# ────────────────────────────────────────────────────────────

def afficher_rapport_extraction(resultat: dict) -> None:
    print("\n" + "═" * 60)
    print("      RAPPORT D'EXTRACTION — SmartClaim")
    print("═" * 60)
    print(f"\nStatut       : {resultat['statut'].upper()}")
    print(f"Complétude   : {resultat.get('score_completude', 0):.0%}")
    print(f"Peut continuer : {' OUI' if resultat.get('peut_continuer') else ' NON'}")
    print(f"Durée LLM    : {resultat.get('llm_duree_ms', 0)}ms")
    print(f"Tentatives   : {resultat.get('llm_tentatives', 0)}")

    dossier = resultat.get("dossier_extrait", {})
    if dossier:
        print(f"\n Champs extraits :")
        for champ, valeur in dossier.items():
            icone = "✅" if valeur is not None else "⬜"
            print(f"  {icone} {champ:<22} : {valeur}")

    manquants = resultat.get("champs_manquants", [])
    if manquants:
        print(f"\n Champs manquants : {', '.join(manquants)}")

    invalides = resultat.get("champs_invalides", [])
    if invalides:
        print(f" Champs invalides  : {', '.join(invalides)}")

    print("═" * 60 + "\n")


# ────────────────────────────────────────────────────────────
# SECTION 7 — TEST
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── Test 1 : avec le texte de votre vrai document OCR ───
    texte_test = """
    ASSURANCES EL AMAN
    FORMULAIRE DE DÉCLARATION DE SINISTRE
    Numéro de dossier : SIN-2026-004587
    Date de déclaration : 14/05/2026
    Nom et prénom : Mohamed Ben Salah
    Numéro CNss : 145789632
    Numéro de contrat : STAR-AUTO-2024-00847
    Date du sinistre : 15/03/2026
    Type de sinistre : Accident automobile
    Montant total estimé : 2800 TND
    Description : Collision avec un autre véhicule
    au carrefour de l'Avenue Mohamed V, Tunis.
    """

    print("TEST 1 — Texte simulé document réel")
    r1 = executer_extraction(texte_test)
    afficher_rapport_extraction(r1)

    # Assertions Test 1
    assert r1["statut"] == "succes", \
        f"Attendu: succes, obtenu: {r1['statut']}"
    assert r1["peut_continuer"] is True
    assert r1["dossier_extrait"]["numero_contrat"] \
        == "STAR-AUTO-2024-00847", \
        f"Contrat incorrect: {r1['dossier_extrait']['numero_contrat']}"
    assert r1["dossier_extrait"]["montant_reclame"] == 2800.0, \
        f"Montant incorrect: {r1['dossier_extrait']['montant_reclame']}"
    assert r1["dossier_extrait"]["date_sinistre"] == "2026-03-15", \
        f"Date incorrecte: {r1['dossier_extrait']['date_sinistre']}"
    print("✅ Test 1 — toutes les assertions passent\n")

    # ── Test 2 : pipeline Capture → Extraction ──────────────
    print("TEST 2 — Pipeline Capture + Extraction sur PDF réel")

    from agents.capture import executer_capture
    import os
    from pathlib import Path

    # Chercher un PDF dans data/
    pdfs = list(Path("data").rglob("*.pdf"))
    if pdfs:
        pdf_path = str(pdfs[0])
        print(f"PDF trouvé : {pdf_path}")

        r_capture = executer_capture(pdf_path)

        if r_capture["statut"] == "succes":
            print(f"Capture OK — {r_capture['nb_mots_total']} mots")
            r2 = executer_extraction(r_capture["texte_complet"])
            afficher_rapport_extraction(r2)

            if r2["statut"] == "succes":
                print("✅ Test 2 — Pipeline Capture→Extraction validé")
            else:
                print(
                    f"⚠️  Extraction partielle : "
                    f"statut={r2['statut']}, "
                    f"manquants={r2.get('champs_manquants')}"
                )
        else:
            print(f"❌ Capture échouée : {r_capture.get('message')}")
    else:
        print("Aucun PDF trouvé dans data/ — Test 2 ignoré")
        print("Placez un PDF dans data/contrats/ pour tester")