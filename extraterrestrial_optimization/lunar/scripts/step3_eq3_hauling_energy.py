#!/usr/bin/env python3
"""
Step 3: Equation 3 - ISRU Terramechanics Hauling Energy (E_haul)

Reads: extraterrestrial_optimization/lunar/eq2_horizon_sites.parquet (Only sites that survived both Eq 1 & Eq 2)
Applies:
  E_haul = g_Moon * d_ice * ( mu_roll * cos(mu_S) + sin(mu_S) )
  Units: J/kg
Requirement:
  Orders ALL surviving candidate sites from LEAST energy to HIGHEST energy.

"""

import math
from pathlib import Path
import sqlite3
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
LUNAR_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = LUNAR_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "planetary_moon_mars.db"

INPUT_PARQUET = LUNAR_DIR / "eq2_horizon_sites.parquet"
OUTPUT_CSV = LUNAR_DIR / "eq3_energy_ranked_sites.csv"
OUTPUT_PARQUET = LUNAR_DIR / "eq3_energy_ranked_sites.parquet"

# Physical constants
G_MOON = 1.622          # m/s^2 surface gravity
MU_ROLL = 0.15          # Regolith rolling resistance coefficient
UNSHIELDED_MOON_RAD = 280.0  # mSv/year surface cosmic radiation
R_MOON_KM = 1737.4      # Mean lunar radius in km


def haversine_km(lat1, lon1, lat2, lon2, r_km):
    n_lon1 = ((lon1 + 180.0) % 360.0) - 180.0
    n_lon2 = ((lon2 + 180.0) % 360.0) - 180.0
    p1, l1 = math.radians(lat1), math.radians(n_lon1)
    p2, l2 = math.radians(lat2), math.radians(n_lon2)
    dp, dl = p2 - p1, l2 - l1
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r_km * math.asin(math.sqrt(min(1.0, a)))


def main():
    print("=" * 70)
    print(" STEP 3: EQUATION 3 - ISRU TERRAMECHANICS HAULING ENERGY (E_haul)")
    print(f" Reading Eq 2 Survived Sites from: {INPUT_PARQUET.name}")
    print(" Output Directory: extraterrestrial_optimization/lunar/")
    print("=" * 70)

    if not INPUT_PARQUET.exists():
        print(f"❌ Error: {INPUT_PARQUET} not found. Run step2_eq2_horizon_calculus.py first!")
        return

    df = pd.read_parquet(INPUT_PARQUET)
    print(f"Loaded {len(df)} candidate sites that survived both Equation 1 and Equation 2.")

    # Compute Hauling Energy: E_haul (J/kg)
    def calc_e_haul(row):
        d_ice_m = (row["traverse_distance_km"] or 2.5) * 1000.0
        slope_rad = row["mu_S_rad"]
        e_haul = G_MOON * d_ice_m * (MU_ROLL * math.cos(slope_rad) + math.sin(slope_rad))
        return round(e_haul, 2)

    df["e_haul_j_kg"] = df.apply(calc_e_haul, axis=1)

    # Populate 12-Dimensional Physical Vector components
    # Axis B: Geochem/ISRU
    df["I_mafic"] = (df["fe_wt_pct"] + df["ti_wt_pct"]).round(2)
    df["I_hyd"] = df["mineral_resource_pct"].apply(lambda m: round(min(1.0, (m or 4.0) / 15.0), 3))
    df["W_ice"] = df["water_equivalent_hydrogen_pct"].fillna(6.5).round(2)

    # Axis C: Thermophysics
    df["Gamma"] = df["thermal_inertia_si"].fillna(55.0).round(1)
    df["Delta_T_norm"] = df.apply(
        lambda r: round(r["diurnal_temp_swing_k"] / (120.0 if abs(r["center_lat"]) >= 80 else 250.0), 3),
        axis=1
    )

    # Axis D: Environment/Shelter
    df["Theta_aeolian"] = 0.0  # Vacuum exosphere

    # Link P_void dynamically to subsurface_voids_caves via Haversine distance
    conn = sqlite3.connect(str(DB_PATH))
    caves_rows = conn.execute(
        "SELECT center_lat, center_lon FROM subsurface_voids_caves WHERE body_id = 'Moon'"
    ).fetchall()
    conn.close()

    def calc_p_void(row):
        lat = row["center_lat"]
        lon = row["center_lon"]
        d0_km = 750.0  # Characteristic proximity scale for lunar subsurface void score
        min_d_km = 9999.0
        for clat, clon in caves_rows:
            if clat is not None and clon is not None:
                d_km = haversine_km(lat, lon, clat, clon, R_MOON_KM)
                if d_km < min_d_km:
                    min_d_km = d_km
        prox_score = round(0.95 * math.exp(-min_d_km / d0_km), 3)
        base_score = 0.85 if row.get("has_subsurface_void") == 1 else 0.05
        return max(base_score, min(0.95, max(0.05, prox_score)))

    df["P_void"] = df.apply(calc_p_void, axis=1)
    df["DeltaT_norm"] = df["Delta_T_norm"]
    df["R_rad"] = df.apply(
        lambda r: round(UNSHIELDED_MOON_RAD * (r["radiation_svf"] if r["radiation_svf"] else 0.75) * (0.10 if r["P_void"] > 0.5 else 1.0), 1),
        axis=1
    )

    # SORT ALL SURVIVORS BY LEAST ENERGY TO HIGHEST ENERGY
    df = df.sort_values(by="e_haul_j_kg", ascending=True).reset_index(drop=True)
    df["energy_rank"] = df.index + 1

    df.to_csv(OUTPUT_CSV, index=False)
    df.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy")

    print(f"\n[RESULTS - ALL {len(df)} SURVIVORS RANKED LEAST TO HIGHEST ENERGY]")
    print(f"  • Processed Sites                 : {len(df)}")
    print(f"  • Minimum Energy (Best Efficiency): {df.iloc[0]['e_haul_j_kg']} J/kg ({df.iloc[0]['site_id']})")
    print(f"  • Maximum Energy (Highest Work)   : {df.iloc[-1]['e_haul_j_kg']} J/kg ({df.iloc[-1]['site_id']})")
    print(f"  • Average Energy                  : {round(df['e_haul_j_kg'].mean(), 2)} J/kg")

    print(f"\n[SAVED IN LUNAR FOLDER]")
    print(f"  • CSV     : {OUTPUT_CSV}")
    print(f"  • Parquet : {OUTPUT_PARQUET}")
    print("\n✅ Step 3 completed. Run Step 4 next.")


if __name__ == "__main__":
    main()
