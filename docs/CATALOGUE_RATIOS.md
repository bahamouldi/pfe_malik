# Catalogue des ratios financiers (MSI20000)

*Généré automatiquement depuis `src/ratios.py` — ne pas éditer à la main.*

> Les formules ont été reconstituées d'après les définitions financières standard et la table des matières MSI20000 (Malik n'ayant pas fourni les formules). À valider/ajuster avec lui si besoin.


**Hypothèses paramétrables** : coût du capital (EVA) = 8% ; TVA (crédits clients/fournisseurs) = 19%.


**Total : 43 ratios.**


## Solidité


### Liquidités

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `LIQ_GEN` | Ratio de liquidité générale | Actif courant / Dettes courantes | ratio (fois) | >1 : l'actif courant couvre les dettes à court terme. |
| `LIQ_RED` | Ratio de liquidité réduite | (Actif courant − Stocks) / Dettes courantes | ratio (fois) | Liquidité hors stocks (quick ratio). |
| `LIQ_IMM` | Ratio de liquidité immédiate | Liquidités / Dettes courantes | ratio (fois) | Capacité à payer immédiatement avec les disponibilités. |
| `INT_DEF_RED` | Intervalle défensif réduit | (Liquidités + Placements) / (Charges décaissables / 365) | jours | Nb de jours de charges couverts par les actifs très liquides. |
| `INT_DEF` | Intervalle défensif | (Liquidités + Placements + Clients) / (Charges décaissables / 365) | jours | Jours de charges couverts par actifs liquides + créances. |
| `RFR` | Ratio de fonds de roulement | (Capitaux permanents − Actif immobilisé) / Actif total × 100 | pourcentage | Fonds de roulement net en % de l'actif total. |
| `RBFR` | Ratio de besoin en fonds de roulement | (Stocks + Clients − Fournisseurs) / CA × 100 | pourcentage | BFR en % du chiffre d'affaires. |

### Gestion des actifs

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `LEV_ECO` | Ratio du levier économique | Actif total / Capitaux propres | ratio (fois) | Actif total rapporté aux capitaux propres. |
| `POIDS_IMMO` | Poids des immobilisations | Actif immobilisé / Actif total × 100 | pourcentage | Part de l'actif immobilisé dans l'actif total. |
| `FIN_IMMO` | Financement des immobilisations | Capitaux permanents / Actif immobilisé | ratio (fois) | >1 : les ressources stables financent les immobilisations. |
| `VETUSTE` | Vétusté de l'actif | Amortissements cumulés / Immobilisations brutes × 100 | pourcentage | Amortissements cumulés / immobilisations brutes (usure de l'outil). |

### Gestion des passifs

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `ENDET_GLOB` | Ratio d'endettement global | Dettes totales / Total passif × 100 | pourcentage | Part des dettes dans le total du passif. |
| `ENDET_TERME` | Ratio d'endettement à terme | Dettes non courantes / Capitaux propres × 100 | pourcentage | Dettes long terme / capitaux propres (gearing LT). |
| `INDEP_FIN` | Ratio d'indépendance financière | Capitaux propres / Total passif × 100 | pourcentage | Part des capitaux propres dans le financement total. |
| `COUV_CF` | Couverture des charges financières | Résultat d'exploitation / Charges financières | ratio (fois) | Résultat d'exploitation / charges financières (NaN si charges ~0). |
| `POIDS_CF` | Poids des charges financières | Charges financières / CA × 100 | pourcentage | Charges financières en % du CA. |
| `AUTO_FIN` | Ratio d'autonomie financière | Capitaux propres / Dettes totales | ratio (fois) | Capitaux propres / total des dettes. |
| `SOLVA` | Ratio de solvabilité | Actif total / Dettes totales | ratio (fois) | Actif total / total des dettes (capacité de remboursement). |

### Ressources humaines

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `EFF_BRUT_RH` | Efficacité brute des RH | Valeur ajoutée / Charges de personnel | ratio (fois) | Valeur ajoutée générée par dinar de charges de personnel. |
| `EFF_NET_RH` | Efficacité nette des RH | EBE / Charges de personnel | ratio (fois) | EBE par dinar de charges de personnel. |

