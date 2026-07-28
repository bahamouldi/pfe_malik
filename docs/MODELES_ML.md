# Modèles de prévision (Machine Learning)

Prévision des valeurs financières de SFBT. **Trois modèles comparés** (choix de
Malik) : **Régression linéaire** (baseline simple, interprétable),
**Random Forest** (ML robuste, non-linéaire) et **Arbre de décision** (modèle
interprétable, élagué). Code : `src/ml_forecast.py`.

## Indicateurs prévus
Revenus (CA), Total des actifs, Capitaux propres, Résultat net — séries
trimestrielles ~2005→2025 (réel + trimestres estimés).

## Démarche

1. **Cible = taux de croissance** `r_t = V_t / V_{t-1}` (et non le niveau brut).
   > Point méthodologique clé : sur une série qui croît, un modèle à base
   > d'arbres **ne sait pas extrapoler** le niveau (les arbres plafonnent à la
   > valeur max vue en entraînement → R² négatif). En modélisant un taux
   > quasi-stationnaire, les modèles deviennent comparables et performants. Le
   > niveau est reconstruit : `V̂_t = V_{t-1} × r̂_t`. C'est l'approche standard
   > en finance (on modélise les *rendements*, pas les *niveaux*).
2. **Variables explicatives** : tendance (index temps), retards du taux
   (`r_{t-1..t-4}`), saisonnalité (période T1/S1/9M/FY en one-hot).
3. **Découpage temporel** 75 % / 25 % (sans mélange) : on prédit des clôtures
   postérieures jamais vues.
4. **Métriques** : MAE, RMSE, MAPE (%), R².
5. **Deux régimes d'évaluation** (voir section dédiée) : à 1 pas d'avance, et
   par horizon en mode récursif.
6. **Prévision future récursive** : 4 prochaines clôtures.

## Modèles retenus

| Modèle | Configuration | Rôle |
|---|---|---|
| Régression linéaire | — | Baseline interprétable |
| Random Forest | 400 arbres, `min_samples_leaf=2` | Ensembliste robuste |
| Arbre de décision | `max_depth=3`, `min_samples_leaf=5` | Interprétabilité des règles |

## Résultats — évaluation à 1 pas d'avance

| Indicateur | Modèle | MAPE | R² |
|---|---|---|---|
| Revenus (CA) | **Régression linéaire** | 15,3 % | **0,93** |
| Revenus (CA) | Random Forest | 17,2 % | 0,85 |
| Revenus (CA) | Arbre de décision | 24,9 % | 0,58 |
| Total des actifs | Régression linéaire | 4,5 % | 0,85 |
| Total des actifs | Random Forest | 5,2 % | 0,81 |
| Total des actifs | **Arbre de décision** | **4,1 %** | **0,88** |
| Capitaux propres | **Régression linéaire** | 4,0 % | **0,77** |
| Capitaux propres | Random Forest | 5,9 % | 0,68 |
| Capitaux propres | Arbre de décision | 6,0 % | 0,66 |
| Résultat net | **Régression linéaire** | 7,9 % | **0,96** |
| Résultat net | Random Forest | 9,1 % | 0,93 |
| Résultat net | Arbre de décision | 10,6 % | 0,92 |

**Verdict** : la **Régression linéaire** l'emporte sur 3 indicateurs sur 4.
L'**Arbre de décision** remporte le **Total des actifs** (meilleur R² *et*
meilleure MAPE des trois modèles). Les séries de SFBT ont une croissance très
régulière, bien captée par un modèle simple avec saisonnalité ; les modèles à
base d'arbres n'apportent pas de gain systématique sur si peu de points. Résultat
classique et défendable : *sur des séries courtes et régulières, le modèle simple
gagne.*

### Apport pédagogique de l'arbre de décision

L'arbre est le seul modèle dont les règles se lisent directement. Sur le
**Résultat net** (profondeur 3, 5 feuilles), les variables dominantes sont
`rlag1` (69 %) et `per_T1` (30 %) :

```
Si r(t-1) <= 0,814                  -> r(t) = 2,00   (rebond après contraction)
Sinon si ce n'est PAS le T1         -> r(t) ~ 1,10 à 1,20  (progression régulière)
Sinon (T1) et r(t-2) <= 1,114       -> r(t) = 0,530
Sinon (T1)                          -> r(t) = 0,388  (remise à zéro du cumul)
```

Le modèle retrouve seul deux régularités économiques réelles : l'effet de
rattrapage après un trimestre de contraction, et la chute du ratio au T1 due à la
remise à zéro du cumul annuel.

L'élagage illustre empiriquement le **sur-apprentissage** (R² moyen sur les 4
indicateurs, régime 1 pas) :

| Contrainte de l'arbre | R² moyen |
|---|---|
| Sans limite de profondeur | 0,662 |
| `max_depth=3` | 0,673 |
| `max_depth=2` | 0,734 |
| **`max_depth=3`, `min_samples_leaf=5`** | **0,758** |

