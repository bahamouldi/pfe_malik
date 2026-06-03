# Rapport de qualité des données

*Généré automatiquement par `src/quality_report.py`.*

## 1. Volumétrie

| Societe   |   Lignes |   Indicateurs |   Dates |   Annee_min |   Annee_max | Devise   | Echelle   |
|:----------|---------:|--------------:|--------:|------------:|------------:|:---------|:----------|
| AB inBev  |     1228 |           278 |      11 |        2015 |        2025 | USD      | million   |
| Coca-Cola |     1005 |           140 |      11 |        2015 |        2025 | USD      | million   |
| DELICE    |      592 |            65 |      11 |        2015 |        2025 | TND      | unite     |
| SFBT      |     3979 |           206 |      41 |        2005 |        2025 | TND      | unite     |

## 2. Couverture par état financier

| Statement          |   AB inBev |   Coca-Cola |   DELICE |   SFBT |
|:-------------------|-----------:|------------:|---------:|-------:|
| Bilan              |          0 |           0 |      290 |      0 |
| Bilan - Actif      |          0 |           0 |        0 |   1059 |
| Bilan - Passif     |          0 |           0 |        0 |    672 |
| Compte de resultat |          0 |           0 |      166 |    811 |
| Flux de tresorerie |          0 |           0 |      136 |    929 |
| Inconnu            |       1228 |         952 |        0 |      0 |
| SIG                |          0 |           0 |        0 |    272 |

## 3. Complétude

- Valeurs manquantes (`Valeur` nulle) : **289** / 6804 (4.25 %).

## 4. Collisions résiduelles (à valider métier)

| Societe   |   Groupes_ambigus |
|:----------|------------------:|
| AB inBev  |               154 |
| Coca-Cola |                21 |
| DELICE    |                58 |
| SFBT      |                 9 |

> Une *collision* = un même (Société, État, Indicateur, Date) porte plusieurs valeurs distinctes. Pour SFBT il s'agit surtout de « résultat avant/après affectation » et de conventions de signe ; pour AB inBev, du fait que le fichier source ne distingue pas les états (même libellé dans bilan/résultat/flux). Voir `rapport_collisions.csv`.

## 5. Contrôle d'équilibre du bilan SFBT

- Dates contrôlées : 41 ; écarts |Actif−Passif| > 0,5 % : **4**.

- **Dates en déséquilibre (défaut de la source à corriger sur les états financiers d'origine)** :

| Date                |   Valeur_actif |   Valeur_passif |   Ecart_% |
|:--------------------|---------------:|----------------:|----------:|
| 2009-06-30 00:00:00 |    2.83556e+08 |     2.86562e+08 |    -1.06  |
| 2017-12-31 00:00:00 |    7.95584e+08 |     6.98155e+08 |    12.246 |
| 2018-12-31 00:00:00 |    9.14278e+08 |     7.95584e+08 |    12.982 |
| 2019-12-31 00:00:00 |    7.95584e+08 |     9.14278e+08 |   -14.919 |

> ⚠️ 2017–2019 : les colonnes Actif/Passif sont décalées d'un an dans le fichier source (mêmes montants 795,58 M / 914,28 M permutés entre années). À recaler manuellement à partir des rapports annuels SFBT.

## 6. Augmentation trimestrielle (SFBT)

- Lignes estimées : **3320** (T1=1755, 9M=1565).

- Plage : 2005-03-31 → 2025-03-31.
