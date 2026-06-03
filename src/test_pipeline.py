"""
test_pipeline.py — Suite de tests de bout en bout du projet PFE SFBT.

Valide CHAQUE étape : sources -> unification -> augmentation -> qualité ->
ratios -> Data Warehouse -> ML. Affiche un verdict ✔/✗ par test et un bilan
final. À relancer après toute modification : `python3 test_pipeline.py`.
"""

import sqlite3
import sys
import numpy as np
import pandas as pd

import config as C

DWB = C.ROOT / "data" / "warehouse" / "sfbt_dw.sqlite"

_OK = 0
_KO = 0
_FAILS = []


def chk(label, cond, detail=""):
    global _OK, _KO
    print(("  ✔ " if cond else "  ✗ ") + label + ("" if cond else f"   →  {detail}"))
    if cond:
        _OK += 1
    else:
        _KO += 1
        _FAILS.append(label)


def section(titre):
    print("\n" + "=" * 72 + f"\n  {titre}\n" + "=" * 72)


# =====================================================================
# ÉTAPE 0 — Fichiers sources et sorties présents
# =====================================================================
def test_fichiers():
    section("ÉTAPE 0 — Présence des fichiers")
    for nom, meta in C.SOCIETES.items():
        chk(f"Source brute présente : {meta['fichier']}", (C.RAW_DIR / meta['fichier']).exists())
    for f in [C.OUT_UNIFIED, C.OUT_FULL, C.OUT_AUGMENTED,
              C.PROCESSED_DIR / "ratios.csv", C.PROCESSED_DIR / "ml_metrics.csv",
              C.PROCESSED_DIR / "ml_forecasts.csv", DWB]:
        chk(f"Sortie générée : {f.name}", f.exists())


# =====================================================================
# ÉTAPE 1 — Unification
# =====================================================================
def test_unification():
    section("ÉTAPE 1 — Unification")
    uni = pd.read_csv(C.OUT_UNIFIED, parse_dates=["Date"])
    chk("Colonnes conformes au schéma", list(uni.columns) == C.SCHEMA, str(list(uni.columns)))
    chk("Les 4 sociétés présentes",
        set(uni.Societe) == {"SFBT", "DELICE", "AB inBev", "Coca-Cola"}, str(set(uni.Societe)))
    chk("Clé primaire unique (Societe,Statement,Cle,Date,Occurrence)",
        not uni.duplicated(["Societe", "Statement", "Cle_indicateur", "Date", "Occurrence"]).any())
    chk("Aucune date manquante", uni.Date.notna().all())
    chk("Devises cohérentes (TND/USD)", set(uni.Devise) <= {"TND", "USD"})
    # SFBT couverture 41 dates
    sfbt = uni[uni.Societe == "SFBT"]
    chk("SFBT : 41 dates (2005-2025, juin+déc)", sfbt.Date.nunique() == 41, sfbt.Date.nunique())
    chk("SFBT : 5 types d'états classés",
        {"Bilan - Actif", "Bilan - Passif", "Compte de resultat", "Flux de tresorerie", "SIG"}
        <= set(sfbt.Statement.unique()))
    return uni


# =====================================================================
# ÉTAPE 1bis — Équilibre comptable du bilan SFBT
# =====================================================================
def test_equilibre(uni):
    section("ÉTAPE 1bis — Équilibre comptable (Actif = Passif)")
    s = uni[(uni.Societe == "SFBT") & (uni.Occurrence == 1)]
    a = s[(s.Statement == "Bilan - Actif") & (s.Cle_indicateur == "totaldesactifs")][["Date", "Valeur"]]
    p = s[(s.Statement == "Bilan - Passif") &
          (s.Cle_indicateur == "totaldescapitauxpropresetdespassifs")][["Date", "Valeur"]]
    m = a.merge(p, on="Date", suffixes=("_a", "_p")).dropna()
    ecart = (m.Valeur_a - m.Valeur_p).abs() / m.Valeur_a
    nb_ok = (ecart < 0.005).sum()
    chk(f"Bilan équilibré sur {nb_ok}/{len(m)} dates (les 2017-2019 = défaut source connu)",
        nb_ok >= len(m) - 4, f"{len(m)-nb_ok} dates déséquilibrées")
    # 2019 corrigé par le résolveur de fuites comparatives
    v2019 = s[(s.Cle_indicateur == "totaldesactifs") & (s.Date == "2019-12-31")].Valeur
    chk("Bug 2019 corrigé (Total actifs ≈ 795 M, pas 914 M)",
        len(v2019) and abs(v2019.iloc[0] - 795_583_804) < 1e6,
        v2019.iloc[0] if len(v2019) else "absent")


