import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
from pathlib import Path
from loguru import logger
from config import DB_PATH

# Configuration

DB_FILE = Path(DB_PATH)
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;


-- Couche 1 – Données métier principales


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

CREATE INDEX IF NOT EXISTS idx_employes_employeur_id
ON employes(employeur_id);

CREATE INDEX IF NOT EXISTS idx_employes_numero_cnss
ON employes(numero_cnss);

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

CREATE INDEX IF NOT EXISTS idx_ayants_droit_employe_id
ON ayants_droit(employe_id);

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


-- Couche 2 – Documents & OCR


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

CREATE INDEX IF NOT EXISTS idx_documents_dossier_id
ON documents(dossier_id);

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


-- Couche 3 – IA / Validation / Audit


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
    resultat TEXT NOT NULL,
    valeur_evaluee TEXT,
    valeur_attendue TEXT,
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
    detail_scoring_id INTEGER PRIMARY KEY AUTOINCREMENT,
    score_id INTEGER NOT NULL,
    regle_id TEXT NOT NULL,
    condition_evaluee TEXT,
    condition_remplie INTEGER CHECK(condition_remplie IN (0,1)),
    delta_score INTEGER NOT NULL,
    flag_genere TEXT,
    justification TEXT,
    source_legale TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (score_id)
        REFERENCES scores(score_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    score_id INTEGER,
    decision TEXT NOT NULL,
    motif_principal TEXT,
    message_client TEXT,
    seuil_utilise TEXT,
    flag_bloquant TEXT,
    necessite_validation_humaine INTEGER DEFAULT 0 CHECK(necessite_validation_humaine IN (0,1)),
    confirmee_par_expert INTEGER DEFAULT 0 CHECK(confirmee_par_expert IN (0,1)),
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
    description TEXT,
    agent_source TEXT NOT NULL,
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
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedbacks_humains (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL,
    decision_originale TEXT NOT NULL,
    decision_corrigee TEXT NOT NULL,
    motif_correction TEXT,
    regles_a_ajuster TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (decision_id)
        REFERENCES decisions(decision_id)
        ON DELETE CASCADE
);
"""

# =========================================================
# Connexion DB
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# Initialisation
# =========================================================

def init_db():
    logger.info(f"Initialisation DB : {DB_PATH}")

    try:
        conn = get_connection()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()

        logger.success("Base initialisée avec succès ")

    except Exception as e:
        logger.error(f"Erreur DB : {e}")
        raise


# =========================================================
# Vérification tables
# =========================================================

def test_db():
    conn = get_connection()

    cursor = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)

    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    return tables
# =========================================================
# SECTION CRUD — Fonctions d'écriture par agent
# =========================================================

import json
from datetime import datetime


# ─────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────

def generer_reference_dossier() -> str:
    """Génère une référence unique : SC-2026-XXXXXX"""
    import random
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"SC-{datetime.now().year}-{ts[-6:]}{rand}"


def log_audit(conn, dossier_id: int, agent: str,
              action: str, details: dict = None):
    """Insère une ligne dans audit_logs."""
    conn.execute("""
        INSERT INTO audit_logs
            (dossier_id, agent_nom, action, details, date_action)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (
        dossier_id,
        agent,
        action,
        json.dumps(details, ensure_ascii=False) if details else None
    ))


# ─────────────────────────────────────────────────────────
# AGENT CAPTURE — sauvegarder le document et les pages OCR
# ─────────────────────────────────────────────────────────

