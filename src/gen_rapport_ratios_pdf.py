"""
gen_rapport_ratios_pdf.py — Génère un RAPPORT PDF des ratios financiers.

Document destiné à présenter, à l'encadrant, les ratios MSI20000 retenus :
formule, valeur réelle SFBT 2024, interprétation + lecture financière + benchmark.
Sortie : docs/Rapport_Ratios_SFBT.pdf
"""

import datetime as dt
import pandas as pd
import weasyprint

import config as C
from ratios import RATIOS, BENCHMARKS
from gen_catalogue_ratios import FORMULES

ANNEE = 2024
RATIOS_BENCH = ["MARGE_NETTE", "ROE", "ROA", "LIQ_GEN", "SOLVA", "ENDET_GLOB", "INDEP_FIN"]


def fmt(val, unite):
    if pd.isna(val):
        return "<span class='na'>N/A</span>"
    if unite == "%":
        return f"{val:,.2f} %"
    if unite == "x":
        return f"{val:,.2f} ×"
    if unite == "j":
        return f"{val:,.0f} j"
    if unite == "score":
        return f"{val:,.3f}"
    if unite == "montant":
        return f"{val/1e6:,.1f} M"
    return f"{val:,.2f}"


def charger():
    r = pd.read_csv(C.PROCESSED_DIR / "ratios.csv")
    sf = r[(r.Societe == "SFBT") & (r.Annee == ANNEE) & (r.Periode == "FY")] \
        .set_index("Code_ratio")["Valeur"].to_dict()
    bench = r[(r.Annee == ANNEE) & (r.Periode == "FY") & (r.Code_ratio.isin(RATIOS_BENCH))]
    sgpi = pd.read_csv(C.PROCESSED_DIR / "sgpi.csv")
    sgpi = sgpi[(sgpi.Annee == ANNEE) & (sgpi.Periode == "FY")]
    return sf, bench, sgpi


def section_sgpi(sgpi):
    cats = ["Liquidité", "Structure financière", "Gestion des actifs",
            "Gestion des risques", "Rentabilité", "Productivité RH", "Cycle d'exploitation"]
    sf = sgpi[sgpi.Societe == "SFBT"]
    if sf.empty:
        return ""
    row = sf.iloc[0]
    note_cells = "".join(
        f"<tr><td class='nom'>{c}</td><td class='val'>"
        f"{row[c]:.2f} / 5</td></tr>" for c in cats if c in row and pd.notna(row[c]))
    classement = sgpi.dropna(subset=["SGPI_sur_100"]).sort_values("SGPI_sur_100", ascending=False)
    rank = "".join(
        f"<tr><td class='nom'>{r.Societe}</td><td class='val'>{r.SGPI_sur_100:.1f} / 100</td></tr>"
        for r in classement.itertuples())
    return f"""
    <div class="sgpi-score">SGPI SFBT {ANNEE} : <b>{row['SGPI_sur_100']:.1f} / 100</b></div>
    <table class='ratios' style='width:55%;display:inline-block;vertical-align:top'>
      <thead><tr><th>Catégorie</th><th class='val'>Note</th></tr></thead>
      <tbody>{note_cells}</tbody></table>
    <table class='ratios' style='width:40%;display:inline-block;vertical-align:top;margin-left:3%'>
      <thead><tr><th>Classement SGPI</th><th class='val'>Score</th></tr></thead>
      <tbody>{rank}</tbody></table>"""


def section_ratios(sf):
    """Construit les tableaux HTML par catégorie > sous-catégorie."""
    cur_cat = cur_sous = None
    html = []
    for code, (cat, sous, libelle, unite, fn, interp) in RATIOS.items():
        if cat != cur_cat or sous != cur_sous:
            if cur_sous is not None:                 # ferme le tableau en cours
                html.append("</tbody></table>")
            if cat != cur_cat:
                html.append(f"<h2>{cat}</h2>")
                cur_cat = cat
            html.append(f"<h3>{sous}</h3>")
            html.append("<table class='ratios'><thead><tr>"
                        "<th>Ratio</th><th>Formule</th><th class='val'>SFBT "
                        f"{ANNEE}</th><th class='val'>Benchmark</th>"
                        "<th>Interprétation</th></tr></thead><tbody>")
            cur_sous = sous
        val = fmt(sf.get(code), unite)
        bm = BENCHMARKS.get(code, "—")
        html.append(f"<tr><td class='nom'>{libelle}</td>"
                    f"<td class='form'>{FORMULES.get(code,'')}</td>"
                    f"<td class='val'>{val}</td>"
                    f"<td class='val' style='color:#777;font-weight:normal'>{bm}</td>"
                    f"<td class='interp'>{interp}</td></tr>")
    html.append("</tbody></table>")
    return "\n".join(html)


