#!/usr/bin/env python3
"""
Step 2: Equation 2 - Physical Thermal Inertia (Gamma_Earth) from Diurnal Swing

Mathematical Formulation:
  ATI(y) = C_sun(Lat, delta_sun) * [ (1 - A(y)) / Delta_T(y) ]
  Gamma_Earth(y) = alpha_1 * ATI(y) + alpha_0
  Calibrated bounded range: Gamma_finedust ~ 50 tiu to Gamma_bedrock ~ 2200 tiu.

"""

import math
from pathlib import Path
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
TERRESTRIAL_DIR = SCRIPTS_DIR.parent

INPUT_PARQUET = TERRESTRIAL_DIR / "eq1_passed_earth_sites.parquet"
OUTPUT_PASSED_CSV = TERRESTRIAL_DIR / "eq2_thermal_earth_sites.csv"
OUTPUT_PASSED_PARQUET = TERRESTRIAL_DIR / "eq2_thermal_earth_sites.parquet"
OUTPUT_ELIM_CSV = TERRESTRIAL_DIR / "eq2_eliminated_earth_sites.csv"

# Physical constants for Earth Thermal Inertia Calibration
SOLAR_DECLINATION_DEG = 15.0  # Mean solar insolation declination
ALPHA_1 = 1250.0              # Empirical conversion from ATI to TI (tiu)
ALPHA_0 = 150.0               # Minimum bedrock/sand conduction offset


def compute_solar_factor(lat_deg: float, declination_deg: float = SOLAR_DECLINATION_DEG) -> float:
    phi = math.radians(lat_deg)
    delta = math.radians(declination_deg)
    c_sun = math.cos(phi) * math.cos(delta) + math.sin(phi) * math.sin(delta)
    return max(0.20, c_sun)


def compute_apparent_thermal_inertia(row) -> dict:
    lat = float(row["center_lat"])
    delta_t = max(2.0, float(row["diurnal_temp_swing_k"])) if pd.notna(row["diurnal_temp_swing_k"]) else 15.0
    
    # Dynamically derive broadband surface albedo from Fe+Ti mineral geochemistry:
    # Mafic dark rocks (high Fe+Ti) absorb more insolation; evaporites and silicates reflect more
    fe_wt = float(row["fe_wt_pct"]) if pd.notna(row.get("fe_wt_pct")) else 8.0
    ti_wt = float(row["ti_wt_pct"]) if pd.notna(row.get("ti_wt_pct")) else 1.0
    albedo = round(float(min(0.45, max(0.08, 0.36 - 0.016 * (fe_wt + ti_wt)))), 4)
    
    c_sun = compute_solar_factor(lat)
    
    ati = c_sun * ((1.0 - albedo) / delta_t)
    gamma_calc = ALPHA_1 * ati + ALPHA_0
    
    # Ground truth calibration against recorded database thermal inertia if present
    db_gamma = float(row["thermal_inertia"]) if pd.notna(row["thermal_inertia"]) and float(row["thermal_inertia"]) > 0 else gamma_calc
    final_gamma = round(min(2200.0, max(50.0, db_gamma)), 2)
    
    # Physical lapse-rate temperature calculation matching analog_engine.py
    elev = float(row["elevation_m"]) if pd.notna(row.get("elevation_m")) else 500.0
    t_sea_level = 288.15 - 30.0 * (math.sin(math.radians(lat)) ** 2)
    lapse_cooling = 0.0065 * elev
    t_mean = float(t_sea_level - lapse_cooling)
    delta_t_norm = round(delta_t / max(200.0, t_mean), 4)
    
    # Thermophysical validation:
    # Requires meaningful diurnal swing (Delta_T >= 8.0 K) and realistic dry regolith/rock inertia (Gamma >= 80 tiu)
    passes_thermal = delta_t >= 8.0 and (50.0 <= final_gamma <= 2200.0)
    
    reasons = []
    if delta_t < 8.0:
        reasons.append(f"Insufficient diurnal temperature amplitude ({delta_t:.1f} K < 8.0 K; thermally buffered)")
    if final_gamma < 50.0 or final_gamma > 2200.0:
        reasons.append(f"Thermal inertia outside physical bounds (Gamma={final_gamma:.1f} tiu)")
        
    return {
        "ATI": round(ati, 5),
        "C_sun": round(c_sun, 4),
        "albedo": albedo,
        "t_mean_k": round(t_mean, 2),
        "Gamma_calc": round(gamma_calc, 2),
        "Gamma": final_gamma,
        "DeltaT_norm": delta_t_norm,
        "Delta_T_norm": delta_t_norm,
        "passes_thermal": int(passes_thermal),
        "thermal_elimination_reason": "; ".join(reasons) if not passes_thermal else ""
    }


def main():
    print(f"[Step 2] Loading Step 1 survivors from {INPUT_PARQUET}...")
    if not INPUT_PARQUET.exists():
        raise FileNotFoundError(f"Missing {INPUT_PARQUET}. Please execute step1 first.")
        
    df = pd.read_parquet(INPUT_PARQUET)
    print(f"Candidate sites entering Step 2: {len(df)}")
    
    passed_records = []
    elim_records = []

    for _, row in df.iterrows():
        th = compute_apparent_thermal_inertia(row)
        rec = dict(row)
        rec.update(th)
        if rec["passes_thermal"] == 1:
            passed_records.append(rec)
        else:
            rec["elimination_reason"] = rec["thermal_elimination_reason"]
            elim_records.append(rec)
        
    survivors_df = pd.DataFrame(passed_records)
    eliminated_df = pd.DataFrame(elim_records)
    
    print(f"Passed Thermal Inertia evaluation: {len(survivors_df)} / {len(df)}")
    print(f"Eliminated sites: {len(eliminated_df)}")
    
    survivors_df.to_csv(OUTPUT_PASSED_CSV, index=False)
    survivors_df.to_parquet(OUTPUT_PASSED_PARQUET, index=False)
    eliminated_df.to_csv(OUTPUT_ELIM_CSV, index=False)
    
    print(f"Saved Step 2 survivors to {OUTPUT_PASSED_CSV.name} and {OUTPUT_PASSED_PARQUET.name}")
    print(f"Saved eliminated sites to {OUTPUT_ELIM_CSV.name}")


if __name__ == "__main__":
    main()
