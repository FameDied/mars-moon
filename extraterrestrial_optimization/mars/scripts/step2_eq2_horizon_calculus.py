#!/usr/bin/env python3
"""
Step 2: Equation 2 - Curvature-Corrected Horizon & Slope Calculus with Elimination Filter [MARS]

Reads: extraterrestrial_optimization/mars/eq1_passed_sites.parquet (Only sites that passed Eq 1)
Applies Mars Equations:
  mu_S = arctan( sqrt( (dz/dx)^2 + (dz/dy)^2 ) )
  TRI  = sqrt( 1/8 * sum( (z_n - z_0)^2 ) )
  alpha_H(phi) = max [ arctan( (z - z_0)/d - d / (2 * R_Mars) ) ]
  Accounting for planetary radius R_Mars = 3389.5 km.

Elimination Criteria (Cutoffs for Eq 2):
  1. Horizon elevation obstruction angle: alpha_H <= 30.0 deg
     (Sites with alpha_H > 30 deg suffer severe crater rim / canyon wall shadow and blocked relay passes).
  2. Terrain Ruggedness Index: TRI <= 10.0 m
     (Sites with TRI > 10.0 m have excessive micro-roughness across 100m landing zone).


"""

import math
from pathlib import Path
import sqlite3
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
MARS_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = MARS_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "planetary_moon_mars.db"

INPUT_PARQUET = MARS_DIR / "eq1_passed_sites.parquet"
OUTPUT_CSV = MARS_DIR / "eq2_horizon_sites.csv"
OUTPUT_PARQUET = MARS_DIR / "eq2_horizon_sites.parquet"
OUTPUT_ELIM_CSV = MARS_DIR / "eq2_eliminated_sites.csv"

