"""
ratios.py — Calcul des ratios financiers (référentiel MSI20000).

Malik n'ayant pas fourni les formules, elles sont reconstituées d'après les
définitions financières standard et la table des matières MSI20000 (images du
cahier des charges). Chaque ratio est documenté (catégorie, formule, unité,
interprétation) dans le catalogue RATIOS ci-dessous et dans
`docs/CATALOGUE_RATIOS.md`.

Principe :
  1. CONCEPTS   : associe un poste financier « métier » à un/des (état, clé)
                  réels du jeu de données (robuste aux variantes de libellés).
  2. matrice    : on reconstruit un tableau large (1 ligne = société × date,
                  colonnes = postes financiers).
  3. RATIOS     : chaque ratio = une fonction sur cette ligne, avec division
                  sécurisée (NaN si dénominateur nul ou poste manquant).

Sortie : data/processed/ratios.csv  (format long, prêt pour Power BI / le DW).
"""

import numpy as np
import pandas as pd

import config as C

# Coût du capital (CMPC) supposé pour la création de valeur (EVA). Paramétrable.
COUT_CAPITAL = 0.08
# Taux de TVA pour passer HT -> TTC (crédits clients/fournisseurs).
TVA = 0.19


# =============================================================================
#  1. CONCEPTS — poste métier -> liste ordonnée de candidats (Statement, cle)
#     Le 1er candidat présent (valeur non nulle) est retenu. Couvre SFBT
#     (Bilan scindé Actif/Passif) ET DELICE (Bilan unique), même vocabulaire.
# =============================================================================
A, P = "Bilan - Actif", "Bilan - Passif"
CR, FT, SG, BL = "Compte de resultat", "Flux de tresorerie", "SIG", "Bilan"
X = "*"   # joker : correspond à n'importe quel état (utile pour AB inBev / Coca,
          # dont les lignes ne sont pas rattachées à un état — Statement=Inconnu).