Plus l'arbre est contraint, meilleure est sa généralisation. Cela explique aussi
pourquoi le Random Forest (0,819) surpasse l'arbre seul : moyenner 400 arbres
réduit la variance.

## Backtest par horizon (point méthodologique essentiel)

> **Attention à l'interprétation des métriques ci-dessus.** L'évaluation de
> `evaluer()` fournit au modèle le **niveau réel précédent** (`prev_level`) à
> chaque point de test : elle mesure donc une prévision **à 1 pas d'avance**. Or
> `prevoir_futur()` fonctionne en mode **récursif** (le modèle se nourrit de ses
> propres sorties). Les métriques à 1 pas ne décrivent donc pas le régime dans
> lequel les prévisions publiées sont produites.

`evaluer_horizon()` corrige ce biais : pour chaque origine du jeu de test, on
réancre sur les données réelles puis on projette 1 à 4 pas en mode récursif. Une
**baseline naïve saisonnière** `V(t-4)` fournit la référence minimale à battre.
Sortie : `data/processed/ml_metrics_horizon.csv`.

**MAPE moyenne par modèle et horizon (4 indicateurs)**

| Modèle | h=1 | h=2 | h=3 | h=4 |
|---|---|---|---|---|
| Régression linéaire | **8,35 %** | **15,10 %** | 18,35 % | 20,44 % |
| Random Forest | 10,15 % | 16,87 % | 18,47 % | **19,29 %** |
| Arbre de décision | 12,86 % | 20,27 % | 21,22 % | 22,04 % |
| Naïf `V(t-4)` | 20,72 % | 20,66 % | 20,52 % | 20,13 % |

**Trois enseignements :**

1. **À 1 pas, l'apport des modèles est net** : 8,35 % contre 20,72 % pour la
   baseline naïve, soit une erreur divisée par 2,5. Le modèle apporte une valeur
   réelle et démontrable.
2. **L'erreur croît fortement avec l'horizon** (8,35 % → 20,44 % pour la
   régression linéaire). C'est mécanique : en mode récursif, les erreurs de taux
   se composent multiplicativement.
3. **À 4 pas, l'avantage disparaît en moyenne** : la régression linéaire
   (20,44 %) ne fait plus mieux que la baseline naïve (20,13 %). Les prévisions
   annuelles doivent donc être présentées comme des **ordres de grandeur**, pas
   comme des estimations précises.

**MAPE par indicateur à l'horizon 4** (le plus utile en pratique) :

| Indicateur | Meilleur modèle | MAPE h=4 | Naïf h=4 | Apport |
|---|---|---|---|---|
| Résultat net | Régression linéaire | **7,60 %** | 23,67 % | ✅ très net |
| Total des actifs | Arbre de décision | **7,17 %** | 11,16 % | ✅ net |
| Capitaux propres | Naïf `V(t-4)` | 13,28 % | **11,32 %** | ❌ nul |
| Revenus (CA) | Naïf `V(t-4)` | 44,05 % | **34,38 %** | ❌ négatif |

Les modèles sont donc **fiables à 4 pas sur le Résultat net et le Total des
actifs**, mais **pas sur le CA ni les Capitaux propres**, où la baseline naïve
fait mieux. Le CA est le cas le plus difficile : sa forte saisonnalité cumulée
amplifie les erreurs en mode récursif.

## Sorties
- `data/processed/ml_metrics.csv` — comparaison des 3 modèles (régime 1 pas), 12 lignes.
- `data/processed/ml_metrics_horizon.csv` — MAE/MAPE/R² par modèle et horizon (1→4), baseline naïve incluse.
- `data/processed/ml_predictions.csv` — réel vs prédit (jeu de test).
- `data/processed/ml_forecasts.csv` — prévisions des 4 prochaines clôtures, 48 lignes.

## Limites
- Une partie de l'historique infra-annuel est **estimée** (augmentation) : les
  modèles apprennent donc en partie le profil d'accumulation linéaire supposé.
  Les métriques sont ainsi en partie auto-réalisatrices.
- Peu de points (~80 trimestres, ~20 ans) → on privilégie des modèles simples ;
  un LSTM/réseau profond serait sur-dimensionné et risquerait le sur-apprentissage.
- **La précision se dégrade avec l'horizon** : toute communication sur la
  performance doit préciser le nombre de pas d'avance considéré.
- Sur le **CA à 4 pas**, aucun modèle ne bat la baseline naïve : cette prévision
  doit être utilisée avec prudence.
- Hyperparamètres fixés (400 arbres pour la forêt, profondeur 3 pour l'arbre) ;
  une validation croisée temporelle (`TimeSeriesSplit`) plus poussée pourrait
  être ajoutée.
