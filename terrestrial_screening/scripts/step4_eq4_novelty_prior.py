#!/usr/bin/env python3
"""
Step 4: Equation 4 - Anti-Cliché Spatial Novelty Prior & Master Earth Candidates Ranking

Reads SEPARATELY:
  1. terrestrial_screening/eq2_thermal_earth_sites.parquet (Thermal & baseline environment from Eq 1 & 2)
  2. terrestrial_screening/eq3_spectral_12d_earth_sites.parquet (Spectral depth & canonical 12D vectors from Eq 3)

Mathematical Formulation:
  P_novelty(y) = prod_{m=1}^{M_famous} [ 1 - 0.85 * exp( - d_haversine^2(y, c_m) / (2 * L_m^2) ) ]
  With characteristic scale L_m = 250 km.


Outputs (when executed):
  terrestrial_screening/earth_candidates.csv (universal spreadsheet)
  terrestrial_screening/earth_candidates.xlsx (formatted Excel workbook)
  terrestrial_screening/earth_candidates.parquet (columnar dataset for similarity engine)
  terrestrial_screening/earth_candidates.md (complete readable Markdown report)
  terrestrial_screening/eq4_cliche_eliminated_sites.csv (sites eliminated due to cliche proximity)
"""

import math
from pathlib import Path
import pandas as pd
import numpy as np

SCRIPTS_DIR = Path(__file__).resolve().parent
TERRESTRIAL_DIR = SCRIPTS_DIR.parent

# Separate inputs as specified
INPUT_EQ2_THERMAL = TERRESTRIAL_DIR / "eq2_thermal_earth_sites.parquet"
INPUT_EQ3_SPECTRAL = TERRESTRIAL_DIR / "eq3_spectral_12d_earth_sites.parquet"

OUTPUT_CSV = TERRESTRIAL_DIR / "earth_candidates.csv"
OUTPUT_XLSX = TERRESTRIAL_DIR / "earth_candidates.xlsx"
OUTPUT_PARQUET = TERRESTRIAL_DIR / "earth_candidates.parquet"
OUTPUT_MD = TERRESTRIAL_DIR / "earth_candidates.md"
OUTPUT_ELIM_CSV = TERRESTRIAL_DIR / "eq4_cliche_eliminated_sites.csv"