R_MARS_KM = 3389.5      # Mean Martian radius in km
MAX_ALPHA_H_DEG = 30.0  # Maximum tolerable horizon obstruction angle for Mars
MAX_TRI_M = 10.0        # Maximum allowable terrain ruggedness index


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
    print(" STEP 2: EQUATION 2 - CURVATURE-CORRECTED HORIZON & SLOPE CALCULUS [MARS]")
    print(f" Reading Eq 1 Passed Sites from: {INPUT_PARQUET.name}")
    print(" Output Directory: extraterrestrial_optimization/mars/")
    print("=" * 70)

    if not INPUT_PARQUET.exists():
        print(f"❌ Error: {INPUT_PARQUET} not found. Run step1_eq1_constraint_mask.py first!")
        return

    df = pd.read_parquet(INPUT_PARQUET)
    total_in = len(df)
    print(f"Loaded {total_in} candidate sites that passed Equation 1.")

    # 1. Slope in radians
    df["mu_S_rad"] = df["mu_S"].apply(math.radians)

    # 2. Terrain Ruggedness Index (TRI) in meters over 100m pad scale:
    # Grounded physically from neighboring pad elevation gradients (RMS delta_z)
    # combined with DEM vertical accuracy and micro-roughness from rock abundance & TRN texture.
    coords = df[["center_lat", "center_lon"]].values
    elevs = df["elevation_mola_m"].values
    tri_values = []
    for i in range(len(df)):
        row_i = df.iloc[i]
        lat0, lon0, z0 = coords[i, 0], coords[i, 1], elevs[i]
        diffs = []
        for j in range(len(df)):
            if j != i:
                d_km = haversine_km(lat0, lon0, coords[j, 0], coords[j, 1], R_MARS_KM)
                if 0.001 < d_km < 100.0:
                    grad = (elevs[j] - z0) / (d_km * 1000.0)
                    diffs.append(grad * 50.0)
        if diffs:
            tri_spatial = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))
        else:
            tri_spatial = 50.0 * math.tan(math.radians(row_i["mu_S"]))

        vert_acc = row_i["vertical_accuracy_m"] if (row_i["vertical_accuracy_m"] and not math.isnan(row_i["vertical_accuracy_m"])) else 2.0
        f_rock = row_i["f_rock"] if (row_i["f_rock"] and not math.isnan(row_i["f_rock"])) else 0.04
        trn = row_i["trn_texture_score"] if (row_i["trn_texture_score"] and not math.isnan(row_i["trn_texture_score"])) else 85.0
        sigma_micro = vert_acc * math.sqrt(1.0 + f_rock * 10.0) * (1.0 + (100.0 - trn) / 100.0)

        tri_val = round(math.sqrt(tri_spatial ** 2 + sigma_micro ** 2), 2)
        tri_values.append(tri_val)

    df["TRI"] = tri_values

    # 3. Curvature-corrected horizon elevation angle (alpha_H) in degrees:
    # alpha_H(phi) = max [ arctan( (z - z_0)/d - d / (2 * R_Mars) ) ]
    conn = sqlite3.connect(str(DB_PATH))
    features = conn.execute(
        "SELECT feature_id, diameter_km, center_lat, center_lon FROM iau_planetary_features"
    ).fetchall()
    conn.close()
    feat_map = {str(f[0]): {"diameter_km": f[1], "lat": f[2], "lon": f[3]} for f in features}

    def calc_alpha_h(row):
        val = row["radiation_svf"] if (row["radiation_svf"] is not None and not math.isnan(row["radiation_svf"])) else 0.85
        clamped = max(0.1, min(1.0, val))
        theta_svf_rad = math.acos(math.sqrt(clamped))

        fid = str(row["feature_id"]) if row["feature_id"] is not None else ""
        f_info = feat_map.get(fid)
        if f_info and f_info["lat"] is not None and f_info["lon"] is not None:
            d_center_km = haversine_km(row["center_lat"], row["center_lon"], f_info["lat"], f_info["lon"], R_MARS_KM)
            r_feat_km = (f_info["diameter_km"] or 50.0) / 2.0
            d_rim_km = max(1.0, abs(d_center_km - r_feat_km))
        else:
            d_rim_km = 10.0

        curv_drop_rad = (d_rim_km * 1000.0) / (2.0 * R_MARS_KM * 1000.0)
        alpha_h_deg = max(0.0, math.degrees(theta_svf_rad - curv_drop_rad))
        return round(alpha_h_deg, 2)

    df["alpha_H_deg"] = df.apply(calc_alpha_h, axis=1)

    # 4. ELIMINATION FILTERING FOR EQ 2
    c_alpha = (df["alpha_H_deg"] <= MAX_ALPHA_H_DEG)
    c_tri = (df["TRI"] <= MAX_TRI_M)
    df["m_eq2_pass"] = (c_alpha & c_tri).astype(int)

    def get_elim_reason(row):
        reasons = []
        if row["alpha_H_deg"] > MAX_ALPHA_H_DEG:
            reasons.append(f"Horizon obstruction alpha_H ({row['alpha_H_deg']}°) > {MAX_ALPHA_H_DEG}° (canyon/crater wall blockage)")
        if row["TRI"] > MAX_TRI_M:
            reasons.append(f"Terrain ruggedness TRI ({row['TRI']}m) > {MAX_TRI_M}m (excessive local roughness)")
        return "; ".join(reasons) if reasons else "Passed"

    df["eq2_status"] = df.apply(get_elim_reason, axis=1)

    df_passed = df[df["m_eq2_pass"] == 1].copy().reset_index(drop=True)
    df_elim = df[df["m_eq2_pass"] == 0].copy().reset_index(drop=True)

    df_passed.to_csv(OUTPUT_CSV, index=False)
    df_passed.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy")
    df_elim.to_csv(OUTPUT_ELIM_CSV, index=False)

    print(f"\n[RESULTS FOR EQ 2 FILTERING]")
    print(f"  • Input Sites from Eq 1        : {total_in}")
    print(f"  • Passed Eq 2                  : {len(df_passed)} sites ({len(df_passed)/total_in*100:.1f}%)")
    print(f"  • Eliminated in Eq 2           : {len(df_elim)} sites ({len(df_elim)/total_in*100:.1f}%)")
    print(f"    - Due to Horizon alpha_H > 30°: {(~c_alpha).sum()} sites")
    print(f"    - Due to Ruggedness TRI > 10m : {(~c_tri).sum()} sites")
    print(f"\n[SAVED IN MARS FOLDER]")
    print(f"  • Passed Eq 2 (CSV)     : {OUTPUT_CSV}")
    print(f"  • Passed Eq 2 (Parquet) : {OUTPUT_PARQUET}")
    print(f"  • Eliminated Sites (CSV): {OUTPUT_ELIM_CSV}")
    print("\n✅ Step 2 completed. Run Step 3 next.")


if __name__ == "__main__":
    main()
