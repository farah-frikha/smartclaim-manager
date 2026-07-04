# agents/coordinateur.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sqlite3
import time
from datetime import datetime
from typing import TypedDict, Optional, Any

from langgraph.graph import StateGraph, END
from loguru import logger

from agents.capture    import executer_capture
from agents.extraction import executer_extraction
from engines.validation_engine import executer_validation
from engines.scoring_engine    import executer_scoring
from engines.decision_engine   import executer_decision
from engines.database import (
    init_db, generer_reference_dossier,
    sauvegarder_document, sauvegarder_extraction,
    sauvegarder_validation, sauvegarder_scoring,
    sauvegarder_decision, get_connection, log_audit
)
from config import SEUIL_ACCEPTER, SEUIL_COMPLEMENT

# ────────────────────────────────────────────────────────────
# SECTION 1 — ÉTAT PARTAGÉ LANGGRAPH
# ────────────────────────────────────────────────────────────

class EtatDossier(TypedDict):
    """
    État partagé entre tous les agents du pipeline.
    Chaque agent lit et enrichit cet état.
    """
    # Entrée
    chemin_fichier:       str
    dossier_id:           Optional[int]
    document_id:          Optional[int]
    reference_dossier:    Optional[str]

    # Résultats par agent
    resultat_capture:     Optional[dict]
    resultat_extraction:  Optional[dict]
    resultat_validation:  Optional[dict]
    resultat_scoring:     Optional[dict]
    resultat_decision:    Optional[dict]

    # Contrôle de flux
    etape_actuelle:       Optional[str]
    etape_arret:          Optional[str]
    erreurs:              Optional[list]
    peut_continuer:       Optional[bool]

    # Métriques
    score_id:             Optional[int]
    temps_debut:          Optional[float]


# ────────────────────────────────────────────────────────────
# SECTION 2 — ENRICHISSEMENT DU DOSSIER
# ────────────────────────────────────────────────────────────
def normaliser_date_iso(valeur: str) -> str:
    """
    Convertit n'importe quel format de date vers YYYY-MM-DD.
    Formats acceptés : DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
    """
    if not valeur:
        return valeur
    import re

    # Déjà au format ISO — rien à faire
    if re.match(r'^\d{4}-\d{2}-\d{2}$', str(valeur)):
        return valeur

    # Format DD/MM/YYYY ou DD-MM-YYYY
    m = re.match(r'^(\d{2})[/\-](\d{2})[/\-](\d{4})$', str(valeur))
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    return valeur
def enrichir_dossier(dossier_extrait: dict) -> dict:
    """
    Enrichit le dossier extrait avec :
    1. Les champs calculés (délais, durées)
    2. Les champs métier depuis la BDD (dates contrat, statut)
    """
    from datetime import date, datetime
    dossier = {**dossier_extrait}
    # ── Champs calculés ──────────────────────────────────────
    
    def to_date(valeur):
        if isinstance(valeur, date): return valeur
        if isinstance(valeur, str):
            for fmt in ["%Y-%m-%d", "%d/%m/%Y"]:
                try: return datetime.strptime(valeur, fmt).date()
                except: continue
        return None
    date_sinistre    = to_date(dossier.get("date_sinistre"))
    date_declaration = to_date(dossier.get("date_declaration"))
    aujourd_hui      = date.today()
    if date_sinistre:
        if date_declaration:
            dossier["delai_declaration_jours"] = (
                date_declaration - date_sinistre
            ).days
        else:
            dossier["delai_declaration_jours"] = (
                aujourd_hui - date_sinistre
            ).days
        dossier["jours_depuis_sinistre"] = (
            aujourd_hui - date_sinistre
        ).days
    # ── Champs métier depuis la BDD ──────────────────────────
    numero_contrat = dossier.get("numero_contrat")
    if numero_contrat:
        try:
            conn = get_connection()
            conn.row_factory = sqlite3.Row
            contrat = conn.execute("""
                SELECT date_effet, date_echeance,
                       delai_carence_jours
                FROM contrats_collectifs
                WHERE numero_contrat = ?
            """, (numero_contrat,)).fetchone()
            if contrat:
                dossier["date_debut_contrat"] = normaliser_date_iso(contrat["date_effet"])
                dossier["date_fin_contrat"]   = normaliser_date_iso(contrat["date_echeance"])
                # Log de vérification — confirme que la normalisation a bien eu lieu
                logger.info(
                        f"Dates contrat normalisées — "
                        f"date_debut={dossier['date_debut_contrat']}, "
                        f"date_fin={dossier['date_fin_contrat']}")

                # Calcul jours depuis souscription
                date_debut = to_date(contrat["date_effet"])
                if date_debut and date_sinistre:
                    dossier["jours_depuis_souscription"] = (
                        date_sinistre - date_debut
                    ).days
            else:
                # Contrat non trouvé en BDD — valeurs par défaut
                # pour ne pas bloquer la démo
                logger.warning(
                    f"Contrat '{numero_contrat}' non trouvé en BDD "
                    f"— utilisation valeurs par défaut"
                )
                dossier["date_debut_contrat"] = "2024-01-01"
                dossier["date_fin_contrat"]   = "2027-01-01"
                dossier["jours_depuis_souscription"] = 400
            conn.close()
        except Exception as e:
            logger.warning(f"Enrichissement BDD échoué : {e}")
            dossier["date_debut_contrat"] = "2024-01-01"
            dossier["date_fin_contrat"]   = "2027-01-01"
            dossier["jours_depuis_souscription"] = 400
    # ── Valeurs par défaut pour champs métier manquants ──────
    dossier.setdefault("statut_cotisations_cnss_employeur", "a_jour")
    dossier.setdefault("statut_affiliation",                "actif")
    dossier.setdefault("concerne_ayant_droit",              False)
    dossier.setdefault("cause_sinistre",                    "accident")
    dossier.setdefault("montant_net_complementaire",
                       dossier.get("montant_reclame", 0))
    dossier.setdefault("garanties_contrat",
                       ["AUTO_ACCIDENT", "AUTO_VOL",
                        "AUTO_BRIS_GLACE", "SANTE_CONSUL"])
    dossier.setdefault("documents_fournis",
                       ["formulaire_sinistre", "piece_identite"])
    return dossier


