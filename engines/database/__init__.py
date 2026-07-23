# engines/database/__init__.py
"""
Point d'entrée public du module database.
Réexporte toutes les fonctions publiques pour compatibilité totale.

Tous les imports existants continuent de fonctionner :
    from engines.database import init_db, get_connection
    from engines.database import sauvegarder_document
    from engines.database import creer_utilisateur
"""

# Connexion et initialisation
from engines.database.connection import (
    get_connection,
    init_db,
    test_db,
)

# CRUD documents
from engines.database.crud_documents import (
    log_audit,
    generer_reference_dossier,
    sauvegarder_document,
    sauvegarder_extraction,
    lire_dossier_complet,
    lister_dossiers,
    lister_dossiers_par_employe,
)

# CRUD résultats pipeline
from engines.database.crud_resultats import (
    sauvegarder_validation,
    sauvegarder_scoring,
    sauvegarder_decision,
)

# CRUD utilisateurs
from engines.database.crud_utilisateurs import (
    creer_utilisateur,
    creer_employe_et_utilisateur,
    obtenir_utilisateur_par_email,
    obtenir_utilisateur_par_id,
    mettre_a_jour_derniere_connexion,
    lister_utilisateurs,
    desactiver_utilisateur,
    changer_statut_utilisateur,
)
from engines.database.crud_reclamations import ( creer_reclamation, lister_reclamations, lister_reclamations_utilisateur ,repondre_reclamation ,)

__all__ = [
    # Connexion
    "get_connection", "init_db", "test_db",
    # Documents
    "log_audit", "generer_reference_dossier",
    "sauvegarder_document", "sauvegarder_extraction",
    "lire_dossier_complet", "lister_dossiers", "lister_dossiers_par_employe",
    # Résultats
    "sauvegarder_validation", "sauvegarder_scoring", "sauvegarder_decision",
    # Utilisateurs
    "creer_utilisateur", "creer_employe_et_utilisateur", "obtenir_utilisateur_par_email",
    "obtenir_utilisateur_par_id", "mettre_a_jour_derniere_connexion",
    "lister_utilisateurs", "desactiver_utilisateur", "changer_statut_utilisateur",
    # Réclamations
    "creer_reclamation", "lister_reclamations", "lister_reclamations_utilisateur", "repondre_reclamation"
]