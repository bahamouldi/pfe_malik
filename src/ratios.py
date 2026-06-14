"""
ratios.py — Ratios financiers selon le référentiel OFFICIEL fourni par Malik
(MSI20000 / Référentiel Industriel Normalisé).

Contenu :
  1. CONCEPTS  : poste métier -> (état, clé) réels (robuste aux variantes).
  2. RATIOS    : 46 ratios (formules EXACTES du document de Malik).
  3. BENCHMARKS: fourchettes cibles industrielles par ratio.
  4. SCORING   : note 0-5 par ratio (grilles du document) -> Score Global de
                 Performance Industrielle (SGPI) /100, pondéré par catégorie.

Sorties :
  • data/processed/ratios.csv         (ratios + benchmark + note)
  • data/processed/sgpi.csv           (score global /100 par société/date)
  • data/processed/concepts_matrix.csv
"""

import numpy as np
import pandas as pd

import config as C

TVA = 0.19  # non utilisé dans les délais (formules officielles = HT) ; conservé pour info.

# =============================================================================
#  1. CONCEPTS
# =============================================================================
A, P = "Bilan - Actif", "Bilan - Passif"
CR, FT, SG, BL = "Compte de resultat", "Flux de tresorerie", "SIG", "Bilan"
X = "*"  # joker : n'importe quel état (AB inBev / Coca = Statement Inconnu)

CONCEPTS = {
    "actif_total":         [(A, "totaldesactifs"), (BL, "totaldesactifs"), (X, "totaldesactifs"), (X, "totalassets")],
    "actif_courant":       [(A, "totaldesactifscourants"), (BL, "totaldesactifscourants"), (X, "totaldesactifscourants"), (X, "totalcurrentassets")],
    "actif_immobilise":    [(A, "totaldesactifsimmobilises"), (A, "totaldesactifsnoncourants"), (BL, "totaldesactifsnoncourants"), (X, "totaldesactifsnoncourants")],
    "stocks":              [(A, "stocksapresprovisions"), (A, "stocks"), (BL, "stocks"), (X, "stocks"), (X, "inventories")],
    "clients":             [(A, "clientsetcomptesrattachesapresprovisions"), (A, "clientsetcomptesrattaches"), (BL, "clientsetcomptesrattaches"), (X, "creancescommercialesetautrescreances")],
    "clients_brut":        [(A, "clientsetcomptesrattaches"), (BL, "clientsetcomptesrattaches"), (X, "creancescommercialesetautrescreances")],
    "liquidites":          [(A, "liquiditesetequivalentsdeliquidites"), (BL, "liquiditesetequivalentsdeliquidites"), (X, "liquiditesetequivalentsdeliquidites"), (X, "cashandcashequivalents")],
    "placements":          [(A, "placementsetautresactifsfinanciersapresprovisions"), (A, "placementsetautresactifsfinanciers"), (BL, "placementsetautresactifsfinanciers"), (X, "placements"), (X, "shortterminvestments")],
    "concours_bancaires":  [(P, "concoursbancairesetautrespassifsfinanciers"), (P, "concoursbancaires")],
    "immo_corp_brut":      [(A, "immobilisationscorporelles"), (BL, "immobilisationscorporelles")],
    "immo_incorp_brut":    [(A, "immobilisationsincorporelles"), (BL, "immobilisationsincorporelles")],
    "amort_corp":          [(A, "amortissementsdesimmobilisationscorporelles"), (BL, "amortissementsdesimmobilisationscorporelles")],
    "amort_incorp":        [(A, "amortissementsdesimmobilisationsincorporelles"), (BL, "amortissementsdesimmobilisationsincorporelles")],
    "capitaux_propres":    [(P, "totaldescapitauxpropresavantaffectation"), (BL, "totaldescapitauxpropresavantaffectation"), (X, "totaldescapitauxpropresavantaffectation"), (X, "totalequity"), (X, "capitauxpropresattribuablesauxporteursdetitres")],
    "dettes_total":        [(P, "totaldespassifs"), (BL, "totaldespassifs")],
    "dettes_courantes":    [(P, "totaldespassifscourants"), (BL, "totaldespassifscourants"), (X, "totaldespassifscourants"), (X, "totalcurrentliabilities")],
    "dettes_non_courantes":[(P, "totaldespassifsnoncourants"), (BL, "totaldespassifsnoncourants"), (X, "totaldespassifsnoncourants")],
    "fournisseurs":        [(P, "fournisseursetcomptesrattaches"), (BL, "fournisseursetcomptesrattaches"), (X, "dettescommercialesetautresdettes"), (X, "accountspayableandaccruedexpenses")],
    "passif_total":        [(P, "totaldescapitauxpropresetdespassifs"), (BL, "totaldescapitauxpropresetdespassifs"), (X, "totaldescapitauxpropresetdespassifs"), (X, "totalliabilitiesandequity")],
    "ca":                  [(CR, "revenus"), (X, "produits"), (X, "netoperatingrevenues")],
    "resultat_exploitation":[(CR, "resultatdexploitation"), (X, "ebitnormalise"), (X, "operatingincome")],
    "resultat_net":        [(CR, "resultatnetdelexercice"), (CR, "resultatdesactivitesordinairesapresimpot"), (X, "beneficedelexercice"), (X, "benefice"), (X, "consolidatednetincome")],
    "charges_personnel":   [(CR, "chargesdepersonnel"), (SG, "chargesdepersonnel")],
    "dotations_amort":     [(CR, "dotationsauxamortissementsetauxprovisions"), (CR, "dotationsauxamortissementsetprovisions"), (X, "depreciationandamortization")],
    "charges_expl_total":  [(CR, "totaldeschargesdexploitation")],
    "produits_placements": [(CR, "produitsdesplacements"), (SG, "produitsfinanciers")],
    "ebe":                 [(SG, "excedentbrutdexploitation"), (X, "ebitdanormalise")],
    "va":                  [(SG, "valeurajouteebrute")],
    "production":          [(SG, "production")],
    "achats_consommes":    [(SG, "achatsconsommes"), (CR, "achatsdapprovisionnementsconsommes"), (X, "costofgoodssold"), (X, "coutsdesventes")],
}