def sauvegarder_document(dossier_id: int,
                         resultat_capture: dict) -> int:
    """
    Insère le document reçu dans la table documents.
    Insère chaque page OCR dans pages_ocr.
    Retourne le document_id créé.
    """
    conn = get_connection()
    try:
        meta = resultat_capture.get("metadata", {})

        # Insertion document
        cursor = conn.execute("""
            INSERT INTO documents (
                dossier_id, nom_fichier_original, type_document,
                format_fichier, taille_octets, hash_sha256,
                chemin_stockage, date_reception, statut_traitement
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'ocr_termine')
        """, (
            dossier_id,
            resultat_capture.get("nom_fichier", "inconnu"),
            resultat_capture.get("type_document", "autre"),
            Path(resultat_capture.get("nom_fichier", "")).suffix.lstrip(".") or "pdf",
            int(meta.get("taille_ko", 0) * 1024),
            meta.get("hash_sha256"),
            meta.get("chemin", "")
        ))
        document_id = cursor.lastrowid

        # Insertion pages OCR
        for page in resultat_capture.get("pages", []):
            conn.execute("""
                INSERT INTO pages_ocr (
                    document_id, numero_page, texte_brut,
                    score_confiance_ocr, langue_detectee, date_traitement
                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                document_id,
                page.get("numero_page", 1),
                page.get("texte_brut", ""),
                page.get("score_confiance", 0.0),
                page.get("langue_detectee", "fr")
            ))

        # Audit log
        log_audit(conn, dossier_id, "capture", "DOCUMENT_RECU", {
            "nom_fichier": resultat_capture.get("nom_fichier"),
            "nb_pages":    resultat_capture.get("nb_pages"),
            "confiance":   resultat_capture.get("score_confiance")
        })

        conn.commit()
        logger.success(f"Document sauvegardé — document_id={document_id}")
        return document_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_document : {e}")
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# AGENT EXTRACTION — sauvegarder les champs extraits
# ─────────────────────────────────────────────────────────

def sauvegarder_extraction(dossier_id: int,
                           document_id: int,
                           resultat_extraction: dict) -> bool:
    """
    Insère chaque champ extrait dans champs_extraits.
    Insère les erreurs éventuelles dans erreurs_extraction.
    """
    conn = get_connection()
    try:
        dossier = resultat_extraction.get("dossier_extrait", {})
        completude = resultat_extraction.get("score_completude", 0)

        # Un enregistrement par champ extrait
        for nom_champ, valeur in dossier.items():
            conn.execute("""
                INSERT INTO champs_extraits (
                    dossier_id, document_id, nom_champ,
                    valeur_extraite, valeur_normalisee,
                    score_confiance_llm, date_extraction
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                dossier_id,
                document_id,
                nom_champ,
                str(valeur) if valeur is not None else None,
                str(valeur) if valeur is not None else None,
                completude
            ))

        # Erreurs sur champs manquants
        for champ in resultat_extraction.get("champs_manquants", []):
            conn.execute("""
                INSERT INTO erreurs_extraction (
                    document_id, type_erreur,
                    champ_concerne, message_erreur
                ) VALUES (?, 'champ_manquant', ?, ?)
            """, (
                document_id,
                champ,
                f"Champ obligatoire '{champ}' absent du document"
            ))

        # Audit log
        log_audit(conn, dossier_id, "extraction", "CHAMPS_EXTRAITS", {
            "completude":     completude,
            "nb_champs":      len(dossier),
            "manquants":      resultat_extraction.get("champs_manquants"),
            "llm_duree_ms":   resultat_extraction.get("llm_duree_ms")
        })

        conn.commit()
        logger.success(
            f"Extraction sauvegardée — "
            f"{len(dossier)} champs, complétude={completude}"
        )
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_extraction : {e}")
        return False
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# AGENT VALIDATION — sauvegarder les résultats règle par règle
# ─────────────────────────────────────────────────────────