CONCEPTS = {
    # --- Bilan : actif (stocks) ---
    "actif_total":         [(A, "totaldesactifs"), (BL, "totaldesactifs"),
                            (X, "totaldesactifs"), (X, "totalassets")],
    "actif_courant":       [(A, "totaldesactifscourants"), (BL, "totaldesactifscourants"),
                            (X, "totaldesactifscourants"), (X, "totalcurrentassets")],
    "actif_immobilise":    [(A, "totaldesactifsimmobilises"), (A, "totaldesactifsnoncourants"),
                            (BL, "totaldesactifsnoncourants"), (X, "totaldesactifsnoncourants")],
    "stocks":              [(A, "stocksapresprovisions"), (A, "stocks"), (BL, "stocks"),
                            (X, "stocks"), (X, "inventories")],
    "clients":             [(A, "clientsetcomptesrattachesapresprovisions"),
                            (A, "clientsetcomptesrattaches"), (BL, "clientsetcomptesrattaches"),
                            (X, "creancescommercialesetautrescreances")],
    "liquidites":          [(A, "liquiditesetequivalentsdeliquidites"),
                            (BL, "liquiditesetequivalentsdeliquidites"),
                            (X, "liquiditesetequivalentsdeliquidites"), (X, "cashandcashequivalents")],
    "placements":          [(A, "placementsetautresactifsfinanciersapresprovisions"),
                            (A, "placementsetautresactifsfinanciers"),
                            (BL, "placementsetautresactifsfinanciers"),
                            (X, "placements"), (X, "shortterminvestments")],
    "immo_corp_brut":      [(A, "immobilisationscorporelles"), (BL, "immobilisationscorporelles")],
    "immo_incorp_brut":    [(A, "immobilisationsincorporelles"), (BL, "immobilisationsincorporelles")],
    "amort_corp":          [(A, "amortissementsdesimmobilisationscorporelles"),
                            (BL, "amortissementsdesimmobilisationscorporelles")],
    "amort_incorp":        [(A, "amortissementsdesimmobilisationsincorporelles"),
                            (BL, "amortissementsdesimmobilisationsincorporelles")],
    # --- Bilan : passif (stocks) ---
    "capitaux_propres":    [(P, "totaldescapitauxpropresavantaffectation"),
                            (BL, "totaldescapitauxpropresavantaffectation"),
                            (X, "totaldescapitauxpropresavantaffectation"), (X, "totalequity"),
                            (X, "capitauxpropresattribuablesauxporteursdetitres")],
    "capital_social":      [(P, "capitalsocial"), (BL, "capitalsocial"), (X, "capitalsocial")],
    "dettes_total":        [(P, "totaldespassifs"), (BL, "totaldespassifs")],   # sinon dérivé
    "dettes_courantes":    [(P, "totaldespassifscourants"), (BL, "totaldespassifscourants"),
                            (X, "totaldespassifscourants"), (X, "totalcurrentliabilities")],
    "dettes_non_courantes":[(P, "totaldespassifsnoncourants"), (BL, "totaldespassifsnoncourants"),
                            (X, "totaldespassifsnoncourants")],
    "fournisseurs":        [(P, "fournisseursetcomptesrattaches"), (BL, "fournisseursetcomptesrattaches"),
                            (X, "dettescommercialesetautresdettes"),
                            (X, "accountspayableandaccruedexpenses")],
    "passif_total":        [(P, "totaldescapitauxpropresetdespassifs"),
                            (BL, "totaldescapitauxpropresetdespassifs"),
                            (X, "totaldescapitauxpropresetdespassifs"), (X, "totalliabilitiesandequity")],
    # --- Compte de résultat (flux) ---
    "ca":                  [(CR, "revenus"), (X, "produits"), (X, "netoperatingrevenues")],
    "resultat_exploitation":[(CR, "resultatdexploitation"), (X, "ebitnormalise"), (X, "operatingincome")],
    "resultat_net":        [(CR, "resultatnetdelexercice"), (CR, "resultatdesactivitesordinairesapresimpot"),
                            (X, "beneficedelexercice"), (X, "benefice"), (X, "consolidatednetincome")],
    "charges_personnel":   [(CR, "chargesdepersonnel"), (SG, "chargesdepersonnel")],
    "dotations_amort":     [(CR, "dotationsauxamortissementsetauxprovisions"),
                            (CR, "dotationsauxamortissementsetprovisions"),
                            (X, "depreciationandamortization")],
    "charges_expl_total":  [(CR, "totaldeschargesdexploitation")],
    "produits_expl_total": [(CR, "totaldesproduitsdexploitation")],
    "resultat_financier_net":[(CR, "produitsetchargesfinanciersnets"),
                              (SG, "produitsetchargesfinanciersnets"),
                              (CR, "chargesfinancieresnettes")],
    "produits_placements": [(CR, "produitsdesplacements"), (SG, "produitsfinanciers")],
    # --- SIG / EBITDA (flux) ---
    "ebe":                 [(SG, "excedentbrutdexploitation"), (X, "ebitdanormalise")],
    "va":                  [(SG, "valeurajouteebrute")],
    "marge_commerciale":   [(SG, "margecommerciale")],
    "production":          [(SG, "production")],
    "achats_consommes":    [(SG, "achatsconsommes"), (CR, "achatsdapprovisionnementsconsommes")],
    "marge_cout_matieres": [(SG, "margesurcoutmatieres")],
    "ventes_marchandises": [(SG, "ventesdemarchandisesetautres")],
}