def construire_matrice(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df.Occurrence == 1].copy()
    rows = []
    cols = ["Societe", "Date", "Annee", "Periode", "Devise", "Echelle"]
    for keyvals, g in df.groupby(cols):
        lut = {(r.Statement, r.Cle_indicateur): r.Valeur for r in g.itertuples()}
        lut_cle = {}
        for r in g.itertuples():
            if r.Cle_indicateur not in lut_cle and r.Valeur is not None and not pd.isna(r.Valeur):
                lut_cle[r.Cle_indicateur] = r.Valeur
        rec = dict(zip(cols, keyvals))
        for concept, cands in CONCEPTS.items():
            val = np.nan
            for (st, cle) in cands:
                v = lut_cle.get(cle) if st == X else lut.get((st, cle))
                if v is not None and not pd.isna(v):
                    val = float(v); break
            rec[concept] = val
        rows.append(rec)
    m = pd.DataFrame(rows)

    # Postes dérivés
    m["ressources_stables"] = m["capitaux_propres"] + m["dettes_non_courantes"].fillna(0)
    m["fonds_roulement"] = m["ressources_stables"] - m["actif_immobilise"]
    m["bfr"] = m["stocks"].fillna(0) + m["clients"].fillna(0) - m["fournisseurs"].fillna(0)
    m["amort_corp_cumul"] = m["amort_corp"].fillna(0).abs()
    m["charges_decaissables"] = m["charges_expl_total"] - m["dotations_amort"].fillna(0)
    m["tresorerie_nette"] = m["liquidites"] - m["concours_bancaires"].fillna(0)
    # Replis benchmarks
    mask = m["actif_immobilise"].isna() & m["actif_total"].notna() & m["actif_courant"].notna()
    m.loc[mask, "actif_immobilise"] = m["actif_total"] - m["actif_courant"]
    mask = m["dettes_total"].isna() & m["passif_total"].notna() & m["capitaux_propres"].notna()
    m.loc[mask, "dettes_total"] = m["passif_total"] - m["capitaux_propres"]
    mask = m["dettes_non_courantes"].isna() & m["dettes_total"].notna() & m["dettes_courantes"].notna()
    m.loc[mask, "dettes_non_courantes"] = m["dettes_total"] - m["dettes_courantes"]
    mask = m["ebe"].isna() & m["resultat_exploitation"].notna() & m["dotations_amort"].notna()
    m.loc[mask, "ebe"] = m["resultat_exploitation"] + m["dotations_amort"].abs()
    return m


