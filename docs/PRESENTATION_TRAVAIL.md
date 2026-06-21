# Présentation du travail réalisé — à montrer à Malik

Ce document résume **ce qui a été fait**, **ce qu'il faut dire** et **ce qu'il
faut montrer**. Suis-le dans l'ordre pour présenter le projet.

---

## En une phrase (l'accroche)

> « J'ai construit toute la chaîne de traitement : à partir des fichiers Excel
> bruts, le projet nettoie les données, calcule les 46 ratios de ton référentiel,
> donne un score global /100, compare SFBT aux concurrents et prévoit les valeurs
> futures — le tout testé et documenté. Il ne reste que le montage Power BI. »

---

## Ce qui est livré (vue d'ensemble)

| # | Partie | État |
|---|---|---|
| 1 | Nettoyage + unification des 4 sociétés | ✅ |
| 2 | Augmentation trimestrielle (Mars/Septembre) | ✅ |
| 3 | 46 ratios financiers (ton référentiel officiel) | ✅ |
| 4 | Score Global de Performance Industrielle (SGPI /100) | ✅ |
| 5 | Benchmark SFBT vs DELICE / AB InBev / Coca-Cola | ✅ |
| 6 | Data Warehouse (base SQL en étoile) | ✅ |
| 7 | Machine Learning (2 modèles de prévision) | ✅ |
| 8 | Tests automatiques (70) + documentation | ✅ |
| 9 | Dashboards Power BI | ⏳ à venir |

---

## Déroulé de présentation (5 points)

### 1️⃣ Les données — « j'ai tout unifié et fiabilisé »
**Dire :** « Les 4 fichiers avaient des formats différents (langues, devises,
libellés). Je les ai unifiés en un seul jeu propre. J'ai même corrigé des erreurs
de la source — par exemple le bilan 2019 qui contenait par erreur les chiffres de
2018. »
**Montrer :** `data/processed/financials_unified.csv` + le rapport
`data/reports/rapport_qualite.md`.

### 2️⃣ L'augmentation — « j'ai créé les trimestres manquants »
**Dire :** « SFBT ne publie que juin et décembre. J'ai généré mars et septembre
par estimation, en distinguant les postes de bilan (interpolation) et les flux
(répartition au prorata). »
**Montrer :** `data/processed/sfbt_augmented.csv` + `docs/METHODE_AUGMENTATION.md`.

### 3️⃣ Les ratios + le score — « tes formules, appliquées et notées »
**Dire :** « J'ai implémenté exactement les 46 formules de ton référentiel, avec
les benchmarks industriels et le système de notation. À la fin, chaque société a
un Score Global de Performance Industrielle sur 100. SFBT obtient 83,5/100, devant
les concurrents. »
**Montrer :** le PDF **`docs/Rapport_Ratios_SFBT.pdf`** (LE document à présenter —
ratios, valeurs, benchmarks, page SGPI, lecture financière).

### 4️⃣ Le benchmark — « SFBT face aux géants »
**Dire :** « On compare SFBT à DELICE, AB InBev et Coca-Cola. SFBT est très
liquide, peu endettée et plus rentable — une structure financière très solide. »
**Montrer :** la section Benchmark du PDF.

### 5️⃣ La prévision (ML) — « j'ai comparé 2 modèles »
**Dire :** « J'ai entraîné une Régression linéaire et un Random Forest pour
prévoir les valeurs futures (CA, résultat net, actifs). On compare avec des
métriques (R², MAPE). La Régression linéaire gagne, avec une précision de 85-96 %. »
**Montrer :** `data/processed/ml_metrics.csv` + `docs/MODELES_ML.md`.

---

## La démonstration "qui impressionne" (optionnel mais fort)

Sur ton PC, dans le dossier du projet :

```bash
cd src
python3 run_all.py        # lance TOUTE la chaîne (6 étapes) en direct
python3 test_pipeline.py  # affiche 70 tests ✔ — prouve que tout marche
```

**Dire :** « Tout est automatisé : une commande régénère tout. Et j'ai 70 tests
qui vérifient que chaque calcul est exact — y compris contre les vrais chiffres
publics de Coca-Cola et AB InBev. »

---

## Ce qu'il faut assumer (honnêteté = crédibilité)

- **SFBT 2021 et 2022 (annuel)** : absents du fichier source → ratios non
  calculables ces 2 années. *« Il me faudrait les états financiers annuels 2021
  et 2022 pour compléter. »*
- **Bilan 2017-2019** : léger défaut dans la source (colonnes décalées), signalé.
- **Ratios par salarié** : non calculables (l'effectif n'est pas dans les données).

---

## Le projet en chiffres (pour conclure)

- **4 sociétés**, **2005 → 2025**
- **10 124 lignes** de données (réel + estimé)
- **46 ratios** + **SGPI /100**
- **2 modèles** de prévision comparés
- **70 tests** automatiques, **0 échec**
- Code + données + docs sur **GitHub**

> « Tout est versionné sur GitHub, documenté, et testé. Le seul morceau restant,
> c'est la mise en forme visuelle dans Power BI. »
