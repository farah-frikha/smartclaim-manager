# engines/decision/engine.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from loguru import logger
from config import DECISION_RULES
from engines.decision.loader   import charger_regles_decision
from engines.decision.checkers import (
    verifier_refus_immediat,
    verifier_complement_obligatoire,
    verifier_escalade_humaine
)


def _construire_resultat(
    decision, score, flags, motif, flag_bloquant,
    necessite_humain, motif_escalade,
    message_client, message_interne, seuil_utilise, timestamp
) -> dict:
    escalade_str = f" | ⚠️ Escalade : {motif_escalade}" if necessite_humain else ""
    return {
        "decision":                   decision,
        "score":                      score,
        "flags":                      flags,
        "motif_principal":            motif,
        "flag_bloquant":              flag_bloquant,
        "necessite_validation_humaine": necessite_humain,
        "motif_escalade":             motif_escalade,
        "message_client":             message_client,
        "message_interne":            message_interne,
        "seuil_utilise":              seuil_utilise,
        "timestamp":                  timestamp,
        "resume": (
            f"Décision : {decision.upper()} | Score : {score}/100 | "
            f"Flags : {', '.join(flags) if flags else 'aucun'} | "
            f"Motif : {motif}{escalade_str}"
        )
    }


def executer_decision(
    score: int,
    flags: list,
    montant_reclame: float = 0.0,
    chemin_regles: str = str(DECISION_RULES)
) -> dict:
    """Produit la décision préliminaire en 4 étapes ordonnées."""
    config    = charger_regles_decision(chemin_regles)
    seuil_acc = config["seuils"]["accepter"]
    seuil_com = config["seuils"]["complement"]
    timestamp = datetime.now().isoformat()

    # Étape 1 — Refus immédiat sur flag bloquant
    refus, flag_bloquant = verifier_refus_immediat(flags, config)
    if refus:
        logger.warning(f"Refus immédiat — flag bloquant : {flag_bloquant}")
        return _construire_resultat(
            "refuser", score, flags,
            f"Anomalie bloquante : {flag_bloquant}", flag_bloquant,
            False, None,
            config["messages"]["refuser"]["client"],
            config["messages"]["refuser"]["interne"],
            f"Refus immédiat — flag {flag_bloquant}", timestamp
        )

    # Étape 2 — Complément forcé
    complement, flag_comp = verifier_complement_obligatoire(flags, config)
    if complement:
        humain, motif_esc = verifier_escalade_humaine(score, flags, montant_reclame, config)
        return _construire_resultat(
            "complement_requis", score, flags,
            f"Vérification requise : {flag_comp}", None,
            humain, motif_esc,
            config["messages"]["complement_requis"]["client"],
            config["messages"]["complement_requis"]["interne"],
            f"Complément obligatoire — flag {flag_comp}", timestamp
        )

    # Étape 3 — Vérification escalade
    humain, motif_esc = verifier_escalade_humaine(score, flags, montant_reclame, config)

    # Étape 4 — Décision par seuil
    if score >= seuil_acc:
        decision, motif, seuil = "accepter", f"Score {score}/100 ≥ seuil {seuil_acc}", f"score ≥ {seuil_acc}"
        logger.success(f"Décision : ACCEPTER (score={score})")
    elif score >= seuil_com:
        decision, motif, seuil = "complement_requis", f"Score {score}/100 en zone intermédiaire", f"{seuil_com} ≤ score < {seuil_acc}"
        logger.info(f"Décision : COMPLÉMENT REQUIS (score={score})")
    else:
        decision, motif, seuil = "refuser", f"Score {score}/100 insuffisant (min : {seuil_com})", f"score < {seuil_com}"
        logger.warning(f"Décision : REFUSER (score={score})")

    return _construire_resultat(
        decision, score, flags, motif, None, humain, motif_esc,
        config["messages"][decision]["client"],
        config["messages"][decision]["interne"],
        seuil, timestamp
    )