# =====================================================================
# ÉTAPE 2 — Augmentation
# =====================================================================
def test_augmentation():
    section("ÉTAPE 2 — Augmentation trimestrielle SFBT")
    full = pd.read_csv(C.OUT_FULL, parse_dates=["Date"])
    aug = full[full.Type_donnee == "Estime"]
    chk("Lignes estimées générées (>3000)", len(aug) > 3000, len(aug))
    chk("Estimés uniquement pour SFBT", set(aug.Societe) == {"SFBT"}, set(aug.Societe))
    chk("Périodes estimées = T1 et 9M seulement", set(aug.Periode) == {"T1", "9M"}, set(aug.Periode))
    chk("Réel jamais altéré (réel = lignes unifiées)",
        (full.Type_donnee == "Reel").sum() == len(pd.read_csv(C.OUT_UNIFIED)))

    # STOCK : chaque estimé entre ses 2 voisins réels
    bad = tested = 0
    for (st, cle), g in full[(full.Societe == "SFBT") &
                             (full.Statement.isin(C.STATEMENTS_STOCK))].groupby(["Statement", "Cle_indicateur"]):
        g = g.sort_values("Date").reset_index(drop=True)
        for i, row in g.iterrows():
            if row.Type_donnee != "Estime" or i == 0 or i + 1 >= len(g):
                continue
            prev, nxt = g.iloc[i - 1].Valeur, g.iloc[i + 1].Valeur
            if pd.isna(prev) or pd.isna(nxt) or pd.isna(row.Valeur):
                continue
            tested += 1
            if not (min(prev, nxt) - 1 <= row.Valeur <= max(prev, nxt) + 1):
                bad += 1
    chk(f"STOCK : interpolations dans les bornes ({tested} testées)", bad == 0, f"{bad} hors bornes")

    # FLUX : T1 = 0.5*S1 ; 9M = 0.5*(S1+FY) sur Revenus
    for yr in [2024, 2018, 2010]:
        r = full[(full.Societe == "SFBT") & (full.Cle_indicateur == "revenus") &
                 (full.Annee == yr)].set_index("Periode")["Valeur"]
        if {"T1", "S1", "9M", "FY"} <= set(r.index):
            chk(f"FLUX Revenus {yr} : T1 = ½·S1", abs(r["T1"] - 0.5 * r["S1"]) < 1)
            chk(f"FLUX Revenus {yr} : 9M = ½·(S1+FY)", abs(r["9M"] - 0.5 * (r["S1"] + r["FY"])) < 1)


# =====================================================================
# ÉTAPE 4 — Ratios MSI20000
# =====================================================================
def test_ratios():
    section("ÉTAPE 4 — Ratios MSI20000")
    r = pd.read_csv(C.PROCESSED_DIR / "ratios.csv", parse_dates=["Date"])

    def v(soc, code, date):
        x = r[(r.Societe == soc) & (r.Code_ratio == code) & (r.Date == date)]
        return x.Valeur.iloc[0] if len(x) and pd.notna(x.Valeur.iloc[0]) else np.nan

    chk("43 ratios définis", r.Code_ratio.nunique() == 43, r.Code_ratio.nunique())
    chk("Les 4 sociétés ont des ratios", r[r.Valeur.notna()].Societe.nunique() == 4)

    # Valeurs SFBT 2024 vérifiées à la main (source connue)
    chk("SFBT Liquidité générale ≈ 3,43", abs(v("SFBT", "LIQ_GEN", "2024-12-31") - 3.432) < 0.05)
    chk("SFBT Marge nette ≈ 30,1 %", abs(v("SFBT", "MARGE_NETTE", "2024-12-31") - 30.14) < 0.3)
    chk("SFBT ROE ≈ 26,4 %", abs(v("SFBT", "ROE", "2024-12-31") - 26.43) < 0.4)
    chk("SFBT Solvabilité ≈ 3,91", abs(v("SFBT", "SOLVA", "2024-12-31") - 3.91) < 0.05)
    chk("SFBT Conan&Holder > 0,16 (sain)", v("SFBT", "CONAN_HOLDER", "2024-12-31") > 0.16)
    # Benchmark vérifié vs chiffres publics
    chk("AB inBev Marge nette ≈ 12,4 %", abs(v("AB inBev", "MARGE_NETTE", "2024-12-31") - 12.41) < 0.3)
    chk("Coca-Cola Marge nette ≈ 22,6 %", abs(v("Coca-Cola", "MARGE_NETTE", "2024-12-31") - 22.63) < 0.3)
    chk("Coca-Cola ROE ≈ 40 %", abs(v("Coca-Cola", "ROE", "2024-12-31") - 40.38) < 1.0)
    # Cohérence : pas de pourcentage absurde sur ratios bornés SFBT
    pcts = r[(r.Societe == "SFBT") & (r.Unite == "%") & (r.Code_ratio.isin(
        ["MARGE_NETTE", "ROE", "ROA", "INDEP_FIN", "ENDET_GLOB"]))].Valeur.dropna()
    chk("SFBT : ratios % dans [-100, 150]", ((pcts > -100) & (pcts < 150)).all())


