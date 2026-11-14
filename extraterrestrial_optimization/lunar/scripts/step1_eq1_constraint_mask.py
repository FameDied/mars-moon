#!/usr/bin/env python3
"""
Step 1: Equation 1 - Hard Engineering Constraint Mask (M_go)

Reads: planetary_moon_mars.db (all 266 Moon candidate landing sites)
Applies:
  M_go(x) = I(mu_S <= 10 deg) * I(f_rock <= 0.05) * I(Phi_sol >= 0.80) * I(LoS_Earth >= 0.50)

"""

import math
from pathlib import Path
import sqlite3
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
LUNAR_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = LUNAR_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "planetary_moon_mars.db"

OUTPUT_CSV = LUNAR_DIR / "eq1_passed_sites.csv"
OUTPUT_PARQUET = LUNAR_DIR / "eq1_passed_sites.parquet"

SYNODIC_HOURS = 708.7  # Lunar daylight cycle


def main():
    print("=" * 70)
    print(" STEP 1: EQUATION 1 - HARD ENGINEERING CONSTRAINT MASK (M_go)")
    print(" Target Body: Moon (Lunar South Pole Candidate Sites)")
    print(" Output Directory: extraterrestrial_optimization/lunar/")
    print("=" * 70)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    query = """
        SELECT 
            s.site_id, s.feature_id, s.body, s.site_name, s.target_region, s.catalog_category,
            s.center_lat, s.center_lon, s.h3_index,
            s.macro_slope_deg, s.elevation_mola_m, s.rock_abundance_percent,
            s.dte_visibility_fraction, s.max_eclipse_hours,
            s.radiation_svf, s.trn_texture_score, s.traverse_distance_km,
            s.spatial_resolution_m, s.vertical_accuracy_m, s.measurement_confidence,
            s.water_equivalent_hydrogen_pct, s.mineral_resource_pct,
            s.thermal_inertia_si,
            COALESCE(h.fe_wt_pct, 12.0) as fe_wt_pct,
            COALESCE(h.ti_wt_pct, 3.5) as ti_wt_pct,
            COALESCE(h.diurnal_temp_swing_k, 280.0) as diurnal_temp_swing_k,
            COALESCE(h.has_subsurface_void, 0) as has_subsurface_void
        FROM site_engineering_safety s
        LEFT JOIN harmonized_sites h ON s.site_id = h.site_id
        WHERE s.body = 'Moon'
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    total_sites = len(rows)
    evaluated = []
    fail_counts = {"slope_gt_10": 0, "rock_gt_5": 0, "illum_lt_80": 0, "dte_lt_50": 0}

    for r in rows:
        slope = r["macro_slope_deg"] if r["macro_slope_deg"] is not None else 999.0
        rock_pct = r["rock_abundance_percent"] if r["rock_abundance_percent"] is not None else 999.0
        dte = r["dte_visibility_fraction"] if r["dte_visibility_fraction"] is not None else 0.0
        max_ecl = r["max_eclipse_hours"] or 0.0
        
        # Calculate solar illumination duty cycle fraction (Phi_sol)
        phi_sol = max(0.0, min(1.0, 1.0 - max_ecl / SYNODIC_HOURS))

        c_slope = (slope <= 10.0)
        c_rock = (rock_pct <= 5.0)
        c_illum = (phi_sol >= 0.80)
        c_dte = (dte >= 0.50)

        m_go = 1 if (c_slope and c_rock and c_illum and c_dte) else 0

        if not c_slope: fail_counts["slope_gt_10"] += 1
        if not c_rock: fail_counts["rock_gt_5"] += 1
        if not c_illum: fail_counts["illum_lt_80"] += 1
        if not c_dte: fail_counts["dte_lt_50"] += 1

        d = dict(r)
        d["mu_S"] = round(slope, 2)
        d["f_rock"] = round(rock_pct / 100.0, 4)
        d["Phi_sol"] = round(phi_sol, 4)
        d["m_go"] = m_go
        evaluated.append(d)

    df_all = pd.DataFrame(evaluated)
    df_passed = df_all[df_all["m_go"] == 1].copy().reset_index(drop=True)

    LUNAR_DIR.mkdir(parents=True, exist_ok=True)
    df_passed.to_csv(OUTPUT_CSV, index=False)
    df_passed.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy")

    print(f"\n[RESULTS]")
    print(f"  • Total Moon Sites Evaluated : {total_sites}")
    print(f"  • Passed Eq 1 (M_go = 1)     : {len(df_passed)} sites ({len(df_passed)/total_sites*100:.1f}%)")
    print(f"  • Rejected Sites (M_go = 0)  : {total_sites - len(df_passed)} sites")
    print(f"  • Failure Breakdown          : {fail_counts}")
    print(f"\n[SAVED IN LUNAR FOLDER]")
    print(f"  • CSV     : {OUTPUT_CSV}")
    print(f"  • Parquet : {OUTPUT_PARQUET}")
    print("\n✅ Step 1 completed. Run Step 2 next.")


if __name__ == "__main__":
    main()
