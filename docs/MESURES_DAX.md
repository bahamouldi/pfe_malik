# Mesures DAX (optionnel)

Les ratios sont **déjà calculés** dans `ratios.csv` : pour un dashboard simple,
tu n'as **pas besoin** de DAX (tu glisses `Valeur` et tu filtres par `Ratio`).

Ces mesures servent si tu veux des indicateurs **dynamiques** (qui réagissent aux
filtres) plus élégants. Pour créer une mesure : sélectionne la table `ratios` →
ruban **Outils de table** → **Nouvelle mesure** → colle le code → Entrée.

```DAX
-- Valeur du ratio sélectionné (moyenne = la valeur unique après filtrage)
Valeur ratio = AVERAGE ( ratios[Valeur] )
```

```DAX
-- Dernière année disponible (utile pour des cartes "année en cours")
Derniere annee = MAX ( ratios[Annee] )
```

```DAX
-- Valeur du ratio à la dernière année (carte qui suit toujours l'année max)
Ratio (derniere annee) =
CALCULATE (
    AVERAGE ( ratios[Valeur] ),
    ratios[Annee] = MAX ( ratios[Annee] ),
    ratios[Periode] = "FY"
)
```

```DAX
-- Croissance annuelle d'un ratio (N vs N-1), en points
Variation N vs N-1 =
VAR annee_courante = MAX ( ratios[Annee] )
VAR val_n =
    CALCULATE ( AVERAGE ( ratios[Valeur] ), ratios[Annee] = annee_courante )
VAR val_n1 =
    CALCULATE ( AVERAGE ( ratios[Valeur] ), ratios[Annee] = annee_courante - 1 )
RETURN
    val_n - val_n1
```

```DAX
-- Chiffre d'affaires SFBT (depuis financials_full), année max, FY
CA SFBT =
CALCULATE (
    SUM ( financials_full[Valeur] ),
    financials_full[Cle_indicateur] = "revenus",
    financials_full[Societe] = "SFBT",
    financials_full[Periode] = "FY"
)
```

```DAX
-- Drapeau visuel : entreprise saine selon Conan & Holder (>0,16)
Statut Conan =
VAR s = CALCULATE ( AVERAGE ( ratios[Valeur] ), ratios[Code_ratio] = "CONAN_HOLDER" )
RETURN
    SWITCH ( TRUE (),
        s >= 0.16, "🟢 Sain",
        s >= 0.04, "🟠 Vigilance",
        "🔴 Risque" )
```

> Conseil débutant : commence **sans** DAX. Ajoute ces mesures seulement si le
> jury demande des indicateurs dynamiques ou si tu veux soigner la présentation.
