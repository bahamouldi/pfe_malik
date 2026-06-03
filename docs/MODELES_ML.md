# Modèles de prévision (Machine Learning)

Prévision des valeurs financières de SFBT. **Deux modèles comparés** (choix de
Malik) : **Régression linéaire** (baseline simple, interprétable) vs
**Random Forest** (ML robuste, non-linéaire). Code : `src/ml_forecast.py`.

## Indicateurs prévus
Revenus (CA), Total des actifs, Capitaux propres, Résultat net — séries
trimestrielles ~2005→2025 (réel + trimestres estimés).

## Démarche

1. **Cible = taux de croissance** `r_t = V_t / V_{t-1}` (et non le niveau brut).
   > Point méthodologique clé : sur une série qui croît, un Random Forest **ne
   > sait pas extrapoler** le niveau (les arbres plafonnent à la valeur max vue
   > en entraînement → R² négatif). En modélisant un taux quasi-stationnaire, les
   > deux modèles deviennent comparables et performants. Le niveau est reconstruit :
   > `V̂_t = V_{t-1} × r̂_t`. C'est l'approche standard en finance (on modélise
   > les *rendements*, pas les *niveaux*).
2. **Variables explicatives** : tendance (index temps), retards du taux
   (`r_{t-1..t-4}`), saisonnalité (période T1/S1/9M/FY en one-hot).
3. **Découpage temporel** 75 % / 25 % (sans mélange) → backtest honnête : on
   prédit des clôtures postérieures jamais vues.
4. **Métriques** : MAE, RMSE, MAPE (%), R².
5. **Prévision future récursive** : 4 prochaines clôtures.

## Résultats (backtest)

| Indicateur | Modèle | MAPE | R² |
|---|---|---|---|
| Revenus (CA) | **Régression linéaire** | 15,3 % | **0,93** |
| Revenus (CA) | Random Forest | 17,2 % | 0,85 |
| Total des actifs | **Régression linéaire** | 4,5 % | **0,85** |
| Total des actifs | Random Forest | 5,2 % | 0,81 |
| Capitaux propres | **Régression linéaire** | 4,0 % | **0,77** |
| Capitaux propres | Random Forest | 5,9 % | 0,68 |
| Résultat net | **Régression linéaire** | 7,9 % | **0,96** |
| Résultat net | Random Forest | 9,1 % | 0,93 |

**Verdict** : la **Régression linéaire** l'emporte sur les 4 indicateurs
(meilleur R², MAPE plus faible). Logique : les séries financières de SFBT ont une
croissance très régulière, que le modèle linéaire capte parfaitement avec la
saisonnalité ; le Random Forest, plus complexe, n'apporte pas de gain sur si peu
de points et reste légèrement en retrait. C'est un résultat classique et
défendable : *sur des séries courtes et régulières, le modèle simple gagne.*

## Sorties
- `data/processed/ml_metrics.csv` — comparaison des 2 modèles.
- `data/processed/ml_predictions.csv` — réel vs prédit (jeu de test).
- `data/processed/ml_forecasts.csv` — prévisions des 4 prochaines clôtures.

## Limites
- Une partie de l'historique infra-annuel est **estimée** (augmentation) : les
  modèles apprennent donc en partie le profil d'accumulation linéaire supposé.
- Peu de points (~80 trimestres, ~20 ans) → on privilégie des modèles simples ;
  un LSTM/réseau profond serait sur-dimensionné et risquerait le sur-apprentissage.
- Hyperparamètres Random Forest fixés (400 arbres) ; une validation croisée
  temporelle plus poussée pourrait être ajoutée.
