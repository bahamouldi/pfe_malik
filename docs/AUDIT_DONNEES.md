# Audit des données sources

Constats relevés lors de l'analyse des 4 fichiers reçus (29/05/2026). Ils
justifient les choix de nettoyage du pipeline (`src/`).

## 1. Structure des fichiers

| Fichier | Société | Format | Particularité |
|---|---|---|---|
| `SFBT_beta1.xlsx` | SFBT | 5 feuilles | `Feuil1` = **maîtresse** (tous les états empilés) ; `Feuil2-4` = extraits par état (redondants) ; `Feuil5` = SIG |
| `DELICE_Clean.xlsx` | DELICE | 1 feuille | déjà en long, colonnes `Statement/Indicateur/Date/Year/Period/Valeur` |
| `AB_inBev_Clean.xlsx` | AB InBev | 1 feuille | même schéma **mais `Statement` vide** ; `Date` = année entière |
| `Coca_Cola.xlsx` | Coca-Cola | 1 feuille | libellés **en anglais**, colonne `Société` **vide**, pas de `Statement` ni `Period` |

**Décision** : pour SFBT, on exploite `Feuil1` (reclassée par découpage
positionnel en Actif → Passif → Résultat → Flux) + `Feuil5` pour les SIG.
`Feuil2-4` sont ignorées (sous-ensembles de `Feuil1`).

## 2. Variantes de libellés (SFBT)

Le même concept est écrit de multiples façons : espaces insécables (`\xa0`),
retours ligne, doubles espaces, accents incohérents (`aprés`/`après`),
astérisques de note (`(*)`, `*`), abréviations (`réinvestis.` / `réinvestissements`).
Exemple : **« Résultat net de l'exercice » apparaît en ~15 variantes**.

**Décision** : double traitement —
1. `clean_label()` pour l'affichage (retire le bruit, garde accents/casse) ;
2. `cle_indicateur()` agressive (minuscule, sans accent ni ponctuation) comme
   **clé de regroupement** ; fusionne mécaniquement la majorité des variantes.
3. dictionnaire d'**alias curé** (`normalize.ALIAS`) pour les abréviations
   divergentes restantes (à enrichir avec Malik).

Rapport : `data/reports/rapport_variantes_indicateurs.csv`.

## 3. Colonnes comparatives recopiées (SFBT, 2019)

Les états annuels présentent souvent 2 colonnes (N et N-1). Au 31/12/2019,
**l'actif entier était dupliqué avec les valeurs de 2018** (ex. Total des actifs
= 914 M€ identique à 2018, alors que la vraie valeur 2019 ≈ 795 M).

**Décision** : un *résolveur de fuites comparatives* (`unify._resoudre_fuites_
comparatives`) supprime, parmi les collisions, toute valeur **égale à celle de
l'année N-1** (même période) au profit de la vraie valeur de l'exercice.
→ **21 valeurs erronées corrigées** pour 2019.

## 4. Collisions résiduelles (libellés ambigus)

Après nettoyage, certains `(Société, État, Indicateur, Date)` portent encore
plusieurs valeurs :

- **SFBT (9)** : « résultat avant/après affectation », conventions de signe sur
  l'incidence des taux de change. → **conservées** (`Occurrence > 1`), à trancher
  métier.
- **AB inBev (≈154)** : conséquence directe de l'absence de `Statement` (même
  libellé dans bilan/résultat/flux/OCI). → re-labellisation requise avant ratios.
- **DELICE (≈58)**, **Coca-Cola (≈21)** : doublons sources / sous-postes répétés.

Rapport : `data/reports/rapport_collisions.csv`.

## 5. Devises et échelles hétérogènes

- SFBT, DELICE : **TND**, montants bruts (`unite`).
- AB InBev, Coca-Cola : **USD**, en **millions**.

**Décision** : conserver les montants tels quels + métadonnées `Devise`/`Echelle`.
Les **ratios** restent comparables (sans dimension) ; ne jamais comparer les
montants absolus sans homogénéisation.

## 6. Contrôles de cohérence (validation)

- **Équilibre du bilan SFBT** (Actif = Passif) : écart **0,00 %** sur la grande
  majorité des dates → la séparation Actif/Passif est correcte.
  - **Exceptions à recaler depuis les rapports d'origine** : **2017, 2018, 2019**
    présentent un déséquilibre de 12–15 % car, dans le fichier source, les
    colonnes Actif et Passif sont **décalées d'un an** (les montants 795,58 M et
    914,28 M sont permutés entre années). 2009-06-30 : écart mineur de 1 %
    (collision de sous-totaux). Ces cas sont listés dans `rapport_qualite.md`
    et **ne sont pas corrigés automatiquement** (valeurs vraies indéterminables
    sans les états financiers PDF).
- **Couverture** : SFBT 41 dates (2005–2025, juin+déc) pour Actif/Passif/Résultat/
  Flux ; SIG sur 14 dates (2012–2025).
- **Complétude** : ~4,3 % de valeurs manquantes (cellules non numériques en source).

Rapport de synthèse reproductible : `data/reports/rapport_qualite.md`.
