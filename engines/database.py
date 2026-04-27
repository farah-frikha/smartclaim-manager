
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS Documents (
    document_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER NOT NULL,
    nom_fichier_original     TEXT NOT NULL,
    type_document            TEXT NOT NULL, -- formulaire, attestation, etc.
    format_fichier           TEXT NOT NULL, -- pdf, jpg...
    taille_octets            INTEGER,
    hash_sha256              TEXT,
    chemin_stockage          TEXT NOT NULL,
    date_reception           TEXT NOT NULL, -- ISO8601
    source                   TEXT,          -- email, portail, scan...
    statut_traitement        TEXT DEFAULT 'recu',
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_documents_dossier_id ON Documents(dossier_id);
CREATE INDEX IF NOT EXISTS idx_documents_hash_sha256 ON Documents(hash_sha256);

CREATE TABLE IF NOT EXISTS Pages_ocr (
    page_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id              INTEGER NOT NULL,
    numero_page              INTEGER NOT NULL,
    texte_brut               TEXT,
    score_confiance_ocr      REAL,          -- 0..1
    langue_detectee          TEXT,
    date_traitement          TEXT,          -- ISO8601
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES Documents(document_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pages_ocr_document_id ON Pages_ocr(document_id);
CREATE INDEX IF NOT EXISTS idx_pages_ocr_numero_page ON Pages_ocr(numero_page);

CREATE TABLE IF NOT EXISTS champs_extraits (
    extraction_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER NOT NULL,
    document_id              INTEGER,
    nom_champ                TEXT NOT NULL,
    valeur_extraite          TEXT,
    valeur_normalisee        TEXT,
    score_confiance_llm      REAL,          -- 0..1
    page_source              INTEGER,
    prompt_utilise           TEXT,
    date_extraction          TEXT,          -- ISO8601
    valide_manuellement      INTEGER DEFAULT 0 CHECK (valide_manuellement IN (0,1)),
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES Documents(document_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_champs_extraits_dossier_id ON champs_extraits(dossier_id);
CREATE INDEX IF NOT EXISTS idx_champs_extraits_document_id ON champs_extraits(document_id);
CREATE INDEX IF NOT EXISTS idx_champs_extraits_nom_champ ON champs_extraits(nom_champ);

CREATE TABLE IF NOT EXISTS erreurs_extraction (
    erreur_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id              INTEGER,
    type_erreur              TEXT NOT NULL,
    champ_concerne           TEXT,
    message_erreur           TEXT NOT NULL,
    date_erreur              TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES Documents(document_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_erreurs_extraction_document_id ON erreurs_extraction(document_id);

-- =========================================================
-- Couche 3 – Données métier
-- =========================================================

CREATE TABLE IF NOT EXISTS employeurs (
    employeur_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    raison_sociale           TEXT NOT NULL,
    matricule_fiscale        TEXT UNIQUE,
    secteur_activite         TEXT,
    taille_entreprise        TEXT,
    date_inscription_cnss    TEXT, -- ISO8601
    statut_cotisations_cnss  TEXT, -- ok, en_retard, suspendu...
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS employes (
    employe_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    employeur_id             INTEGER,
    numero_cnss              TEXT UNIQUE NOT NULL,
    nom                      TEXT NOT NULL,
    prenom                   TEXT NOT NULL,
    date_naissance           TEXT, -- ISO8601
    categorie_professionnelle TEXT,
    date_embauche            TEXT, -- ISO8601
    salaire_reference_cnss   REAL,
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employeur_id) REFERENCES employeurs(employeur_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_employes_employeur_id ON employes(employeur_id);
CREATE INDEX IF NOT EXISTS idx_employes_numero_cnss ON employes(numero_cnss);

CREATE TABLE IF NOT EXISTS ayants_droit (
    ayant_droit_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    employe_id               INTEGER NOT NULL,
    lien                     TEXT NOT NULL, -- conjoint, enfant...
    nom                      TEXT NOT NULL,
    prenom                   TEXT NOT NULL,
    date_naissance           TEXT,
    actif                    INTEGER DEFAULT 1 CHECK (actif IN (0,1)),
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employe_id) REFERENCES employes(employe_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ayants_droit_employe_id ON ayants_droit(employe_id);

CREATE TABLE IF NOT EXISTS contrats_collectifs (
    contrat_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    employeur_id             INTEGER NOT NULL,
    numero_contrat           TEXT UNIQUE NOT NULL,
    compagnie_assurance      TEXT NOT NULL,
    type_contrat             TEXT,
    date_effet               TEXT NOT NULL,
    date_echeance            TEXT,
    garanties_couvertes      TEXT, -- JSON string
    exclusions               TEXT, -- JSON string
    delai_carence_jours      INTEGER,
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employeur_id) REFERENCES employeurs(employeur_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_contrats_collectifs_employeur_id ON contrats_collectifs(employeur_id);
CREATE INDEX IF NOT EXISTS idx_contrats_collectifs_numero_contrat ON contrats_collectifs(numero_contrat);

CREATE TABLE IF NOT EXISTS adhesions (
    adhesion_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    employe_id               INTEGER NOT NULL,
    contrat_id               INTEGER NOT NULL,
    date_adhesion            TEXT NOT NULL,
    statut                   TEXT NOT NULL, -- actif, suspendu, termine...
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employe_id) REFERENCES employes(employe_id) ON DELETE CASCADE,
    FOREIGN KEY (contrat_id) REFERENCES contrats_collectifs(contrat_id) ON DELETE CASCADE,
    UNIQUE (employe_id, contrat_id)
);

CREATE INDEX IF NOT EXISTS idx_adhesions_employe_id ON adhesions(employe_id);
CREATE INDEX IF NOT EXISTS idx_adhesions_contrat_id ON adhesions(contrat_id);

CREATE TABLE IF NOT EXISTS types_sinistres (
    type_sinistre_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code                     TEXT UNIQUE NOT NULL,
    libelle                  TEXT NOT NULL,
    categorie                TEXT NOT NULL, -- sante, prevoyance...
    documents_requis         TEXT, -- JSON string
    delai_declaration_jours  INTEGER,
    source_legale            TEXT,
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_types_sinistres_code ON types_sinistres(code);

CREATE TABLE IF NOT EXISTS dossiers_sinistres (
    dossier_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_dossier        TEXT UNIQUE NOT NULL,
    employe_id               INTEGER NOT NULL,
    ayant_droit_id           INTEGER,
    contrat_id               INTEGER NOT NULL,
    type_sinistre_id         INTEGER NOT NULL,
    date_sinistre            TEXT NOT NULL,
    date_declaration         TEXT,
    delai_declaration_jours  INTEGER,
    montant_reclame          REAL DEFAULT 0,
    montant_cnss_rembourse   REAL DEFAULT 0,
    nb_sinistres_anterieurs_12mois INTEGER DEFAULT 0,
    statut_global            TEXT DEFAULT 'recu', -- recu, en_cours, accepte, refuse...
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (employe_id) REFERENCES employes(employe_id) ON DELETE RESTRICT,
    FOREIGN KEY (ayant_droit_id) REFERENCES ayants_droit(ayant_droit_id) ON DELETE SET NULL,
    FOREIGN KEY (contrat_id) REFERENCES contrats_collectifs(contrat_id) ON DELETE RESTRICT,
    FOREIGN KEY (type_sinistre_id) REFERENCES types_sinistres(type_sinistre_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_dossiers_reference ON dossiers_sinistres(reference_dossier);
CREATE INDEX IF NOT EXISTS idx_dossiers_employe_id ON dossiers_sinistres(employe_id);
CREATE INDEX IF NOT EXISTS idx_dossiers_contrat_id ON dossiers_sinistres(contrat_id);
CREATE INDEX IF NOT EXISTS idx_dossiers_statut_global ON dossiers_sinistres(statut_global);

-- =========================================================
-- Couche 4 – IA et traçabilité
-- =========================================================

CREATE TABLE IF NOT EXISTS traitements (
    traitement_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER NOT NULL,
    agent_nom                TEXT NOT NULL,  -- Capture, Extraction...
    statut                   TEXT NOT NULL,  -- started, success, failed
    date_debut               TEXT,
    date_fin                 TEXT,
    duree_ms                 INTEGER,
    version_agent            TEXT,
    message_erreur           TEXT,
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id) REFERENCES dossiers_sinistres(dossier_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_traitements_dossier_id ON traitements(dossier_id);
CREATE INDEX IF NOT EXISTS idx_traitements_agent_nom ON traitements(agent_nom);

CREATE TABLE IF NOT EXISTS resultats_validation (
    resultat_validation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER NOT NULL,
    regle_id                 TEXT NOT NULL,
    regle_description        TEXT,
    source_legale            TEXT,
    resultat                 TEXT NOT NULL, -- passe, echoue, non_applicable
    valeur_evaluee           TEXT,
    valeur_attendue          TEXT,
    message                  TEXT,
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id) REFERENCES dossiers_sinistres(dossier_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resultats_validation_dossier_id ON resultats_validation(dossier_id);
CREATE INDEX IF NOT EXISTS idx_resultats_validation_regle_id ON resultats_validation(regle_id);

CREATE TABLE IF NOT EXISTS scores (
    score_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER NOT NULL,
    score_base               INTEGER DEFAULT 100,
    score_final              INTEGER NOT NULL,
    nb_regles_appliquees     INTEGER DEFAULT 0,
    nb_penalites             INTEGER DEFAULT 0,
    nb_bonus                 INTEGER DEFAULT 0,
    flags_actifs             TEXT, -- JSON string
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id) REFERENCES dossiers_sinistres(dossier_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scores_dossier_id ON scores(dossier_id);

CREATE TABLE IF NOT EXISTS details_scoring (
    detail_scoring_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    score_id                 INTEGER NOT NULL,
    regle_id                 TEXT NOT NULL,
    condition_evaluee        TEXT,
    condition_remplie        INTEGER NOT NULL CHECK (condition_remplie IN (0,1)),
    delta_score              INTEGER NOT NULL,
    flag_genere              TEXT,
    justification            TEXT,
    source_legale            TEXT,
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (score_id) REFERENCES scores(score_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_details_scoring_score_id ON details_scoring(score_id);
CREATE INDEX IF NOT EXISTS idx_details_scoring_regle_id ON details_scoring(regle_id);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER NOT NULL,
    score_id                 INTEGER,
    decision                 TEXT NOT NULL, -- accepter, refuser, complement_requis
    motif_principal          TEXT,
    message_client           TEXT,
    seuil_utilise            TEXT,
    flag_bloquant            TEXT,
    necessite_validation_humaine INTEGER DEFAULT 0 CHECK (necessite_validation_humaine IN (0,1)),
    confirmee_par_expert     INTEGER DEFAULT 0 CHECK (confirmee_par_expert IN (0,1)),
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id) REFERENCES dossiers_sinistres(dossier_id) ON DELETE CASCADE,
    FOREIGN KEY (score_id) REFERENCES scores(score_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_decisions_dossier_id ON decisions(dossier_id);
CREATE INDEX IF NOT EXISTS idx_decisions_score_id ON decisions(score_id);

CREATE TABLE IF NOT EXISTS flags_sinistres (
    flag_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER NOT NULL,
    code_flag                TEXT NOT NULL,
    niveau_severite          TEXT, -- faible, moyen, eleve, critique
    description              TEXT,
    agent_source             TEXT NOT NULL,
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id) REFERENCES dossiers_sinistres(dossier_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_flags_sinistres_dossier_id ON flags_sinistres(dossier_id);
CREATE INDEX IF NOT EXISTS idx_flags_sinistres_code_flag ON flags_sinistres(code_flag);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id               INTEGER,
    agent_nom                TEXT NOT NULL,
    action                   TEXT NOT NULL,
    details                  TEXT, -- JSON string
    date_action              TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (dossier_id) REFERENCES dossiers_sinistres(dossier_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_dossier_id ON audit_logs(dossier_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_agent_nom ON audit_logs(agent_nom);

CREATE TABLE IF NOT EXISTS feedbacks_humains (
    feedback_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id              INTEGER NOT NULL,
    decision_originale       TEXT NOT NULL,
    decision_corrigee        TEXT NOT NULL,
    motif_correction         TEXT,
    regles_a_ajuster         TEXT, -- JSON string
    created_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedbacks_humains_decision_id ON feedbacks_humains(decision_id);
"""