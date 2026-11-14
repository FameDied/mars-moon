#!/usr/bin/env python3
"""
Step 1: Equation 1 - Hard Engineering Constraint Mask (M_go) for Mars

Reads: planetary_moon_mars.db (all 258 Mars candidate landing sites)
Applies Mars Equations:
  M_go(x) = I(mu_S <= 10 deg) * I(f_rock <= 0.05) * I(Gate_Mars(x) == 1)
  Gate_Mars(x) = I(z_MOLA <= -2000 m) * I(|Lat| <= 45 deg)
  - z_MOLA <= -2000m: ensures sufficient atmospheric column mass for supersonic parachute / aerobraking
  - |Lat| <= 45 deg: avoids brutal polar night freezes and heavy CO2 frost deposition

"""

import math
from pathlib import Path
import sqlite3
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
MARS_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = MARS_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "planetary_moon_mars.db"

OUTPUT_CSV = MARS_DIR / "eq1_passed_sites.csv"
OUTPUT_PARQUET = MARS_DIR / "eq1_passed_sites.parquet"


def main():
    print("=" * 70)
    print(" STEP 1: EQUATION 1 - HARD ENGINEERING CONSTRAINT MASK (M_go) [MARS]")
    print(" Target Body: Mars (Candidate Landing Sites & Exploration Zones)")
    print(" Output Directory: extraterrestrial_optimization/mars/")
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
            s.thermal_inertia_si, s.wind_shear_mps,
            COALESCE(h.fe_wt_pct, 18.0) as fe_wt_pct,
            COALESCE(h.ti_wt_pct, 1.2) as ti_wt_pct,
            COALESCE(h.diurnal_temp_swing_k, 90.0) as diurnal_temp_swing_k,
            COALESCE(h.has_subsurface_void, 0) as has_subsurface_void
        FROM site_engineering_safety s
        LEFT JOIN harmonized_sites h ON s.site_id = h.site_id
        WHERE s.body = 'Mars'
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    total_sites = len(rows)
    evaluated = []
    fail_counts = {"slope_gt_10": 0, "rock_gt_5": 0, "elev_gt_minus_2000": 0, "lat_gt_45": 0}

    for r in rows:
        slope = r["macro_slope_deg"] if r["macro_slope_deg"] is not None else 999.0
        rock_pct = r["rock_abundance_percent"] if r["rock_abundance_percent"] is not None else 999.0
        elev = r["elevation_mola_m"] if r["elevation_mola_m"] is not None else 9999.0
        lat = r["center_lat"] if r["center_lat"] is not None else 999.0

        # Mars gating constraints:
        # 1. z_MOLA <= -2000m (atmospheric column mass)
        # 2. |Lat| <= 45 deg (thermal winter & solar angle)
        c_slope = (slope <= 10.0)
        c_rock = (rock_pct <= 5.0)
        c_elev = (elev <= -2000.0)
        c_lat = (abs(lat) <= 45.0)

        gate_mars = 1 if (c_elev and c_lat) else 0
        m_go = 1 if (c_slope and c_rock and gate_mars == 1) else 0

        if not c_slope: fail_counts["slope_gt_10"] += 1
        if not c_rock: fail_counts["rock_gt_5"] += 1
        if not c_elev: fail_counts["elev_gt_minus_2000"] += 1
        if not c_lat: fail_counts["lat_gt_45"] += 1

        d = dict(r)
        d["mu_S"] = round(slope, 2)
        d["f_rock"] = round(rock_pct / 100.0, 4)
        d["gate_mars"] = gate_mars
        d["m_go"] = m_go
        # Mars mid-latitude diurnal solar duty cycle ~0.50 baseline
        d["Phi_sol"] = round(0.50 * math.cos(math.radians(lat)), 4)
        evaluated.append(d)

    df_all = pd.DataFrame(evaluated)
    df_passed = df_all[df_all["m_go"] == 1].copy().reset_index(drop=True)

    MARS_DIR.mkdir(parents=True, exist_ok=True)
    df_passed.to_csv(OUTPUT_CSV, index=False)
    df_passed.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy")

    print(f"\n[RESULTS]")
    print(f"  • Total Mars Sites Evaluated : {total_sites}")
    print(f"  • Passed Eq 1 (M_go = 1)     : {len(df_passed)} sites ({len(df_passed)/total_sites*100:.1f}%)")
    print(f"  • Rejected Sites (M_go = 0)  : {total_sites - len(df_passed)} sites")
    print(f"  • Failure Breakdown          : {fail_counts}")
    print(f"\n[SAVED IN MARS FOLDER]")
    print(f"  • CSV     : {OUTPUT_CSV}")
    print(f"  • Parquet : {OUTPUT_PARQUET}")
    print("\n✅ Step 1 completed. Run Step 2 next.")


if __name__ == "__main__":
    main()
