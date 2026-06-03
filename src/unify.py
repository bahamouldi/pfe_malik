"""
unify.py — Unification des 4 sources financières en un seul jeu de données long.

Sortie : data/processed/financials_unified.{csv,parquet} au schéma config.SCHEMA.

Particularités gérées :
  * SFBT (beta1) : feuille maîtresse Feuil1 = tous les états empilés sans
    colonne « Statement ». Reclassés par DÉCOUPAGE POSITIONNEL en sections
    (Actif -> Passif -> Compte de résultat -> Flux). Les SIG proviennent de la
    feuille dédiée Feuil5 (extrait propre) pour éviter les doublons.
  * DELICE / AB inBev : format long déjà proche du schéma (Statement parfois
    vide -> 'Inconnu').
  * Coca-Cola : format anglais, colonnes différentes, société non renseignée.

Le pipeline produit aussi un rapport des variantes de libellés
(data/reports/rapport_variantes_indicateurs.csv) pour la validation métier.
"""

import sys
import pandas as pd

import config as C
from normalize import clean_label, cle_canonique, cle_indicateur


# =============================================================================
#  Helpers
# =============================================================================
def _periode_from_month(month: int) -> str:
    """Mappe un mois de clôture vers une étiquette de période comparable."""
    return {3: "T1", 6: "S1", 9: "9M", 12: "FY"}.get(month, "FY")


