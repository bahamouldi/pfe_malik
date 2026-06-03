# Plateforme d'Analyse Financière SFBT — Préparation des données

Projet de fin d'études : analyse financière décisionnelle de **SFBT** avec
**benchmark** sectoriel (DELICE, AB InBev, Coca-Cola), calcul de ratios
(référentiel MSI20000), dashboards Power BI et prévision (Machine Learning).

Ce dépôt couvre la **première brique** : *collecte → nettoyage → unification →
augmentation* des données, conformément au `docs/Cahier_des_Charges_SFBT.docx`.

> ℹ️ Deux cahiers des charges existaient. On suit **SFBT** (analyse financière),
> pas STAROIL (BI commerciale Sage X3) qui ne correspond pas aux données reçues.
> Le second est conservé dans `docs/` pour mémoire.

## Sources (4 sociétés)

| Société   | Rôle        | Période     | Fréquence            | Devise / Échelle |
|-----------|-------------|-------------|----------------------|------------------|
| **SFBT**  | principale  | 2005–2025   | semestriel + annuel  | TND (dinars)     |
| DELICE    | benchmark   | 2015–2025   | annuel               | TND (dinars)     |
| AB InBev  | benchmark   | 2015–2025   | annuel               | USD (millions)   |
| Coca-Cola | benchmark   | 2015–2025   | annuel               | USD (millions)   |

> Les **ratios** étant sans dimension, ils sont comparables entre sociétés ; les
> **montants absolus** ne le sont pas (devises/échelles différentes) — d'où les
> colonnes `Devise` et `Echelle` dans le schéma.

## Arborescence

```
pfe_malik/
├── data/
│   ├── raw/            # fichiers sources d'origine (non modifiés)
│   ├── processed/      # sorties propres
│   │   ├── financials_unified.csv/.parquet   # 4 sociétés unifiées (réel)
│   │   ├── sfbt_augmented.csv                 # lignes estimées T1/9M (SFBT)
│   │   └── financials_full.csv/.parquet       # réel + estimé (jeu final)
│   └── reports/        # rapports qualité / variantes / collisions
├── docs/               # cahiers des charges + documentation technique
│   └── warehouse/      # Data Warehouse en étoile
│       ├── sfbt_dw.sqlite                     # base SQL interrogeable
│       └── schema_etoile.sql                  # DDL du schéma
├── docs/               # cahiers des charges + documentation technique
└── src/
    ├── config.py          # métadonnées sociétés, schéma cible, vocab. états
    ├── normalize.py       # normalisation des libellés + clé canonique
    ├── unify.py           # unification des 4 sources -> schéma unique
    ├── augment.py         # augmentation trimestrielle SFBT (Mars/Septembre)
    ├── quality_report.py  # rapport de qualité reproductible
    ├── ratios.py          # 43 ratios MSI20000 (4 sociétés)
    ├── build_warehouse.py # construction du Data Warehouse étoile (SQLite)
    ├── gen_catalogue_ratios.py # génère docs/CATALOGUE_RATIOS.md
    └── run_all.py         # exécute toute la chaîne
```

## Exécution

```bash
pip install -r requirements.txt
cd src && python3 run_all.py    # unify -> augment -> qualité -> ratios -> DW
```

Ou étape par étape : `unify.py`, `augment.py`, `quality_report.py`, `ratios.py`,
`build_warehouse.py`.

## Schéma unifié (format long / *tidy*)

| Colonne | Description |
|---|---|
| `Societe` | SFBT / DELICE / AB inBev / Coca-Cola |
| `Statement` | Bilan, Bilan - Actif, Bilan - Passif, Compte de resultat, Flux de tresorerie, SIG, Inconnu |
| `Indicateur` | libellé lisible (variante canonique) |
| `Indicateur_raw` | libellé brut d'origine (traçabilité) |
| `Cle_indicateur` | clé normalisée (jointure des séries temporelles) |
| `Date` | date de clôture (fin de période) |
| `Annee`, `Periode` | année ; T1 / S1 / 9M / FY |
| `Valeur` | montant (dans la devise/échelle de la société) |
| `Occurrence` | 1 = série unique ; >1 = collision non résolue (cf. rapport) |
| `Devise`, `Echelle` | TND/USD ; unite/million |
| `Type_donnee` | **Reel** ou **Estime** (augmentation) |
| `Source` | fichier d'origine |

Détails : `docs/DICTIONNAIRE_DONNEES.md`. Méthode d'augmentation :
`docs/METHODE_AUGMENTATION.md`. Constats d'audit : `docs/AUDIT_DONNEES.md`.

## État d'avancement

- ✅ Collecte, nettoyage, unification des 4 sources.
- ✅ Augmentation trimestrielle SFBT (Mars/Septembre).
- ✅ **43 ratios MSI20000** calculés (4 sociétés) — voir `docs/CATALOGUE_RATIOS.md`.
- ✅ **Data Warehouse** en schéma étoile (SQLite) — voir `docs/SCHEMA_ETOILE.md`.
- ✅ **Machine Learning** : Régression linéaire vs Random Forest (prévision) — voir `docs/MODELES_ML.md`.
- ⏳ **Dashboards Power BI** + benchmark (données + ratios prêts ; montage dans l'appli).
