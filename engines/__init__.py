# engines/__init__.py
"""
Package engines — exports publics.
Tous les imports existants restent valides :
    from engines.validation_engine import executer_validation
    from engines.scoring_engine    import executer_scoring
    from engines.decision_engine   import executer_decision
"""
from engines.validation import executer_validation, afficher_rapport_validation
from engines.scoring    import executer_scoring,    afficher_rapport_scoring
from engines.decision   import executer_decision,   afficher_rapport_decision
from engines.database   import (
    init_db, get_connection, test_db,
    log_audit, generer_reference_dossier,
    sauvegarder_document, sauvegarder_extraction,
    lire_dossier_complet, lister_dossiers, lister_dossiers_par_employe,
    sauvegarder_validation, sauvegarder_scoring, sauvegarder_decision,
    creer_utilisateur, creer_employe_et_utilisateur , obtenir_utilisateur_par_email,
    obtenir_utilisateur_par_id, mettre_a_jour_derniere_connexion,
    lister_utilisateurs, desactiver_utilisateur,changer_statut_utilisateur, creer_reclamation, lister_reclamations, lister_reclamations_utilisateur ,repondre_reclamation,
)