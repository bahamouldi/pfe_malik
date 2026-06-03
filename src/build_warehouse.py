"""
build_warehouse.py — Construction du Data Warehouse en SCHÉMA EN ÉTOILE (SQLite).

Modèle dimensionnel :

                         Dim_Temps
                             |
        Dim_Societe ── Fait_Etats_Financiers ── Dim_Indicateur
                             |
        Dim_Societe ──   Fait_Ratios   ──        Dim_Ratio
                             |
                         Dim_Temps

  • 2 tables de FAITS :
      - Fait_Etats_Financiers : les valeurs comptables (réel + estimé)
      - Fait_Ratios           : les ratios MSI20000 calculés
  • 4 DIMENSIONS : Societe, Temps, Indicateur, Ratio.

Sorties :
  • data/warehouse/sfbt_dw.sqlite        (base interrogeable)
  • data/warehouse/schema_etoile.sql     (DDL du schéma)
"""

import sqlite3
import pandas as pd

import config as C

DW_DIR = C.ROOT / "data" / "warehouse"
DW_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DW_DIR / "sfbt_dw.sqlite"
DDL_PATH = DW_DIR / "schema_etoile.sql"

SECTEURS = {
    "SFBT": "Boissons (brasserie) - Tunisie",
    "DELICE": "Agroalimentaire (holding) - Tunisie",
    "AB inBev": "Boissons (brasserie) - Monde",
    "Coca-Cola": "Boissons (soft drinks) - Monde",
}

DDL = """
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
    categorie      TEXT,    -- Solidité | Performance
    sous_categorie TEXT,
    unite          TEXT     -- x | % | j | score | montant
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
    valeur     REAL
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
       r.categorie, r.sous_categorie, r.code_ratio, r.ratio, r.unite, f.valeur
FROM Fait_Ratios f
JOIN Dim_Societe s ON s.id_societe = f.id_societe
JOIN Dim_Temps   t ON t.id_temps   = f.id_temps
JOIN Dim_Ratio   r ON r.id_ratio   = f.id_ratio;

DROP VIEW IF EXISTS v_etats;
CREATE VIEW v_etats AS
SELECT s.societe, t.annee, t.periode, t.date, i.statement, i.cle, i.libelle,
       i.nature, f.valeur, f.type_donnee
FROM Fait_Etats_Financiers f
JOIN Dim_Societe s     ON s.id_societe = f.id_societe
JOIN Dim_Temps   t     ON t.id_temps   = f.id_temps
JOIN Dim_Indicateur i  ON i.id_indicateur = f.id_indicateur;
"""


def _type_cloture(periode):
    return {"T1": "Trimestrielle", "S1": "Semestrielle",
            "9M": "Trimestrielle", "FY": "Annuelle"}.get(periode, "Annuelle")


