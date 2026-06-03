# Dictionnaire de données

Jeu de données unifié des états financiers (4 sociétés), format **long / tidy** :
une ligne = une valeur d'un indicateur, pour une société, à une date.

Fichiers : `data/processed/financials_unified.csv` (réel) et
`financials_full.csv` (réel + estimé).

## Colonnes

| Colonne | Type | Description | Valeurs / Exemple |
|---|---|---|---|
| `Societe` | texte | Société émettrice | `SFBT`, `DELICE`, `AB inBev`, `Coca-Cola` |
| `Statement` | catégorie | État financier | voir § *États* |
| `Indicateur` | texte | Libellé lisible, nettoyé (variante canonique retenue) | `Total des actifs` |
| `Indicateur_raw` | texte | Libellé brut d'origine (traçabilité du nettoyage) | `Total\xa0des\xa0actifs` |
| `Cle_indicateur` | texte | Clé normalisée (minuscule, sans accent ni espace) — **clé de jointure** des séries temporelles | `totaldesactifs` |
| `Date` | date | Date de clôture (fin de période) | `2024-12-31` |
| `Annee` | entier | Année de clôture | `2024` |
| `Periode` | catégorie | Période cumulée | `T1` (mars), `S1` (juin), `9M` (sept.), `FY` (déc.) |
| `Valeur` | décimal | Montant **dans la devise/échelle de la société** | `1281772834.0` |
| `Occurrence` | entier | `1` = série unique ; `>1` = collision de libellé non désambiguïsée | `1` |
| `Devise` | catégorie | Devise du montant | `TND`, `USD` |
| `Echelle` | catégorie | Échelle du montant | `unite` (montant brut), `million` |
| `Type_donnee` | catégorie | Origine de la valeur | `Reel`, `Estime` |
| `Source` | texte | Fichier / procédé d'origine | `SFBT_beta1.xlsx` |

## États (`Statement`)

| Valeur | Signification | Nature | Sociétés |
|---|---|---|---|
| `Bilan - Actif` | Actif du bilan | stock | SFBT |
| `Bilan - Passif` | Capitaux propres & passifs | stock | SFBT |
| `Bilan` | Bilan non scindé actif/passif | stock | DELICE |
| `Compte de resultat` | Compte de résultat | flux | SFBT, DELICE |
| `Flux de tresorerie` | Tableau des flux de trésorerie | flux* | SFBT, DELICE |
| `SIG` | Soldes intermédiaires de gestion | flux | SFBT |
| `Inconnu` | État non labellisé dans la source | — | AB inBev, Coca-Cola |

\* Sauf les soldes de trésorerie (clôture/début), de nature *stock*.

> **AB inBev / Coca-Cola** : les fichiers sources ne distinguent pas les états ;
> `Statement = Inconnu`. Un même libellé peut alors apparaître dans plusieurs
> états (d'où des collisions). Une re-labellisation sera nécessaire avant de
> calculer leurs ratios (cf. `data/reports/rapport_collisions.csv`).

## Conventions de période

`Periode` est dérivée du mois de clôture (comparable entre sociétés) :

| Mois clôture | `Periode` | Sens |
|---|---|---|
| 03 | `T1` | cumul 3 mois (1er trimestre) |
| 06 | `S1` | cumul 6 mois (1er semestre) |
| 09 | `9M` | cumul 9 mois |
| 12 | `FY` | exercice complet (*full year*) |

Les sociétés de benchmark ne publient qu'au 31/12 → `Periode = FY`.

## Devises et échelles

Les montants **ne sont pas convertis** : ils restent dans leur devise/échelle
d'origine. Les **ratios** (sans dimension) sont directement comparables ; toute
comparaison de **montants absolus** entre sociétés doit d'abord homogénéiser
devise et échelle.
