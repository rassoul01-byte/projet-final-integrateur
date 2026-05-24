-- ============================================================
-- schema.sql — Gestion Étudiants
-- Base de données PostgreSQL
-- ============================================================

-- Extension pour les UUIDs (optionnelle)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------
-- Suppression des tables existantes (ordre inverse des FK)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS notes_devoir CASCADE;
DROP TABLE IF EXISTS matieres CASCADE;
DROP TABLE IF EXISTS etudiants CASCADE;
DROP TABLE IF EXISTS classes CASCADE;

-- ------------------------------------------------------------
-- Table : classes
-- ------------------------------------------------------------
CREATE TABLE classes (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(50) NOT NULL UNIQUE
);

-- ------------------------------------------------------------
-- Table : etudiants
-- ------------------------------------------------------------
CREATE TABLE etudiants (
    id              SERIAL PRIMARY KEY,
    numero          VARCHAR(20)  NOT NULL UNIQUE,   -- identifiant unique métier
    code            VARCHAR(20)  NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    nom             VARCHAR(100) NOT NULL,
    date_naissance  DATE,
    classe_id       INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    moyenne_generale NUMERIC(5,2),
    archive         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Table : matieres
-- ------------------------------------------------------------
CREATE TABLE matieres (
    id              SERIAL PRIMARY KEY,
    etudiant_id     INTEGER NOT NULL REFERENCES etudiants(id) ON DELETE CASCADE,
    nom             VARCHAR(100) NOT NULL,
    note_examen     NUMERIC(5,2),
    moyenne         NUMERIC(5,2)
);

-- ------------------------------------------------------------
-- Table : notes_devoir
-- ------------------------------------------------------------
CREATE TABLE notes_devoir (
    id          SERIAL PRIMARY KEY,
    matiere_id  INTEGER NOT NULL REFERENCES matieres(id) ON DELETE CASCADE,
    note        NUMERIC(5,2) NOT NULL
);

-- ------------------------------------------------------------
-- Index pour les recherches fréquentes
-- ------------------------------------------------------------
CREATE INDEX idx_etudiants_numero    ON etudiants(numero);
CREATE INDEX idx_etudiants_nom       ON etudiants(nom);
CREATE INDEX idx_etudiants_prenom    ON etudiants(prenom);
CREATE INDEX idx_etudiants_code      ON etudiants(code);
CREATE INDEX idx_etudiants_classe    ON etudiants(classe_id);
CREATE INDEX idx_etudiants_archive   ON etudiants(archive);
CREATE INDEX idx_matieres_etudiant   ON matieres(etudiant_id);
CREATE INDEX idx_notes_matiere       ON notes_devoir(matiere_id);

-- ------------------------------------------------------------
-- Trigger : mise à jour automatique de updated_at
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_etudiants_updated_at
    BEFORE UPDATE ON etudiants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ------------------------------------------------------------
-- Vue : liste complète des étudiants (avec nom de classe)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vue_etudiants AS
SELECT
    e.id,
    e.numero,
    e.code,
    e.prenom,
    e.nom,
    e.date_naissance,
    c.nom           AS classe,
    e.moyenne_generale,
    e.archive,
    e.created_at,
    e.updated_at
FROM etudiants e
LEFT JOIN classes c ON c.id = e.classe_id;

-- ------------------------------------------------------------
-- Vue : statistiques par classe
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vue_stats_classes AS
SELECT
    c.nom                           AS classe,
    COUNT(e.id)                     AS total_etudiants,
    ROUND(AVG(e.moyenne_generale), 2) AS moyenne_classe,
    MAX(e.moyenne_generale)         AS meilleure_moyenne,
    MIN(e.moyenne_generale)         AS plus_basse_moyenne
FROM classes c
LEFT JOIN etudiants e ON e.classe_id = c.id AND e.archive = FALSE
GROUP BY c.nom
ORDER BY c.nom;

-- ------------------------------------------------------------
-- Données initiales : classes (à adapter selon valides.json)
-- ------------------------------------------------------------
INSERT INTO classes (nom) VALUES
    ('Terminale A'),
    ('Terminale B'),
    ('Terminale C'),
    ('Premiere A'),
    ('Premiere B')
ON CONFLICT (nom) DO NOTHING;
