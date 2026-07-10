# engines/decision/checkers.py
"""
Les 3 vérificateurs de la logique de décision.
Fonctions pures — retournent (bool, str | None).
"""


def verifier_refus_immediat(flags: list, config: dict) -> tuple:
    """Vérifie si un flag bloquant impose un refus immédiat."""
    for flag in flags:
        if flag in config.get("flags_refus_immediat", []):
            return True, flag
    return False, None


def verifier_complement_obligatoire(flags: list, config: dict) -> tuple:
    """Vérifie si un flag impose un complément d'information."""
    for flag in flags:
        if flag in config.get("flags_complement_obligatoire", []):
            return True, flag
    return False, None


def verifier_escalade_humaine(
    score: int, flags: list,
    montant_reclame: float, config: dict
) -> tuple:
    """
    Vérifie si le dossier doit être escaladé vers un expert humain.
    Cas : montant élevé, zone grise de score, flag médical.
    """
    esc = config.get("escalade_humaine", {})

    if montant_reclame and montant_reclame > esc.get("montant_seuil", 5000):
        return True, f"Montant réclamé ({montant_reclame} TND) dépasse le seuil"

    zone_min = esc.get("score_zone_grise_min", 45)
    zone_max = esc.get("score_zone_grise_max", 55)
    if zone_min <= score <= zone_max:
        return True, f"Score {score}/100 dans la zone d'ambiguïté ({zone_min}-{zone_max})"

    for flag in flags:
        if flag in esc.get("flags_escalade", []):
            return True, f"Flag '{flag}' nécessite une vérification humaine"

    return False, None