# ────────────────────────────────────────────────────────────
# SECTION 3 — NOEUDS DU GRAPHE (un noeud = un agent)
# ────────────────────────────────────────────────────────────

def noeud_capture(etat: EtatDossier) -> EtatDossier:
    """
    Noeud 1 : Agent Capture
    PDF/image → texte brut OCR
    """
    logger.info("=" * 50)
    logger.info("AGENT CAPTURE — démarrage")
    t0 = time.perf_counter()

    try:
        resultat = executer_capture(etat["chemin_fichier"])

        if resultat["statut"] != "succes":
            logger.error(f"Capture échouée : {resultat.get('message')}")
            return {
                **etat,
                "etape_actuelle": "capture",
                "etape_arret":    "capture",
                "peut_continuer": False,
                "resultat_capture": resultat,
                "erreurs": (etat.get("erreurs") or []) + [
                    f"Capture : {resultat.get('message')}"
                ]
            }

        # Créer le dossier en base et sauvegarder le document
        ref = generer_reference_dossier()
        conn = get_connection()

        # Insertion dossier minimal (sera enrichi par extraction)
        cursor = conn.execute("""
            INSERT INTO dossiers_sinistres (
                reference_dossier, employe_id, contrat_id,
                type_sinistre_id, date_sinistre, statut_global
            ) VALUES (?, 1, 1, 1, date('now'), 'en_traitement')
        """, (ref,))
        dossier_id = cursor.lastrowid
        conn.commit()
        conn.close()

        document_id = sauvegarder_document(dossier_id, resultat)
        duree = round((time.perf_counter() - t0) * 1000)
        logger.success(
            f"Capture OK — {resultat['nb_mots_total']} mots, "
            f"confiance={resultat['score_confiance']}, {duree}ms"
        )

        return {
            **etat,
            "dossier_id":       dossier_id,
            "document_id":      document_id,
            "reference_dossier": ref,
            "resultat_capture": resultat,
            "etape_actuelle":   "capture",
            "peut_continuer":   True,
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
    """
    Noeud 2 : Agent Extraction
    Texte brut → JSON structuré via LLM
    """
    logger.info("=" * 50)
    logger.info("AGENT EXTRACTION — démarrage")
    t0 = time.perf_counter()

    try:
        texte = etat["resultat_capture"]["texte_complet"]
        resultat = executer_extraction(texte)

        sauvegarder_extraction(
            etat["dossier_id"],
            etat["document_id"],
            resultat
        )

        duree = round((time.perf_counter() - t0) * 1000)
        logger.success(
            f"Extraction OK — "
            f"complétude={resultat['score_completude']}, "
            f"LLM={resultat.get('llm_duree_ms')}ms"
        )

        return {
            **etat,
            "resultat_extraction": resultat,
            "etape_actuelle":      "extraction",
            "peut_continuer":      resultat["peut_continuer"],
            "etape_arret": None if resultat["peut_continuer"]
                           else "extraction"
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
    """
    Noeud 3 : Agent Validation
    Vérifie la cohérence et la conformité réglementaire
    """
    logger.info("=" * 50)
    logger.info("AGENT VALIDATION — démarrage")

    try:
        dossier_brut    = etat["resultat_extraction"]["dossier_extrait"]
        dossier_enrichi = enrichir_dossier(dossier_brut)  # ← ajout

        logger.info(
            f"Dossier enrichi — "
            f"date_debut={dossier_enrichi.get('date_debut_contrat')}, "
            f"delai={dossier_enrichi.get('delai_declaration_jours')}j"
        )

        resultat = executer_validation(dossier_enrichi)  # ← dossier enrichi

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
            "peut_continuer":      resultat["peut_continuer"],
            "etape_arret": None if resultat["peut_continuer"]
                           else "validation"
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
    """
    Noeud 4 : Agent Scoring
    Calcule le score de risque composite
    """
    logger.info("=" * 50)
    logger.info("AGENT SCORING — démarrage")

    try:
        dossier = etat["resultat_extraction"]["dossier_extrait"]
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
    """
    Noeud 5 : Agent Décision
    Produit la décision préliminaire finale
    """
    logger.info("=" * 50)
    logger.info("AGENT DÉCISION — démarrage")

    try:
        scoring    = etat["resultat_scoring"]
        extraction = etat["resultat_extraction"]["dossier_extrait"]

        resultat = executer_decision(
            score          = scoring["score"],
            flags          = scoring["flags"],
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
    """
    Noeud terminal d'erreur.
    Enregistre l'arrêt prématuré du pipeline.
    """
    logger.error(
        f"Pipeline arrêté à l'étape '{etat.get('etape_arret')}' "
        f"— erreurs: {etat.get('erreurs')}"
    )

    # Sauvegarder la décision de refus forcé si dossier créé
    if etat.get("dossier_id") and etat.get("score_id") is None:
        try:
            # Score fictif = 0 pour refus
            from engines.database import sauvegarder_scoring
            score_id = sauvegarder_scoring(etat["dossier_id"], {
                "score": 0, "score_base": 100,
                "delta_total": -100, "flags": ["ERREUR_PIPELINE"],
                "nb_penalites": 1, "nb_bonus": 0,
                "details": [], "niveau_risque": "ELEVE",
                "resume": "Erreur pipeline"
            })

            sauvegarder_decision(etat["dossier_id"], score_id, {
                "decision":    "refuser",
                "motif_principal": f"Erreur pipeline à l'étape "
                                   f"'{etat.get('etape_arret')}'",
                "message_client": "Votre dossier n'a pas pu être "
                                  "traité automatiquement. "
                                  "Veuillez contacter notre service.",
                "seuil_utilise":  "erreur_systeme",
                "flag_bloquant":  "ERREUR_PIPELINE",
                "necessite_validation_humaine": True
            })
        except Exception as e:
            logger.error(f"Impossible de sauvegarder l'erreur : {e}")

    return {**etat, "etape_actuelle": "erreur"}


# ────────────────────────────────────────────────────────────
# SECTION 4 — ROUTAGE CONDITIONNEL
# ────────────────────────────────────────────────────────────

def router_apres_capture(etat: EtatDossier) -> str:
    """Après capture : continuer ou terminer en erreur."""
    if not etat.get("peut_continuer"):
        return "erreur"
    if not etat["resultat_capture"].get("confiance_ok"):
        logger.warning("Confiance OCR faible — pipeline continue avec avertissement")
    return "extraction"


def router_apres_extraction(etat: EtatDossier) -> str:
    """Après extraction : continuer si champs critiques présents."""
    if not etat.get("peut_continuer"):
        return "erreur"
    return "validation"


def router_apres_validation(etat: EtatDossier) -> str:
    """
    Après validation : FAIL-FAST si règle obligatoire échouée.
    Sinon continuer vers scoring.
    """
    if not etat.get("peut_continuer"):
        logger.warning(
            "Validation bloquante — "
            "court-circuit vers décision directe"
        )
        return "decision_directe"
    return "scoring"


def router_apres_scoring(etat: EtatDossier) -> str:
    """Après scoring : toujours vers décision."""
    if not etat.get("peut_continuer"):
        return "erreur"
    return "decision"


# ────────────────────────────────────────────────────────────
# SECTION 5 — NOEUD DÉCISION DIRECTE (fail-fast validation)
# ────────────────────────────────────────────────────────────

def noeud_decision_directe(etat: EtatDossier) -> EtatDossier:
    """
    Décision directe sans scoring quand la validation échoue.
    Score forcé à 0, refus immédiat.
    """
    logger.warning("DÉCISION DIRECTE — validation bloquante")

    echecs = etat["resultat_validation"]["echecs_bloquants"]
    motif  = f"Validation échouée — règles bloquantes : {echecs}"

    # Score fictif = 0
    score_id = sauvegarder_scoring(etat["dossier_id"], {
        "score": 0, "score_base": 100,
        "delta_total": -100, "flags": echecs,
        "nb_penalites": len(echecs), "nb_bonus": 0,
        "details": [], "niveau_risque": "ELEVE",
        "resume": motif
    })

    resultat_decision = {
        "decision":    "refuser",
        "motif_principal": motif,
        "message_client":  "Votre dossier a été refusé suite à "
                           "une non-conformité réglementaire.",
        "message_interne": motif,
        "seuil_utilise":   "validation_bloquante",
        "flag_bloquant":   echecs[0] if echecs else None,
        "necessite_validation_humaine": False,
        "flags": echecs,
        "score": 0,
        "timestamp": datetime.now().isoformat(),
        "resume": motif
    }

    sauvegarder_decision(
        etat["dossier_id"], score_id, resultat_decision
    )

    return {
        **etat,
        "score_id":        score_id,
        "resultat_decision": resultat_decision,
        "etape_actuelle":  "decision_directe",
    }


# ────────────────────────────────────────────────────────────
# SECTION 6 — CONSTRUCTION DU GRAPHE LANGGRAPH
# ────────────────────────────────────────────────────────────

def construire_graphe() -> StateGraph:
    """
    Construit et compile le graphe LangGraph.
    Retourne le graphe compilé prêt à être exécuté.
    """
    graphe = StateGraph(EtatDossier)

    # Ajout des noeuds
    graphe.add_node("capture",          noeud_capture)
    graphe.add_node("extraction",       noeud_extraction)
    graphe.add_node("validation",       noeud_validation)
    graphe.add_node("scoring",          noeud_scoring)
    graphe.add_node("decision",         noeud_decision)
    graphe.add_node("decision_directe", noeud_decision_directe)
    graphe.add_node("erreur",           noeud_erreur)

    # Point d'entrée
    graphe.set_entry_point("capture")

    # Arêtes conditionnelles
    graphe.add_conditional_edges(
        "capture",
        router_apres_capture,
        {"extraction": "extraction", "erreur": "erreur"}
    )
    graphe.add_conditional_edges(
        "extraction",
        router_apres_extraction,
        {"validation": "validation", "erreur": "erreur"}
    )
    graphe.add_conditional_edges(
        "validation",
        router_apres_validation,
        {
            "scoring":          "scoring",
            "decision_directe": "decision_directe"
        }
    )
    graphe.add_conditional_edges(
        "scoring",
        router_apres_scoring,
        {"decision": "decision", "erreur": "erreur"}
    )

    # Arêtes fixes (toujours vers END)
    graphe.add_edge("decision",         END)
    graphe.add_edge("decision_directe", END)
    graphe.add_edge("erreur",           END)

    return graphe.compile()


# ────────────────────────────────────────────────────────────
# SECTION 7 — POINT D'ENTRÉE PRINCIPAL
# ────────────────────────────────────────────────────────────

def traiter_dossier(chemin_fichier: str) -> dict:
    """
    Point d'entrée public du système SmartClaim.
    Lance le pipeline complet sur un fichier PDF ou image.

    Paramètres :
        chemin_fichier : chemin absolu vers le document

    Retourne le résultat complet du pipeline.
    """
    logger.info("=" * 60)
    logger.info(f"SMARTCLAIM — Nouveau dossier : {chemin_fichier}")
    logger.info("=" * 60)

    init_db()  # S'assure que la BDD existe
    t_debut = time.perf_counter()

    # État initial
    etat_initial: EtatDossier = {
        "chemin_fichier":      chemin_fichier,
        "dossier_id":          None,
        "document_id":         None,
        "reference_dossier":   None,
        "resultat_capture":    None,
        "resultat_extraction": None,
        "resultat_validation": None,
        "resultat_scoring":    None,
        "resultat_decision":   None,
        "etape_actuelle":      "debut",
        "etape_arret":         None,
        "erreurs":             [],
        "peut_continuer":      True,
        "score_id":            None,
        "temps_debut":         t_debut,
    }

    # Exécution du graphe
    graphe = construire_graphe()
    etat_final = graphe.invoke(etat_initial)

    duree_totale = round((time.perf_counter() - t_debut) * 1000)

    # Résumé final
    decision = etat_final.get("resultat_decision", {})
    logger.info("=" * 60)
    logger.info(
        f"PIPELINE TERMINÉ en {duree_totale}ms — "
        f"Décision : {decision.get('decision', 'N/A').upper()}"
    )
    logger.info("=" * 60)

    return {
        "reference_dossier":   etat_final.get("reference_dossier"),
        "dossier_id":          etat_final.get("dossier_id"),
        "etape_arret":         etat_final.get("etape_arret"),
        "resultat_capture":    etat_final.get("resultat_capture"),
        "resultat_extraction": etat_final.get("resultat_extraction"),
        "resultat_validation": etat_final.get("resultat_validation"),
        "resultat_scoring":    etat_final.get("resultat_scoring"),
        "resultat_decision":   etat_final.get("resultat_decision"),
        "duree_totale_ms":     duree_totale,
        "erreurs":             etat_final.get("erreurs", []),
    }


# ────────────────────────────────────────────────────────────
# SECTION 8 — TEST
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from pathlib import Path

    # Trouver un PDF dans data/
    pdfs = list(Path("data").rglob("*.pdf"))
    if not pdfs:
        print("❌ Aucun PDF trouvé dans data/")
        print("   Placez un PDF dans data/contrats/ ou data/dossiers_test/")
        exit(1)

    pdf_path = str(pdfs[0])
    print(f"\nPDF utilisé : {pdf_path}")

    # Lancer le pipeline complet
    resultat = traiter_dossier(pdf_path)

    # Affichage du résumé
    print("\n" + "═" * 60)
    print("   RÉSUMÉ DU PIPELINE SMARTCLAIM")
    print("═" * 60)
    print(f"Référence dossier : {resultat['reference_dossier']}")
    print(f"Durée totale      : {resultat['duree_totale_ms']}ms")
    print(f"Étape d'arrêt     : {resultat['etape_arret'] or 'aucune (pipeline complet)'}")

    if resultat["resultat_capture"]:
        r = resultat["resultat_capture"]
        print(f"\n[Capture]     ✅ {r['nb_pages']} pages, "
              f"{r['nb_mots_total']} mots, "
              f"confiance={r['score_confiance']}")

    if resultat["resultat_extraction"]:
        r = resultat["resultat_extraction"]
        print(f"[Extraction]  ✅ complétude={r['score_completude']}, "
              f"LLM={r.get('llm_duree_ms')}ms")
        d = r.get("dossier_extrait", {})
        print(f"              → {d.get('nom_assure')} | "
              f"{d.get('numero_contrat')} | "
              f"{d.get('date_sinistre')}")

    if resultat["resultat_validation"]:
        r = resultat["resultat_validation"]
        statut = "✅" if r["valide"] else "❌"
        print(f"[Validation]  {statut} {r['nb_reussies']}/"
              f"{r['nb_regles_total']} règles passées")

    if resultat["resultat_scoring"]:
        r = resultat["resultat_scoring"]
        print(f"[Scoring]     ✅ score={r['score']}/100, "
              f"risque={r['niveau_risque']}, "
              f"flags={r['flags']}")

    if resultat["resultat_decision"]:
        r = resultat["resultat_decision"]
        icones = {
            "accepter":         "✅ ACCEPTÉ",
            "refuser":          "❌ REFUSÉ",
            "complement_requis": "⚠️  COMPLÉMENT REQUIS"
        }
        label = icones.get(r["decision"], r["decision"].upper())
        print(f"[Décision]    {label}")
        print(f"              → {r['motif_principal']}")
        if r.get("necessite_validation_humaine"):
            print(f"              ⚠️  Escalade humaine : "
                  f"{r.get('motif_escalade')}")

    if resultat["erreurs"]:
        print(f"\n❌ Erreurs : {resultat['erreurs']}")

    print("═" * 60)