# =============================================================================
#  2. RATIOS (formules officielles de Malik)
# =============================================================================
def _d(a, b):
    try:
        if b is None or pd.isna(b) or b == 0 or a is None or pd.isna(a):
            return np.nan
        return a / b
    except Exception:
        return np.nan


def _v(r, name):
    x = getattr(r, name, np.nan)
    return np.nan if x is None else x


# code : (categorie, sous_categorie, libelle, unite, fonction, interpretation)
RATIOS = {
    # ---------- GESTION DES LIQUIDITÉS ----------
    "LIQ_GEN": ("Gestion des liquidités", "Liquidités", "Ratio de liquidité générale", "x",
        lambda r: _d(r.actif_courant, r.dettes_courantes), "Capacité à couvrir les dettes court terme."),
    "LIQ_RED": ("Gestion des liquidités", "Liquidités", "Ratio de liquidité réduite", "x",
        lambda r: _d(r.actif_courant - (0 if pd.isna(r.stocks) else r.stocks), r.dettes_courantes), "Sans vendre les stocks."),
    "LIQ_IMM": ("Gestion des liquidités", "Liquidités", "Ratio de liquidité immédiate", "x",
        lambda r: _d(r.liquidites, r.dettes_courantes), "Couverture immédiate des dettes exigibles."),
    "INT_DEF_RED": ("Gestion des liquidités", "Liquidités", "Intervalle défensif réduit", "j",
        lambda r: _d(r.liquidites, _d(r.charges_decaissables, 365)), "Jours de charges couverts par les liquidités."),
    "INT_DEF": ("Gestion des liquidités", "Liquidités", "Intervalle défensif", "j",
        lambda r: _d(r.liquidites + (0 if pd.isna(r.clients) else r.clients), _d(r.charges_decaissables, 365)), "Jours couverts par liquidités + clients."),
    "FR": ("Gestion des liquidités", "Fonds de roulement", "Fonds de roulement (FR)", "montant",
        lambda r: r.ressources_stables - r.actif_immobilise if not (pd.isna(r.ressources_stables) or pd.isna(r.actif_immobilise)) else np.nan,
        "Ressources stables − actifs immobilisés (doit être positif)."),
    "COUV_IMMO": ("Gestion des liquidités", "Fonds de roulement", "Couverture des immobilisations", "x",
        lambda r: _d(r.ressources_stables, r.actif_immobilise), "Financement durable des investissements."),
    "BFR": ("Gestion des liquidités", "Fonds de roulement", "Besoin en fonds de roulement (BFR)", "montant",
        lambda r: r.bfr, "Stocks nets + clients nets − fournisseurs."),
    "BFR_JOURS": ("Gestion des liquidités", "Fonds de roulement", "Ratio BFR (jours de CA)", "j",
        lambda r: _d(r.bfr, _d(r.ca, 365)), "Jours de CA immobilisés dans l'exploitation."),
    # ---------- GESTION DES ACTIFS ----------
    "LEV_ECO": ("Gestion des actifs", "Gestion des actifs", "Ratio du levier économique", "x",
        lambda r: _d(r.actif_total, r.capitaux_propres), "Financement des actifs par les capitaux propres."),
    "POIDS_IMMO": ("Gestion des actifs", "Gestion des actifs", "Poids des immobilisations", "%",
        lambda r: 100 * _d(r.actif_immobilise, r.actif_total), "Part des investissements durables."),
    "VETUSTE": ("Gestion des actifs", "Gestion des actifs", "Vétusté des immobilisations corporelles", "%",
        lambda r: 100 * _d(r.amort_corp_cumul, r.immo_corp_brut), "Âge économique du parc industriel."),
    # ---------- GESTION DES PASSIFS ----------
    "ENDET_GLOB": ("Gestion des passifs", "Structure financière", "Ratio d'endettement global", "%",
        lambda r: 100 * _d(r.dettes_total, r.actif_total), "Part des actifs financés par la dette."),
    "ENDET_TERME": ("Gestion des passifs", "Structure financière", "Ratio d'endettement à terme", "%",
        lambda r: 100 * _d(r.dettes_non_courantes, r.capitaux_propres), "Dettes long terme / capitaux propres."),
    "INDEP_FIN": ("Gestion des passifs", "Structure financière", "Indépendance financière", "x",
        lambda r: _d(r.capitaux_propres, r.dettes_total), "Capitaux propres / total des dettes."),
    "AUTO_FIN": ("Gestion des passifs", "Structure financière", "Autonomie financière", "%",
        lambda r: 100 * _d(r.capitaux_propres, r.actif_total), "Capacité de financement autonome."),
    "SOLVA": ("Gestion des passifs", "Structure financière", "Solvabilité", "x",
        lambda r: _d(r.actif_total, r.dettes_total), "Capacité théorique à rembourser les dettes."),
    # ---------- RESSOURCES HUMAINES ----------
    "EFF_BRUT_RH": ("Ressources humaines", "Productivité RH", "Efficacité brute des RH", "x",
        lambda r: _d(r.ca, r.charges_personnel), "Revenus / charges de personnel."),
    "EFF_NET_RH": ("Ressources humaines", "Productivité RH", "Efficacité nette des RH", "x",
        lambda r: _d(r.resultat_net, r.charges_personnel), "Résultat net / charges de personnel."),
    # ---------- GESTION DES RISQUES ----------
    "RISQ_PLACEMENT": ("Gestion des risques", "Gestion des risques", "Risque de placement", "%",
        lambda r: 100 * _d(r.placements, r.actif_courant), "Placements / actifs courants."),
    "RISQ_COMMERCIAL": ("Gestion des risques", "Gestion des risques", "Risque commercial", "%",
        lambda r: 100 * _d(r.clients_brut, r.ca), "Clients bruts / revenus."),
    "CREDIT_CLIENT": ("Gestion des risques", "Gestion des risques", "Crédit moyen clients", "j",
        lambda r: _d(r.clients_brut, _d(r.ca, 365)), "Clients bruts / (revenus / 365)."),
    "CREDIT_FOURN": ("Gestion des risques", "Gestion des risques", "Crédit moyen fournisseurs", "j",
        lambda r: _d(r.fournisseurs, _d(r.achats_consommes, 365)), "Fournisseurs / (achats consommés / 365)."),
    "CONAN_HOLDER": ("Gestion des risques", "Gestion des risques", "Score de Conan & Holder", "score",
        lambda r: (0.24 * _d(r.actif_courant - (0 if pd.isna(r.stocks) else r.stocks), r.actif_total)
                   + 0.22 * _d(r.resultat_net, r.actif_total)
                   + 0.16 * _d(r.ca, r.actif_total)
                   - 0.87 * _d(r.charges_personnel, r.actif_total)
                   - 0.10 * _d(r.dettes_non_courantes, r.actif_total)),
        "Score de défaillance (formule MSI : > 0,16 = sain)."),
    # ---------- RENTABILITÉ ----------
    "RENT_COM": ("Rentabilité", "Rentabilité commerciale", "Rentabilité commerciale", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.ca), "Résultat d'exploitation / revenus."),
    "MARGE_NETTE": ("Rentabilité", "Rentabilité commerciale", "Marge nette", "%",
        lambda r: 100 * _d(r.resultat_net, r.ca), "Résultat net / revenus."),
    "ROT_CAP": ("Rentabilité", "Rentabilité commerciale", "Rotation des capitaux", "x",
        lambda r: _d(r.ca, r.actif_total), "Revenus / total actifs."),
    "ROA": ("Rentabilité", "Rentabilité économique", "Rendement de l'actif (ROA)", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.actif_total), "Résultat d'exploitation / total actifs."),
    "ROCE": ("Rentabilité", "Rentabilité économique", "Rentabilité du capital investi (ROCE)", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.ressources_stables), "Résultat d'exploitation / ressources stables."),
    "REND_IMMO": ("Rentabilité", "Rentabilité économique", "Rendement brut des immobilisations", "%",
        lambda r: 100 * _d(r.ebe, r.actif_immobilise), "EBE / actifs immobilisés."),
    "REND_RES_STABLE": ("Rentabilité", "Rentabilité économique", "Rendement brut des ressources stables", "%",
        lambda r: 100 * _d(r.ebe, r.ressources_stables), "EBE / ressources stables."),
    "MARGE_BRUTE_EXPL": ("Rentabilité", "Rentabilité d'exploitation", "Marge brute d'exploitation", "%",
        lambda r: 100 * _d(r.ebe, r.ca), "EBE / revenus."),
    "MARGE_BENEF_EXPL": ("Rentabilité", "Rentabilité d'exploitation", "Marge bénéficiaire d'exploitation", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.ca), "Résultat d'exploitation / revenus."),
    "REND_PRODUCTION": ("Rentabilité", "Rentabilité opérationnelle", "Rendement de la production", "%",
        lambda r: 100 * _d(r.resultat_exploitation, r.production), "Résultat d'exploitation / production."),
    "ROT_STOCKS": ("Rentabilité", "Rentabilité opérationnelle", "Rotation des stocks", "x",
        lambda r: _d(r.achats_consommes, r.stocks), "Achats consommés / stocks."),
    "PROFIT_OP": ("Rentabilité", "Rentabilité opérationnelle", "Profit opérationnel", "montant",
        lambda r: r.resultat_exploitation, "Résultat d'exploitation (montant)."),
    "CREATION_VALEUR": ("Rentabilité", "Rentabilité opérationnelle", "Création de valeur annuelle", "montant",
        lambda r: r.va, "Valeur ajoutée."),
    "ROE": ("Rentabilité", "Rentabilité financière", "Rentabilité des capitaux propres (ROE)", "%",
        lambda r: 100 * _d(r.resultat_net, r.capitaux_propres), "Résultat net / capitaux propres."),
    "PERF_PLACEMENT": ("Rentabilité", "Rentabilité financière", "Performance des placements", "%",
        lambda r: 100 * _d(r.produits_placements, r.placements), "Produits des placements / placements."),
    "ROI": ("Rentabilité", "Rentabilité financière", "Retour sur investissement (ROI)", "%",
        lambda r: 100 * _d(r.resultat_net, r.ressources_stables), "Résultat net / ressources stables."),
    # ---------- CYCLE D'EXPLOITATION ----------
    "DSO": ("Cycle d'exploitation", "Cycle d'exploitation", "Délai moyen de recouvrement clients (DSO)", "j",
        lambda r: _d(r.clients, _d(r.ca, 365)), "Clients / (CA / 365)."),
    "DPO": ("Cycle d'exploitation", "Cycle d'exploitation", "Délai moyen de paiement fournisseurs (DPO)", "j",
        lambda r: _d(r.fournisseurs, _d(r.achats_consommes, 365)), "Fournisseurs / (achats / 365)."),
    "DIO": ("Cycle d'exploitation", "Cycle d'exploitation", "Durée moyenne de stockage (DIO)", "j",
        lambda r: _d(r.stocks, _d(r.achats_consommes, 365)), "Stocks / (achats / 365)."),
    # ---------- INDICATEURS COMPLÉMENTAIRES ----------
    "TRESO_NETTE": ("Indicateurs complémentaires", "Complémentaires", "Trésorerie nette", "montant",
        lambda r: r.tresorerie_nette, "Liquidités − concours bancaires."),
    "TAUX_VA": ("Indicateurs complémentaires", "Complémentaires", "Taux de valeur ajoutée", "%",
        lambda r: 100 * _d(r.va, r.ca), "Valeur ajoutée / revenus."),
    "PART_PERSO_VA": ("Indicateurs complémentaires", "Complémentaires", "Part du personnel dans la VA", "%",
        lambda r: 100 * _d(r.charges_personnel, r.va), "Charges de personnel / valeur ajoutée."),
}


