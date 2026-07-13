# agents/classification/domaines.py
"""
Catalogue des domaines métier reconnus par le système.
Chaque domaine définit les mots-clés qui permettent de le détecter
dans le texte OCR, et le nom de sa configuration.
"""

DOMAINES = {
    "AUTO": {
        "libelle": "Sinistre automobile",
        "mots_cles": [
            "auto", "véhicule", "accident", "collision", "constat",
            "immatriculation", "star-auto", "carte grise", "assurance auto",
        ],
        "poids": {  # certains mots sont plus discriminants
            "star-auto": 5,
            "constat": 3,
            "collision": 3,
            "véhicule": 2,
        },
    },
    "CNAM_MALADIE": {
        "libelle": "Demande d'indemnité CNAM (maladie/accident)",
        "mots_cles": [
            "cnam", "indemnité", "demande d'indemnité", "arrêt de travail",
            "caisse nationale d'assurance maladie", "الصندوق الوطني",
            "maladie non professionnelle", "couches", "interruption",
        ],
        "poids": {
            "demande d'indemnité": 5,
            "indemnité": 3,
            "arrêt de travail": 4,
            "الصندوق الوطني": 4,
        },
    },
    "CNAM_SOINS": {
        "libelle": "Prise en charge / remboursement de soins CNAM",
        "mots_cles": [
            "cnam", "prise en charge", "remboursement", "frais de soins",
            "appareillage", "bulletin de remboursement", "soins",
            "caisse nationale d'assurance maladie", "الصندوق الوطني",
            "consultation médicale", "hospitalisation",
        ],
        "poids": {
            "prise en charge": 5,
            "bulletin de remboursement": 5,
            "remboursement": 3,
            "appareillage": 4,
        },
    },
}

DOMAINE_PAR_DEFAUT = "AUTO"