def _read_sheet(fichier: str, feuille: str) -> list:
    """Lit une feuille Excel et renvoie la liste des lignes (valeurs)."""
    import openpyxl
    wb = openpyxl.load_workbook(C.RAW_DIR / fichier, data_only=True, read_only=True)
    ws = wb[feuille]
    rows = [tuple(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


# =============================================================================
#  Classification positionnelle des sections (SFBT / Feuil1)
# =============================================================================
# Ancres de DÉBUT de section (clés normalisées). On repère la 1re occurrence de
# chaque ancre dans le bloc d'une date pour délimiter les sections.
_ANCRES = {
    "Bilan - Passif":      lambda k: k == "capitalsocial",
    "Compte de resultat":  lambda k: k in ("revenus", "totaldesproduitsdexploitation"),
    "Flux de tresorerie":  lambda k: k.startswith("ajustements"),
    "SIG":                 lambda k: k in ("ventesdemarchandisesetautres",
                                           "margecommerciale",
                                           "valeurajouteebrute"),
}


def _classer_bloc(cles: list) -> list:
    """Pour un bloc (liste de clés normalisées d'une même date), renvoie la
    liste des Statements correspondants. La section SIG est marquée pour être
    DROPPÉE (None) : les SIG viennent de Feuil5."""
    n = len(cles)
    # Indice de départ de chaque section (None si absente).
    debut = {"Bilan - Actif": 0}
    for sec, test in _ANCRES.items():
        for i, k in enumerate(cles):
            if test(k):
                debut[sec] = i
                break
    # Ordonne les sections présentes par indice de départ.
    presentes = sorted(((idx, sec) for sec, idx in debut.items()), key=lambda x: x[0])
    # Construit les frontières [start, end) et étiquette chaque ligne.
    statements = [None] * n
    for j, (start, sec) in enumerate(presentes):
        end = presentes[j + 1][0] if j + 1 < len(presentes) else n
        for i in range(start, end):
            # SIG dans Feuil1 -> None (on prendra Feuil5).
            statements[i] = None if sec == "SIG" else sec
    return statements


# =============================================================================
#  Loaders par société
# =============================================================================
def load_sfbt(nom: str, meta: dict) -> pd.DataFrame:
    """SFBT : Feuil1 (Actif/Passif/Résultat/Flux, classés) + Feuil5 (SIG)."""
    records = []

    # --- Feuil1 : états empilés, classés par découpage positionnel ----------
    rows = _read_sheet(meta["fichier"], meta["feuille_maitresse"])[1:]  # skip header
    # Regroupe par date en CONSERVANT l'ordre des lignes (essentiel).
    bloc, cur_date = [], None

    def flush(date_str, lignes):
        if not lignes:
            return
        cles = [cle_indicateur(lbl) for (lbl, _) in lignes]
        stmts = _classer_bloc(cles)
        dt = pd.to_datetime(date_str, format="%d/%m/%Y")
        for (lbl, val), st in zip(lignes, stmts):
            if st is None:        # ligne SIG de Feuil1 -> ignorée
                continue
            records.append(_record(nom, meta, st, lbl, dt, val))

    for (lbl, soc, date_str, val) in [(r[0], r[1], r[2], r[3]) for r in rows]:
        if lbl is None or date_str is None:
            continue
        if date_str != cur_date and bloc:
            flush(cur_date, bloc)
            bloc = []
        cur_date = date_str
        bloc.append((lbl, val))
    flush(cur_date, bloc)

    # --- Feuil5 : SIG (extrait dédié, propre) -------------------------------
    sig = _read_sheet(meta["fichier"], meta["feuille_sig"])[1:]
    for (lbl, soc, date_str, val) in [(r[0], r[1], r[2], r[3]) for r in sig]:
        if lbl is None or date_str is None:
            continue
        dt = pd.to_datetime(date_str, format="%d/%m/%Y")
        records.append(_record(nom, meta, "SIG", lbl, dt, val))

    return pd.DataFrame.from_records(records)


def load_clean_long(nom: str, meta: dict) -> pd.DataFrame:
    """DELICE / AB inBev : déjà en format long proche du schéma."""
    rows = _read_sheet(meta["fichier"], meta["feuille"])
    hdr = [str(h).strip() if h is not None else "" for h in rows[0]]
    idx = {h.lower(): i for i, h in enumerate(hdr)}

    def col(*names):
        for nm in names:
            if nm in idx:
                return idx[nm]
        return None

    i_stmt = col("statement")
    i_ind = col("indicateur")
    i_date = col("date")
    i_year = col("year", "année", "annee")
    i_val = col("valeur")

    records = []
    for r in rows[1:]:
        lbl = r[i_ind] if i_ind is not None else None
        if lbl is None:
            continue
        val = r[i_val] if i_val is not None else None
        # Date : datetime, ou simple année entière.
        raw_date = r[i_date] if i_date is not None else None
        year = r[i_year] if i_year is not None else None
        dt = _to_date(raw_date, year)
        stmt = r[i_stmt] if i_stmt is not None else None
        stmt = clean_label(stmt) if stmt else "Inconnu"
        records.append(_record(nom, meta, stmt, lbl, dt, val))
    return pd.DataFrame.from_records(records)


def load_cocacola(nom: str, meta: dict) -> pd.DataFrame:
    """Coca-Cola : colonnes INDICATEUR / Société(vide) / Année / Valeur."""
    rows = _read_sheet(meta["fichier"], meta["feuille"])
    hdr = [str(h).strip().lower() if h is not None else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(hdr)}
    i_ind = idx.get("indicateur")
    i_year = idx.get("année", idx.get("annee"))
    i_val = idx.get("valeur")

    records = []
    for r in rows[1:]:
        lbl = r[i_ind]
        if lbl is None:
            continue
        year = r[i_year]
        dt = _to_date(None, year)
        records.append(_record(nom, meta, "Inconnu", lbl, dt, r[i_val]))
    return pd.DataFrame.from_records(records)


# =============================================================================
#  Construction d'un enregistrement au schéma
# =============================================================================
def _to_date(raw_date, year):
    """Renvoie un Timestamp de fin de période à partir d'une date ou d'une année."""
    if raw_date is not None and not isinstance(raw_date, (int, float)):
        return pd.to_datetime(raw_date)
    # Sinon : année -> clôture au 31/12.
    yr = raw_date if isinstance(raw_date, (int, float)) else year
    if yr is None:
        return pd.NaT
    return pd.Timestamp(int(yr), 12, 31)


def _record(nom, meta, statement, lbl_raw, dt, val):
    """Crée un dict conforme à C.SCHEMA."""
    try:
        valeur = float(val) if val is not None and val != "" else None
    except (ValueError, TypeError):
        valeur = None
    annee = int(dt.year) if pd.notna(dt) else None
    periode = _periode_from_month(dt.month) if pd.notna(dt) else None
    statement = C.STATEMENT_CANON.get(cle_indicateur(statement), statement)
    return {
        "Societe": nom,
        "Statement": statement,
        "Indicateur": clean_label(lbl_raw),
        "Indicateur_raw": str(lbl_raw),
        "Cle_indicateur": cle_canonique(lbl_raw),
        "Date": dt,
        "Annee": annee,
        "Periode": periode,
        "Valeur": valeur,
        "Devise": meta["devise"],
        "Echelle": meta["echelle"],
        "Type_donnee": "Reel",
        "Source": meta["fichier"],
    }


# =============================================================================
#  Pipeline principal
# =============================================================================
LOADERS = {
    "load_sfbt": load_sfbt,
    "load_clean_long": load_clean_long,
    "load_cocacola": load_cocacola,
}


def unifier() -> pd.DataFrame:
    frames = []
    for nom, meta in C.SOCIETES.items():
        loader = LOADERS[meta["loader"]]
        df = loader(nom, meta)
        print(f"  • {nom:12s}: {len(df):5d} lignes  ({meta['frequence']}, {meta['devise']})")
        frames.append(df)
    full = pd.concat(frames, ignore_index=True)
    full = full.sort_values(["Societe", "Date", "Statement", "Indicateur"]).reset_index(drop=True)

    cle = ["Societe", "Statement", "Cle_indicateur", "Date"]

    # 1) On supprime UNIQUEMENT les doublons strictement identiques (même valeur).
    #    -> élimine les répétitions de bloc SFBT sans jamais perdre d'information.
    avant = len(full)
    full = full.drop_duplicates(subset=cle + ["Valeur"], keep="first").reset_index(drop=True)

    # 2) Résolution des « fuites de colonne comparative » : certains états
    #    présentent 2 colonnes (N et N-1). Quand un (cle, date) porte plusieurs
    #    valeurs et que l'une d'elles est ÉGALE à la valeur de l'année
    #    précédente (même période), c'est la colonne comparative recopiée par
    #    erreur -> on la supprime au profit de la vraie valeur de l'exercice.
    full, n_leak = _resoudre_fuites_comparatives(full, cle)

    # 3) Collisions résiduelles (même clé, valeurs DIFFÉRENTES) : CONSERVÉES avec
    #    un indice d'occurrence (surtout AB inBev, états non labellisés ; ou
    #    « avant/après affectation »). Flaggées dans le rapport de collisions.
    full = full.sort_values(["Societe", "Date", "Statement", "Indicateur"]).reset_index(drop=True)
    full["Occurrence"] = full.groupby(cle).cumcount() + 1
    full = full[C.SCHEMA]
    n_coll = (full["Occurrence"] > 1).sum()
    print(f"  → doublons exacts retirés : {avant} → {len(full)} lignes "
          f"| fuites comparatives corrigées : {n_leak} "
          f"| collisions résiduelles conservées : {n_coll}")
    return full


def _resoudre_fuites_comparatives(full: pd.DataFrame, cle: list):
    """Supprime, parmi les collisions, les valeurs identiques à celles de
    l'année N-1 (même Société/Statement/Indicateur/Période) — recopies de
    colonne comparative. Renvoie (df nettoyé, nb lignes supprimées)."""
    # Valeur représentative par (Societe, Statement, Cle, Periode, Annee) :
    # médiane (robuste si la cellule N-1 colle elle aussi). Sert de référence N-1.
    ref = (full.groupby(["Societe", "Statement", "Cle_indicateur", "Periode", "Annee"])
                ["Valeur"].median().to_dict())

    def val_n_moins_1(row):
        return ref.get((row.Societe, row.Statement, row.Cle_indicateur,
                        row.Periode, (row.Annee - 1) if pd.notna(row.Annee) else None))

    grp = full.groupby(cle)
    a_supprimer = []
    for _, idx in grp.groups.items():
        if len(idx) < 2:
            continue
        sub = full.loc[idx]
        prev = val_n_moins_1(sub.iloc[0])
        if prev is None:
            continue
        est_fuite = sub["Valeur"].apply(lambda v: v is not None and abs(v - prev) < 1e-6)
        # On ne supprime que s'il reste au moins une valeur « vraie » (non-fuite).
        if est_fuite.any() and (~est_fuite).any():
            a_supprimer.extend(sub.index[est_fuite].tolist())
    full2 = full.drop(index=a_supprimer).reset_index(drop=True)
    return full2, len(a_supprimer)


def rapport_variantes(df: pd.DataFrame) -> pd.DataFrame:
    """Liste, par clé canonique, toutes les variantes de libellés rencontrées —
    pour repérer les regroupements à valider/affiner manuellement."""
    g = (df.groupby(["Societe", "Cle_indicateur"])["Indicateur"]
           .agg(lambda s: " | ".join(sorted(set(s))))
           .reset_index()
           .rename(columns={"Indicateur": "Variantes"}))
    g["Nb_variantes"] = g["Variantes"].str.count(r"\|").add(1)
    g = g.sort_values(["Nb_variantes", "Societe"], ascending=[False, True])
    return g


def rapport_collisions(df: pd.DataFrame) -> pd.DataFrame:
    """Recense les (Societe, Statement, Cle, Date) ayant >1 valeur distincte —
    libellés ambigus à désambiguïser (surtout AB inBev, états non labellisés)."""
    cle = ["Societe", "Statement", "Cle_indicateur", "Date"]
    g = df.groupby(cle).agg(
        Nb_occurrences=("Valeur", "size"),
        Valeurs=("Valeur", lambda s: " | ".join(f"{v:g}" for v in s)),
        Indicateur=("Indicateur", "first"),
    ).reset_index()
    g = g[g["Nb_occurrences"] > 1].sort_values(["Societe", "Nb_occurrences"], ascending=[True, False])
    return g


def main():
    print("=== Unification des sources financières ===")
    df = unifier()
    df.to_csv(C.OUT_UNIFIED, index=False)
    try:
        df.to_parquet(C.OUT_UNIFIED_PARQUET, index=False)
    except Exception as e:
        print("  (parquet ignoré:", e, ")")

    var = rapport_variantes(df)
    var.to_csv(C.REPORT_VARIANTS, index=False)
    coll = rapport_collisions(df)
    coll.to_csv(C.REPORTS_DIR / "rapport_collisions.csv", index=False)

    print(f"\n✔ Écrit : {C.OUT_UNIFIED}  ({len(df)} lignes)")
    print(f"✔ Rapport variantes  : {C.REPORT_VARIANTS} "
          f"({(var['Nb_variantes'] > 1).sum()} clés à variantes multiples)")
    print(f"✔ Rapport collisions : {C.REPORTS_DIR / 'rapport_collisions.csv'} "
          f"({len(coll)} groupes ambigus, dont SFBT={ (coll.Societe=='SFBT').sum() })")
    return df


if __name__ == "__main__":
    sys.exit(0 if main() is not None else 1)
