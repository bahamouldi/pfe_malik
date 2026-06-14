-- ====================== DIMENSIONS ======================
DROP TABLE IF EXISTS Dim_Societe;
CREATE TABLE Dim_Societe (
    id_societe   INTEGER PRIMARY KEY,
    societe      TEXT NOT NULL UNIQUE,
    role         TEXT,      -- principale | benchmark
    secteur      TEXT,
    devise       TEXT,      -- TND | USD
    echelle      TEXT       -- unite | million
);

DROP TABLE IF EXISTS Dim_Temps;
CREATE TABLE Dim_Temps (
    id_temps     INTEGER PRIMARY KEY,
    date         TEXT NOT NULL UNIQUE,
    annee        INTEGER,
    mois         INTEGER,
    periode      TEXT,      -- T1 | S1 | 9M | FY
    type_cloture TEXT       -- Trimestrielle | Semestrielle | Annuelle
);

DROP TABLE IF EXISTS Dim_Indicateur;
CREATE TABLE Dim_Indicateur (
    id_indicateur INTEGER PRIMARY KEY,
    cle           TEXT NOT NULL,
    libelle       TEXT,
    statement     TEXT,     -- Bilan - Actif | ... | SIG | Inconnu
    nature        TEXT,     -- stock | flux
    UNIQUE (cle, statement)
);

DROP TABLE IF EXISTS Dim_Ratio;
CREATE TABLE Dim_Ratio (
    id_ratio       INTEGER PRIMARY KEY,
    code_ratio     TEXT NOT NULL UNIQUE,
    ratio          TEXT,
    categorie      TEXT,
    sous_categorie TEXT,
    unite          TEXT,    -- x | % | j | score | montant
    benchmark      TEXT     -- fourchette cible industrielle
);

-- ====================== FAITS ======================
DROP TABLE IF EXISTS Fait_Etats_Financiers;
CREATE TABLE Fait_Etats_Financiers (
    id_societe    INTEGER NOT NULL REFERENCES Dim_Societe(id_societe),
    id_temps      INTEGER NOT NULL REFERENCES Dim_Temps(id_temps),
    id_indicateur INTEGER NOT NULL REFERENCES Dim_Indicateur(id_indicateur),
    valeur        REAL,
    type_donnee   TEXT,     -- Reel | Estime
    occurrence    INTEGER
);

DROP TABLE IF EXISTS Fait_Ratios;
CREATE TABLE Fait_Ratios (
    id_societe INTEGER NOT NULL REFERENCES Dim_Societe(id_societe),
    id_temps   INTEGER NOT NULL REFERENCES Dim_Temps(id_temps),
    id_ratio   INTEGER NOT NULL REFERENCES Dim_Ratio(id_ratio),
    valeur     REAL,
    note_sur_5 REAL          -- note de scoring (NULL si non noté)
);

DROP TABLE IF EXISTS Fait_SGPI;
CREATE TABLE Fait_SGPI (
    id_societe   INTEGER NOT NULL REFERENCES Dim_Societe(id_societe),
    id_temps     INTEGER NOT NULL REFERENCES Dim_Temps(id_temps),
    sgpi_sur_100 REAL,
    couverture   REAL
);

-- ====================== INDEX ======================
CREATE INDEX ix_faitef_soc   ON Fait_Etats_Financiers(id_societe);
CREATE INDEX ix_faitef_temps ON Fait_Etats_Financiers(id_temps);
CREATE INDEX ix_faitef_ind   ON Fait_Etats_Financiers(id_indicateur);
CREATE INDEX ix_faitr_soc    ON Fait_Ratios(id_societe);
CREATE INDEX ix_faitr_temps  ON Fait_Ratios(id_temps);
CREATE INDEX ix_faitr_ratio  ON Fait_Ratios(id_ratio);

-- ====================== VUES ANALYTIQUES ======================
DROP VIEW IF EXISTS v_ratios;
CREATE VIEW v_ratios AS
SELECT s.societe, s.role, s.secteur, t.annee, t.periode, t.date,
       r.categorie, r.sous_categorie, r.code_ratio, r.ratio, r.unite,
       r.benchmark, f.valeur, f.note_sur_5
FROM Fait_Ratios f
JOIN Dim_Societe s ON s.id_societe = f.id_societe
JOIN Dim_Temps   t ON t.id_temps   = f.id_temps
JOIN Dim_Ratio   r ON r.id_ratio   = f.id_ratio;

DROP VIEW IF EXISTS v_sgpi;
CREATE VIEW v_sgpi AS
SELECT s.societe, s.role, t.annee, t.periode, t.date, g.sgpi_sur_100, g.couverture
FROM Fait_SGPI g
JOIN Dim_Societe s ON s.id_societe = g.id_societe
JOIN Dim_Temps   t ON t.id_temps   = g.id_temps;

DROP VIEW IF EXISTS v_etats;
CREATE VIEW v_etats AS
SELECT s.societe, t.annee, t.periode, t.date, i.statement, i.cle, i.libelle,
       i.nature, f.valeur, f.type_donnee
FROM Fait_Etats_Financiers f
JOIN Dim_Societe s     ON s.id_societe = f.id_societe
JOIN Dim_Temps   t     ON t.id_temps   = f.id_temps
JOIN Dim_Indicateur i  ON i.id_indicateur = f.id_indicateur;