### Gestion des risques

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `CONAN_HOLDER` | Score de Conan & Holder | 0,24·(EBE/Dettes) + 0,22·(Cap.perm/Actif) + 0,16·(Actif circ. hors stock/Actif) − 0,87·(Charges fin./CA) − 0,10·(Charges pers./VA) | score | Score de défaillance : >0,16 bon ; <0,04 risque élevé. |
| `RISQ_PLACEMENT` | Risque de placement | Placements / Actif total × 100 | pourcentage | Part des placements financiers dans l'actif. |
| `RISQ_COMMERCIAL` | Risque commercial | Clients / CA × 100 | pourcentage | Exposition clients rapportée au CA. |
| `CREDIT_FOURN` | Crédits moyens fournisseurs | Fournisseurs / (Achats × 1.19) × 365 | jours | Délai moyen de paiement des fournisseurs (jours, TTC). |
| `CREDIT_CLIENT` | Crédits moyens clients | Clients / (CA × 1.19) × 365 | jours | Délai moyen d'encaissement des clients (jours, TTC). |

## Performance


### Rentabilité commerciale

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `RENT_COM` | Rentabilité commerciale | Résultat d'exploitation / CA × 100 | pourcentage | Résultat d'exploitation / CA. |
| `MARGE_NETTE` | Ratio de la marge nette | Résultat net / CA × 100 | pourcentage | Résultat net / CA. |
| `TAUX_MARQUE` | Taux de marque | Marge sur coût matières / Production × 100 | pourcentage | Marge sur coût matières / production. |
| `ROT_CAP` | Rotation des capitaux échangés | CA / Capitaux propres | ratio (fois) | CA généré par dinar de capitaux propres. |

### Rentabilité économique

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `ROA` | Rendement de l'actif (ROA) | Résultat net / Actif total × 100 | pourcentage | Résultat net / actif total. |
| `ROCE` | Rentabilité du capital investi (ROCE) | Résultat d'exploitation / Capitaux permanents × 100 | pourcentage | Résultat d'exploitation / capitaux permanents. |
| `REND_IMMO` | Rendement brut des immobilisations | EBE / Actif immobilisé × 100 | pourcentage | EBE / actif immobilisé. |
| `REND_RES_STABLE` | Rendement brut des ressources stables | EBE / Capitaux permanents × 100 | pourcentage | EBE / capitaux permanents. |

### Rentabilité d'exploitation

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `MARGE_BRUTE_EXPL` | Marge brute d'exploitation | EBE / CA × 100 | pourcentage | EBE / CA. |
| `MARGE_BENEF_EXPL` | Marge bénéficiaire d'exploitation | Résultat d'exploitation / CA × 100 | pourcentage | Résultat d'exploitation / CA. |

### Rentabilité opérationnelle

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `REND_GLOBAL_NET` | Rendement global net | Résultat net / Total ressources × 100 | pourcentage | Résultat net / total des ressources. |
| `CREATION_VALEUR` | Création de valeur annuelle | Résultat d'exploitation − 8% × Capitaux permanents | montant (devise société) | EVA = Rés. exploitation − CMPC×capitaux permanents (CMPC=8%). |
| `REND_PRODUCTION` | Rendement de la production | Résultat d'exploitation / Production × 100 | pourcentage | Résultat d'exploitation / production. |
| `ROT_STOCKS` | Ratio de rotation des stocks | Achats consommés / Stocks | ratio (fois) | Nb de rotations des stocks dans l'année. |
| `PROFIT_OP` | Profit opérationnel | Résultat d'exploitation (montant) | montant (devise société) | Résultat d'exploitation (montant). |

### Rentabilité financière

| Code | Ratio | Formule | Unité | Interprétation |
|---|---|---|---|---|
| `ROE` | Rentabilité des capitaux propres (ROE) | Résultat net / Capitaux propres × 100 | pourcentage | Résultat net / capitaux propres. |
| `ROI` | Retour sur investissement (ROI) | Résultat net / Actif total × 100 | pourcentage | Résultat net / actif total. |
| `PERF_PLACEMENT` | Performance placement | Produits des placements / Placements × 100 | pourcentage | Produits des placements / placements. |

## Disponibilité par société

- **SFBT** : tous les ratios (états complets + SIG).
- **DELICE** : pas de SIG ni de stocks (holding) → ratios EBE/VA et stocks indisponibles. ⚠️ Marge nette > 100 % : normal, c'est une holding dont le résultat vient des dividendes, pas du CA opérationnel — à interpréter avec prudence dans le benchmark.
- **AB inBev / Coca-Cola** : ratios de structure et de rentabilité disponibles ; ratios nécessitant la VA ou les charges de personnel (efficacité RH, Conan & Holder) indisponibles (postes absents des sources).

## Limites connues

- **Charges financières** : la source ne donne pas le montant brut pour SFBT ; estimé par la part « charge » du résultat financier net (≈0 car SFBT a un résultat financier positif). Les ratios COUV_CF / POIDS_CF sont donc peu significatifs pour SFBT.
- **Création de valeur (EVA)** : dépend d'un coût du capital supposé (paramètre).
