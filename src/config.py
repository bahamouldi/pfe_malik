"""
config.py — Configuration centrale du pipeline d'analyse financière SFBT.

Décrit les sources de données (4 sociétés), leurs métadonnées (devise, échelle,
fréquence) et le schéma unifié cible. Toute la chaîne de traitement
(unify.py, augment.py) s'appuie sur ces constantes.
"""

from pathlib import Path

# --- Arborescence du projet ---------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "data" / "reports"
DOCS_DIR = ROOT / "docs"

for _d in (PROCESSED_DIR, REPORTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- Schéma unifié cible ------------------------------------------------------
# Toutes les sociétés sont ramenées à ce format long (tidy).
SCHEMA = [
    "Societe",          # Nom de la société
    "Statement",        # Bilan - Actif | Bilan - Passif | Compte de resultat | Flux de tresorerie | SIG
    "Indicateur",       # Libellé lisible (variante canonique choisie)
    "Indicateur_raw",   # Libellé brut d'origine (traçabilité)
    "Cle_indicateur",   # Clé normalisée (jointure temporelle / regroupement variantes)
    "Date",             # Date de clôture (datetime, fin de période)
    "Annee",            # Année (int)
    "Periode",          # T1 | S1 | 9M | FY  (voir METADATA / docs)
    "Valeur",           # Montant (float, dans la devise/échelle de la société)
    "Occurrence",       # 1 si série unique ; >1 = collision de libellé non désambiguïsée (cf. rapport)
    "Devise",           # TND | USD
    "Echelle",          # unite | millier | million
    "Type_donnee",      # Reel | Estime  (Estime = généré par augmentation)
    "Source",           # Fichier source d'origine
]

# --- Métadonnées par société --------------------------------------------------
# 'devise'/'echelle' : indispensables car les ratios sont comparables (sans
#   dimension) mais PAS les montants absolus (TND dinars vs USD millions).
# 'role'  : 'principale' (SFBT) ou 'benchmark'.
# 'loader': fonction de chargement dédiée dans unify.py (formats hétérogènes).
SOCIETES = {
    "SFBT": {
        "fichier": "SFBT_beta1.xlsx",
        "role": "principale",
        "devise": "TND",
        "echelle": "unite",          # dinars (montants bruts)
        "frequence": "Semestriel",   # clôtures Juin + Décembre
        "loader": "load_sfbt",
        # Feuil1 est la feuille MAÎTRESSE (contient tous les états concaténés).
        # Feuil2..4 sont des extraits par état ; Feuil5 = SIG (absent de Feuil1
        # pour les vieilles années -> on la fusionne en complément).
        "feuille_maitresse": "Feuil1",
        "feuille_sig": "Feuil5",
    },
    "DELICE": {
        "fichier": "DELICE_Clean.xlsx",
        "role": "benchmark",
        "devise": "TND",
        "echelle": "unite",
        "frequence": "Annuel",
        "loader": "load_clean_long",   # déjà au schéma quasi-cible
        "feuille": "DELICE_Clean",
    },
    "AB inBev": {
        "fichier": "AB_inBev_Clean.xlsx",
        "role": "benchmark",
        "devise": "USD",
        "echelle": "million",          # rapports en millions USD
        "frequence": "Annuel",
        "loader": "load_clean_long",
        "feuille": "Sheet1",
    },
    "Coca-Cola": {
        "fichier": "Coca_Cola.xlsx",
        "role": "benchmark",
        "devise": "USD",
        "echelle": "million",
        "frequence": "Annuel",
        "loader": "load_cocacola",     # format particulier (anglais, colonnes différentes)
        "feuille": "Feuil1",
    },
}

# --- Classification des états (SFBT / Feuil1) ---------------------------------
# Feuil1 empile, pour chaque date : Actif -> Passif -> Compte de résultat ->
# Flux -> (SIG). On découpe par MARQUEURS de fin de section (clés normalisées).
# La détection est positionnelle (l'ordre des sections est stable), ce qui évite
# les erreurs dues aux libellés identiques présents dans 2 états.
SECTION_ORDER = [
    "Bilan - Actif",
    "Bilan - Passif",
    "Compte de resultat",
    "Flux de tresorerie",
    "SIG",
]

# --- Vocabulaire contrôlé des états (harmonisation inter-sociétés) ------------
# Clé = clé normalisée du libellé d'état rencontré ; Valeur = label canonique.
# (DELICE écrit « Bilan », SFBT distingue Actif/Passif, accents variables...)
STATEMENT_CANON = {
    "bilan": "Bilan",
    "bilanactif": "Bilan - Actif",
    "bilanpassif": "Bilan - Passif",
    "comptederesultat": "Compte de resultat",
    "fluxdetresorerie": "Flux de tresorerie",
    "sig": "SIG",
    "inconnu": "Inconnu",
    "": "Inconnu",
}

# --- Catégorie stock vs flux (pour l'augmentation) ----------------------------
# Stock  = grandeur instantanée (photo à la date)  -> interpolation linéaire.
# Flux   = grandeur cumulée sur l'exercice          -> répartition au prorata.
STATEMENTS_STOCK = {"Bilan - Actif", "Bilan - Passif"}
STATEMENTS_FLUX = {"Compte de resultat", "Flux de tresorerie", "SIG"}

# --- Fichiers de sortie -------------------------------------------------------
OUT_UNIFIED = PROCESSED_DIR / "financials_unified.csv"
OUT_UNIFIED_PARQUET = PROCESSED_DIR / "financials_unified.parquet"
OUT_AUGMENTED = PROCESSED_DIR / "sfbt_augmented.csv"
OUT_FULL = PROCESSED_DIR / "financials_full.csv"          # unifié + augmenté
OUT_FULL_PARQUET = PROCESSED_DIR / "financials_full.parquet"

REPORT_VARIANTS = REPORTS_DIR / "rapport_variantes_indicateurs.csv"
REPORT_QUALITE = REPORTS_DIR / "rapport_qualite.md"
