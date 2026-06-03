"""
quality_report.py — Génère un rapport de qualité reproductible (Markdown).

Synthétise l'état du jeu de données unifié + augmenté : volumétrie, couverture
temporelle, complétude, collisions résiduelles, déséquilibre du bilan SFBT, etc.
Sortie : data/reports/rapport_qualite.md
"""

import pandas as pd
import config as C


def _md_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def generer():
    uni = pd.read_csv(C.OUT_UNIFIED, parse_dates=["Date"])
    full = pd.read_csv(C.OUT_FULL, parse_dates=["Date"]) if C.OUT_FULL.exists() else uni
    coll = pd.read_csv(C.REPORTS_DIR / "rapport_collisions.csv") if (C.REPORTS_DIR / "rapport_collisions.csv").exists() else pd.DataFrame()

    L = []
    L.append("# Rapport de qualité des données\n")
    L.append(f"*Généré automatiquement par `src/quality_report.py`.*\n")

    # 1. Volumétrie par société
    L.append("## 1. Volumétrie\n")
    vol = (uni.groupby("Societe")
              .agg(Lignes=("Valeur", "size"),
                   Indicateurs=("Cle_indicateur", "nunique"),
                   Dates=("Date", "nunique"),
                   Annee_min=("Annee", "min"), Annee_max=("Annee", "max"),
                   Devise=("Devise", "first"), Echelle=("Echelle", "first"))
              .reset_index())
    L.append(_md_table(vol) + "\n")

    # 2. Couverture par état (Statement)
    L.append("## 2. Couverture par état financier\n")
    cov = uni.pivot_table(index="Statement", columns="Societe", values="Valeur",
                          aggfunc="count", fill_value=0).reset_index()
    L.append(_md_table(cov) + "\n")

    # 3. Complétude (valeurs manquantes)
    L.append("## 3. Complétude\n")
    na = uni["Valeur"].isna().sum()
    L.append(f"- Valeurs manquantes (`Valeur` nulle) : **{na}** / {len(uni)} "
             f"({100*na/len(uni):.2f} %).\n")

    # 4. Collisions résiduelles (libellés ambigus)
    L.append("## 4. Collisions résiduelles (à valider métier)\n")
    if len(coll):
        par_soc = coll.groupby("Societe").size().reset_index(name="Groupes_ambigus")
        L.append(_md_table(par_soc) + "\n")
        L.append("> Une *collision* = un même (Société, État, Indicateur, Date) porte "
                 "plusieurs valeurs distinctes. Pour SFBT il s'agit surtout de "
                 "« résultat avant/après affectation » et de conventions de signe ; "
                 "pour AB inBev, du fait que le fichier source ne distingue pas les "
                 "états (même libellé dans bilan/résultat/flux). Voir "
                 "`rapport_collisions.csv`.\n")
    else:
        L.append("- Aucune.\n")

    # 5. Contrôle d'équilibre du bilan SFBT (Actif = Passif)
    L.append("## 5. Contrôle d'équilibre du bilan SFBT\n")
    s = uni[(uni.Societe == "SFBT") & (uni.Occurrence == 1)]
    actif = s[(s.Statement == "Bilan - Actif") & (s.Cle_indicateur == "totaldesactifs")]
    passif = s[(s.Statement == "Bilan - Passif") &
               (s.Cle_indicateur == "totaldescapitauxpropresetdespassifs")]
    m = actif.merge(passif, on="Date", suffixes=("_actif", "_passif"))
    m["Ecart_%"] = (100 * (m.Valeur_actif - m.Valeur_passif) / m.Valeur_actif).round(3)
    ctrl = m[["Date", "Valeur_actif", "Valeur_passif", "Ecart_%"]].sort_values("Date")
    desq = ctrl[ctrl["Ecart_%"].abs() > 0.5]
    nb_desq = len(desq)
    L.append(f"- Dates contrôlées : {len(ctrl)} ; écarts |Actif−Passif| > 0,5 % : **{nb_desq}**.\n")
    if nb_desq:
        L.append("- **Dates en déséquilibre (défaut de la source à corriger sur les "
                 "états financiers d'origine)** :\n")
        L.append(_md_table(desq) + "\n")
        L.append("> ⚠️ 2017–2019 : les colonnes Actif/Passif sont décalées d'un an dans "
                 "le fichier source (mêmes montants 795,58 M / 914,28 M permutés entre "
                 "années). À recaler manuellement à partir des rapports annuels SFBT.\n")
    else:
        L.append("- ✅ Bilan équilibré sur toutes les dates.\n")

    # 6. Augmentation
    if "Type_donnee" in full.columns:
        L.append("## 6. Augmentation trimestrielle (SFBT)\n")
        aug = full[full.Type_donnee == "Estime"]
        L.append(f"- Lignes estimées : **{len(aug)}** "
                 f"(T1={ (aug.Periode=='T1').sum() }, 9M={ (aug.Periode=='9M').sum() }).\n")
        L.append(f"- Plage : {aug.Date.min().date()} → {aug.Date.max().date()}.\n")

    out = C.REPORTS_DIR / "rapport_qualite.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"✔ Rapport qualité : {out}")
    print(f"  équilibre bilan SFBT : {nb_desq} dates déséquilibrées (>0,5%)")


if __name__ == "__main__":
    generer()
