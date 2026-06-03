"""run_all.py — Exécute toute la chaîne : données -> ratios -> Data Warehouse."""
import unify
import augment
import quality_report
import ratios
import build_warehouse
import ml_forecast

if __name__ == "__main__":
    print("\n========== 1/6 UNIFICATION ==========")
    unify.main()
    print("\n========== 2/6 AUGMENTATION ==========")
    augment.main()
    print("\n========== 3/6 RAPPORT QUALITÉ ==========")
    quality_report.generer()
    print("\n========== 4/6 RATIOS MSI20000 ==========")
    ratios.main()
    print("\n========== 5/6 DATA WAREHOUSE (étoile) ==========")
    build_warehouse.construire()
    print("\n========== 6/6 PRÉVISION ML (LinReg vs Random Forest) ==========")
    ml_forecast.main()
    print("\n✅ Chaîne complète terminée. Sorties dans data/processed/, data/reports/, data/warehouse/.")
