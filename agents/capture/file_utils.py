# agents/capture/file_utils.py
"""
Utilitaires fichier pour l'Agent Capture.
Fonctions pures — pas de dépendances vers OpenCV ou PaddleOCR.
"""
import hashlib


def calculer_hash(chemin_fichier: str) -> str:
    """
    Calcule le hash SHA-256 d'un fichier.
    Utilisé pour détecter les doublons dans la base.
    Lit le fichier par blocs de 8 Ko pour les gros fichiers.
    """
    sha256 = hashlib.sha256()
    with open(chemin_fichier, "rb") as f:
        for bloc in iter(lambda: f.read(8192), b""):
            sha256.update(bloc)
    return sha256.hexdigest()


def detecter_type_document(nom_fichier: str) -> str:
    """
    Détecte le type de document depuis le nom du fichier.
    Retourne un code parmi les types définis dans la BDD.

    Limitation : détection par mots-clés dans le nom.
    En production, ce serait enrichi par la classification LLM.
    """
    nom = nom_fichier.lower()

    if any(mot in nom for mot in ["formulaire", "sinistre", "declaration"]):
        return "formulaire_sinistre"
    if any(mot in nom for mot in ["attestation", "assurance"]):
        return "attestation"
    if any(mot in nom for mot in ["contrat", "police", "conditions"]):
        return "contrat"
    if any(mot in nom for mot in ["certificat", "medical", "arret"]):
        return "certificat_medical"
    if any(mot in nom for mot in ["facture", "recu", "note"]):
        return "facture"
    if any(mot in nom for mot in ["identite", "cin", "passeport"]):
        return "piece_identite"
    if any(mot in nom for mot in ["deces", "acte"]):
        return "acte_deces"
    return "autre"