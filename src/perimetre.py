"""Corrections de qualite des donnees DELICE (voir annexe A.11 du rapport).

Deux anomalies sont traitees ici :
  1. Rupture de perimetre comptable en 2020 : les comptes passent du
     perimetre consolide au perimetre de la societe mere. Les ratios qui
     rapportent un flux a un agregat de bilan deviennent non comparables.
  2. Occurrence erronee des capitaux propres : la valeur retenue est
     identique au resultat net du meme exercice, ce qui produit un ROE
     de 100,0000 pourcent.
"""
import numpy as np
import pandas as pd

RUPTURES_PERIMETRE = {"DELICE": 2020}

CLE_CAPITAUX = "totaldescapitauxpropresavantaffectation"

# Ratios rapportant un flux a un agregat de bilan, ou bases sur les revenus.
# Ils perdent toute comparabilite quand le perimetre comptable change.
CODES_SENSIBLES_PERIMETRE = [
    "RENT_COM", "MARGE_NETTE", "ROT_CAP", "MARGE_BRUTE_EXPL",
    "MARGE_BENEF_EXPL", "TAUX_VA", "BFR_JOURS", "RISQ_COMMERCIAL",
    "CREDIT_CLIENT", "DSO", "EFF_BRUT_RH", "EFF_NET_RH",
    "ROA", "ROCE", "ROE", "ROI", "REND_PRODUCTION",
]



# Cles possibles du resultat net dans les donnees sources.
CLES_RESULTAT = [
    "resultatnetdelexercice",
    "resultatdesactivitesordinairesapresimpot",
    "beneficedelexercice",
    "benefice",
    "consolidatednetincome",
]


def reparer_capitaux_propres(m, df_all, verbose=True):
    """Rejette toute valeur de capitaux propres egale au resultat net.

    La comparaison porte sur TOUTES les occurrences du resultat net de
    cet exercice, car la valeur fautive peut correspondre a une occurrence
    autre que celle retenue par la matrice.
    """
    if "capitaux_propres" not in m.columns:
        return m, 0, 0
    n_rep, n_inv = 0, 0
    for idx in m.index[m["capitaux_propres"].notna()]:
        soc = m.at[idx, "Societe"]
        an = m.at[idx, "Annee"]
        per = m.at[idx, "Periode"]
        base = df_all[(df_all["Societe"] == soc) & (df_all["Annee"] == an)
                      & (df_all["Periode"] == per)]
        rn = base[base["Cle_indicateur"].isin(CLES_RESULTAT)]["Valeur"]
        rn = [float(v) for v in rn.dropna().tolist()]
        if not rn:
            continue
        cp = float(m.at[idx, "capitaux_propres"])
        if min([abs(cp - v) for v in rn]) > 1.0:
            continue
        cands = base[base["Cle_indicateur"] == CLE_CAPITAUX]["Valeur"]
        alt = []
        for v in cands.dropna().tolist():
            v = float(v)
            if min([abs(v - w) for w in rn]) > 1.0:
                alt.append(v)
        if alt:
            m.at[idx, "capitaux_propres"] = max(alt)
            n_rep += 1
        else:
            m.at[idx, "capitaux_propres"] = np.nan
            n_inv += 1
    if verbose and (n_rep or n_inv):
        print("  - capitaux propres suspects : %d reparees, %d invalidees"
              % (n_rep, n_inv))
    return m, n_rep, n_inv


def invalider_ratios_perimetre(ratios_df, verbose=True):
    """Invalide les ratios non comparables apres une rupture de perimetre.

    Les valeurs ne sont pas corrigees mais retirees, car aucun retraitement
    fiable ne permet de reconstituer un perimetre homogene.
    """
    n = 0
    for soc, annee in RUPTURES_PERIMETRE.items():
        masque = ((ratios_df["Societe"] == soc)
                  & (ratios_df["Annee"] >= annee)
                  & (ratios_df["Code_ratio"].isin(CODES_SENSIBLES_PERIMETRE))
                  & (ratios_df["Valeur"].notna()))
        n += int(masque.sum())
        ratios_df.loc[masque, "Valeur"] = np.nan
        ratios_df.loc[masque, "Note_sur_5"] = np.nan
    if verbose and n:
        print("  - rupture de perimetre : %d valeurs de ratios invalidees" % n)
    return ratios_df, n
