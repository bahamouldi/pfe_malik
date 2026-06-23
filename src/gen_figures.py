"""
gen_figures.py — Génère les figures (PNG) du rapport à partir des données réelles.

Sortie : rapport/figures/*.png  (utilisées par le rapport LaTeX).
Lancer : python3 gen_figures.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import config as C

FIGDIR = C.ROOT / "rapport" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

# Charte graphique (cohérente avec le rapport)
DARK = "#1B4F72"; MID = "#2874A6"; RED = "#C51E3A"; GREEN = "#1E8449"; ORANGE = "#CA6F1E"
plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 150,
    "savefig.bbox": "tight", "axes.spines.top": False, "axes.spines.right": False,
})


def _save(fig, name):
    p = FIGDIR / name
    fig.savefig(p)
    plt.close(fig)
    print(f"  ✔ {name}")


def fig_ca_evolution(full):
    s = full[(full.Societe == "SFBT") & (full.Cle_indicateur == "revenus")
             & (full.Statement == "Compte de resultat") & (full.Periode == "FY")
             & (full.Type_donnee == "Reel")].sort_values("Annee")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(s.Annee, s.Valeur / 1e6, "-o", color=DARK, lw=2, ms=4)
    ax.set_title("Évolution du chiffre d'affaires de la SFBT (2005–2024)")
    ax.set_xlabel("Année"); ax.set_ylabel("Chiffre d'affaires (M TND)")
    ax.fill_between(s.Annee, s.Valeur / 1e6, alpha=0.08, color=DARK)
    _save(fig, "ca_evolution.png")


def fig_augmentation(full):
    s = full[(full.Societe == "SFBT") & (full.Cle_indicateur == "revenus")
             & (full.Statement == "Compte de resultat") & (full.Annee == 2024)]
    order = ["T1", "S1", "9M", "FY"]
    s = s.set_index("Periode").reindex(order)
    colors = [RED if t == "Estime" else DARK for t in s.Type_donnee]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(order, s.Valeur / 1e6, color=colors)
    ax.set_title("Augmentation : chiffre d'affaires SFBT 2024 (réel vs estimé)")
    ax.set_ylabel("M TND"); ax.set_xlabel("Période")
    for b, v in zip(bars, s.Valeur / 1e6):
        ax.text(b.get_x() + b.get_width() / 2, v + 8, f"{v:.0f}", ha="center", fontsize=10)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=DARK, label="Réel (publié)"),
                       Patch(color=RED, label="Estimé (augmentation)")], loc="upper left")
    _save(fig, "augmentation.png")


def fig_sgpi_radar(sgpi):
    row = sgpi[(sgpi.Societe == "SFBT") & (sgpi.Annee == 2024) & (sgpi.Periode == "FY")].iloc[0]
    cats = ["Liquidité", "Structure financière", "Gestion des actifs",
            "Gestion des risques", "Rentabilité", "Productivité RH", "Cycle d'exploitation"]
    vals = [float(row[c]) for c in cats]
    labels = [c.replace(" ", "\n") for c in cats]
    ang = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist()
    vals_c = vals + [vals[0]]; ang_c = ang + [ang[0]]
    fig, ax = plt.subplots(figsize=(6.5, 6), subplot_kw=dict(polar=True))
    ax.plot(ang_c, vals_c, color=DARK, lw=2)
    ax.fill(ang_c, vals_c, color=MID, alpha=0.25)
    ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 5); ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_title("Notes du SGPI par catégorie — SFBT 2024\n(score global : 83,5/100)", pad=20)
    _save(fig, "sgpi_radar.png")


def fig_benchmark(ratios):
    socs = ["SFBT", "AB inBev", "Coca-Cola"]
    codes = [("MARGE_NETTE", "Marge nette"), ("ROE", "ROE"), ("ROA", "ROA")]
    data = {}
    for soc in socs:
        data[soc] = [ratios[(ratios.Societe == soc) & (ratios.Code_ratio == c)
                            & (ratios.Annee == 2024) & (ratios.Periode == "FY")].Valeur.iloc[0]
                     for c, _ in codes]
    x = np.arange(len(codes)); w = 0.25
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for i, (soc, col) in enumerate(zip(socs, [DARK, ORANGE, RED])):
        ax.bar(x + (i - 1) * w, data[soc], w, label=soc, color=col)
    ax.set_xticks(x); ax.set_xticklabels([l for _, l in codes])
    ax.set_ylabel("%"); ax.set_title("Benchmark : rentabilité (2024)")
    ax.legend()
    _save(fig, "benchmark_bar.png")


def fig_ml_comparison(metrics):
    inds = metrics.Indicateur.unique()
    x = np.arange(len(inds)); w = 0.38
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, col, ttl, ylab in [(a1, "R2", "Coefficient de détermination ($R^2$)", "$R^2$"),
                               (a2, "MAPE_%", "Erreur moyenne (MAPE)", "MAPE (%)")]:
        lr = [metrics[(metrics.Indicateur == i) & (metrics.Modele == "Régression linéaire")][col].iloc[0] for i in inds]
        rf = [metrics[(metrics.Indicateur == i) & (metrics.Modele == "Random Forest")][col].iloc[0] for i in inds]
        ax.bar(x - w / 2, lr, w, label="Régression linéaire", color=DARK)
        ax.bar(x + w / 2, rf, w, label="Random Forest", color=ORANGE)
        ax.set_xticks(x); ax.set_xticklabels([i.replace(" ", "\n") for i in inds], fontsize=8)
        ax.set_title(ttl); ax.set_ylabel(ylab); ax.legend(fontsize=8)
    fig.suptitle("Comparaison des modèles de prévision (backtest)", fontweight="bold")
    _save(fig, "ml_comparison.png")


def fig_ml_backtest(preds):
    p = preds[(preds.Indicateur == "Revenus (CA)") & (preds.Modele == "Régression linéaire")].copy()
    p["Date"] = pd.to_datetime(p["Date"]); p = p.sort_values("Date")
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.plot(p.Date, p.Reel / 1e6, "-o", color=DARK, lw=2, ms=4, label="Réel")
    ax.plot(p.Date, p.Predit / 1e6, "--s", color=RED, lw=2, ms=4, label="Prédit (Régression linéaire)")
    ax.set_title("Prévision du chiffre d'affaires : réel vs prédit (jeu de test)")
    ax.set_xlabel("Date"); ax.set_ylabel("CA (M TND)"); ax.legend()
    fig.autofmt_xdate()
    _save(fig, "ml_backtest.png")


def fig_gantt():
    phases = [
        ("Collecte & compréhension", 0, 2),
        ("Nettoyage & unification", 2, 3),
        ("Augmentation des données", 5, 1),
        ("Ratios & score (SGPI)", 6, 2),
        ("Data Warehouse", 8, 2),
        ("Machine Learning", 10, 2),
        ("Tests & validation", 12, 1),
        ("Rédaction du rapport", 13, 3),
    ]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    colors = plt.cm.Blues(np.linspace(0.5, 0.9, len(phases)))
    for i, (name, start, dur) in enumerate(phases):
        ax.barh(i, dur, left=start, color=colors[i], edgecolor="white")
        ax.text(start + dur / 2, i, name, va="center", ha="center", fontsize=8, color="white", fontweight="bold")
    ax.set_yticks([]); ax.invert_yaxis()
    ax.set_xlabel("Semaines"); ax.set_title("Planning prévisionnel du projet (diagramme de Gantt)")
    ax.set_xlim(0, 16); ax.grid(axis="x", alpha=0.3)
    _save(fig, "gantt.png")


def main():
    print("=== Génération des figures du rapport ===")
    full = pd.read_csv(C.OUT_FULL, parse_dates=["Date"])
    ratios = pd.read_csv(C.PROCESSED_DIR / "ratios.csv")
    sgpi = pd.read_csv(C.PROCESSED_DIR / "sgpi.csv")
    metrics = pd.read_csv(C.PROCESSED_DIR / "ml_metrics.csv")
    preds = pd.read_csv(C.PROCESSED_DIR / "ml_predictions.csv")

    fig_ca_evolution(full)
    fig_augmentation(full)
    fig_sgpi_radar(sgpi)
    fig_benchmark(ratios)
    fig_ml_comparison(metrics)
    fig_ml_backtest(preds)
    fig_gantt()
    print(f"\n✔ Figures écrites dans {FIGDIR}")


if __name__ == "__main__":
    main()
