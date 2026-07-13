# agents/classification/classifieur.py
"""
Classifieur de domaine par mots-clés pondérés.
Analyse le texte OCR et détermine le domaine métier le plus probable,
pour permettre le chargement de la configuration adaptée.
"""
from loguru import logger
from agents.classification.domaines import DOMAINES, DOMAINE_PAR_DEFAUT


def classifier_domaine(texte_ocr: str) -> dict:
    """
    Détermine le domaine d'un document à partir de son texte OCR.

    Retourne un dict :
        domaine     : code du domaine détecté (ex: "CNAM_MALADIE")
        libelle     : libellé lisible
        score       : score de confiance du domaine gagnant
        scores_tous : scores de tous les domaines (pour transparence)
    """
    texte = texte_ocr.lower()
    scores = {}

    for code, config in DOMAINES.items():
        score = 0
        poids = config.get("poids", {})

        for mot in config["mots_cles"]:
            if mot.lower() in texte:
                # Un mot pondéré compte plus, sinon poids par défaut de 1
                score += poids.get(mot.lower(), 1)

        scores[code] = score

    # Le domaine gagnant est celui au score le plus élevé
    domaine_gagnant = max(scores, key=scores.get)
    score_max = scores[domaine_gagnant]

    # Si aucun mot-clé trouvé, on retombe sur le domaine par défaut
    if score_max == 0:
        logger.warning(
            "Aucun mot-clé de domaine détecté — "
            f"domaine par défaut : {DOMAINE_PAR_DEFAUT}"
        )
        domaine_gagnant = DOMAINE_PAR_DEFAUT

    logger.info(
        f"Domaine détecté : {domaine_gagnant} "
        f"(score={score_max}) — scores : {scores}"
    )

    return {
        "domaine":     domaine_gagnant,
        "libelle":     DOMAINES[domaine_gagnant]["libelle"],
        "score":       score_max,
        "scores_tous": scores,
    }