def sauvegarder_validation(dossier_id: int,
                           resultat_validation: dict) -> bool:
    """
    Insère chaque résultat de règle dans resultats_validation.
    Met à jour statut_global du dossier.
    """
    conn = get_connection()
    try:
        # Une ligne par règle évaluée
        for detail in resultat_validation.get("details", []):
            conn.execute("""
                INSERT INTO resultats_validation (
                    dossier_id, regle_id, regle_description,
                    source_legale, resultat, message
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dossier_id,
                detail.get("id"),
                detail.get("description"),
                detail.get("source"),
                detail.get("resultat"),  # PASS ou FAIL
                detail.get("message")
            ))

        # Mise à jour statut dossier
        nouveau_statut = "valide" if resultat_validation["valide"] \
                         else "invalide"
        conn.execute("""
            UPDATE dossiers_sinistres
            SET statut_global = ?, updated_at = datetime('now')
            WHERE dossier_id = ?
        """, (nouveau_statut, dossier_id))

        # Audit log
        log_audit(conn, dossier_id, "validation", "VALIDATION_TERMINEE", {
            "valide":           resultat_validation["valide"],
            "nb_regles":        resultat_validation["nb_regles_total"],
            "echecs_bloquants": resultat_validation["echecs_bloquants"],
            "echecs_mineurs":   resultat_validation["echecs_mineurs"]
        })

        conn.commit()
        logger.success(
            f"Validation sauvegardée — "
            f"valide={resultat_validation['valide']}, "
            f"dossier_id={dossier_id}"
        )
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_validation : {e}")
        return False
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# AGENT SCORING — sauvegarder le score et les détails
# ─────────────────────────────────────────────────────────

def sauvegarder_scoring(dossier_id: int,
                        resultat_scoring: dict) -> int:
    """
    Insère le score dans scores.
    Insère chaque règle déclenchée dans details_scoring.
    Insère les flags dans flags_sinistres.
    Retourne le score_id créé.
    """
    conn = get_connection()
    try:
        # Insertion score global
        cursor = conn.execute("""
            INSERT INTO scores (
                dossier_id, score_base, score_final,
                nb_regles_appliquees, nb_penalites,
                nb_bonus, flags_actifs
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dossier_id,
            resultat_scoring.get("score_base", 100),
            resultat_scoring.get("score", 0),
            len(resultat_scoring.get("details", [])),
            resultat_scoring.get("nb_penalites", 0),
            resultat_scoring.get("nb_bonus", 0),
            json.dumps(resultat_scoring.get("flags", []))
        ))
        score_id = cursor.lastrowid

        # Détail par règle déclenchée
        for detail in resultat_scoring.get("details", []):
            if detail.get("declenchee"):
                conn.execute("""
                    INSERT INTO details_scoring (
                        score_id, regle_id, condition_evaluee,
                        condition_remplie, delta_score,
                        flag_genere, justification
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    score_id,
                    detail.get("id"),
                    detail.get("condition"),
                    1 if detail.get("declenchee") else 0,
                    detail.get("delta_score", 0),
                    detail.get("flag_genere"),
                    detail.get("justification")
                ))

        # Flags dans flags_sinistres
        for flag in resultat_scoring.get("flags", []):
            conn.execute("""
                INSERT INTO flags_sinistres (
                    dossier_id, code_flag,
                    niveau_severite, agent_source
                ) VALUES (?, ?, 'avertissement', 'scoring')
            """, (dossier_id, flag))

        # Audit log
        log_audit(conn, dossier_id, "scoring", "SCORE_CALCULE", {
            "score_final":   resultat_scoring.get("score"),
            "niveau_risque": resultat_scoring.get("niveau_risque"),
            "flags":         resultat_scoring.get("flags")
        })

        conn.commit()
        logger.success(
            f"Scoring sauvegardé — "
            f"score={resultat_scoring.get('score')}, "
            f"score_id={score_id}"
        )
        return score_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_scoring : {e}")
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# AGENT DECISION — sauvegarder la décision finale
# ─────────────────────────────────────────────────────────

def sauvegarder_decision(dossier_id: int,
                         score_id: int,
                         resultat_decision: dict) -> int:
    """
    Insère la décision dans decisions.
    Met à jour statut_global du dossier.
    Retourne le decision_id créé.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO decisions (
                dossier_id, score_id, decision,
                motif_principal, message_client,
                seuil_utilise, flag_bloquant,
                necessite_validation_humaine
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dossier_id,
            score_id,
            resultat_decision.get("decision"),
            resultat_decision.get("motif_principal"),
            resultat_decision.get("message_client"),
            resultat_decision.get("seuil_utilise"),
            resultat_decision.get("flag_bloquant"),
            1 if resultat_decision.get("necessite_validation_humaine")
              else 0
        ))
        decision_id = cursor.lastrowid

        # Mise à jour statut final du dossier
        statut_map = {
            "accepter":         "accepte",
            "refuser":          "refuse",
            "complement_requis": "complement_requis"
        }
        statut_final = statut_map.get(
            resultat_decision.get("decision"), "en_traitement"
        )
        conn.execute("""
            UPDATE dossiers_sinistres
            SET statut_global = ?, updated_at = datetime('now')
            WHERE dossier_id = ?
        """, (statut_final, dossier_id))

        # Audit log
        log_audit(conn, dossier_id, "decision", "DECISION_RENDUE", {
            "decision":    resultat_decision.get("decision"),
            "motif":       resultat_decision.get("motif_principal"),
            "escalade":    resultat_decision.get(
                               "necessite_validation_humaine"
                           )
        })

        conn.commit()
        logger.success(
            f"Décision sauvegardée — "
            f"{resultat_decision.get('decision').upper()}, "
            f"decision_id={decision_id}"
        )
        return decision_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur sauvegarder_decision : {e}")
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────
# LECTURE — récupérer un dossier complet
# ─────────────────────────────────────────────────────────