# Coordinates of famous/over-studied analog stations to suppress (Anti-Cliche Prior)
FAMOUS_CLICHE_STATIONS = [
    (-77.85, 166.67, "McMurdo Dry Valleys, Antarctica"),
    (-24.08, -69.87, "Atacama Desert (Yungay Station), Chile"),
    (19.54, -155.58, "Mauna Loa (HI-SEAS), Hawaii"),
    (65.03, -16.75, "Askja Caldera, Iceland"),
    (75.38, -89.82, "Devon Island (Haughton Mars Project), Canada"),
    (37.70, -6.55, "Rio Tinto Mining District, Spain"),
    (31.05, -114.85, "Pinacate Volcanic Field, Mexico"),
]
CHARACTERISTIC_LENGTH_KM = 250.0  # L_m = 250 km
CLICHE_DISTANCE_CUTOFF_KM = 250.0 # Proximity threshold to eliminate over-studied sites


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two points on Earth (WGS84 spherical)."""
    R_EARTH_KM = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R_EARTH_KM * c


def compute_spatial_novelty_prior(lat: float, lon: float) -> tuple:
    """
    Computes P_novelty(y) penalizing proximity to over-studied analog facilities.
    Returns (novelty_score [0.15, 1.0], nearest_cliche_station, distance_km).
    """
    penalty_product = 1.0
    nearest_station = None
    min_dist = float("inf")

    for c_lat, c_lon, name in FAMOUS_CLICHE_STATIONS:
        dist = haversine_distance_km(lat, lon, c_lat, c_lon)
        if dist < min_dist:
            min_dist = dist
            nearest_station = name

        gaussian_term = math.exp(-(dist ** 2) / (2.0 * (CHARACTERISTIC_LENGTH_KM ** 2)))
        penalty_product *= (1.0 - 0.85 * gaussian_term)

    return round(float(penalty_product), 4), nearest_station, round(float(min_dist), 1)


def generate_earth_candidate_tradeoffs(row):
    """
    Generates data-driven Pros, Cons, and Tradeoffs for Earth Analog Training Grounds.
    """
    pros = []
    cons = []

    # 1. Geological & Lithological Fidelity
    name = str(row["site_name"]).lower()
    if "playa" in name or "danakil" in name or "pans" in name:
        pros.append("High evaporite salt flat fidelity; exceptional Mars sedimentary/lacustrine analog")
    if "crater" in name:
        pros.append("Impact crater morphology with authentic breccia and shock metamorphism")
    if "tube" in name or row["P_void"] > 0.5:
        pros.append("Accessible basaltic lava tube simulating subsurface planetary radiation shelter")
    if "ophiolite" in name:
        pros.append("Ultramafic peridotite mantle exposure; ideal for methane serpentinization studies")

    # 2. Thermal Regime
    delta_t = row.get("diurnal_temp_swing_k", 15.0)
    if delta_t >= 20.0:
        pros.append(f"Strong diurnal temperature swing ({delta_t:.1f} K) replicating day/night thermal stress")
    else:
        cons.append(f"Moderate diurnal temperature amplitude ({delta_t:.1f} K)")

    # 3. Spatial Novelty vs Over-Studied Cliché
    novelty = row["P_novelty"]
    if novelty >= 0.90:
        pros.append(f"High scientific novelty ({novelty*100:.1f}%); pristine under-studied training environment")
    elif novelty < 0.40:
        cons.append(f"Over-studied analog region near {row['nearest_famous_station']} ({row['dist_to_famous_km']:.0f} km away)")
    else:
        pros.append(f"Moderate spatial novelty ({novelty*100:.1f}%)")

    return "; ".join(pros), "; ".join(cons)


def main():
    print(f"[Step 4] Reading Step 2 and Step 3 inputs independently...")
    if not INPUT_EQ2_THERMAL.exists() or not INPUT_EQ3_SPECTRAL.exists():
        raise FileNotFoundError("Missing inputs. Ensure step2 and step3 have completed.")

    df_thermal = pd.read_parquet(INPUT_EQ2_THERMAL)
    df_spectral = pd.read_parquet(INPUT_EQ3_SPECTRAL)

    # Merge on analog_id
    shared_cols = [c for c in df_thermal.columns if c in df_spectral.columns and c != "analog_id"]
    df_merged = pd.merge(df_thermal.drop(columns=shared_cols, errors="ignore"), df_spectral, on="analog_id")

    # Compute Novelty Prior & Separate Novel Sites from Over-Studied / Cliché Sites
    passed_records = []
    elim_records = []

    for _, row in df_merged.iterrows():
        lat = float(row["center_lat"])
        lon = float(row["center_lon"])
        p_nov, nearest_station, dist_km = compute_spatial_novelty_prior(lat, lon)

        # Baseline Fidelity Score based on slope, thermal inertia, mafic/hydration minerals
        u_slope = max(0.0, 1.0 - (row["mu_S"] / 40.0))
        u_mafic = min(1.0, row["I_mafic"] / 15.0)
        u_hyd = min(1.0, row["I_hyd"] / 0.60)
        u_gamma = min(1.0, row["Gamma"] / 900.0)
        
        raw_fidelity = (0.25 * u_slope + 0.30 * u_mafic + 0.25 * u_hyd + 0.20 * u_gamma) * 100.0
        
        # Composite score weighted by Spatial Novelty Prior
        composite_score = round(raw_fidelity * p_nov, 2)

        rec = dict(row)
        rec["P_novelty"] = p_nov
        rec["nearest_famous_station"] = nearest_station
        rec["dist_to_famous_km"] = dist_km
        rec["raw_fidelity_score"] = round(raw_fidelity, 2)
        rec["composite_score"] = composite_score

        pros, cons = generate_earth_candidate_tradeoffs(rec)
        rec["pros"] = pros
        rec["cons"] = cons

        # Elimination Condition for Step 4:
        # Sites situated within 250 km of an over-studied cliche station (P_novelty < 0.35)
        # are removed into the cliche elimination file so researchers focus on novel environments.
        is_too_close = dist_km < CLICHE_DISTANCE_CUTOFF_KM or p_nov < 0.35
        if is_too_close:
            rec["elimination_reason"] = f"Over-studied / redundant cliché analog site: located within {dist_km:.1f} km of {nearest_station} (Novelty={p_nov*100:.1f}%)"
            elim_records.append(rec)
        else:
            passed_records.append(rec)

    final_df = pd.DataFrame(passed_records)
    elim_df = pd.DataFrame(elim_records)

    final_df = final_df.sort_values(by="composite_score", ascending=False).reset_index(drop=True)
    final_df["overall_rank"] = final_df.index + 1

    # Preserve ALL 12 physical dimensions and geochemical oxides in final outputs
    cols_order = [
        "overall_rank", "analog_id", "site_name", "country", "target_planetary_body", "composite_score", "raw_fidelity_score", "P_novelty",
        "mu_S", "TRI", "f_rock", "I_mafic", "I_hyd", "W_ice", "Gamma", "DeltaT_norm", "Delta_T_norm", "Phi_sol", "Theta_aeolian", "P_void", "R_rad",
        "p_pa", "t_min_k", "SiO2", "TiO2", "Al2O3", "FeO", "MgO", "CaO",
        "center_lat", "center_lon", "nearest_famous_station", "dist_to_famous_km", "pros", "cons"
    ]
    export_df = final_df[[c for c in cols_order if c in final_df.columns]].copy()

    # Save outputs
    export_df.to_csv(OUTPUT_CSV, index=False)
    export_df.to_parquet(OUTPUT_PARQUET, index=False)
    elim_df.to_csv(OUTPUT_ELIM_CSV, index=False)
    
    try:
        export_df.to_excel(OUTPUT_XLSX, index=False, engine="openpyxl")
    except Exception as e:
        print(f"Warning: Excel export error: {e}")

    # Generate Markdown summary without external tabulate dependency
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# Master Earth Analog Candidates Catalog (`earth_candidates`)\n\n")
        f.write("Evaluated using Step 2's 4-Equation Terrestrial Analog Characterization Pipeline.\n\n")
        f.write(f"**Total Surviving Candidates:** **{len(export_df)} sites** (Filtered through Eq 1-4)\n\n")
        
        # Headers
        headers = [
            "Rank", "Site ID", "Site Name", "Country", "Body", "Score", "Novelty",
            "Slope", "TRI", "Rocks", "I_mafic", "I_hyd", "Gamma", "Tradeoffs & Summary"
        ]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join([":---:" if i == 0 else ":---" for i in range(len(headers))]) + " |\n")
        
        for _, r in export_df.iterrows():
            f.write(
                f"| **{r['overall_rank']}** | `{r['analog_id']}` | {r['site_name']} | {r['country']} | "
                f"{r['target_planetary_body']} | **{r['composite_score']:.1f}%** | {r['P_novelty']*100:.1f}% | "
                f"{r['mu_S']:.1f}° | {r['TRI']:.2f}m | {r['f_rock']*100:.1f}% | {r['I_mafic']:.1f} | "
                f"{r['I_hyd']:.3f} | {r['Gamma']:.0f} | **Pros:** {r['pros']} <br>**Cons:** {r['cons']} |\n"
            )

    print(f"Successfully generated master Earth analog candidates in {TERRESTRIAL_DIR}:")
    print(f"  - Survivors: {len(export_df)} -> {OUTPUT_CSV.name}")
    print(f"  - Cliché Eliminated: {len(elim_df)} -> {OUTPUT_ELIM_CSV.name}")
    print(f"  - {OUTPUT_XLSX.name}")
    print(f"  - {OUTPUT_PARQUET.name}")
    print(f"  - {OUTPUT_MD.name}")


if __name__ == "__main__":
    main()