# =============================================================================
#  3. BENCHMARKS industriels (fourchettes cibles)
# =============================================================================
BENCHMARKS = {
    "LIQ_GEN": "1,5 à 2,0", "LIQ_RED": "0,9 à 1,2", "LIQ_IMM": "0,30 à 0,80",
    "FR": "positif", "COUV_IMMO": "1,2 à 1,5", "BFR_JOURS": "30 à 60 j",
    "LEV_ECO": "2 à 3", "POIDS_IMMO": "45 % à 65 %", "VETUSTE": "30 % à 60 %",
    "ENDET_GLOB": "40 % à 60 %", "AUTO_FIN": "35 % à 50 %", "SOLVA": "1,5 à 2",
    "ROA": "5 % à 10 %", "ROCE": "10 % à 15 %", "ROE": "10 % à 15 %",
    "DSO": "30 à 60 j", "DPO": "45 à 75 j", "DIO": "45 à 90 j",
}


# =============================================================================
#  4. SCORING : note 0-5 par ratio + SGPI /100
# =============================================================================
# Grilles (lo<=v<hi -> note). lo/hi None = ±infini. Ordre = parcours.
GRIDS = {
    "LIQ_GEN":   [(None, 1.0, 0), (1.0, 1.2, 1), (1.2, 1.5, 2), (1.5, 2.0, 4), (2.0, None, 5)],
    "LIQ_RED":   [(None, 0.7, 0), (0.7, 0.9, 2), (0.9, 1.2, 4), (1.2, None, 5)],
    "LIQ_IMM":   [(None, 0.15, 0), (0.15, 0.30, 2), (0.30, 0.80, 5), (0.80, None, 4)],
    "COUV_IMMO": [(None, 1.0, 0), (1.0, 1.2, 3), (1.2, 1.5, 5), (1.5, None, 4)],
    "BFR_JOURS": [(90, None, 0), (60, 90, 2), (30, 60, 4), (None, 30, 5)],
    "LEV_ECO":   [(5, None, 0), (3, 5, 2), (2, 3, 4), (None, 2, 5)],
    "POIDS_IMMO":[(80, None, 0), (65, 80, 2), (45, 65, 5), (None, 45, 4)],
    "VETUSTE":   [(80, None, 0), (60, 80, 2), (30, 60, 5), (None, 30, 4)],
    "ENDET_GLOB":[(75, None, 0), (60, 75, 2), (40, 60, 5), (None, 40, 4)],
    "AUTO_FIN":  [(None, 20, 0), (20, 35, 2), (35, 50, 5), (50, None, 4)],
    "SOLVA":     [(None, 1.2, 0), (1.2, 1.5, 2), (1.5, 2, 5), (2, None, 4)],
    "ROA":       [(None, 2, 0), (2, 5, 2), (5, 10, 5), (10, None, 4)],
    "ROCE":      [(None, 5, 0), (5, 10, 2), (10, 15, 5), (15, None, 4)],
    "ROE":       [(None, 5, 0), (5, 10, 2), (10, 15, 5), (15, None, 4)],
    # Grilles dérivées des benchmarks (pas de table fournie) :
    "DSO":       [(90, None, 0), (60, 90, 2), (30, 60, 5), (None, 30, 4)],
    "DPO":       [(None, 30, 2), (30, 45, 4), (45, 75, 5), (75, None, 3)],
    "DIO":       [(120, None, 0), (90, 120, 2), (45, 90, 5), (None, 45, 4)],
    "EFF_NET_RH":[(None, 1, 1), (1, 2, 3), (2, 4, 4), (4, None, 5)],
}