def section_benchmark(bench):
    piv = bench.pivot_table(index="Code_ratio", columns="Societe", values="Valeur")
    socs = ["SFBT", "DELICE", "AB inBev", "Coca-Cola"]
    socs = [s for s in socs if s in piv.columns]
    labels = {c: RATIOS[c][2] for c in RATIOS_BENCH}
    unites = {c: RATIOS[c][3] for c in RATIOS_BENCH}
    rows = ["<table class='ratios'><thead><tr><th>Ratio</th>"
            + "".join(f"<th class='val'>{s}</th>" for s in socs) + "</tr></thead><tbody>"]
    for c in RATIOS_BENCH:
        if c not in piv.index:
            continue
        cells = "".join(f"<td class='val'>{fmt(piv.loc[c, s], unites[c])}</td>" for s in socs)
        rows.append(f"<tr><td class='nom'>{labels[c]}</td>{cells}</tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


def lecture_financiere(sf):
    """Phrases prêtes à dire en réunion, basées sur les valeurs réelles."""
    def g(c):
        return sf.get(c)
    return f"""
    <ul class='lecture'>
      <li><b>Liquidité très confortable :</b> avec un ratio de liquidité générale de
        <b>{g('LIQ_GEN'):.2f}×</b>, SFBT couvre {g('LIQ_GEN'):.1f} fois ses dettes à
        court terme — aucune tension de trésorerie.</li>
      <li><b>Endettement faible / forte autonomie :</b> les dettes ne représentent que
        <b>{g('ENDET_GLOB'):.1f} %</b> du passif et les capitaux propres en financent
        <b>{g('INDEP_FIN'):.1f} %</b> : structure financière très solide.</li>
      <li><b>Rentabilité élevée :</b> marge nette de <b>{g('MARGE_NETTE'):.1f} %</b> et
        rentabilité des capitaux propres (ROE) de <b>{g('ROE'):.1f} %</b> — performance
        nettement supérieure à la moyenne sectorielle.</li>
      <li><b>Outil de production amorti :</b> vétusté de l'actif à
        <b>{g('VETUSTE'):.0f} %</b> : une partie des immobilisations est ancienne,
        des investissements de renouvellement sont à prévoir.</li>
      <li><b>Risque de défaillance quasi nul :</b> score de Conan &amp; Holder à
        <b>{g('CONAN_HOLDER'):.2f}</b> (seuil de sécurité &gt; 0,16) : entreprise saine.</li>
    </ul>"""


def html_doc():
    sf, bench, sgpi = charger()
    date = dt.date.today().strftime("%d/%m/%Y")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 2cm 1.8cm; @bottom-center {{ content: "Page " counter(page) " / " counter(pages); font-size:8pt; color:#888; }} }}
body {{ font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 9.5pt; color:#222; line-height:1.4; }}
.cover {{ text-align:center; margin-top:7cm; }}
.cover h1 {{ font-size:26pt; color:#1b4f72; margin-bottom:0.2cm; }}
.cover h2 {{ font-size:14pt; color:#555; font-weight:normal; border:none; }}
.cover .sub {{ margin-top:3cm; font-size:10pt; color:#777; }}
.badge {{ display:inline-block; background:#1b4f72; color:#fff; padding:4px 12px; border-radius:4px; font-size:10pt; }}
h1 {{ color:#1b4f72; font-size:16pt; border-bottom:3px solid #1b4f72; padding-bottom:4px; }}
h2 {{ color:#fff; background:#1b4f72; padding:6px 10px; font-size:13pt; margin-top:18px; border-radius:3px; }}
h3 {{ color:#2874a6; font-size:11pt; margin:14px 0 4px; border-left:4px solid #2874a6; padding-left:8px; }}
table.ratios {{ width:100%; border-collapse:collapse; margin:4px 0 10px; font-size:8.5pt; }}
table.ratios th {{ background:#d6eaf8; color:#1b4f72; text-align:left; padding:5px 6px; border:1px solid #aed6f1; }}
table.ratios td {{ padding:4px 6px; border:1px solid #e5e5e5; vertical-align:top; }}
table.ratios tr:nth-child(even) td {{ background:#f7fbfe; }}
td.nom {{ font-weight:bold; width:20%; }}
td.form {{ font-family:'DejaVu Sans Mono',monospace; font-size:7.8pt; color:#444; width:28%; }}
td.val, th.val {{ text-align:center; font-weight:bold; color:#1b4f72; white-space:nowrap; }}
td.interp {{ color:#555; font-size:8.2pt; }}
.na {{ color:#c0392b; font-style:italic; }}
.box {{ background:#fef9e7; border:1px solid #f7dc6f; border-radius:5px; padding:10px 14px; margin:10px 0; }}
ul.lecture li {{ margin-bottom:6px; }}
.note {{ font-size:8pt; color:#777; }}
.intro {{ background:#eaf2f8; border-radius:5px; padding:12px 16px; }}
.sgpi-score {{ background:#1b4f72; color:#fff; font-size:15pt; text-align:center; padding:10px; border-radius:6px; margin:8px 0 14px; }}
</style></head><body>

<div class="cover">
  <div class="badge">Référentiel MSI20000®</div>
  <h1>Diagnostic Financier de SFBT</h1>
  <h2>Analyse par ratios — {len(RATIOS)} indicateurs</h2>
  <div class="sub">Société Frigorifique et Brasserie de Tunis<br>
  Exercice de référence : {ANNEE}<br>Document généré le {date}</div>
</div>

<div style="page-break-before:always"></div>
<h1>1. Présentation et méthode</h1>
<div class="intro">
<p>Ce document présente les <b>{len(RATIOS)} ratios financiers</b> calculés pour
diagnostiquer la santé de <b>SFBT</b>, structurés selon le <b>référentiel
industriel normalisé (MSI20000)</b> : gestion des liquidités, des actifs, des
passifs, des ressources humaines, des risques, rentabilité et cycle d'exploitation.</p>
<p>Les ratios sont calculés à partir des <b>états financiers réels</b> de SFBT
(bilan, compte de résultat, soldes intermédiaires de gestion). Les valeurs
affichées correspondent à l'exercice <b>{ANNEE}</b>, comparées aux <b>benchmarks
industriels</b>. Un <b>Score Global de Performance Industrielle (SGPI /100)</b>
synthétise le diagnostic (section 3), et un <b>benchmark</b> avec DELICE, AB InBev
et Coca-Cola complète l'analyse (section 5).</p>
</div>

<h1>2. Tableau des ratios (SFBT {ANNEE} vs benchmark)</h1>
{section_ratios(sf)}

<div style="page-break-before:always"></div>
<h1>3. Score Global de Performance Industrielle (SGPI)</h1>
<p>Chaque ratio clé reçoit une note 0-5 selon les grilles du référentiel ; le SGPI
est leur moyenne pondérée (Rentabilité 25 %, Structure financière 20 %, Liquidité
15 %, Gestion des actifs 15 %, Cycle d'exploitation 10 %, Risques 10 %, RH 5 %).</p>
{section_sgpi(sgpi)}

<h1>4. Lecture financière — ce que disent les chiffres</h1>
<div class="box">
{lecture_financiere(sf)}
</div>

<div style="page-break-before:always"></div>
<h1>5. Benchmark sectoriel ({ANNEE})</h1>
<p>Comparaison des ratios clés entre SFBT et trois références du secteur des
boissons.</p>
{section_benchmark(bench)}
<p class="note">⚠️ DELICE est une <b>holding</b> : ses ratios opérationnels (marge)
sont distordus car ses revenus proviennent de dividendes, pas de ventes. Les
montants étant en devises différentes (TND vs USD), seuls les <b>ratios</b> (sans
dimension) sont comparables, pas les montants absolus.</p>

<h1>6. Notes méthodologiques</h1>
<ul>
<li>Formules conformes au <b>référentiel officiel</b> (MSI20000 / Référentiel
Industriel Normalisé).</li>
<li><b>Ratios par salarié</b> (VA/salarié, RN/salarié) : non calculés —
l'effectif (nombre d'employés) n'est pas fourni dans les données.</li>
<li><b>Données SFBT 2021 et 2022 (annuel)</b> : absentes du fichier source —
ratios non calculables pour ces deux exercices (à compléter).</li>
<li>Le SGPI est renormalisé lorsque certaines catégories ne sont pas disponibles
(cas des benchmarks AB InBev / Coca-Cola, sans charges de personnel).</li>
</ul>

</body></html>"""


def main():
    out = C.DOCS_DIR / "Rapport_Ratios_SFBT.pdf"
    weasyprint.HTML(string=html_doc()).write_pdf(str(out))
    print(f"✔ PDF généré : {out}")
    print(f"  ({len(RATIOS)} ratios, valeurs SFBT {ANNEE} + benchmark + lecture financière)")


if __name__ == "__main__":
    main()
