# engines/decision_engine.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from loguru import logger
from config import DECISION_RULES, SEUIL_ACCEPTER, SEUIL_COMPLEMENT

# SECTION 1 — CHARGEMENT DES RÈGLES
_cache_regles = {}
def charger_regles_decision(chemin: str = str(DECISION_RULES)) -> dict:
    if chemin in _cache_regles:
        return _cache_regles[chemin]
    try:
        with open(chemin, encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"✓ Règles de décision chargées depuis {chemin}")
        _cache_regles[chemin] = config
        return config
    except FileNotFoundError:
        logger.warning(f"  Fichier JSON non trouvé : {chemin} — utilisation des valeurs par défaut")
        return _config_defaut()
    except json.JSONDecodeError as e:
        logger.error(f"Erreur JSON dans {chemin} : {e}")
        return _config_defaut()


def _config_defaut() -> dict:
    return {
        "seuils": {
            "accepter":   SEUIL_ACCEPTER,
            "complement": SEUIL_COMPLEMENT
        },
        "flags_refus_immediat": [
            "INELIGIBILITE",
            "DEPASSEMENT_SALAIRE",
            "SINISTRE_HORS_CONTRAT"
        ],
        "flags_complement_obligatoire": [
            "DECLARATION_TARDIVE_AT",
            "INCOHERENCE_MEDICALE",
            "DOCUMENT_ETRANGER",
            "FREQUENCE_ANORMALE"
        ],
        "escalade_humaine": {
            "montant_seuil":       5000,
            "score_zone_grise_min": 45,
            "score_zone_grise_max": 55,
            "flags_escalade": ["INCOHERENCE_MEDICALE", "DOCUMENT_ETRANGER"]
        },
        "messages": {
            "accepter": {
                "client":  "Votre dossier a été accepté. Vous serez contacté sous 48h.",
                "interne": "Dossier validé automatiquement — score suffisant, aucune anomalie bloquante."
            },
            "complement_requis": {
                "client":  "Votre dossier nécessite des informations complémentaires. Notre équipe vous contactera.",
                "interne": "Score intermédiaire ou flag nécessitant vérification humaine."
            },
            "refuser": {
                "client":  "Votre dossier ne peut pas être pris en charge. Vous pouvez contacter notre service client.",
                "interne": "Refus automatique — score insuffisant ou anomalie bloquante détectée."
            }
        }
    }

# SECTION 2 — LOGIQUE DE DÉCISION
def _verifier_refus_immediat(flags: list, config: dict) -> tuple:
    """
    Vérifie si un flag bloquant impose un refus immédiat.
    Retourne (refus_immediat: bool, flag_coupable: str | None)
    """
    flags_bloquants = config.get("flags_refus_immediat", [])
    for flag in flags:
        if flag in flags_bloquants:
            return True, flag
    return False, None


def _verifier_complement_obligatoire(flags: list, config: dict) -> tuple:
    """
    Vérifie si un flag impose un complément d'information.
    Retourne (complement_obligatoire: bool, flag_coupable: str | None)
    """
    flags_complement = config.get("flags_complement_obligatoire", [])
    for flag in flags:
        if flag in flags_complement:
            return True, flag
    return False, None


def _verifier_escalade_humaine(
    score: int,
    flags: list,
    montant_reclame: float,
    config: dict
) -> tuple:

    escalade_config = config.get("escalade_humaine", {})

    # RD-08 : montant élevé
    montant_seuil = escalade_config.get("montant_seuil", 5000)
    if montant_reclame and montant_reclame > montant_seuil:
        return True, f"Montant réclamé ({montant_reclame} TND) dépasse le seuil de validation automatique ({montant_seuil} TND)"

    # RD-09 : zone grise de score
    zone_min = escalade_config.get("score_zone_grise_min", 45)
    zone_max = escalade_config.get("score_zone_grise_max", 55)
    if zone_min <= score <= zone_max:
        return True, f"Score {score}/100 dans la zone d'ambiguïté ({zone_min}-{zone_max}) — vérification humaine recommandée"

    # RD-10 / RD-11 : flags spécifiques
    flags_escalade = escalade_config.get("flags_escalade", [])
    for flag in flags:
        if flag in flags_escalade:
            return True, f"Flag '{flag}' nécessite une vérification humaine spécialisée"

    return False, None

