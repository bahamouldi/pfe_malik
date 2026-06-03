# 🍼 Guide Power BI — pas à pas pour grand débutant

Ce guide suppose que **tu n'as jamais ouvert Power BI**. Suis les étapes dans
l'ordre, sans en sauter. À la fin tu auras un tableau de bord financier complet
avec 5 onglets + benchmark + prévisions.

> 💡 Toutes les données sont **déjà calculées** (ratios, prévisions). Power BI
> sert juste à **afficher** : tu glisses des champs, tu choisis un graphique.
> Presque **aucune formule** à écrire.

---

## SOMMAIRE
0. Récupérer le projet sur Windows (Git + clone)
1. Installer Power BI Desktop
2. Importer les données
3. Vérifier les types de colonnes
4. Comprendre l'écran de Power BI
5. Page 1 — Vue d'ensemble SFBT
6. Page 2 — Solidité financière
7. Page 3 — Performance financière
8. Page 4 — Benchmark (comparaison sociétés)
9. Page 5 — Prévision Machine Learning
10. Ajouter les filtres (slicers)
11. Mettre en forme et enregistrer

---

## 0. Récupérer le projet sur Windows

### a) Installer Git
1. Va sur **https://git-scm.com/download/win** → le téléchargement démarre seul.
2. Lance le `.exe`, clique **Next** à toutes les étapes (les défauts conviennent),
   puis **Install**, puis **Finish**.

### b) Cloner le dépôt
1. Crée un dossier, ex. `Documents\PFE`.
2. Dedans, clic droit → **« Open Git Bash here »** (ou « Git Bash Here »).
3. Tape (remplace `TON_COMPTE` par ton pseudo GitHub, ici `bahamouldi`) :
   ```bash
   git clone https://github.com/bahamouldi/pfe_malik.git
   ```
