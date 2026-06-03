"""
augment.py — Augmentation trimestrielle des données SFBT (Mars + Septembre).

CONTEXTE (demande de Malik) : SFBT ne publie que le 30/06 (semestriel) et le
31/12 (annuel). On génère les clôtures manquantes 31/03 (T1) et 30/09 (9 mois)
par estimation, pour densifier la série (utile pour le ML / les dashboards
trimestriels) au cas où aucune donnée réelle supplémentaire n'arriverait.

MÉTHODE — distincte selon la nature de l'indicateur :

  • GRANDEURS DE STOCK (Bilan : actif, passif) = photo à la date de clôture.
    -> Interpolation linéaire dans le temps entre deux photos connues :
         31/03/N  entre  31/12/(N-1)  et  30/06/N
         30/09/N  entre  30/06/N       et  31/12/N

  • GRANDEURS DE FLUX (Compte de résultat, Flux de trésorerie, SIG) = cumul
    depuis le début de l'exercice (remis à zéro au 1er janvier).
         31/03/N (cumul 3 mois) ≈ 0,5 × Valeur(30/06/N)            [accrual linéaire H1]
         30/09/N (cumul 9 mois) ≈ Valeur(30/06/N) + 0,5 × (Valeur(31/12/N) − Valeur(30/06/N))

    Exception : les SOLDES de trésorerie (« Trésorerie à la clôture / au début »)
    sont des stocks malgré leur présence dans l'état de flux -> interpolés.

HYPOTHÈSE clé : accumulation linéaire des flux à l'intérieur de chaque semestre.
C'est une approximation (la saisonnalité réelle n'est pas captée) ; les lignes
produites sont explicitement marquées Type_donnee = 'Estime'.
"""

import pandas as pd

import config as C
from normalize import cle_indicateur

# Soldes de trésorerie présents dans l'état de flux mais de nature « stock ».
_FLUX_STOCK_KEYS = {
    cle_indicateur("Trésorerie à la clôture de l'exercice"),
    cle_indicateur("Trésorerie au début de l'exercice"),
}


def _interp(d0, v0, d1, v1, d):
    """Interpolation linéaire de la valeur à la date d entre (d0,v0) et (d1,v1)."""
    if v0 is None or v1 is None:
        return None
    frac = (d - d0).days / (d1 - d0).days
    return v0 + (v1 - v0) * frac


def _ligne(modele: dict, date, periode, valeur):
    """Construit une ligne estimée à partir d'une ligne modèle (même indicateur)."""
    r = dict(modele)
    r["Date"] = date
    r["Annee"] = int(date.year)
    r["Periode"] = periode
    r["Valeur"] = None if valeur is None else round(float(valeur), 3)
    r["Type_donnee"] = "Estime"
    r["Source"] = "augmentation (estimation trimestrielle)"
    r["Occurrence"] = 1
    return r


def augmenter_sfbt(df: pd.DataFrame) -> pd.DataFrame:
    """Renvoie UNIQUEMENT les lignes estimées (T1 / 9M) pour SFBT."""
    s = df[(df.Societe == "SFBT") & (df.Occurrence == 1)].copy()
    s["Date"] = pd.to_datetime(s["Date"])

    nouvelles = []
    # Une série = (Statement, Cle_indicateur). On itère indicateur par indicateur.
    for (stmt, cle), g in s.groupby(["Statement", "Cle_indicateur"]):
        g = g.sort_values("Date")
        # Valeur connue par date, et ligne-modèle (métadonnées/libellé).
        val = {d: v for d, v in zip(g["Date"], g["Valeur"])}
        modele = g.iloc[-1].to_dict()           # libellé canonique le plus récent
        est_stock = (stmt in C.STATEMENTS_STOCK) or (cle in _FLUX_STOCK_KEYS)

        annees = sorted({d.year for d in g["Date"]})
        for N in annees:
            dec_prev = pd.Timestamp(N - 1, 12, 31)
            jun = pd.Timestamp(N, 6, 30)
            dec = pd.Timestamp(N, 12, 31)
            mar = pd.Timestamp(N, 3, 31)
            sep = pd.Timestamp(N, 9, 30)

            if est_stock:
                # --- T1 (Mars) : interp entre Déc(N-1) et Juin(N)
                if dec_prev in val and jun in val:
                    nouvelles.append(_ligne(modele, mar, "T1",
                                            _interp(dec_prev, val[dec_prev], jun, val[jun], mar)))
                # --- 9M (Sept) : interp entre Juin(N) et Déc(N)
                if jun in val and dec in val:
                    nouvelles.append(_ligne(modele, sep, "9M",
                                            _interp(jun, val[jun], dec, val[dec], sep)))
            else:
                # FLUX cumulés.
                if jun in val and val[jun] is not None:
                    nouvelles.append(_ligne(modele, mar, "T1", 0.5 * val[jun]))
                if jun in val and dec in val and val[jun] is not None and val[dec] is not None:
                    nouvelles.append(_ligne(modele, sep, "9M",
                                            val[jun] + 0.5 * (val[dec] - val[jun])))

    out = pd.DataFrame.from_records(nouvelles)
    if not out.empty:
        out = out[C.SCHEMA].sort_values(["Statement", "Indicateur", "Date"]).reset_index(drop=True)
    return out


def main():
    print("=== Augmentation trimestrielle SFBT (Mars / Septembre) ===")
    df = pd.read_csv(C.OUT_UNIFIED, parse_dates=["Date"])
    aug = augmenter_sfbt(df)
    aug.to_csv(C.OUT_AUGMENTED, index=False)

    # Jeu complet = réel + estimé.
    full = pd.concat([df, aug], ignore_index=True)
    full = full.sort_values(["Societe", "Date", "Statement", "Indicateur"]).reset_index(drop=True)
    full.to_csv(C.OUT_FULL, index=False)
    try:
        full.to_parquet(C.OUT_FULL_PARQUET, index=False)
    except Exception as e:
        print("  (parquet ignoré:", e, ")")

    n_t1 = (aug.Periode == "T1").sum()
    n_9m = (aug.Periode == "9M").sum()
    print(f"  • lignes estimées : {len(aug)}  (T1={n_t1}, 9M={n_9m})")
    print(f"  • plage dates estimées : {aug.Date.min().date()} → {aug.Date.max().date()}")
    print(f"\n✔ Écrit : {C.OUT_AUGMENTED}  (estimations seules)")
    print(f"✔ Écrit : {C.OUT_FULL}  ({len(full)} lignes = réel + estimé)")
    return aug


if __name__ == "__main__":
    main()
