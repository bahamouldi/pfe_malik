"""gen_catalogue_ratios.py — Génère docs/CATALOGUE_RATIOS.md depuis le registre RATIOS
(garantit que la doc reste synchronisée avec le code)."""
import inspect
import config as C
from ratios import RATIOS, COUT_CAPITAL, TVA

# Formules « lisibles » par code (le code source utilise des fonctions ; ici on
# documente la formule mathématique en clair).
FORMULES = {
    "LIQ_GEN": "Actif courant / Dettes courantes",
    "LIQ_RED": "(Actif courant − Stocks) / Dettes courantes",
    "LIQ_IMM": "Liquidités / Dettes courantes",
    "INT_DEF_RED": "(Liquidités + Placements) / (Charges décaissables / 365)",
    "INT_DEF": "(Liquidités + Placements + Clients) / (Charges décaissables / 365)",
    "RFR": "(Capitaux permanents − Actif immobilisé) / Actif total × 100",
    "RBFR": "(Stocks + Clients − Fournisseurs) / CA × 100",
    "LEV_ECO": "Actif total / Capitaux propres",
    "POIDS_IMMO": "Actif immobilisé / Actif total × 100",
    "FIN_IMMO": "Capitaux permanents / Actif immobilisé",
    "VETUSTE": "Amortissements cumulés / Immobilisations brutes × 100",
    "ENDET_GLOB": "Dettes totales / Total passif × 100",
    "ENDET_TERME": "Dettes non courantes / Capitaux propres × 100",
    "INDEP_FIN": "Capitaux propres / Total passif × 100",
    "COUV_CF": "Résultat d'exploitation / Charges financières",
    "POIDS_CF": "Charges financières / CA × 100",
    "AUTO_FIN": "Capitaux propres / Dettes totales",
    "SOLVA": "Actif total / Dettes totales",
    "EFF_BRUT_RH": "Valeur ajoutée / Charges de personnel",
    "EFF_NET_RH": "EBE / Charges de personnel",
    "CONAN_HOLDER": "0,24·(EBE/Dettes) + 0,22·(Cap.perm/Actif) + 0,16·(Actif circ. hors stock/Actif) − 0,87·(Charges fin./CA) − 0,10·(Charges pers./VA)",
    "RISQ_PLACEMENT": "Placements / Actif total × 100",
    "RISQ_COMMERCIAL": "Clients / CA × 100",
    "CREDIT_FOURN": f"Fournisseurs / (Achats × {1+TVA:.2f}) × 365",
    "CREDIT_CLIENT": f"Clients / (CA × {1+TVA:.2f}) × 365",
    "RENT_COM": "Résultat d'exploitation / CA × 100",
    "MARGE_NETTE": "Résultat net / CA × 100",
    "TAUX_MARQUE": "Marge sur coût matières / Production × 100",
    "ROT_CAP": "CA / Capitaux propres",
    "ROA": "Résultat net / Actif total × 100",
    "ROCE": "Résultat d'exploitation / Capitaux permanents × 100",
    "REND_IMMO": "EBE / Actif immobilisé × 100",
    "REND_RES_STABLE": "EBE / Capitaux permanents × 100",
    "MARGE_BRUTE_EXPL": "EBE / CA × 100",
    "MARGE_BENEF_EXPL": "Résultat d'exploitation / CA × 100",
    "REND_GLOBAL_NET": "Résultat net / Total ressources × 100",
    "CREATION_VALEUR": f"Résultat d'exploitation − {COUT_CAPITAL:.0%} × Capitaux permanents",
    "REND_PRODUCTION": "Résultat d'exploitation / Production × 100",
    "ROT_STOCKS": "Achats consommés / Stocks",
    "PROFIT_OP": "Résultat d'exploitation (montant)",
    "ROE": "Résultat net / Capitaux propres × 100",
    "ROI": "Résultat net / Actif total × 100",
    "PERF_PLACEMENT": "Produits des placements / Placements × 100",
}

UNITES = {"x": "ratio (fois)", "%": "pourcentage", "j": "jours",
          "score": "score", "montant": "montant (devise société)"}


def generer():
    L = ["# Catalogue des ratios financiers (MSI20000)\n",
         "*Généré automatiquement depuis `src/ratios.py` — ne pas éditer à la main.*\n",
         "> Les formules ont été reconstituées d'après les définitions financières "
         "standard et la table des matières MSI20000 (Malik n'ayant pas fourni les "
         "formules). À valider/ajuster avec lui si besoin.\n",
         f"\n**Hypothèses paramétrables** : coût du capital (EVA) = {COUT_CAPITAL:.0%} ; "
         f"TVA (crédits clients/fournisseurs) = {TVA:.0%}.\n",
         f"\n**Total : {len(RATIOS)} ratios.**\n"]

    # Regroupe par catégorie > sous-catégorie en respectant l'ordre du registre.
    cat_order, seen = [], set()
    for code, (cat, sous, *_ ) in RATIOS.items():
        if (cat, sous) not in seen:
            seen.add((cat, sous)); cat_order.append((cat, sous))

    cur_cat = None
    for (cat, sous) in cat_order:
        if cat != cur_cat:
            L.append(f"\n## {cat}\n"); cur_cat = cat
        L.append(f"\n### {sous}\n")
        L.append("| Code | Ratio | Formule | Unité | Interprétation |")
        L.append("|---|---|---|---|---|")
        for code, (c, s, libelle, unite, fn, interp) in RATIOS.items():
            if (c, s) != (cat, sous):
                continue
            L.append(f"| `{code}` | {libelle} | {FORMULES.get(code,'')} | "
                     f"{UNITES.get(unite,unite)} | {interp} |")

    L.append("\n## Disponibilité par société\n")
    L.append("- **SFBT** : tous les ratios (états complets + SIG).")
    L.append("- **DELICE** : pas de SIG ni de stocks (holding) → ratios EBE/VA et stocks indisponibles. "
             "⚠️ Marge nette > 100 % : normal, c'est une holding dont le résultat vient des dividendes, "
             "pas du CA opérationnel — à interpréter avec prudence dans le benchmark.")
    L.append("- **AB inBev / Coca-Cola** : ratios de structure et de rentabilité disponibles ; "
             "ratios nécessitant la VA ou les charges de personnel (efficacité RH, Conan & Holder) "
             "indisponibles (postes absents des sources).")
    L.append("\n## Limites connues\n")
    L.append("- **Charges financières** : la source ne donne pas le montant brut pour SFBT ; "
             "estimé par la part « charge » du résultat financier net (≈0 car SFBT a un résultat "
             "financier positif). Les ratios COUV_CF / POIDS_CF sont donc peu significatifs pour SFBT.")
    L.append("- **Création de valeur (EVA)** : dépend d'un coût du capital supposé (paramètre).")

    out = C.DOCS_DIR / "CATALOGUE_RATIOS.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"✔ Catalogue : {out}  ({len(RATIOS)} ratios documentés)")


if __name__ == "__main__":
    generer()
