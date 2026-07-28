"""
ml_forecast.py — Prévision des valeurs financières de SFBT.

Trois modèles comparés (choix de Malik) :
  • Régression linéaire  — baseline simple, interprétable.
  • Random Forest        — modèle ML robuste, non-linéaire.
  • Arbre de decision    — modèle interprétable (élagué : prof.=3, feuille>=5)
                           pour visualiser les règles de décision apprises.

Démarche (forecasting supervisé sur série temporelle) :
  1. On reconstruit la série trimestrielle de chaque indicateur cible
     (réel + trimestres estimés -> ~80 points, 2005→2025).
  2. Mise au format supervisé avec variables explicatives :
        - tendance temporelle (index)
        - retards (lags t-1 … t-4)
        - saisonnalité (période T1/S1/9M/FY en one-hot)
  3. Découpage TEMPOREL (pas de mélange) : ~75 % entraînement / 25 % test
     -> backtest honnête (on prédit des points jamais vus, postérieurs).
  4. Métriques : MAE, RMSE, MAPE (%), R².
  5. Prévision future récursive (4 prochaines clôtures).

Sorties :
  • data/processed/ml_metrics.csv     (comparaison des 3 modèles par indicateur)
  • data/processed/ml_predictions.csv (test : réel vs prédit, par modèle)
  • data/processed/ml_forecasts.csv   (prévisions futures)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import config as C

# Indicateurs cibles (clé canonique, état, libellé).
TARGETS = [
    ("revenus", "Compte de resultat", "Revenus (CA)"),
    ("totaldesactifs", "Bilan - Actif", "Total des actifs"),
    ("totaldescapitauxpropresavantaffectation", "Bilan - Passif", "Capitaux propres"),
    ("resultatnetdelexercice", "Compte de resultat", "Résultat net"),
]
LAGS = [1, 2, 3, 4]
PERIODES = ["T1", "S1", "9M", "FY"]
TEST_FRAC = 0.25


def _mape(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    m = y != 0
    return 100 * np.mean(np.abs((y[m] - yhat[m]) / y[m]))


def serie_cible(full, cle, statement):
    """Renvoie la série trimestrielle ordonnée d'un indicateur."""
    g = full[(full.Societe == "SFBT") & (full.Occurrence == 1)
             & (full.Cle_indicateur == cle) & (full.Statement == statement)]
    g = g[["Date", "Periode", "Valeur"]].dropna().sort_values("Date").reset_index(drop=True)
    return g


def construire_supervise(serie):
    """Format supervisé. La cible est le TAUX DE CROISSANCE r_t = V_t / V_{t-1}
    (et non le niveau brut). C'est essentiel : sur une série qui croît, un Random
    Forest ne sait PAS extrapoler le niveau (les arbres plafonnent au max vu en
    entraînement). En modélisant un taux ~stationnaire, les deux modèles
    deviennent comparables et performants. Le niveau est ensuite reconstruit :
    V̂_t = V_{t-1} × r̂_t. Les variables de période capturent la saisonnalité
    (ex. revenus cumulés : forte hausse intra-année, chute au T1 suivant)."""
    df = serie.copy()
    df["t"] = np.arange(len(df))
    df["prev_level"] = df["Valeur"].shift(1)
    df["ratio"] = df["Valeur"] / df["prev_level"]
    for L in LAGS:
        df[f"rlag{L}"] = df["ratio"].shift(L)
    for p in PERIODES:
        df[f"per_{p}"] = (df["Periode"] == p).astype(int)
    df = df.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    feats = ["t"] + [f"rlag{L}" for L in LAGS] + [f"per_{p}" for p in PERIODES]
    return df, feats