# =====================================================================
# ÉTAPE 5 — Data Warehouse
# =====================================================================
def test_warehouse():
    section("ÉTAPE 5 — Data Warehouse (schéma étoile)")
    con = sqlite3.connect(DWB)
    # Comptages dimensions/faits
    for t, mini in [("Dim_Societe", 4), ("Dim_Temps", 50), ("Dim_Indicateur", 100),
                    ("Dim_Ratio", 43), ("Fait_Etats_Financiers", 9000), ("Fait_Ratios", 3000)]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        chk(f"{t} peuplée (≥{mini})", n >= mini, n)
    # Intégrité référentielle (aucun fait orphelin)
    for ft, fk, dim, pk in [("Fait_Ratios", "id_societe", "Dim_Societe", "id_societe"),
                            ("Fait_Ratios", "id_temps", "Dim_Temps", "id_temps"),
                            ("Fait_Ratios", "id_ratio", "Dim_Ratio", "id_ratio"),
                            ("Fait_Etats_Financiers", "id_indicateur", "Dim_Indicateur", "id_indicateur"),
                            ("Fait_Etats_Financiers", "id_societe", "Dim_Societe", "id_societe")]:
        n = con.execute(f"SELECT COUNT(*) FROM {ft} f LEFT JOIN {dim} d "
                        f"ON f.{fk}=d.{pk} WHERE d.{pk} IS NULL").fetchone()[0]
        chk(f"{ft}.{fk} : aucun orphelin", n == 0, f"{n} orphelins")
    # Vue + requête analytique cohérente avec ratios.csv
    v = con.execute("SELECT valeur FROM v_ratios WHERE societe='SFBT' AND code_ratio='MARGE_NETTE' "
                    "AND annee=2024 AND periode='FY'").fetchone()
    chk("Vue v_ratios : marge nette SFBT 2024 = 30,14", v and abs(v[0] - 30.14) < 0.01,
        v[0] if v else "absent")
    # Le total des faits = lignes du fichier full
    n_full = len(pd.read_csv(C.OUT_FULL))
    n_fait = con.execute("SELECT COUNT(*) FROM Fait_Etats_Financiers").fetchone()[0]
    chk("Fait_Etats = lignes financials_full (aucune perte de jointure)", n_fait == n_full,
        f"{n_fait} vs {n_full}")
    con.close()


# =====================================================================
# ÉTAPE 6 — Machine Learning
# =====================================================================
def test_ml():
    section("ÉTAPE 6 — Prévision ML")
    m = pd.read_csv(C.PROCESSED_DIR / "ml_metrics.csv")
    f = pd.read_csv(C.PROCESSED_DIR / "ml_forecasts.csv", parse_dates=["Date"])
    chk("4 indicateurs × 2 modèles = 8 lignes de métriques", len(m) == 8, len(m))
    chk("Aucun R² négatif (modèles cohérents)", (m.R2 >= 0).all(),
        m[m.R2 < 0][["Indicateur", "Modele", "R2"]].to_dict("records"))
    chk("Tous les R² ≥ 0,6 (bonne qualité)", (m.R2 >= 0.6).all(), f"min={m.R2.min()}")
    chk("Toutes les MAPE < 20 %", (m["MAPE_%"] < 20).all(), f"max={m['MAPE_%'].max()}")
    chk("Découpage temporel (jeu de test ≥ 4 points)", (m.n_test >= 4).all())
    chk("Prévisions futures positives", (f.Prevision > 0).all())
    chk("Prévisions = 4 indic × 2 modèles × 4 pas = 32", len(f) == 32, len(f))
    chk("Prévision CA 2025 plausible (700-950 M)",
        700e6 < f[(f.Indicateur == "Revenus (CA)") & (f.Periode == "FY")].Prevision.iloc[0] < 950e6)


def main():
    print("\n" + "#" * 72 + "\n#  SUITE DE TESTS — PROJET PFE SFBT  #\n" + "#" * 72)
    test_fichiers()
    uni = test_unification()
    test_equilibre(uni)
    test_augmentation()
    test_ratios()
    test_warehouse()
    test_ml()

    print("\n" + "#" * 72)
    print(f"#  BILAN : {_OK} tests réussis, {_KO} échecs")
    if _KO:
        print("#  ÉCHECS :")
        for f in _FAILS:
            print(f"#    - {f}")
    else:
        print("#  ✅ TOUT EST PARFAIT — pipeline validé de bout en bout.")
    print("#" * 72)
    return 0 if _KO == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