def lire_dossier_complet(dossier_id: int) -> dict:
    """
    Lit toutes les données d'un dossier depuis la BDD.
    Utile pour l'interface Streamlit et l'Agent Feedback.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        # Dossier principal
        dossier = conn.execute("""
            SELECT * FROM dossiers_sinistres
            WHERE dossier_id = ?
        """, (dossier_id,)).fetchone()

        if not dossier:
            return {"erreur": f"Dossier {dossier_id} introuvable"}

        # Champs extraits
        champs = conn.execute("""
            SELECT nom_champ, valeur_normalisee
            FROM champs_extraits
            WHERE dossier_id = ?
        """, (dossier_id,)).fetchall()

        # Résultats validation
        validation = conn.execute("""
            SELECT regle_id, resultat, message
            FROM resultats_validation
            WHERE dossier_id = ?
        """, (dossier_id,)).fetchall()

        # Score
        score = conn.execute("""
            SELECT * FROM scores
            WHERE dossier_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (dossier_id,)).fetchone()

        # Décision
        decision = conn.execute("""
            SELECT * FROM decisions
            WHERE dossier_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (dossier_id,)).fetchone()

        # Audit log
        logs = conn.execute("""
            SELECT agent_nom, action, details, date_action
            FROM audit_logs
            WHERE dossier_id = ?
            ORDER BY date_action ASC
        """, (dossier_id,)).fetchall()

        return {
            "dossier":    dict(dossier),
            "champs":     {r["nom_champ"]: r["valeur_normalisee"]
                           for r in champs},
            "validation": [dict(r) for r in validation],
            "score":      dict(score) if score else None,
            "decision":   dict(decision) if decision else None,
            "audit_logs": [dict(r) for r in logs]
        }

    finally:
        conn.close()


def lister_dossiers(statut: str = None, limite: int = 50) -> list:
    """
    Liste les dossiers avec filtre optionnel sur le statut.
    Utilisé par l'interface Streamlit — page historique.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        if statut:
            rows = conn.execute("""
                SELECT dossier_id, reference_dossier,
                       statut_global, montant_reclame,
                       date_sinistre, created_at
                FROM dossiers_sinistres
                WHERE statut_global = ?
                ORDER BY created_at DESC LIMIT ?
            """, (statut, limite)).fetchall()
        else:
            rows = conn.execute("""
                SELECT dossier_id, reference_dossier,
                       statut_global, montant_reclame,
                       date_sinistre, created_at
                FROM dossiers_sinistres
                ORDER BY created_at DESC LIMIT ?
            """, (limite,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

# =========================================================
# Main
# =========================================================

if __name__ == "__main__":
    init_db()
    tables = test_db()
    print(f"\n✅ {len(tables)} tables créées")

    # ── Test CRUD complet ─────────────────────────────────
    print("\nTest CRUD...")
    conn = get_connection()

    # Insérer données de référence minimales
    conn.execute("""
        INSERT OR IGNORE INTO types_sinistres
            (code, libelle, categorie)
        VALUES ('AUTO_ACCIDENT', 'Accident automobile', 'auto')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO employeurs
            (raison_sociale, statut_cotisations_cnss)
        VALUES ('Société Test', 'a_jour')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO employes
            (employeur_id, numero_cnss, nom, prenom)
        VALUES (1, '145789632', 'Ben Salah', 'Mohamed')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO contrats_collectifs
            (employeur_id, numero_contrat, compagnie_assurance, date_effet)
        VALUES (1, 'STAR-AUTO-2024-00847', 'El Aman', '2024-01-05')
    """)
    conn.commit()

    # Créer un dossier
    ref = generer_reference_dossier()
    cursor = conn.execute("""
        INSERT INTO dossiers_sinistres (
            reference_dossier, employe_id, contrat_id,
            type_sinistre_id, date_sinistre, montant_reclame,
            statut_global
        ) VALUES (?, 1, 1, 1, '2026-03-15', 2800.0, 'recu')
    """, (ref,))
    dossier_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f" Dossier créé — id={dossier_id}, ref={ref}")

    # Lire le dossier
    dossier = lire_dossier_complet(dossier_id)
    print(f" Lecture OK — statut={dossier['dossier']['statut_global']}")
    print("\n CRUD validé — database.py prêt")