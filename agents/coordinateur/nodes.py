# agents/coordinateur/nodes.py
"""
Les 7 nœuds du graphe LangGraph.
Chaque nœud correspond à une étape du pipeline de traitement.
Convention : chaque nœud reçoit EtatDossier et retourne EtatDossier.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import time
import sqlite3
from datetime import datetime
from loguru import logger
from agents.classification import classifier_domaine
from agents.capture    import executer_capture
from agents.extraction import executer_extraction
from engines.validation import executer_validation
from engines.validation.domaines import get_regles_domaine
from engines.scoring    import executer_scoring
from engines.decision   import executer_decision
from engines.database import (
    generer_reference_dossier, sauvegarder_document,
    sauvegarder_extraction, sauvegarder_validation,
    sauvegarder_scoring, sauvegarder_decision,
    get_connection, log_audit
)
from agents.coordinateur.state      import EtatDossier
from agents.coordinateur.enrichment import enrichir_dossier


def noeud_capture(etat: EtatDossier) -> EtatDossier:
    logger.info("=" * 50)
    logger.info("AGENT CAPTURE — démarrage")
    t0 = time.perf_counter()

    try:
        resultat = executer_capture(etat["chemin_fichier"])

        if resultat["statut"] != "succes":
            logger.error(f"Capture échouée : {resultat.get('message')}")
            return {
                **etat,
                "etape_actuelle":   "capture",
                "etape_arret":      "capture",
                "peut_continuer":   False,
                "resultat_capture": resultat,
                "erreurs": (etat.get("erreurs") or []) + [
                    f"Capture : {resultat.get('message')}"
                ]
            }
        texte_ocr = resultat.get("texte_complet", "")
        classification = classifier_domaine(texte_ocr)
        domaine = classification["domaine"]

        ref  = generer_reference_dossier()
        conn = get_connection()

        employe_id = etat.get("employe_id") or 1

        cursor = conn.execute("""
            INSERT INTO dossiers_sinistres (
                reference_dossier, employe_id, contrat_id, domaine,
                type_sinistre_id, date_sinistre, statut_global
            ) VALUES (?, ?, 1, ?, date('now'), 'en_traitement')
        """, (ref, employe_id, domaine))
        dossier_id = cursor.lastrowid
        conn.commit()
        conn.close()

        document_id = sauvegarder_document(dossier_id, resultat)
        duree = round((time.perf_counter() - t0) * 1000)
        logger.success(
            f"Capture OK — {resultat['nb_mots_total']} mots, "
            f"confiance={resultat['score_confiance']}, {duree}ms"
        )
        texte_ocr = resultat.get("texte_complet", "")
        classification = classifier_domaine(texte_ocr)
        domaine = classification["domaine"]

        duree = round((time.perf_counter() - t0) * 1000)
        logger.success(
            f"Capture OK — {resultat['nb_mots_total']} mots, "
            f"confiance={resultat['score_confiance']}, "
            f"domaine={domaine}, {duree}ms"
        )
        return {
            **etat,
            "dossier_id":        dossier_id,
            "document_id":       document_id,
            "reference_dossier": ref,
            "domaine":           domaine,
            "resultat_capture":  resultat,
            "etape_actuelle":    "capture",
            "peut_continuer":    True,
        }

    except Exception as e:
        logger.error(f"Erreur noeud_capture : {e}")
        return {
            **etat,
            "etape_actuelle": "capture",
            "etape_arret":    "capture",
            "peut_continuer": False,
            "erreurs": (etat.get("erreurs") or []) + [str(e)]
        }
    
def noeud_extraction(etat: EtatDossier) -> EtatDossier:
    """Nœud 2 — Extraction LLM du texte OCR vers JSON structuré."""
    logger.info("=" * 50)
    logger.info("AGENT EXTRACTION — démarrage")
    t0 = time.perf_counter()

    try:
        texte    = etat["resultat_capture"]["texte_complet"]
        domaine  = etat.get("domaine", "AUTO")
        resultat = executer_extraction(texte , domaine=domaine)

        sauvegarder_extraction(
            etat["dossier_id"],
            etat["document_id"],
            resultat
        )

        duree = round((time.perf_counter() - t0) * 1000)
        logger.success(
            f"Extraction OK — "
            f"complétude={resultat.get('score_completude', 0)}, "
            f"domaine={domaine}, "
            f"LLM={resultat.get('llm_duree_ms')}ms"

        )

        return {
            **etat,
            "resultat_extraction": resultat,
            "etape_actuelle":      "extraction",
            "peut_continuer":      resultat.get("peut_continuer", False),
            "etape_arret": None if resultat.get("peut_continuer") else "extraction"
        }

    except Exception as e:
        logger.error(f"Erreur noeud_extraction : {e}")
        return {
            **etat,
            "etape_actuelle": "extraction",
            "etape_arret":    "extraction",
            "peut_continuer": False,
            "erreurs": (etat.get("erreurs") or []) + [str(e)]
        }


def noeud_validation(etat: EtatDossier) -> EtatDossier:
    """Nœud 3 — Validation réglementaire des 15 règles tunisiennes."""
    logger.info("=" * 50)
    logger.info("AGENT VALIDATION — démarrage")

    try:
        dossier_brut    = etat["resultat_extraction"]["dossier_extrait"]
        dossier_enrichi = enrichir_dossier(dossier_brut)

        logger.info(
            f"Dossier enrichi — domaine={etat.get('domaine', 'AUTO')}, "
            f"date_debut={dossier_enrichi.get('date_debut_contrat')}, "
            f"delai={dossier_enrichi.get('delai_declaration_jours')}j"
        )
        domaine       = etat.get("domaine", "AUTO")
        chemin_regles = get_regles_domaine(domaine)
        resultat      = executer_validation(dossier_enrichi, chemin_regles)
        sauvegarder_validation(etat["dossier_id"], resultat)

        if resultat["valide"]:
            logger.success(
                f"Validation OK — "
                f"{resultat['nb_reussies']}/{resultat['nb_regles_total']} "
                f"règles passées"
            )
        else:
            logger.warning(
                f"Validation ÉCHOUÉE — "
                f"bloquants: {resultat['echecs_bloquants']}"
            )

        return {
            **etat,
            "resultat_validation": resultat,
            "etape_actuelle":      "validation",
            "peut_continuer":      resultat.get("peut_continuer", False),
            "etape_arret": None if resultat.get("peut_continuer") else "validation"
        }

    except Exception as e:
        logger.error(f"Erreur noeud_validation : {e}")
        return {
            **etat,
            "etape_actuelle": "validation",
            "etape_arret":    "validation",
            "peut_continuer": False,
            "erreurs": (etat.get("erreurs") or []) + [str(e)]
        }


def noeud_scoring(etat: EtatDossier) -> EtatDossier:
    """Nœud 4 — Calcul du score de risque composite 0-100."""
    logger.info("=" * 50)
    logger.info("AGENT SCORING — démarrage")

    try:
        dossier  = etat["resultat_extraction"]["dossier_extrait"]
        resultat = executer_scoring(dossier)
        score_id = sauvegarder_scoring(etat["dossier_id"], resultat)

        logger.success(
            f"Scoring OK — score={resultat['score']}/100, "
            f"risque={resultat['niveau_risque']}, "
            f"flags={resultat['flags']}"
        )

        return {
            **etat,
            "resultat_scoring": resultat,
            "score_id":         score_id,
            "etape_actuelle":   "scoring",
            "peut_continuer":   True,
        }

    except Exception as e:
        logger.error(f"Erreur noeud_scoring : {e}")
        return {
            **etat,
            "etape_actuelle": "scoring",
            "etape_arret":    "scoring",
            "peut_continuer": False,
            "erreurs": (etat.get("erreurs") or []) + [str(e)]
        }


def noeud_decision(etat: EtatDossier) -> EtatDossier:
    """Nœud 5 — Décision préliminaire finale."""
    logger.info("=" * 50)
    logger.info("AGENT DÉCISION — démarrage")

    try:
        scoring    = etat["resultat_scoring"]
        extraction = etat["resultat_extraction"]["dossier_extrait"]

        resultat = executer_decision(
            score           = scoring["score"],
            flags           = scoring["flags"],
            montant_reclame = extraction.get("montant_reclame", 0) or 0
        )

        decision_id = sauvegarder_decision(
            etat["dossier_id"],
            etat["score_id"],
            resultat
        )

        logger.success(
            f"Décision : {resultat['decision'].upper()} — "
            f"{resultat['motif_principal']}"
        )

        return {
            **etat,
            "resultat_decision": resultat,
            "etape_actuelle":    "decision",
            "peut_continuer":    True,
        }

    except Exception as e:
        logger.error(f"Erreur noeud_decision : {e}")
        return {
            **etat,
            "etape_actuelle": "decision",
            "etape_arret":    "decision",
            "peut_continuer": False,
            "erreurs": (etat.get("erreurs") or []) + [str(e)]
        }


def noeud_erreur(etat: EtatDossier) -> EtatDossier:
    """Nœud terminal — enregistre l'arrêt prématuré du pipeline."""
    logger.error(
        f"Pipeline arrêté à l'étape '{etat.get('etape_arret')}' "
        f"— erreurs: {etat.get('erreurs')}"
    )

    if etat.get("dossier_id") and etat.get("score_id") is None:
        try:
            score_id = sauvegarder_scoring(etat["dossier_id"], {
                "score": 0, "score_base": 100, "delta_total": -100,
                "flags": ["ERREUR_PIPELINE"], "nb_penalites": 1,
                "nb_bonus": 0, "details": [], "niveau_risque": "ELEVE",
                "resume": "Erreur pipeline"
            })
            sauvegarder_decision(etat["dossier_id"], score_id, {
                "decision":       "refuser",
                "motif_principal": f"Erreur pipeline à '{etat.get('etape_arret')}'",
                "message_client":  "Votre dossier n'a pas pu être traité automatiquement.",
                "seuil_utilise":   "erreur_systeme",
                "flag_bloquant":   "ERREUR_PIPELINE",
                "necessite_validation_humaine": True
            })
        except Exception as e:
            logger.error(f"Impossible de sauvegarder l'erreur : {e}")

    return {**etat, "etape_actuelle": "erreur"}


