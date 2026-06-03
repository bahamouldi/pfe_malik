# Data Warehouse — Schéma en étoile

Base : `data/warehouse/sfbt_dw.sqlite` (SQLite, interrogeable en SQL).
DDL complet : `data/warehouse/schema_etoile.sql`. Construit par
`src/build_warehouse.py`.

## Modèle dimensionnel

```
                          Dim_Temps
                              │
   Dim_Societe ── Fait_Etats_Financiers ── Dim_Indicateur
                              │
   Dim_Societe ──     Fait_Ratios     ──   Dim_Ratio
                              │
                          Dim_Temps
```

Deux tables de faits partagent les dimensions conformes **Dim_Societe** et
**Dim_Temps** (schéma en étoile classique, *conformed dimensions*).

## Tables de faits

### `Fait_Etats_Financiers` (≈10 100 lignes)
Granularité : 1 ligne = une valeur comptable (société × date × indicateur).
| Colonne | Description |
|---|---|
| `id_societe`, `id_temps`, `id_indicateur` | clés étrangères vers les dimensions |
| `valeur` | montant (devise/échelle de la société) |
| `type_donnee` | `Reel` ou `Estime` (trimestres générés) |
| `occurrence` | 1 = série unique ; >1 = collision conservée |

### `Fait_Ratios` (≈3 750 lignes)
Granularité : 1 ligne = un ratio (société × date × ratio).
| Colonne | Description |
|---|---|
| `id_societe`, `id_temps`, `id_ratio` | clés étrangères |
| `valeur` | valeur du ratio (unité selon `Dim_Ratio.unite`) |

## Dimensions

| Dimension | Clé | Attributs |
|---|---|---|
| `Dim_Societe` | `id_societe` | societe, role (principale/benchmark), secteur, devise, echelle |
| `Dim_Temps` | `id_temps` | date, annee, mois, periode (T1/S1/9M/FY), type_cloture |
| `Dim_Indicateur` | `id_indicateur` | cle, libelle, statement, nature (stock/flux) |
| `Dim_Ratio` | `id_ratio` | code_ratio, ratio, categorie, sous_categorie, unite |

## Vues prêtes à l'emploi

- **`v_ratios`** : ratios « aplatis » avec société, temps et libellés — idéale
  pour Power BI et le benchmark.
- **`v_etats`** : valeurs comptables aplaties (avec nature stock/flux et
  type réel/estimé).

### Exemples de requêtes

```sql
-- Benchmark : marge nette FY 2024
SELECT societe, valeur FROM v_ratios
WHERE code_ratio='MARGE_NETTE' AND annee=2024 AND periode='FY'
ORDER BY valeur DESC;

-- Évolution trimestrielle du CA de SFBT (réel + estimé)
SELECT periode, valeur, type_donnee FROM v_etats
WHERE societe='SFBT' AND cle='revenus' AND annee=2024 ORDER BY date;

-- Tous les ratios de solidité de SFBT en 2023
SELECT sous_categorie, ratio, valeur, unite FROM v_ratios
WHERE societe='SFBT' AND categorie='Solidité' AND annee=2023 AND periode='FY';
```

## Connexion depuis Power BI

Power BI lit nativement les fichiers CSV/Parquet de `data/processed/`. Pour le
DW SQLite, utiliser le connecteur ODBC SQLite, **ou** (plus simple) importer
directement `ratios.csv`, `financials_full.csv` et reconstituer les relations
en suivant ce schéma. Les `Dim_*` deviennent des tables de dimension et les
`Fait_*` des tables de faits dans le modèle Power BI.
