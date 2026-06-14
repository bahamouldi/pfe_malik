"""gen_catalogue_ratios.py — Génère docs/CATALOGUE_RATIOS.md depuis le registre
RATIOS (synchronisé avec le code et les formules officielles de Malik)."""
import config as C
from ratios import RATIOS, BENCHMARKS, SGPI_CATEGORIES, TVA

FORMULES = {
    "LIQ_GEN": "Actifs courants / Passifs courants",
    "LIQ_RED": "(Actifs courants − Stocks) / Passifs courants",
    "LIQ_IMM": "Liquidités / Passifs courants",
    "INT_DEF_RED": "Liquidités / ((Charges d'exploitation − Dotations) / 365)",
    "INT_DEF": "(Liquidités + Clients nets) / ((Charges d'exploitation − Dotations) / 365)",
    "FR": "Ressources stables − Actifs immobilisés",
    "COUV_IMMO": "Ressources stables / Actifs immobilisés",
    "BFR": "Stocks nets + Clients nets − Fournisseurs",
    "BFR_JOURS": "BFR / (Revenus / 365)",
    "LEV_ECO": "Total Actifs / Capitaux propres",
    "POIDS_IMMO": "Actifs immobilisés / Total Actifs × 100",
    "VETUSTE": "Amortissements corporels / Immobilisations corporelles × 100",
    "ENDET_GLOB": "Total Dettes / Total Actifs × 100",
    "ENDET_TERME": "Dettes long terme / Capitaux propres × 100",
    "INDEP_FIN": "Capitaux propres / Total Dettes",
    "AUTO_FIN": "Capitaux propres / Total Actifs × 100",
    "SOLVA": "Total Actifs / Total Dettes",
    "EFF_BRUT_RH": "Revenus / Charges de personnel",
    "EFF_NET_RH": "Résultat net / Charges de personnel",
    "RISQ_PLACEMENT": "Placements / Actifs courants × 100",
    "RISQ_COMMERCIAL": "Clients bruts / Revenus × 100",
    "CREDIT_CLIENT": "Clients bruts / (Revenus / 365)",
    "CREDIT_FOURN": "Fournisseurs / (Achats consommés / 365)",
    "CONAN_HOLDER": "0,24·(AC−Stocks)/TA + 0,22·(RN/TA) + 0,16·(Rev/TA) − 0,87·(Ch.pers/TA) − 0,10·(Dettes LT/TA)",
    "RENT_COM": "Résultat d'exploitation / Revenus × 100",
    "MARGE_NETTE": "Résultat net / Revenus × 100",
    "ROT_CAP": "Revenus / Total Actifs",
    "ROA": "Résultat d'exploitation / Total Actifs × 100",
    "ROCE": "Résultat d'exploitation / Ressources stables × 100",
    "REND_IMMO": "EBE / Actifs immobilisés × 100",
    "REND_RES_STABLE": "EBE / Ressources stables × 100",
    "MARGE_BRUTE_EXPL": "EBE / Revenus × 100",
    "MARGE_BENEF_EXPL": "Résultat d'exploitation / Revenus × 100",
    "REND_PRODUCTION": "Résultat d'exploitation / Production × 100",
    "ROT_STOCKS": "Achats consommés / Stocks",
    "PROFIT_OP": "Résultat d'exploitation",
    "CREATION_VALEUR": "Valeur Ajoutée",
    "ROE": "Résultat net / Capitaux propres × 100",
    "PERF_PLACEMENT": "Produits des placements / Placements × 100",
    "ROI": "Résultat net / Ressources stables × 100",
    "DSO": "Clients / (Revenus / 365)",
    "DPO": "Fournisseurs / (Achats consommés / 365)",
    "DIO": "Stocks / (Achats consommés / 365)",
    "TRESO_NETTE": "Liquidités − Concours bancaires",
    "TAUX_VA": "Valeur Ajoutée / Revenus × 100",
    "PART_PERSO_VA": "Charges de personnel / Valeur Ajoutée × 100",
}

UNITES = {"x": "ratio (×)", "%": "pourcentage", "j": "jours", "score": "score",
          "montant": "montant (devise société)"}


def generer():
    L = ["# Catalogue des ratios financiers\n",
         "*Généré automatiquement depuis `src/ratios.py`.*\n",
         "> Formules conformes au **référentiel officiel fourni par Malik** "
         "(MSI20000 / Référentiel Industriel Normalisé).\n",
         f"\n**Total : {len(RATIOS)} ratios** + Score Global de Performance "
         "Industrielle (SGPI /100).\n"]

    cat_order, seen = [], set()
    for code, (cat, sous, *_) in RATIOS.items():
        if (cat, sous) not in seen:
            seen.add((cat, sous)); cat_order.append((cat, sous))

    cur_cat = None
    for (cat, sous) in cat_order:
        if cat != cur_cat:
            L.append(f"\n## {cat}\n"); cur_cat = cat
        L.append(f"\n### {sous}\n")
        L.append("| Code | Ratio | Formule | Unité | Benchmark | Interprétation |")
        L.append("|---|---|---|---|---|---|")
        for code, (c, s, libelle, unite, fn, interp) in RATIOS.items():
            if (c, s) != (cat, sous):
                continue
            L.append(f"| `{code}` | {libelle} | {FORMULES.get(code,'')} | "
                     f"{UNITES.get(unite,unite)} | {BENCHMARKS.get(code,'—')} | {interp} |")

    # SGPI
    L.append("\n## Score Global de Performance Industrielle (SGPI /100)\n")
    L.append("Chaque ratio clé reçoit une **note 0-5** selon des grilles de benchmark. "
             "Le SGPI est la moyenne pondérée des catégories :\n")
    L.append("| Catégorie | Poids | Ratios notés |")
    L.append("|---|---|---|")
    for cat, (poids, codes) in SGPI_CATEGORIES.items():
        L.append(f"| {cat} | {poids:.0%} | {', '.join(codes)} |")
    L.append("\n> Note catégorie = moyenne des notes /5 ; SGPI = Σ (note/5 × poids) × 100. "
             "Si une catégorie manque (benchmark incomplet), les poids sont renormalisés.\n")

    L.append("\n## Disponibilité par société\n")
    L.append("- **SFBT** : tous les ratios + SGPI complet (couverture 100 %).")
    L.append("- **DELICE** : holding (pas de SIG/stocks) → certains ratios indisponibles ; "
             "marge distordue (revenus = dividendes).")
    L.append("- **AB inBev / Coca-Cola** : ratios de structure et rentabilité disponibles ; "
             "RH (charges de personnel) absentes → efficacité RH et part personnel indisponibles.")
    L.append("\n## Limites connues\n")
    L.append("- **Ratios par salarié** (VA/salarié, RN/salarié) : non calculés — "
             "l'effectif (nombre d'employés) n'est pas fourni dans les données.")
    L.append("- **SFBT 2021 et 2022 (annuel)** : données absentes de la source → "
             "ratios non calculables ces années.")

    out = C.DOCS_DIR / "CATALOGUE_RATIOS.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"✔ Catalogue : {out}  ({len(RATIOS)} ratios + SGPI)")


if __name__ == "__main__":
    generer()