def noeud_decision_directe(etat: EtatDossier) -> EtatDossier:
    """
    Nœud fail-fast — décision directe sans scoring.
    Activé quand la validation échoue sur une règle obligatoire.
    """
    logger.warning("DÉCISION DIRECTE — validation bloquante")

    echecs = etat["resultat_validation"]["echecs_bloquants"]
    motif  = f"Validation échouée — règles bloquantes : {echecs}"

    score_id = sauvegarder_scoring(etat["dossier_id"], {
        "score": 0, "score_base": 100, "delta_total": -100,
        "flags": echecs, "nb_penalites": len(echecs), "nb_bonus": 0,
        "details": [], "niveau_risque": "ELEVE", "resume": motif
    })

    resultat_decision = {
        "decision":       "refuser",
        "motif_principal": motif,
        "message_client":  "Votre dossier a été refusé suite à une non-conformité réglementaire.",
        "message_interne": motif,
        "seuil_utilise":   "validation_bloquante",
        "flag_bloquant":   echecs[0] if echecs else None,
        "necessite_validation_humaine": False,
        "flags":           echecs,
        "score":           0,
        "timestamp":       datetime.now().isoformat(),
        "resume":          motif
    }

    sauvegarder_decision(etat["dossier_id"], score_id, resultat_decision)

    return {
        **etat,
        "score_id":          score_id,
        "resultat_decision": resultat_decision,
        "etape_actuelle":    "decision_directe",
    }