def note_ratio(code, val):
    """Note 0-5 d'un ratio selon sa grille (ou règle dédiée)."""
    if val is None or pd.isna(val):
        return np.nan
    if code == "FR":
        return 5 if val > 0 else (0 if val < 0 else 2)
    if code == "CONAN_HOLDER":
        return 5 if val > 0.16 else (3 if val >= 0.04 else 0)
    grid = GRIDS.get(code)
    if grid is None:
        return np.nan
    for lo, hi, note in grid:
        if (lo is None or val >= lo) and (hi is None or val < hi):
            return note
    return np.nan


# SGPI : catégorie -> (poids, [codes notés])
SGPI_CATEGORIES = {
    "Liquidité":             (0.15, ["LIQ_GEN", "LIQ_RED", "LIQ_IMM", "FR"]),
    "Structure financière":  (0.20, ["COUV_IMMO", "ENDET_GLOB", "AUTO_FIN", "SOLVA"]),
    "Gestion des actifs":    (0.15, ["LEV_ECO", "POIDS_IMMO", "VETUSTE"]),
    "Gestion des risques":   (0.10, ["CONAN_HOLDER"]),
    "Rentabilité":           (0.25, ["ROA", "ROCE", "ROE"]),
    "Productivité RH":       (0.05, ["EFF_NET_RH"]),
    "Cycle d'exploitation":  (0.10, ["BFR_JOURS", "DSO", "DPO", "DIO"]),
}