# SECTION 3 — MOTEUR PRINCIPAL
def executer_decision(
    score: int,
    flags: list,
    montant_reclame: float = 0.0,
    chemin_regles: str = str(DECISION_RULES)
) -> dict:
   
    config = charger_regles_decision(chemin_regles)
    seuil_accepter   = config["seuils"]["accepter"]
    seuil_complement = config["seuils"]["complement"]

    timestamp = datetime.now().isoformat()
    flag_bloquant    = None
    necessite_humain = False
    motif_escalade   = None

    # ── Étape 1 : Refus immédiat sur flag bloquant ──────────
    refus_immediat, flag_bloquant = _verifier_refus_immediat(flags, config)
    if refus_immediat:
        logger.warning(f" Refus immédiat — flag bloquant : {flag_bloquant}")
        return _construire_resultat(
            decision              = "refuser",
            score                 = score,
            flags                 = flags,
            motif                 = f"Anomalie bloquante détectée : {flag_bloquant}",
            flag_bloquant         = flag_bloquant,
            necessite_humain      = False,
            motif_escalade        = None,
            message_client        = config["messages"]["refuser"]["client"],
            message_interne       = config["messages"]["refuser"]["interne"],
            seuil_utilise         = f"Refus immédiat — flag {flag_bloquant}",
            timestamp             = timestamp
        )

    # ── Étape 2 : Complément forcé sur flag intermédiaire ───
    complement_force, flag_complement = _verifier_complement_obligatoire(flags, config)
    if complement_force:
        logger.info(f"Complément obligatoire — flag : {flag_complement}")
        necessite_humain, motif_escalade = _verifier_escalade_humaine(
            score, flags, montant_reclame, config
        )
        return _construire_resultat(
            decision              = "complement_requis",
            score                 = score,
            flags                 = flags,
            motif                 = f"Vérification requise pour : {flag_complement}",
            flag_bloquant         = None,
            necessite_humain      = necessite_humain,
            motif_escalade        = motif_escalade,
            message_client        = config["messages"]["complement_requis"]["client"],
            message_interne       = config["messages"]["complement_requis"]["interne"],
            seuil_utilise         = f"Complément obligatoire — flag {flag_complement}",
            timestamp             = timestamp
        )

    # ── Étape 3 : Vérification escalade humaine ─────────────
    necessite_humain, motif_escalade = _verifier_escalade_humaine(
        score, flags, montant_reclame, config
    )

    # ── Étape 4 : Décision par seuil de score ───────────────
    if score >= seuil_accepter:
        decision = "accepter"
        motif    = f"Score {score}/100 — seuil d'acceptation ({seuil_accepter}) atteint"
        seuil    = f"score ≥ {seuil_accepter}"
        logger.success(f" Décision : ACCEPTER (score={score})")

    elif score >= seuil_complement:
        decision = "complement_requis"
        motif    = f"Score {score}/100 — zone intermédiaire (entre {seuil_complement} et {seuil_accepter})"
        seuil    = f"{seuil_complement} ≤ score < {seuil_accepter}"
        logger.info(f" Décision : COMPLÉMENT REQUIS (score={score})")

    else:
        decision = "refuser"
        motif    = f"Score {score}/100 — insuffisant (seuil minimum : {seuil_complement})"
        seuil    = f"score < {seuil_complement}"
        logger.warning(f" Décision : REFUSER (score={score})")

    return _construire_resultat(
        decision              = decision,
        score                 = score,
        flags                 = flags,
        motif                 = motif,
        flag_bloquant         = None,
        necessite_humain      = necessite_humain,
        motif_escalade        = motif_escalade,
        message_client        = config["messages"][decision]["client"],
        message_interne       = config["messages"][decision]["interne"],
        seuil_utilise         = seuil,
        timestamp             = timestamp
    )


def _construire_resultat(
    decision, score, flags, motif, flag_bloquant,
    necessite_humain, motif_escalade,
    message_client, message_interne, seuil_utilise, timestamp
) -> dict:
    """Construit le dictionnaire de résultat standardisé."""

    escalade_str = f" |  Escalade : {motif_escalade}" if necessite_humain else ""
    resume = (
        f"Décision : {decision.upper()} | "
        f"Score : {score}/100 | "
        f"Flags : {', '.join(flags) if flags else 'aucun'} | "
        f"Motif : {motif}{escalade_str}"
    )

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
        "resume":                     resume
    }

# SECTION 4 — AFFICHAGE
def afficher_rapport_decision(resultat: dict) -> None:
    """Affiche un rapport lisible de la décision."""
    icones = {
        "accepter":         " ACCEPTÉ",
        "refuser":          " REFUSÉ",
        "complement_requis": "COMPLÉMENT REQUIS"
    }

    print("\n" + "═" * 60)
    print("         RAPPORT DE DÉCISION — SmartClaim")


    decision_label = icones.get(resultat["decision"], resultat["decision"].upper())
    print(f"\n  Décision : {decision_label}")
    print(f"  Score    : {resultat['score']}/100")
    print(f"  Seuil    : {resultat['seuil_utilise']}")

    if resultat["flag_bloquant"]:
        print(f"\n  Flag bloquant : {resultat['flag_bloquant']}")

    if resultat["flags"]:
        print(f"\n   Flags actifs  : {', '.join(resultat['flags'])}")

    print(f"\n  Motif          : {resultat['motif_principal']}")
    print(f" Message client : {resultat['message_client']}")
    print(f" Note interne   : {resultat['message_interne']}")

    if resultat["necessite_validation_humaine"]:
        print(f"\n   ESCALADE HUMAINE : {resultat['motif_escalade']}")

    print(f"\n  Horodatage : {resultat['timestamp']}")