def construire():
    full = pd.read_csv(C.OUT_FULL, parse_dates=["Date"])
    ratios = pd.read_csv(C.PROCESSED_DIR / "ratios.csv", parse_dates=["Date"])

    con = sqlite3.connect(DB_PATH)
    con.executescript(DDL)

    # --- Dim_Societe ---
    dim_soc = pd.DataFrame({"societe": sorted(full.Societe.unique())})
    dim_soc["id_societe"] = range(1, len(dim_soc) + 1)
    dim_soc["role"] = dim_soc.societe.map(lambda s: C.SOCIETES.get(s, {}).get("role", ""))
    dim_soc["secteur"] = dim_soc.societe.map(SECTEURS)
    dim_soc["devise"] = dim_soc.societe.map(lambda s: C.SOCIETES.get(s, {}).get("devise", ""))
    dim_soc["echelle"] = dim_soc.societe.map(lambda s: C.SOCIETES.get(s, {}).get("echelle", ""))
    dim_soc[["id_societe", "societe", "role", "secteur", "devise", "echelle"]].to_sql(
        "Dim_Societe", con, if_exists="append", index=False)

    # --- Dim_Temps ---
    dates = pd.Index(pd.concat([full.Date, ratios.Date]).dropna().unique()).sort_values()
    dim_t = pd.DataFrame({"date": pd.to_datetime(dates).strftime("%Y-%m-%d")})
    dt = pd.to_datetime(dim_t.date)
    dim_t["id_temps"] = range(1, len(dim_t) + 1)
    dim_t["annee"] = dt.dt.year.values
    dim_t["mois"] = dt.dt.month.values
    dim_t["periode"] = dim_t["mois"].map({3: "T1", 6: "S1", 9: "9M", 12: "FY"})
    dim_t["type_cloture"] = dim_t["periode"].map(_type_cloture)
    dim_t[["id_temps", "date", "annee", "mois", "periode", "type_cloture"]].to_sql(
        "Dim_Temps", con, if_exists="append", index=False)

    # --- Dim_Indicateur ---
    di = (full.groupby(["Cle_indicateur", "Statement"])
              .agg(libelle=("Indicateur", "first")).reset_index()
              .rename(columns={"Cle_indicateur": "cle", "Statement": "statement"}))
    di["nature"] = di.statement.map(
        lambda s: "stock" if s in C.STATEMENTS_STOCK else ("flux" if s in C.STATEMENTS_FLUX else "indetermine"))
    di["id_indicateur"] = range(1, len(di) + 1)
    di[["id_indicateur", "cle", "libelle", "statement", "nature"]].to_sql(
        "Dim_Indicateur", con, if_exists="append", index=False)

    # --- Dim_Ratio ---
    dr = (ratios.groupby("Code_ratio")
                .agg(ratio=("Ratio", "first"), categorie=("Categorie", "first"),
                     sous_categorie=("Sous_categorie", "first"), unite=("Unite", "first"))
                .reset_index().rename(columns={"Code_ratio": "code_ratio"}))
    dr["id_ratio"] = range(1, len(dr) + 1)
    dr[["id_ratio", "code_ratio", "ratio", "categorie", "sous_categorie", "unite"]].to_sql(
        "Dim_Ratio", con, if_exists="append", index=False)

    # --- Fait_Etats_Financiers ---
    f = full.copy()
    f["date"] = f.Date.dt.strftime("%Y-%m-%d")
    f = f.merge(dim_soc[["societe", "id_societe"]], left_on="Societe", right_on="societe")
    f = f.merge(dim_t[["date", "id_temps"]], on="date")
    f = f.merge(di[["cle", "statement", "id_indicateur"]],
                left_on=["Cle_indicateur", "Statement"], right_on=["cle", "statement"])
    f[["id_societe", "id_temps", "id_indicateur", "Valeur", "Type_donnee", "Occurrence"]].rename(
        columns={"Valeur": "valeur", "Type_donnee": "type_donnee", "Occurrence": "occurrence"}
    ).to_sql("Fait_Etats_Financiers", con, if_exists="append", index=False)

    # --- Fait_Ratios ---
    fr = ratios.dropna(subset=["Valeur"]).copy()
    fr["date"] = fr.Date.dt.strftime("%Y-%m-%d")
    fr = fr.merge(dim_soc[["societe", "id_societe"]], left_on="Societe", right_on="societe")
    fr = fr.merge(dim_t[["date", "id_temps"]], on="date")
    fr = fr.merge(dr[["code_ratio", "id_ratio"]], left_on="Code_ratio", right_on="code_ratio")
    fr[["id_societe", "id_temps", "id_ratio", "Valeur"]].rename(
        columns={"Valeur": "valeur"}).to_sql("Fait_Ratios", con, if_exists="append", index=False)

    con.commit()
    DDL_PATH.write_text(DDL.strip() + "\n", encoding="utf-8")

    # Résumé
    cur = con.cursor()
    print("=== Data Warehouse (schéma étoile) construit ===")
    for t in ["Dim_Societe", "Dim_Temps", "Dim_Indicateur", "Dim_Ratio",
              "Fait_Etats_Financiers", "Fait_Ratios"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  • {t:24s}: {n:6d} lignes")
    con.close()
    print(f"✔ Base : {DB_PATH}")
    print(f"✔ DDL  : {DDL_PATH}")


if __name__ == "__main__":
    construire()
