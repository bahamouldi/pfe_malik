# Catalogue des ratios financiers

*Généré automatiquement depuis `src/ratios.py`.*

> Formules conformes au **référentiel officiel fourni par Malik** (MSI20000 / Référentiel Industriel Normalisé).


**Total : 46 ratios** + Score Global de Performance Industrielle (SGPI /100).


## Gestion des liquidités


### Liquidités

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `LIQ_GEN` | Ratio de liquidité générale | Actifs courants / Passifs courants | ratio (×) | 1,5 à 2,0 | Capacité à couvrir les dettes court terme. |
| `LIQ_RED` | Ratio de liquidité réduite | (Actifs courants − Stocks) / Passifs courants | ratio (×) | 0,9 à 1,2 | Sans vendre les stocks. |
| `LIQ_IMM` | Ratio de liquidité immédiate | Liquidités / Passifs courants | ratio (×) | 0,30 à 0,80 | Couverture immédiate des dettes exigibles. |
| `INT_DEF_RED` | Intervalle défensif réduit | Liquidités / ((Charges d'exploitation − Dotations) / 365) | jours | — | Jours de charges couverts par les liquidités. |
| `INT_DEF` | Intervalle défensif | (Liquidités + Clients nets) / ((Charges d'exploitation − Dotations) / 365) | jours | — | Jours couverts par liquidités + clients. |

### Fonds de roulement

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `FR` | Fonds de roulement (FR) | Ressources stables − Actifs immobilisés | montant (devise société) | positif | Ressources stables − actifs immobilisés (doit être positif). |
| `COUV_IMMO` | Couverture des immobilisations | Ressources stables / Actifs immobilisés | ratio (×) | 1,2 à 1,5 | Financement durable des investissements. |
| `BFR` | Besoin en fonds de roulement (BFR) | Stocks nets + Clients nets − Fournisseurs | montant (devise société) | — | Stocks nets + clients nets − fournisseurs. |
| `BFR_JOURS` | Ratio BFR (jours de CA) | BFR / (Revenus / 365) | jours | 30 à 60 j | Jours de CA immobilisés dans l'exploitation. |

## Gestion des actifs


### Gestion des actifs

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `LEV_ECO` | Ratio du levier économique | Total Actifs / Capitaux propres | ratio (×) | 2 à 3 | Financement des actifs par les capitaux propres. |
| `POIDS_IMMO` | Poids des immobilisations | Actifs immobilisés / Total Actifs × 100 | pourcentage | 45 % à 65 % | Part des investissements durables. |
| `VETUSTE` | Vétusté des immobilisations corporelles | Amortissements corporels / Immobilisations corporelles × 100 | pourcentage | 30 % à 60 % | Âge économique du parc industriel. |

## Gestion des passifs


### Structure financière

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `ENDET_GLOB` | Ratio d'endettement global | Total Dettes / Total Actifs × 100 | pourcentage | 40 % à 60 % | Part des actifs financés par la dette. |
| `ENDET_TERME` | Ratio d'endettement à terme | Dettes long terme / Capitaux propres × 100 | pourcentage | — | Dettes long terme / capitaux propres. |
| `INDEP_FIN` | Indépendance financière | Capitaux propres / Total Dettes | ratio (×) | — | Capitaux propres / total des dettes. |
| `AUTO_FIN` | Autonomie financière | Capitaux propres / Total Actifs × 100 | pourcentage | 35 % à 50 % | Capacité de financement autonome. |
| `SOLVA` | Solvabilité | Total Actifs / Total Dettes | ratio (×) | 1,5 à 2 | Capacité théorique à rembourser les dettes. |

## Ressources humaines


### Productivité RH

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `EFF_BRUT_RH` | Efficacité brute des RH | Revenus / Charges de personnel | ratio (×) | — | Revenus / charges de personnel. |
| `EFF_NET_RH` | Efficacité nette des RH | Résultat net / Charges de personnel | ratio (×) | — | Résultat net / charges de personnel. |

## Gestion des risques


### Gestion des risques

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `RISQ_PLACEMENT` | Risque de placement | Placements / Actifs courants × 100 | pourcentage | — | Placements / actifs courants. |
| `RISQ_COMMERCIAL` | Risque commercial | Clients bruts / Revenus × 100 | pourcentage | — | Clients bruts / revenus. |
| `CREDIT_CLIENT` | Crédit moyen clients | Clients bruts / (Revenus / 365) | jours | — | Clients bruts / (revenus / 365). |
| `CREDIT_FOURN` | Crédit moyen fournisseurs | Fournisseurs / (Achats consommés / 365) | jours | — | Fournisseurs / (achats consommés / 365). |
| `CONAN_HOLDER` | Score de Conan & Holder | 0,24·(AC−Stocks)/TA + 0,22·(RN/TA) + 0,16·(Rev/TA) − 0,87·(Ch.pers/TA) − 0,10·(Dettes LT/TA) | score | — | Score de défaillance (formule MSI : > 0,16 = sain). |

## Rentabilité


### Rentabilité commerciale

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `RENT_COM` | Rentabilité commerciale | Résultat d'exploitation / Revenus × 100 | pourcentage | — | Résultat d'exploitation / revenus. |
| `MARGE_NETTE` | Marge nette | Résultat net / Revenus × 100 | pourcentage | — | Résultat net / revenus. |
| `ROT_CAP` | Rotation des capitaux | Revenus / Total Actifs | ratio (×) | — | Revenus / total actifs. |

### Rentabilité économique

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `ROA` | Rendement de l'actif (ROA) | Résultat d'exploitation / Total Actifs × 100 | pourcentage | 5 % à 10 % | Résultat d'exploitation / total actifs. |
| `ROCE` | Rentabilité du capital investi (ROCE) | Résultat d'exploitation / Ressources stables × 100 | pourcentage | 10 % à 15 % | Résultat d'exploitation / ressources stables. |
| `REND_IMMO` | Rendement brut des immobilisations | EBE / Actifs immobilisés × 100 | pourcentage | — | EBE / actifs immobilisés. |
| `REND_RES_STABLE` | Rendement brut des ressources stables | EBE / Ressources stables × 100 | pourcentage | — | EBE / ressources stables. |

### Rentabilité d'exploitation

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `MARGE_BRUTE_EXPL` | Marge brute d'exploitation | EBE / Revenus × 100 | pourcentage | — | EBE / revenus. |
| `MARGE_BENEF_EXPL` | Marge bénéficiaire d'exploitation | Résultat d'exploitation / Revenus × 100 | pourcentage | — | Résultat d'exploitation / revenus. |

### Rentabilité opérationnelle

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `REND_PRODUCTION` | Rendement de la production | Résultat d'exploitation / Production × 100 | pourcentage | — | Résultat d'exploitation / production. |
| `ROT_STOCKS` | Rotation des stocks | Achats consommés / Stocks | ratio (×) | — | Achats consommés / stocks. |
| `PROFIT_OP` | Profit opérationnel | Résultat d'exploitation | montant (devise société) | — | Résultat d'exploitation (montant). |
| `CREATION_VALEUR` | Création de valeur annuelle | Valeur Ajoutée | montant (devise société) | — | Valeur ajoutée. |

### Rentabilité financière

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `ROE` | Rentabilité des capitaux propres (ROE) | Résultat net / Capitaux propres × 100 | pourcentage | 10 % à 15 % | Résultat net / capitaux propres. |
| `PERF_PLACEMENT` | Performance des placements | Produits des placements / Placements × 100 | pourcentage | — | Produits des placements / placements. |
| `ROI` | Retour sur investissement (ROI) | Résultat net / Ressources stables × 100 | pourcentage | — | Résultat net / ressources stables. |

## Cycle d'exploitation


### Cycle d'exploitation

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `DSO` | Délai moyen de recouvrement clients (DSO) | Clients / (Revenus / 365) | jours | 30 à 60 j | Clients / (CA / 365). |
| `DPO` | Délai moyen de paiement fournisseurs (DPO) | Fournisseurs / (Achats consommés / 365) | jours | 45 à 75 j | Fournisseurs / (achats / 365). |
| `DIO` | Durée moyenne de stockage (DIO) | Stocks / (Achats consommés / 365) | jours | 45 à 90 j | Stocks / (achats / 365). |

## Indicateurs complémentaires


### Complémentaires

| Code | Ratio | Formule | Unité | Benchmark | Interprétation |
|---|---|---|---|---|---|
| `TRESO_NETTE` | Trésorerie nette | Liquidités − Concours bancaires | montant (devise société) | — | Liquidités − concours bancaires. |
| `TAUX_VA` | Taux de valeur ajoutée | Valeur Ajoutée / Revenus × 100 | pourcentage | — | Valeur ajoutée / revenus. |
| `PART_PERSO_VA` | Part du personnel dans la VA | Charges de personnel / Valeur Ajoutée × 100 | pourcentage | — | Charges de personnel / valeur ajoutée. |

## Score Global de Performance Industrielle (SGPI /100)

Chaque ratio clé reçoit une **note 0-5** selon des grilles de benchmark. Le SGPI est la moyenne pondérée des catégories :

| Catégorie | Poids | Ratios notés |
|---|---|---|
| Liquidité | 15% | LIQ_GEN, LIQ_RED, LIQ_IMM, FR |
| Structure financière | 20% | COUV_IMMO, ENDET_GLOB, AUTO_FIN, SOLVA |
| Gestion des actifs | 15% | LEV_ECO, POIDS_IMMO, VETUSTE |
| Gestion des risques | 10% | CONAN_HOLDER |
| Rentabilité | 25% | ROA, ROCE, ROE |
| Productivité RH | 5% | EFF_NET_RH |
| Cycle d'exploitation | 10% | BFR_JOURS, DSO, DPO, DIO |

> Note catégorie = moyenne des notes /5 ; SGPI = Σ (note/5 × poids) × 100. Si une catégorie manque (benchmark incomplet), les poids sont renormalisés.


## Disponibilité par société

- **SFBT** : tous les ratios + SGPI complet (couverture 100 %).
- **DELICE** : holding (pas de SIG/stocks) → certains ratios indisponibles ; marge distordue (revenus = dividendes).
- **AB inBev / Coca-Cola** : ratios de structure et rentabilité disponibles ; RH (charges de personnel) absentes → efficacité RH et part personnel indisponibles.

## Limites connues

- **Ratios par salarié** (VA/salarié, RN/salarié) : non calculés — l'effectif (nombre d'employés) n'est pas fourni dans les données.
- **SFBT 2021 et 2022 (annuel)** : données absentes de la source → ratios non calculables ces années.