def construire_matrice(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruit le tableau large des postes financiers (1 ligne / société×date)."""
    df = df[df.Occurrence == 1].copy()
    rows = []
    cols = ["Societe", "Date", "Annee", "Periode", "Devise", "Echelle"]
    for keyvals, g in df.groupby(cols):
        lut = {(r.Statement, r.Cle_indicateur): r.Valeur for r in g.itertuples()}
        # Repli par clé seule (1re valeur non nulle) pour les candidats joker "*".
        lut_cle = {}
        for r in g.itertuples():
            if r.Cle_indicateur not in lut_cle and r.Valeur is not None and not pd.isna(r.Valeur):
                lut_cle[r.Cle_indicateur] = r.Valeur
        rec = dict(zip(cols, keyvals))
        for concept, candidats in CONCEPTS.items():
            val = np.nan
            for (st, cle) in candidats:
                v = lut_cle.get(cle) if st == X else lut.get((st, cle))
                if v is not None and not pd.isna(v):
                    val = float(v)
                    break
            rec[concept] = val
        rows.append(rec)
    m = pd.DataFrame(rows)

    # --- Replis dérivés (surtout pour les benchmarks au format hétérogène) ---
    # Actif immobilisé = Actif total − Actif courant (si non publié tel quel).
    mask = m["actif_immobilise"].isna() & m["actif_total"].notna() & m["actif_courant"].notna()
    m.loc[mask, "actif_immobilise"] = m["actif_total"] - m["actif_courant"]
    # Dettes totales = Passif total − Capitaux propres (si non publié tel quel).
    mask = m["dettes_total"].isna() & m["passif_total"].notna() & m["capitaux_propres"].notna()
    m.loc[mask, "dettes_total"] = m["passif_total"] - m["capitaux_propres"]
    # Dettes non courantes = Dettes totales − Dettes courantes.
    mask = m["dettes_non_courantes"].isna() & m["dettes_total"].notna() & m["dettes_courantes"].notna()
    m.loc[mask, "dettes_non_courantes"] = m["dettes_total"] - m["dettes_courantes"]
    # EBE ≈ Résultat d'exploitation + Dotations aux amortissements (proxy EBITDA).
    mask = m["ebe"].isna() & m["resultat_exploitation"].notna() & m["dotations_amort"].notna()
    m.loc[mask, "ebe"] = m["resultat_exploitation"] + m["dotations_amort"].abs()

    # --- Postes dérivés ---
    m["capitaux_permanents"] = m["capitaux_propres"] + m["dettes_non_courantes"].fillna(0)
    m["fonds_roulement"] = m["capitaux_permanents"] - m["actif_immobilise"]
    m["bfr"] = m["stocks"].fillna(0) + m["clients"].fillna(0) - m["fournisseurs"].fillna(0)
    m["amort_cumul"] = m["amort_corp"].fillna(0).abs() + m["amort_incorp"].fillna(0).abs()
    m["immo_brut"] = m["immo_corp_brut"].fillna(0) + m["immo_incorp_brut"].fillna(0)
    m["charges_decaissables"] = m["charges_expl_total"] - m["dotations_amort"].fillna(0)
    # Charges financières estimées (la source ne donne pas le brut) :
    #   = part « charge » du résultat financier net (0 si résultat financier positif).
    m["charges_financieres_est"] = (-m["resultat_financier_net"]).clip(lower=0)
    return m


# =============================================================================
#  2. RATIOS — registre : code -> (catégorie, sous-catégorie, libellé, unité,
#     fonction, interprétation)
# =============================================================================
def _d(a, b):
    """Division sécurisée -> NaN si dénominateur nul/manquant."""
    try:
        if b is None or pd.isna(b) or b == 0 or a is None or pd.isna(a):
            return np.nan
        return a / b
    except Exception:
        return np.nan


# unités : "x" (fois), "%" (pourcentage), "j" (jours), "score", "montant"
RATIOS = {
    # ===================== SOLIDITÉ — Liquidités =====================
    "LIQ_GEN": ("Solidité", "Liquidités", "Ratio de liquidité générale", "x",
        lambda r: _d(r.actif_courant, r.dettes_courantes),
        ">1 : l'actif courant couvre les dettes à court terme."),
    "LIQ_RED": ("Solidité", "Liquidités", "Ratio de liquidité réduite", "x",
        lambda r: _d((r.actif_courant - (r.stocks if not pd.isna(r.stocks) else 0)), r.dettes_courantes),
        "Liquidité hors stocks (quick ratio)."),
    "LIQ_IMM": ("Solidité", "Liquidités", "Ratio de liquidité immédiate", "x",
        lambda r: _d(r.liquidites, r.dettes_courantes),
        "Capacité à payer immédiatement avec les disponibilités."),
    "INT_DEF_RED": ("Solidité", "Liquidités", "Intervalle défensif réduit", "j",
        lambda r: _d(r.liquidites + (r.placements if not pd.isna(r.placements) else 0),
                     _d(r.charges_decaissables, 365)),
        "Nb de jours de charges couverts par les actifs très liquides."),
    "INT_DEF": ("Solidité", "Liquidités", "Intervalle défensif", "j",
        lambda r: _d(r.liquidites + (r.placements if not pd.isna(r.placements) else 0)
                     + (r.clients if not pd.isna(r.clients) else 0),
                     _d(r.charges_decaissables, 365)),
        "Jours de charges couverts par actifs liquides + créances."),
    "RFR": ("Solidité", "Liquidités", "Ratio de fonds de roulement", "%",
        lambda r: 100 * _d(r.fonds_roulement, r.actif_total),
        "Fonds de roulement net en % de l'actif total."),
    "RBFR": ("Solidité", "Liquidités", "Ratio de besoin en fonds de roulement", "%",
        lambda r: 100 * _d(r.bfr, r.ca),
        "BFR en % du chiffre d'affaires."),
    # ===================== SOLIDITÉ — Gestion des actifs =====================
    "LEV_ECO": ("Solidité", "Gestion des actifs", "Ratio du levier économique", "x",
        lambda r: _d(r.actif_total, r.capitaux_propres),
        "Actif total rapporté aux capitaux propres."),
    "POIDS_IMMO": ("Solidité", "Gestion des actifs", "Poids des immobilisations", "%",
        lambda r: 100 * _d(r.actif_immobilise, r.actif_total),
        "Part de l'actif immobilisé dans l'actif total."),
    "FIN_IMMO": ("Solidité", "Gestion des actifs", "Financement des immobilisations", "x",
        lambda r: _d(r.capitaux_permanents, r.actif_immobilise),
        ">1 : les ressources stables financent les immobilisations."),
    "VETUSTE": ("Solidité", "Gestion des actifs", "Vétusté de l'actif", "%",
        lambda r: 100 * _d(r.amort_cumul, r.immo_brut),
        "Amortissements cumulés / immobilisations brutes (usure de l'outil)."),
    # ===================== SOLIDITÉ — Gestion des passifs =====================
    "ENDET_GLOB": ("Solidité", "Gestion des passifs", "Ratio d'endettement global", "%",
        lambda r: 100 * _d(r.dettes_total, r.passif_total),
        "Part des dettes dans le total du passif."),
    "ENDET_TERME": ("Solidité", "Gestion des passifs", "Ratio d'endettement à terme", "%",
        lambda r: 100 * _d(r.dettes_non_courantes, r.capitaux_propres),
        "Dettes long terme / capitaux propres (gearing LT)."),
    "INDEP_FIN": ("Solidité", "Gestion des passifs", "Ratio d'indépendance financière", "%",
        lambda r: 100 * _d(r.capitaux_propres, r.passif_total),
        "Part des capitaux propres dans le financement total."),
    "COUV_CF": ("Solidité", "Gestion des passifs", "Couverture des charges financières", "x",
        lambda r: _d(r.resultat_exploitation, r.charges_financieres_est),
        "Résultat d'exploitation / charges financières (NaN si charges ~0)."),
    "POIDS_CF": ("Solidité", "Gestion des passifs", "Poids des charges financières", "%",
        lambda r: 100 * _d(r.charges_financieres_est, r.ca),
        "Charges financières en % du CA."),
    "AUTO_FIN": ("Solidité", "Gestion des passifs", "Ratio d'autonomie financière", "x",
        lambda r: _d(r.capitaux_propres, r.dettes_total),
        "Capitaux propres / total des dettes."),
    "SOLVA": ("Solidité", "Gestion des passifs", "Ratio de solvabilité", "x",
        lambda r: _d(r.actif_total, r.dettes_total),
        "Actif total / total des dettes (capacité de remboursement)."),
    # ===================== SOLIDITÉ — Ressources humaines =====================
    "EFF_BRUT_RH": ("Solidité", "Ressources humaines", "Efficacité brute des RH", "x",
        lambda r: _d(r.va, r.charges_personnel),
        "Valeur ajoutée générée par dinar de charges de personnel."),
    "EFF_NET_RH": ("Solidité", "Ressources humaines", "Efficacité nette des RH", "x",
        lambda r: _d(r.ebe, r.charges_personnel),
        "EBE par dinar de charges de personnel."),
    # ===================== SOLIDITÉ — Gestion des risques =====================
    "CONAN_HOLDER": ("Solidité", "Gestion des risques", "Score de Conan & Holder", "score",
        lambda r: (0.24 * _d(r.ebe, r.dettes_total)
                   + 0.22 * _d(r.capitaux_permanents, r.actif_total)
                   + 0.16 * _d((r.actif_courant - (r.stocks if not pd.isna(r.stocks) else 0)), r.actif_total)
                   - 0.87 * _d(r.charges_financieres_est, r.ca)
                   - 0.10 * _d(r.charges_personnel, r.va)),
        "Score de défaillance : >0,16 bon ; <0,04 risque élevé."),
    "RISQ_PLACEMENT": ("Solidité", "Gestion des risques", "Risque de placement", "%",
        lambda r: 100 * _d(r.placements, r.actif_total),
        "Part des placements financiers dans l'actif."),
    "RISQ_COMMERCIAL": ("Solidité", "Gestion des risques", "Risque commercial", "%",
        lambda r: 100 * _d(r.clients, r.ca),
        "Exposition clients rapportée au CA."),
    "CREDIT_FOURN": ("Solidité", "Gestion des risques", "Crédits moyens fournisseurs", "j",
        lambda r: _d(r.fournisseurs, r.achats_consommes * (1 + TVA)) * 365 if not pd.isna(r.achats_consommes) else np.nan,
        "Délai moyen de paiement des fournisseurs (jours, TTC)."),
    "CREDIT_CLIENT": ("Solidité", "Gestion des risques", "Crédits moyens clients", "j",
        lambda r: _d(r.clients, r.ca * (1 + TVA)) * 365,
        "Délai moyen d'encaissement des clients (jours, TTC)."),
    # ===================== PERFORMANCE — Rentabilité commerciale =====================
    "RENT_COM": ("Performance", "Rentabilité commerciale", "Rentabilité commerciale", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.ca),
        "Résultat d'exploitation / CA."),
    "MARGE_NETTE": ("Performance", "Rentabilité commerciale", "Ratio de la marge nette", "%",
        lambda r: 100 * _d(r.resultat_net, r.ca),
        "Résultat net / CA."),
    "TAUX_MARQUE": ("Performance", "Rentabilité commerciale", "Taux de marque", "%",
        lambda r: 100 * _d(r.marge_cout_matieres, r.production),
        "Marge sur coût matières / production."),
    "ROT_CAP": ("Performance", "Rentabilité commerciale", "Rotation des capitaux échangés", "x",
        lambda r: _d(r.ca, r.capitaux_propres),
        "CA généré par dinar de capitaux propres."),
    # ===================== PERFORMANCE — Rentabilité économique =====================
    "ROA": ("Performance", "Rentabilité économique", "Rendement de l'actif (ROA)", "%",
        lambda r: 100 * _d(r.resultat_net, r.actif_total),
        "Résultat net / actif total."),
    "ROCE": ("Performance", "Rentabilité économique", "Rentabilité du capital investi (ROCE)", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.capitaux_permanents),
        "Résultat d'exploitation / capitaux permanents."),
    "REND_IMMO": ("Performance", "Rentabilité économique", "Rendement brut des immobilisations", "%",
        lambda r: 100 * _d(r.ebe, r.actif_immobilise),
        "EBE / actif immobilisé."),
    "REND_RES_STABLE": ("Performance", "Rentabilité économique", "Rendement brut des ressources stables", "%",
        lambda r: 100 * _d(r.ebe, r.capitaux_permanents),
        "EBE / capitaux permanents."),
    # ===================== PERFORMANCE — Rentabilité d'exploitation =====================
    "MARGE_BRUTE_EXPL": ("Performance", "Rentabilité d'exploitation", "Marge brute d'exploitation", "%",
        lambda r: 100 * _d(r.ebe, r.ca),
        "EBE / CA."),
    "MARGE_BENEF_EXPL": ("Performance", "Rentabilité d'exploitation", "Marge bénéficiaire d'exploitation", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.ca),
        "Résultat d'exploitation / CA."),
    # ===================== PERFORMANCE — Rentabilité opérationnelle =====================
    "REND_GLOBAL_NET": ("Performance", "Rentabilité opérationnelle", "Rendement global net", "%",
        lambda r: 100 * _d(r.resultat_net, r.passif_total),
        "Résultat net / total des ressources."),
    "CREATION_VALEUR": ("Performance", "Rentabilité opérationnelle", "Création de valeur annuelle", "montant",
        lambda r: (r.resultat_exploitation - COUT_CAPITAL * r.capitaux_permanents)
                  if not (pd.isna(r.resultat_exploitation) or pd.isna(r.capitaux_permanents)) else np.nan,
        f"EVA = Rés. exploitation − CMPC×capitaux permanents (CMPC={COUT_CAPITAL:.0%})."),
    "REND_PRODUCTION": ("Performance", "Rentabilité opérationnelle", "Rendement de la production", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.production),
        "Résultat d'exploitation / production."),
    "ROT_STOCKS": ("Performance", "Rentabilité opérationnelle", "Ratio de rotation des stocks", "x",
        lambda r: _d(r.achats_consommes, r.stocks),
        "Nb de rotations des stocks dans l'année."),
    "PROFIT_OP": ("Performance", "Rentabilité opérationnelle", "Profit opérationnel", "montant",
        lambda r: r.resultat_exploitation,
        "Résultat d'exploitation (montant)."),
    # ===================== PERFORMANCE — Rentabilité financière =====================
    "ROE": ("Performance", "Rentabilité financière", "Rentabilité des capitaux propres (ROE)", "%",
        lambda r: 100 * _d(r.resultat_net, r.capitaux_propres),
        "Résultat net / capitaux propres."),
    "ROI": ("Performance", "Rentabilité financière", "Retour sur investissement (ROI)", "%",
        lambda r: 100 * _d(r.resultat_net, r.actif_total),
        "Résultat net / actif total."),
    "PERF_PLACEMENT": ("Performance", "Rentabilité financière", "Performance placement", "%",
        lambda r: 100 * _d(r.produits_placements, r.placements),
        "Produits des placements / placements."),
}


def calculer_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Renvoie les ratios au format long."""
    m = construire_matrice(df)
    out = []
    for r in m.itertuples():
        for code, (cat, sous, libelle, unite, fn, interp) in RATIOS.items():
            try:
                val = fn(r)
            except Exception:
                val = np.nan
            out.append({
                "Societe": r.Societe, "Date": r.Date, "Annee": r.Annee,
                "Periode": r.Periode, "Devise": r.Devise,
                "Categorie": cat, "Sous_categorie": sous,
                "Code_ratio": code, "Ratio": libelle, "Unite": unite,
                "Valeur": (round(float(val), 4) if val is not None and not pd.isna(val) else np.nan),
            })
    res = pd.DataFrame(out)
    return res, m


def main():
    print("=== Calcul des ratios MSI20000 ===")
    df = pd.read_csv(C.OUT_FULL, parse_dates=["Date"]) if C.OUT_FULL.exists() \
        else pd.read_csv(C.OUT_UNIFIED, parse_dates=["Date"])
    res, m = calculer_ratios(df)
    out = C.PROCESSED_DIR / "ratios.csv"
    res.to_csv(out, index=False)
    mat = C.PROCESSED_DIR / "concepts_matrix.csv"
    m.to_csv(mat, index=False)
    n_calc = res.Valeur.notna().sum()
    print(f"  • {len(RATIOS)} ratios × {m.shape[0]} points = {len(res)} lignes "
          f"({n_calc} calculées, {len(res)-n_calc} NaN)")
    print(f"  • sociétés : {sorted(res.Societe.unique())}")
    print(f"✔ Écrit : {out}")
    print(f"✔ Matrice des postes : {mat}")
    return res


if __name__ == "__main__":
    main()