def evaluer(full):
    metrics, preds = [], []
    modeles = {
        "Régression linéaire": lambda: LinearRegression(),
        "Random Forest": lambda: RandomForestRegressor(
            n_estimators=400, max_depth=None, min_samples_leaf=2, random_state=42),
        "Arbre de decision": lambda: DecisionTreeRegressor(
            max_depth=3, min_samples_leaf=5, random_state=42),
    }
    for cle, st, libelle in TARGETS:
        serie = serie_cible(full, cle, st)
        df, feats = construire_supervise(serie)
        n = len(df)
        n_test = max(4, int(round(n * TEST_FRAC)))
        train, test = df.iloc[:-n_test], df.iloc[-n_test:]
        X_tr, r_tr = train[feats], train["ratio"]
        X_te = test[feats]
        # Niveaux réels & niveau précédent (pour reconstruire le niveau prédit).
        y_te = test["Valeur"].values
        prev_te = test["prev_level"].values

        for nom, ctor in modeles.items():
            mdl = ctor().fit(X_tr, r_tr)
            r_hat = mdl.predict(X_te)
            yhat = prev_te * r_hat                      # reconstruction du niveau
            metrics.append({
                "Indicateur": libelle, "Modele": nom,
                "n_train": len(train), "n_test": len(test),
                "MAE": round(mean_absolute_error(y_te, yhat), 1),
                "RMSE": round(np.sqrt(mean_squared_error(y_te, yhat)), 1),
                "MAPE_%": round(_mape(y_te, yhat), 2),
                "R2": round(r2_score(y_te, yhat), 4),
            })
            for d, yr, yp in zip(test["Date"], y_te, yhat):
                preds.append({"Indicateur": libelle, "Modele": nom, "Date": d,
                              "Reel": round(float(yr), 1), "Predit": round(float(yp), 1)})
    return pd.DataFrame(metrics), pd.DataFrame(preds)


def prevoir_futur(full, n_steps=4):
    """Prévision récursive des n prochaines clôtures, avec le modèle le meilleur
    (réentraîné sur TOUTE la série) pour chaque indicateur."""
    cycle = PERIODES  # T1 -> S1 -> 9M -> FY -> T1 ...
    mois_de = {"T1": 3, "S1": 6, "9M": 9, "FY": 12}
    jour_de = {3: 31, 6: 30, 9: 30, 12: 31}
    out = []
    for cle, st, libelle in TARGETS:
        serie = serie_cible(full, cle, st)
        df, feats = construire_supervise(serie)
        X, r = df[feats], df["ratio"]
        models = {
            "Régression linéaire": LinearRegression().fit(X, r),
            "Random Forest": RandomForestRegressor(
                n_estimators=400, min_samples_leaf=2, random_state=42).fit(X, r),
            "Arbre de decision": DecisionTreeRegressor(
                max_depth=3, min_samples_leaf=5, random_state=42).fit(X, r),
        }
        for nom, mdl in models.items():
            levels = serie["Valeur"].tolist()         # historique des niveaux
            ratios = df["ratio"].tolist()             # historique des taux
            cur = serie["Date"].iloc[-1]
            pi = cycle.index(serie["Periode"].iloc[-1])
            t_next = len(serie)
            for _ in range(n_steps):
                pi = (pi + 1) % 4
                per = cycle[pi]
                mois = mois_de[per]
                annee = cur.year + 1 if per == "T1" else (cur.year if mois > cur.month else cur.year + 1)
                nd = pd.Timestamp(annee, mois, jour_de[mois])
                row = {"t": t_next}
                for L in LAGS:
                    row[f"rlag{L}"] = ratios[-L]
                for p in PERIODES:
                    row[f"per_{p}"] = 1 if p == per else 0
                r_hat = float(mdl.predict(pd.DataFrame([row])[feats])[0])
                niveau = levels[-1] * r_hat            # reconstruction du niveau
                out.append({"Indicateur": libelle, "Modele": nom, "Date": nd,
                            "Periode": per, "Prevision": round(niveau, 1)})
                levels.append(niveau)
                ratios.append(r_hat)
                cur = nd
                t_next += 1
    return pd.DataFrame(out)


