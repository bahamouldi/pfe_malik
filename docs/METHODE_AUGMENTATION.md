# Méthode d'augmentation trimestrielle (SFBT)

## Besoin

SFBT ne publie que deux clôtures par an : **30/06** (semestriel) et **31/12**
(annuel). Pour densifier la série (analyses trimestrielles, entraînement des
modèles de prévision), on **estime** les clôtures manquantes :

- **31/03** → période `T1` (cumul 3 mois) ;
- **30/09** → période `9M` (cumul 9 mois).

Les lignes produites sont marquées `Type_donnee = Estime` et
`Source = augmentation (estimation trimestrielle)`. Elles n'écrasent jamais le
réel : le réel reste `Type_donnee = Reel`.

## Principe : distinguer STOCK et FLUX

La nature de l'indicateur détermine la formule. C'est le point clé pour ne pas
produire d'aberrations.

### 1. Grandeurs de **stock** (Bilan : actif & passif)

Photo à la date de clôture → **interpolation linéaire dans le temps** entre deux
photos réelles encadrantes :

```
31/03/N   interpolé entre   31/12/(N-1)   et   30/06/N
30/09/N   interpolé entre   30/06/N        et   31/12/N

valeur(d) = v0 + (v1 - v0) × (d - d0) / (d1 - d0)        [fraction en jours]
```

Exemple (Total des actifs, 2024) : Juin = 1,1858 Md ; Déc = 1,2818 Md →
**30/09/2024 ≈ 1,2338 Md** (entre les deux). ✔

### 2. Grandeurs de **flux** (Compte de résultat, Flux de trésorerie, SIG)

Cumul depuis le 1er janvier (remis à zéro chaque exercice). On répartit le flux
au prorata du temps **à l'intérieur de chaque semestre** :

```
31/03/N (cumul 3 mois) ≈ 0,5 × Valeur(30/06/N)
30/09/N (cumul 9 mois) ≈ Valeur(30/06/N) + 0,5 × ( Valeur(31/12/N) − Valeur(30/06/N) )
                       = 0,5 × ( Valeur(30/06/N) + Valeur(31/12/N) )
```

Exemple (Revenus, 2024) : Juin = 367,1 M ; Déc = 836,6 M →
**T1 ≈ 183,5 M**, **9M ≈ 601,8 M**. ✔

#### Exception : soldes de trésorerie

« Trésorerie à la clôture / au début de l'exercice » figurent dans l'état de
flux mais sont des **stocks** → traités par interpolation (cas 1), pas par
prorata.

## Couverture et limites

- **T1 (mars)** exige Déc(N-1) *(stock)* ou Juin(N) *(flux)* :
  - non produit pour **mars 2005** (pas de Déc 2004) côté stock.
- **9M (septembre)** exige Juin(N) **et** Déc(N) :
  - non produit pour **sept. 2025** (Déc 2025 pas encore publié).
- Volume généré : **3 320 lignes** (T1 = 1 755 ; 9M = 1 565), couvrant
  2005 → 2025.

### Hypothèse forte

L'accumulation des flux est supposée **linéaire** à l'intérieur de chaque
semestre. La **saisonnalité réelle** (les ventes de boissons sont plus fortes en
été) n'est donc pas captée par cette estimation simple. Pour une version
affinée, on pourra :

1. caler un **profil de saisonnalité** trimestriel (à partir d'années où des
   données infra-annuelles existeraient) ;
2. ou estimer les trimestres via le **modèle de prévision** (ML) une fois
   celui-ci entraîné, puis comparer aux estimations linéaires.

Ces estimations sont à **valider avec Malik / l'encadrant** avant exploitation
analytique fine.
