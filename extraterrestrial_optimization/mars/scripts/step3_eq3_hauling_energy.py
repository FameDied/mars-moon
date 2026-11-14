#!/usr/bin/env python3
"""
Step 3: Equation 3 - ISRU Terramechanics Hauling Energy (E_haul) [MARS]

Reads: extraterrestrial_optimization/mars/eq2_horizon_sites.parquet (Only sites that survived both Eq 1 & Eq 2)
Applies Mars Physics:
  E_haul = g_Mars * d_ice * ( mu_roll * cos(mu_S) + sin(mu_S) )
  Units: J/kg
  Where g_Mars = 3.721 m/s^2, mu_roll = 0.15.

Requirement:
  Orders ALL surviving candidate sites from LEAST energy to HIGHEST energy.

"""

import math
from pathlib import Path
import sqlite3
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
MARS_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = MARS_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "planetary_moon_mars.db"

INPUT_PARQUET = MARS_DIR / "eq2_horizon_sites.parquet"
OUTPUT_CSV = MARS_DIR / "eq3_energy_ranked_sites.csv"
OUTPUT_PARQUET = MARS_DIR / "eq3_energy_ranked_sites.parquet"

# Physical constants for Mars
G_MARS = 3.721               # Martian surface gravity (m/s^2)
MU_ROLL = 0.15               # Regolith rolling resistance coefficient
MARS_SURFACE_RAD = 240.0     # mSv/year surface galactic cosmic radiation background
MARS_SCALE_HEIGHT_M = 11100.0  # Barometric scale height (11.1 km)
R_MARS_KM = 3389.5           # Mean Martian radius in km


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
    print(" STEP 3: EQUATION 3 - ISRU TERRAMECHANICS HAULING ENERGY (E_haul) [MARS]")
    print(f" Reading Eq 2 Survived Sites from: {INPUT_PARQUET.name}")
    print(" Output Directory: extraterrestrial_optimization/mars/")
    print("=" * 70)

    if not INPUT_PARQUET.exists():
        print(f"❌ Error: {INPUT_PARQUET} not found. Run step2_eq2_horizon_calculus.py first!")
        return

    df = pd.read_parquet(INPUT_PARQUET)
    print(f"Loaded {len(df)} candidate sites that survived both Equation 1 and Equation 2.")

    # Compute Hauling Energy: E_haul (J/kg) on Mars
    def calc_e_haul(row):
        d_ice_m = (row["traverse_distance_km"] or 3.0) * 1000.0
        slope_rad = row["mu_S_rad"]
        e_haul = G_MARS * d_ice_m * (MU_ROLL * math.cos(slope_rad) + math.sin(slope_rad))
        return round(e_haul, 2)

    df["e_haul_j_kg"] = df.apply(calc_e_haul, axis=1)

    # Populate 12-Dimensional Physical Vector components for Mars
    # Axis B: Geochem/ISRU (calibrated to CRISM continuum-removed band depth in [0.01, 0.15])
    df["I_mafic"] = (df["fe_wt_pct"] + df["ti_wt_pct"]).round(2)
    df["I_hyd"] = df["mineral_resource_pct"].apply(lambda m: round(min(0.15, 0.015 + 0.005 * (m or 5.0)), 4))
    df["W_ice"] = df["water_equivalent_hydrogen_pct"].fillna(10.0).round(2)

    # Axis C: Thermophysics
    df["Gamma"] = df["thermal_inertia_si"].fillna(260.0).round(1)
    # Normalized temperature swing (Delta T / T_mean, mean Mars temp ~210 K)
    df["Delta_T_norm"] = df.apply(
        lambda r: round(r["diurnal_temp_swing_k"] / 210.0, 3),
        axis=1
    )

    # Axis D: Environment/Shelter
    # Theta_aeolian: Shields wind shear parameter (dimensionless, derived from friction velocity u_*)
    # Theta = (rho_atm * u_star^2) / ((rho_grain - rho_atm) * g_Mars * d_p)
    # Using friction velocity u_* = sqrt(C_d) * w ≈ 0.05 * w (drag coefficient C_d ~ 0.0025)
    def calc_shields(wind_mps):
        w = wind_mps if (wind_mps is not None and not math.isnan(wind_mps)) else 10.0
        u_star = 0.05 * w  # boundary layer friction velocity (m/s)
        rho_atm = 0.020    # kg/m^3 atmospheric density at datum
        rho_grain = 2500.0 # kg/m^3 basaltic mineral sediment density
        d_p = 0.0001       # 100 microns mean grain diameter
        theta = (rho_atm * (u_star ** 2)) / ((rho_grain - rho_atm) * G_MARS * d_p)
        return round(max(0.0, min(2.0, theta)), 4)

    df["Theta_aeolian"] = df["wind_shear_mps"].apply(calc_shields)

    # Link P_void dynamically to subsurface_voids_caves via Haversine distance
    conn = sqlite3.connect(str(DB_PATH))
    caves_rows = conn.execute(
        "SELECT center_lat, center_lon FROM subsurface_voids_caves WHERE body_id = 'Mars'"
    ).fetchall()
    conn.close()

    def calc_p_void(row):
        lat = row["center_lat"]
        lon = row["center_lon"]
        d0_km = 1500.0  # Characteristic proximity scale for Martian subsurface void score
        min_d_km = 9999.0
        for clat, clon in caves_rows:
            if clat is not None and clon is not None:
                d_km = haversine_km(lat, lon, clat, clon, R_MARS_KM)
                if d_km < min_d_km:
                    min_d_km = d_km
        prox_score = round(0.95 * math.exp(-min_d_km / d0_km), 3)
        base_score = 0.90 if row.get("has_subsurface_void") == 1 else 0.05
        return max(base_score, min(0.95, max(0.05, prox_score)))

    df["P_void"] = df.apply(calc_p_void, axis=1)
    df["DeltaT_norm"] = df["Delta_T_norm"]

    # R_rad: Surface ionizing radiation dose (mSv/year)
    # Atmospheric column shielding factor: exp(-elev / scale_height)
    # Cavity/cave attenuation factor: 0.10 if P_void > 0.5
    def calc_radiation(row):
        elev = row["elevation_mola_m"] if row["elevation_mola_m"] is not None else -2000.0
        # Lower elevation = more atmosphere overhead = more shielding
        atm_factor = max(0.60, min(1.0, 1.0 - abs(elev) / 30000.0))
        void_factor = 0.10 if row["P_void"] > 0.5 else 1.0
        return round(MARS_SURFACE_RAD * atm_factor * void_factor, 1)

    df["R_rad"] = df.apply(calc_radiation, axis=1)

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

    print(f"\n[SAVED IN MARS FOLDER]")
    print(f"  • CSV     : {OUTPUT_CSV}")
    print(f"  • Parquet : {OUTPUT_PARQUET}")
    print("\n✅ Step 3 completed. Run Step 4 next.")


if __name__ == "__main__":
    main()