# =============================================================================
#  Calcul
# =============================================================================
def calculer_ratios(df):
    m = construire_matrice(df)
    out = []
    for r in m.itertuples():
        for code, (cat, sous, libelle, unite, fn, interp) in RATIOS.items():
            try:
                val = fn(r)
            except Exception:
                val = np.nan
            note = note_ratio(code, val)
            out.append({
                "Societe": r.Societe, "Date": r.Date, "Annee": r.Annee, "Periode": r.Periode,
                "Devise": r.Devise, "Categorie": cat, "Sous_categorie": sous,
                "Code_ratio": code, "Ratio": libelle, "Unite": unite,
                "Valeur": (round(float(val), 4) if val is not None and not pd.isna(val) else np.nan),
                "Benchmark": BENCHMARKS.get(code, ""),
                "Note_sur_5": (note if not pd.isna(note) else np.nan),
            })
    return pd.DataFrame(out), m


def calculer_sgpi(ratios_df):
    """Score Global de Performance Industrielle /100 par société et date."""
    rows = []
    for (soc, date, annee, per), g in ratios_df.groupby(["Societe", "Date", "Annee", "Periode"]):
        notes = g.set_index("Code_ratio")["Note_sur_5"].to_dict()
        rec = {"Societe": soc, "Date": date, "Annee": annee, "Periode": per}
        sgpi, poids_utilise = 0.0, 0.0
        for cat, (poids, codes) in SGPI_CATEGORIES.items():
            vals = [notes[c] for c in codes if c in notes and not pd.isna(notes[c])]
            if not vals:
                rec[cat] = np.nan
                continue
            cat_note = np.mean(vals)              # note moyenne /5
            rec[cat] = round(cat_note, 2)
            sgpi += (cat_note / 5) * poids
            poids_utilise += poids
        # Renormalisation si certaines catégories absentes (benchmarks).
        rec["SGPI_sur_100"] = round(100 * sgpi / poids_utilise, 1) if poids_utilise > 0 else np.nan
        rec["Couverture_%"] = round(100 * poids_utilise, 0)
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    print("=== Ratios financiers (référentiel officiel Malik) ===")
    df = pd.read_csv(C.OUT_FULL, parse_dates=["Date"]) if C.OUT_FULL.exists() \
        else pd.read_csv(C.OUT_UNIFIED, parse_dates=["Date"])
    res, m = calculer_ratios(df)
    sgpi = calculer_sgpi(res)

    res.to_csv(C.PROCESSED_DIR / "ratios.csv", index=False)
    m.to_csv(C.PROCESSED_DIR / "concepts_matrix.csv", index=False)
    sgpi.to_csv(C.PROCESSED_DIR / "sgpi.csv", index=False)

    n_calc = res.Valeur.notna().sum()
    print(f"  • {len(RATIOS)} ratios × {m.shape[0]} points = {len(res)} lignes ({n_calc} calculées)")
    sf = sgpi[(sgpi.Societe == "SFBT") & (sgpi.Annee == 2024) & (sgpi.Periode == "FY")]
    if len(sf):
        cov = sf["Couverture_%"].iloc[0]
        print(f"  • SGPI SFBT 2024 : {sf.SGPI_sur_100.iloc[0]}/100 (couverture {cov:.0f}%)")
    print(f"✔ ratios.csv, sgpi.csv, concepts_matrix.csv")
    return res


if __name__ == "__main__":
    main()
