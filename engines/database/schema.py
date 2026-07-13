# engines/database/schema.py
"""
Schéma SQL complet de SmartClaim.
Ce fichier contient UNIQUEMENT les CREATE TABLE et CREATE INDEX.
Il est lu une seule fois par init_db() dans connection.py.
"""

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- ═══════════════════════════════════════════════════════
-- COUCHE 1 — Données métier principales
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS employeurs (
    employeur_id INTEGER PRIMARY KEY AUTOINCREMENT,
    raison_sociale TEXT NOT NULL,
    matricule_fiscale TEXT UNIQUE,
    secteur_activite TEXT,
    taille_entreprise TEXT,
    date_inscription_cnss TEXT,
    statut_cotisations_cnss TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS employes (
    employe_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employeur_id INTEGER,
    numero_cnss TEXT UNIQUE NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    date_naissance TEXT,
    categorie_professionnelle TEXT,
    date_embauche TEXT,
    salaire_reference_cnss REAL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employeur_id)
        REFERENCES employeurs(employeur_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_employes_employeur_id ON employes(employeur_id);
CREATE INDEX IF NOT EXISTS idx_employes_numero_cnss  ON employes(numero_cnss);

CREATE TABLE IF NOT EXISTS ayants_droit (
    ayant_droit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employe_id INTEGER NOT NULL,
    lien TEXT NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    date_naissance TEXT,
    actif INTEGER DEFAULT 1 CHECK(actif IN (0,1)),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employe_id)
        REFERENCES employes(employe_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ayants_droit_employe_id ON ayants_droit(employe_id);

CREATE TABLE IF NOT EXISTS contrats_collectifs (
    contrat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employeur_id INTEGER NOT NULL,
    numero_contrat TEXT UNIQUE NOT NULL,
    compagnie_assurance TEXT NOT NULL,
    type_contrat TEXT,
    date_effet TEXT NOT NULL,
    date_echeance TEXT,
    garanties_couvertes TEXT,
    exclusions TEXT,
    delai_carence_jours INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employeur_id)
        REFERENCES employeurs(employeur_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_contrats_collectifs_employeur_id
ON contrats_collectifs(employeur_id);

CREATE TABLE IF NOT EXISTS adhesions (
    adhesion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employe_id INTEGER NOT NULL,
    contrat_id INTEGER NOT NULL,
    date_adhesion TEXT NOT NULL,
    statut TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employe_id)
        REFERENCES employes(employe_id)
        ON DELETE CASCADE,
    FOREIGN KEY (contrat_id)
        REFERENCES contrats_collectifs(contrat_id)
        ON DELETE CASCADE,
    UNIQUE(employe_id, contrat_id)
);

CREATE TABLE IF NOT EXISTS types_sinistres (
    type_sinistre_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    libelle TEXT NOT NULL,
    categorie TEXT NOT NULL,
    documents_requis TEXT,
    delai_declaration_jours INTEGER,
    source_legale TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS dossiers_sinistres (
    dossier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_dossier TEXT UNIQUE NOT NULL,
    employe_id INTEGER NOT NULL,
    ayant_droit_id INTEGER,
    contrat_id INTEGER NOT NULL,
    type_sinistre_id INTEGER NOT NULL,
    date_sinistre TEXT NOT NULL,
    date_declaration TEXT,
    delai_declaration_jours INTEGER,
    montant_reclame REAL DEFAULT 0,
    montant_cnss_rembourse REAL DEFAULT 0,
    nb_sinistres_anterieurs_12mois INTEGER DEFAULT 0,
    statut_global TEXT DEFAULT 'recu',
    domaine TEXT DEFAULT 'AUTO',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employe_id)
        REFERENCES employes(employe_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (ayant_droit_id)
        REFERENCES ayants_droit(ayant_droit_id)
        ON DELETE SET NULL,
    FOREIGN KEY (contrat_id)
        REFERENCES contrats_collectifs(contrat_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (type_sinistre_id)
        REFERENCES types_sinistres(type_sinistre_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_dossiers_reference
ON dossiers_sinistres(reference_dossier);

-- ═══════════════════════════════════════════════════════
-- COUCHE 2 — Documents et OCR
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    nom_fichier_original TEXT NOT NULL,
    type_document TEXT NOT NULL,
    format_fichier TEXT NOT NULL,
    taille_octets INTEGER CHECK(taille_octets >= 0),
    hash_sha256 TEXT,
    chemin_stockage TEXT NOT NULL,
    date_reception TEXT NOT NULL,
    source TEXT,
    statut_traitement TEXT DEFAULT 'recu',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_documents_dossier_id ON documents(dossier_id);

CREATE TABLE IF NOT EXISTS pages_ocr (
    page_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    numero_page INTEGER NOT NULL,
    texte_brut TEXT,
    score_confiance_ocr REAL,
    langue_detectee TEXT,
    date_traitement TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS champs_extraits (
    extraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    document_id INTEGER,
    nom_champ TEXT NOT NULL,
    valeur_extraite TEXT,
    valeur_normalisee TEXT,
    score_confiance_llm REAL,
    page_source INTEGER,
    prompt_utilise TEXT,
    date_extraction TEXT,
    valide_manuellement INTEGER DEFAULT 0 CHECK(valide_manuellement IN (0,1)),
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE,
    FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS erreurs_extraction (
    erreur_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    type_erreur TEXT NOT NULL,
    champ_concerne TEXT,
    message_erreur TEXT NOT NULL,
    date_erreur TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE SET NULL
);

-- ═══════════════════════════════════════════════════════
-- COUCHE 3 — IA / Validation / Audit
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS traitements (
    traitement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    agent_nom TEXT NOT NULL,
    statut TEXT NOT NULL,
    date_debut TEXT,
    date_fin TEXT,
    duree_ms INTEGER,
    version_agent TEXT,
    message_erreur TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS resultats_validation (
    resultat_validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    regle_id TEXT NOT NULL,
    regle_description TEXT,
    source_legale TEXT,
    resultat TEXT NOT NULL CHECK(resultat IN ('PASS', 'FAIL')),
    message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    score_base INTEGER DEFAULT 100,
    score_final INTEGER NOT NULL,
    nb_regles_appliquees INTEGER DEFAULT 0,
    nb_penalites INTEGER DEFAULT 0,
    nb_bonus INTEGER DEFAULT 0,
    flags_actifs TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS details_scoring (
    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    score_id INTEGER NOT NULL,
    regle_id TEXT NOT NULL,
    condition_evaluee TEXT,
    condition_remplie INTEGER CHECK(condition_remplie IN (0,1)),
    delta_score INTEGER DEFAULT 0,
    flag_genere TEXT,
    justification TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (score_id)
        REFERENCES scores(score_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    score_id INTEGER,
    decision TEXT NOT NULL CHECK(decision IN ('accepter','refuser','complement_requis')),
    motif_principal TEXT,
    message_client TEXT,
    seuil_utilise TEXT,
    flag_bloquant TEXT,
    necessite_validation_humaine INTEGER DEFAULT 0 CHECK(necessite_validation_humaine IN (0,1)),
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE,
    FOREIGN KEY (score_id)
        REFERENCES scores(score_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS flags_sinistres (
    flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    code_flag TEXT NOT NULL,
    niveau_severite TEXT,
    agent_source TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER,
    agent_nom TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    date_action TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS feedbacks_humains (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    utilisateur_id INTEGER,
    type_feedback TEXT NOT NULL,
    decision_originale TEXT,
    decision_corrigee TEXT,
    motif_correction TEXT,
    date_feedback TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id)
        REFERENCES dossiers_sinistres(dossier_id)
        ON DELETE CASCADE
);

-- ═══════════════════════════════════════════════════════
-- COUCHE 4 — Authentification
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS utilisateurs (
    utilisateur_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    mot_de_passe_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('EMPLOYE','GESTIONNAIRE','ADMIN')),
    employe_id INTEGER,
    nom_complet TEXT NOT NULL,
    actif INTEGER DEFAULT 1 CHECK(actif IN (0,1)),
    derniere_connexion TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employe_id)
        REFERENCES employes(employe_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_utilisateurs_email ON utilisateurs(email);
CREATE INDEX IF NOT EXISTS idx_utilisateurs_role  ON utilisateurs(role);
"""