def evaluer_horizon(full, hmax=4):
    """Backtest par HORIZON (origine glissante, mode recursif).

    Nuance methodologique importante : evaluer() fournit au modele le niveau
    REEL precedent a chaque point de test (prev_level). Il mesure donc une
    prevision a 1 pas d'avance. Or prevoir_futur() travaille en mode RECURSIF :
    le modele se nourrit de ses propres sorties. Les metriques de evaluer() ne
    correspondent donc pas au regime dans lequel les previsions publiees sont
    produites.

    Cette fonction mesure la performance a l'horizon reellement utilise (1 a 4
    pas). Pour chaque origine du jeu de test, on reancre sur les donnees reelles
    puis on projette hmax pas en mode recursif. Une baseline naive V(t-4) donne
    la reference minimale a battre.
    """
    modeles = {
        "Régression linéaire": lambda: LinearRegression(),
        "Random Forest": lambda: RandomForestRegressor(
            n_estimators=400, max_depth=None, min_samples_leaf=2, random_state=42),
        "Arbre de decision": lambda: DecisionTreeRegressor(
            max_depth=3, min_samples_leaf=5, random_state=42),
    }
    lignes = []
    for cle, st, libelle in TARGETS:
        serie = serie_cible(full, cle, st)
        df, feats = construire_supervise(serie)
        n = len(df)
        n_test = max(4, int(round(n * TEST_FRAC)))
        train = df.iloc[:-n_test]
        base = len(train)
        ratios_reels = df["ratio"].tolist()
        niveaux = df["Valeur"].tolist()
        prev_niv = df["prev_level"].tolist()
        n_org = n_test - hmax + 1
        if n_org < 1:
            continue

        def _ajouter(nom, paires):
            for h in range(1, hmax + 1):
                if not paires[h]:
                    continue
                y = np.array([a for a, _ in paires[h]], dtype=float)
                yh = np.array([b for _, b in paires[h]], dtype=float)
                lignes.append({
                    "Indicateur": libelle, "Modele": nom, "Horizon": h,
                    "n_origines": len(y),
                    "MAE": round(mean_absolute_error(y, yh), 1),
                    "MAPE_%": round(_mape(y, yh), 2),
                    "R2": round(r2_score(y, yh), 4)})

        for nom, ctor in modeles.items():
            mdl = ctor().fit(train[feats], train["ratio"])
            paires = {h: [] for h in range(1, hmax + 1)}
            for i in range(n_org):
                hist = list(ratios_reels[:base + i])
                niveau = prev_niv[base + i]
                for h in range(1, hmax + 1):
                    k = base + i + h - 1
                    row = {"t": df["t"].iloc[k]}
                    for L in LAGS:
                        row[f"rlag{L}"] = hist[-L]
                    for pp in PERIODES:
                        row[f"per_{pp}"] = df[f"per_{pp}"].iloc[k]
                    r_hat = float(mdl.predict(pd.DataFrame([row])[feats])[0])
                    niveau = niveau * r_hat
                    hist.append(r_hat)
                    paires[h].append((niveaux[k], niveau))
            _ajouter(nom, paires)

        paires = {h: [] for h in range(1, hmax + 1)}
        for i in range(n_org):
            for h in range(1, hmax + 1):
                k = base + i + h - 1
                if k - 4 >= 0:
                    paires[h].append((niveaux[k], niveaux[k - 4]))
        _ajouter("Naif saisonnier V(t-4)", paires)
    return pd.DataFrame(lignes)


def main():
    print("=== Prévision ML : LinReg vs Random Forest vs Arbre de decision (SFBT) ===")
    full = pd.read_csv(C.OUT_FULL, parse_dates=["Date"])
    metrics, preds = evaluer(full)
    forecasts = prevoir_futur(full)
    horizon = evaluer_horizon(full)

    metrics.to_csv(C.PROCESSED_DIR / "ml_metrics.csv", index=False)
    preds.to_csv(C.PROCESSED_DIR / "ml_predictions.csv", index=False)
    forecasts.to_csv(C.PROCESSED_DIR / "ml_forecasts.csv", index=False)
    horizon.to_csv(C.PROCESSED_DIR / "ml_metrics_horizon.csv", index=False)

    print("\n--- Comparaison des modèles (backtest temporel) ---")
    print(metrics.to_string(index=False))
    # Verdict par indicateur (meilleur R²).
    print("\n--- Meilleur modèle par indicateur (R²) ---")
    for ind in metrics.Indicateur.unique():
        sub = metrics[metrics.Indicateur == ind].sort_values("R2", ascending=False)
        best = sub.iloc[0]
        print(f"  {ind:20s} -> {best.Modele:20s} (R²={best.R2}, MAPE={best['MAPE_%']}%)")
    print("\n--- Backtest par horizon (origine glissante, mode récursif) ---")
    piv = horizon.pivot_table(index=["Indicateur", "Modele"],
                              columns="Horizon", values="MAPE_%")
    piv.columns = [f"MAPE h={c}" for c in piv.columns]
    print(piv.round(2).to_string())
    print("\n--- MAPE moyenne par modèle et horizon (4 indicateurs) ---")
    print(horizon.pivot_table(index="Modele", columns="Horizon",
                              values="MAPE_%").round(2).to_string())
    print(f"\n✔ Écrit : ml_metrics.csv, ml_predictions.csv, ml_forecasts.csv,"
          f" ml_metrics_horizon.csv")
    return metrics


if __name__ == "__main__":
    main()
