"""run_all.py — Exécute toute la chaîne : données -> ratios -> Data Warehouse."""
import unify
import augment
import quality_report
import ratios
import build_warehouse
import ml_forecast
import gen_figures

if __name__ == "__main__":
    print("\n========== 1/7 UNIFICATION ==========")
    unify.main()
    print("\n========== 2/7 AUGMENTATION ==========")
    augment.main()
    print("\n========== 3/7 RAPPORT QUALITÉ ==========")
    quality_report.generer()
    print("\n========== 4/7 RATIOS MSI20000 ==========")
    ratios.main()
    print("\n========== 5/7 DATA WAREHOUSE (étoile) ==========")
    build_warehouse.construire()
    print("\n========== 6/7 PRÉVISION ML (LinReg vs RF vs Arbre de decision) ==========")
    ml_forecast.main()
    print("\n========== 7/7 FIGURES DU RAPPORT ==========")
    gen_figures.main()
    print("\n✅ Chaîne complète terminée. Sorties dans data/processed/, data/reports/, data/warehouse/.")