4. Un dossier `pfe_malik` apparaît. Les fichiers de données sont dans
   `pfe_malik\data\processed\`.

> Si le dépôt est **privé**, Git te demandera de te connecter à GitHub
> (une fenêtre s'ouvre) — connecte-toi, c'est tout.

### Les 4 fichiers qui nous intéressent (dans `data\processed\`)
| Fichier | Contient |
|---|---|
| `ratios.csv` | **Le principal** : tous les ratios, par société et par date |
| `financials_full.csv` | Les valeurs brutes (CA, actifs…) réel + estimé |
| `ml_forecasts.csv` | Les prévisions futures |
| `ml_predictions.csv` | Backtest : réel vs prédit |

---

## 1. Installer Power BI Desktop

**Méthode la plus simple (Microsoft Store)** :
1. Ouvre le **Microsoft Store** (dans le menu Démarrer de Windows).
2. Cherche **« Power BI Desktop »**.
3. Clique **Installer** (gratuit). Attends la fin.
4. Lance **Power BI Desktop**. Ferme la fenêtre d'accueil/connexion (croix ✕) si
   elle apparaît — pas besoin de compte pour commencer.

> Alternative : https://aka.ms/pbidesktopstore

---

## 2. Importer les données

On importe les 4 fichiers CSV.

1. En haut à gauche : **Accueil** (Home) → **Obtenir les données** (Get data) →
   **Texte/CSV**.
2. Va dans `pfe_malik\data\processed\`, choisis **`ratios.csv`**, clique **Ouvrir**.
3. Une fenêtre d'aperçu s'ouvre. **TRÈS IMPORTANT** :
   - En haut, vérifie **« Origine du fichier »** = **65001: Unicode (UTF-8)**
     (sinon les accents é/è seront cassés). Change-la si besoin.
   - Clique **Charger** (Load).
4. **Répète** l'opération (Obtenir les données → Texte/CSV) pour :
   - `financials_full.csv`
   - `ml_forecasts.csv`
   - `ml_predictions.csv`

À droite, dans le volet **Données** (Data), tu vois maintenant 4 tables. ✅

---

## 3. Vérifier les types de colonnes

Power BI devine les types mais vérifie les 2 plus importants pour `ratios` :

1. Clique sur la table **`ratios`** à droite.
2. Clique sur la colonne **`Date`** → ruban **Outils de colonne** (Column tools)
   → **Type de données** = **Date**.
3. Clique sur **`Valeur`** → **Type de données** = **Nombre décimal**.
4. (Pareil pour `financials_full` : `Date`=Date, `Valeur`=Nombre décimal ;
   et `ml_forecasts`/`ml_predictions` : `Date`=Date, `Prevision`/`Reel`/`Predit`
   = Nombre décimal.)

> Si une colonne année (`Annee`) est en décimal (2024,00), passe-la en
> **Nombre entier**.

---

## 4. Comprendre l'écran (30 secondes)

- **À gauche** : 3 icônes pour changer de vue → **Rapport** (les graphiques),
  **Données** (les tables), **Modèle** (les relations). Reste sur **Rapport**.
- **Au centre** : la page blanche = ta feuille (le « canvas »).
- **À droite, 3 volets** :
  - **Visualisations** : les icônes de graphiques (barres, courbes, camembert…).
  - **Champs/Données** : tes tables et colonnes.
- **En bas** : les onglets de pages (comme Excel). Le **+** ajoute une page.

**Le geste de base** : tu cliques une icône de graphique → un cadre apparaît →
tu **glisses des colonnes** depuis « Données » vers les **puits** (Axe, Valeurs,
Légende) du graphique. C'est tout.

> Renomme une page : double-clic sur son onglet en bas.

---

## 5. PAGE 1 — Vue d'ensemble SFBT

Renomme la page (onglet en bas) en **« Vue d'ensemble »**.

### 5.1 Des cartes KPI (les gros chiffres)
On veut 4 cartes : CA, Résultat net, Total actifs, ROE — pour SFBT, dernière année.

1. Clique l'icône **Carte** (Card) dans Visualisations (icône « 123 »).
2. Depuis la table **`ratios`**, glisse **`Valeur`** dans le puits **Champs**.
3. La carte montre une somme énorme (tous ratios mélangés). On filtre :
   - Avec la carte sélectionnée, dans le volet **Filtres** (à droite), glisse
     **`Code_ratio`** dans « Filtres sur ce visuel » → coche **`MARGE_NETTE`**.
   - Glisse **`Societe`** → coche **`SFBT`**.
   - Glisse **`Periode`** → coche **`FY`**.
   - Glisse **`Annee`** → coche **`2024`**.
   - La carte affiche **30,14** → c'est la marge nette % de SFBT en 2024. ✅
4. Renomme la carte : sélectionne-la → volet **Format** (icône pinceau) →
   **Titre** = active-le et écris « Marge nette % ».
5. **Copie-colle** cette carte 3 fois (Ctrl+C / Ctrl+V) et change juste le
   `Code_ratio` du filtre :
   - `ROE` → « Rentabilité capitaux propres % »
   - `ROA` → « Rendement actif % »
   - `SOLVA` → « Solvabilité (x) »

> 💡 Astuce : pour afficher un **montant** (CA, Résultat net) plutôt qu'un ratio,
> fais la même carte mais avec la table **`financials_full`** : `Valeur` en champ,
> et filtres `Cle_indicateur`=`revenus` (ou `resultatnetdelexercice`),
> `Societe`=SFBT, `Annee`=2024, `Periode`=FY.

### 5.2 Courbe d'évolution du CA (20 ans)
1. Clique une zone vide, puis l'icône **Graphique en courbes** (Line chart).
2. Depuis **`financials_full`** :
   - **`Date`** → puits **Axe X**.
   - **`Valeur`** → puits **Axe Y**.
3. Filtres sur ce visuel : `Cle_indicateur`=`revenus`, `Societe`=`SFBT`,
   `Periode`=`FY`.
4. Titre : « Évolution du chiffre d'affaires (FY) ».

---

## 6. PAGE 2 — Solidité financière

Nouvelle page (**+** en bas), nomme-la **« Solidité »**.

### 6.1 Filtre global de la page
1. Clique une zone vide → icône **Segment** (Slicer).
2. Glisse **`Societe`** dedans → choisis **SFBT**.
3. Ajoute un 2e Segment avec **`Annee`**.
4. Ajoute un 3e Segment avec **`Periode`** → mets **FY**.

### 6.2 Graphique en barres des ratios de solidité
1. Icône **Histogramme groupé** (Clustered bar chart).
2. Depuis **`ratios`** :
   - **`Ratio`** → **Axe Y**.
   - **`Valeur`** → **Axe X (Valeurs)**.
3. Filtres sur ce visuel : **`Categorie`** = **Solidité**, et choisis une
   `Sous_categorie` (ex. **Gestion des passifs**) pour ne pas tout afficher d'un coup.
4. Titre : « Ratios de solidité — SFBT ».

> Tu peux dupliquer ce visuel et changer la `Sous_categorie` (Liquidités,
> Gestion des actifs…). Les segments en haut filtrent **tous** les visuels de la page.

---

## 7. PAGE 3 — Performance financière

Nouvelle page **« Performance »**. Même logique que la page Solidité :
1. Ajoute les **Segments** `Societe` (SFBT) et `Annee`.
2. **Histogramme groupé** : `Ratio` en Axe, `Valeur` en Valeurs, filtre
   `Categorie`=**Performance**.
3. Ajoute une **courbe d'évolution du ROE** :
   - Graphique en courbes, **`Annee`** en Axe X, **`Valeur`** en Axe Y,
     filtres `Code_ratio`=`ROE`, `Societe`=`SFBT`, `Periode`=`FY`.

---

## 8. PAGE 4 — Benchmark (LE point fort)

Nouvelle page **« Benchmark »**. Ici on compare les 4 sociétés.

### 8.1 Comparaison d'un ratio entre sociétés
1. Icône **Histogramme groupé**.
2. Depuis **`ratios`** :
   - **`Societe`** → **Axe X**.
   - **`Valeur`** → **Axe Y (Valeurs)**.
3. Filtres : `Code_ratio`=**MARGE_NETTE**, `Annee`=2024, `Periode`=FY.
4. Titre : « Marge nette % — Benchmark 2024 ».
   → Tu verras 4 barres : SFBT, DELICE, AB inBev, Coca-Cola.

### 8.2 Tableau comparatif multi-ratios
1. Icône **Matrice** (Matrix).
2. **`Ratio`** → **Lignes** ; **`Societe`** → **Colonnes** ; **`Valeur`** →
   **Valeurs**.
3. Filtres : `Annee`=2024, `Periode`=FY, et choisis quelques `Code_ratio`
   parlants (MARGE_NETTE, ROE, ROA, SOLVA, ENDET_GLOB, LIQ_GEN).

> ⚠️ Rappel : **DELICE est une holding** → sa marge nette dépasse 100 % (revenus =
> dividendes). Mets une zone de texte pour l'expliquer (Insertion → Zone de texte).

---

## 9. PAGE 5 — Prévision Machine Learning

Nouvelle page **« Prévision ML »**.

### 9.1 Courbe : réel + prévision
On veut voir l'historique puis la prévision. Le plus simple :
1. **Graphique en courbes**.
2. Depuis **`ml_forecasts`** : **`Date`** → Axe X, **`Prevision`** → Axe Y,
   **`Modele`** → **Légende** (2 courbes : Régression linéaire / Random Forest).
3. Filtre : **`Indicateur`** = **Revenus (CA)**.
4. Titre : « Prévision du CA — LinReg vs Random Forest ».

### 9.2 Backtest : réel vs prédit
1. **Graphique en courbes** depuis **`ml_predictions`** :
   - **`Date`** → Axe X.
   - **`Reel`** et **`Predit`** → tous deux dans **Valeurs** (2 courbes).
   - Filtre `Indicateur`=Revenus (CA), `Modele`=Régression linéaire.
2. Titre : « Vérification : réel vs prédit ».

---

## 10. Les filtres (slicers) — pour rendre interactif

- Un **Segment** (Slicer) placé sur une page filtre **tous** les visuels de
  cette page.
- Mets en haut de chaque page : `Societe`, `Annee`, `Periode`.
- Clique une valeur → tout se met à jour. Clique la gomme du slicer pour
  réinitialiser.

---

## 11. Mise en forme & enregistrement

### Rendre joli (optionnel mais conseillé)
- **Affichage** (View) → **Thèmes** → choisis un thème coloré.
- Sélectionne chaque visuel → **Format** (pinceau) → active **Titre**, ajuste
  les couleurs.
- Ajoute un titre de page : **Insertion** → **Zone de texte** → « SFBT — … ».

### Enregistrer
1. **Fichier** → **Enregistrer sous** → nomme-le `Dashboard_SFBT.pbix`.
2. Mets-le dans le dossier `pfe_malik` pour le repush sur GitHub si tu veux
   (voir plus bas).

### (Optionnel) Renvoyer le .pbix sur GitHub
Dans Git Bash, dans le dossier `pfe_malik` :
```bash
git add Dashboard_SFBT.pbix
git commit -m "Ajout du dashboard Power BI"
git push
```

---

## 🆘 Problèmes fréquents
- **Accents cassés (Ã©)** → tu as oublié UTF-8 à l'import. Supprime la table
  (clic droit → Supprimer) et réimporte en choisissant **65001 UTF-8**.
- **La carte montre un chiffre énorme** → il manque un filtre (`Code_ratio` +
  `Periode`=FY + une `Annee`).
- **« Valeur » fait une somme** → normal, avec les bons filtres il ne reste
  qu'une ligne donc la somme = la vraie valeur. Sinon mets l'agrégation sur
  **Moyenne** (clic sur le champ dans le puits → Moyenne).
- **Rien ne s'affiche** → vérifie que les filtres ne s'excluent pas (ex.
  Periode=FY mais tu as choisi une date de juin).

---

## ✅ Récapitulatif des 5 pages
| Page | Contenu |
|---|---|
| Vue d'ensemble | Cartes KPI SFBT + courbe CA |
| Solidité | Ratios de liquidité, endettement… (SFBT) |
| Performance | Marges, ROE, ROA (SFBT) |
| Benchmark | SFBT vs DELICE vs AB inBev vs Coca-Cola |
| Prévision ML | Réel + prévision (2 modèles) |

Tu as un dashboard de PFE complet. Pour aller plus loin (mesures calculées),
voir `docs/MESURES_DAX.md`.
