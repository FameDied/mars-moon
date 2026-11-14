#!/usr/bin/env python3
"""
Step 4: Equation 4 - Multi-Attribute Utility Score (U_base) & Comprehensive Tradeoff Index [LUNAR]

Reads SEPARATELY:
  1. extraterrestrial_optimization/lunar/eq2_horizon_sites.parquet (Terrain, safety & horizon profile from Eq 1 & 2)
  2. extraterrestrial_optimization/lunar/eq3_energy_ranked_sites.parquet (ISRU hauling work & energy rank from Eq 3)

Performs Dual-Perspective Cross-Analysis:
  - Contrasts Terrain/Horizon Safety (Eq 1 & 2) vs ISRU Mining Efficiency (Eq 3)
  - Identifies sites that are champions in Eq 1 & 2 but low in Eq 3, and vice versa.
  - Computes composite U_base score with sensor resolution penalty:
    U_base(x) = M_go(x) * [ sum(w_k * u^k(x)) - lambda * sum(w_k^2 * (sigma_k / Range_k)^2) ]
  - Generates comprehensive tradeoffs, pros & cons for every site.

"""

import math
from pathlib import Path
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
LUNAR_DIR = SCRIPTS_DIR.parent

# Separate inputs as requested:
INPUT_EQ2_SURVIVORS = LUNAR_DIR / "eq2_horizon_sites.parquet"  # Eq 1 & Eq 2 surviving profile
INPUT_EQ3_ENERGY = LUNAR_DIR / "eq3_energy_ranked_sites.parquet"   # Eq 3 hauling work & energy rank

OUTPUT_CSV = LUNAR_DIR / "Lunarbases_locations.csv"
OUTPUT_XLSX = LUNAR_DIR / "Lunarbases_locations.xlsx"
OUTPUT_PARQUET = LUNAR_DIR / "Lunarbases_locations.parquet"
OUTPUT_MD = LUNAR_DIR / "Lunarbases_locations.md"


def generate_tradeoff_analysis(row):
    """
    Cross-analyzes Eq 1 & 2 findings against Eq 3 energy ranking.
    Articulates specific pros, cons, and tradeoffs for each candidate site.
    """
    pros = []
    cons = []

    # 1. Slope & Terrain (Eq 1 & 2)
    slope = row["mu_S"]
    if slope <= 6.0:
        pros.append(f"Very gentle terrain ({slope:.1f}° slope, minimal tip-over hazard)")
    elif slope <= 7.5:
        pros.append(f"Manageable landing slope ({slope:.1f}°)")
    else:
        cons.append(f"Steeper incline ({slope:.1f}° slope, higher landing gear stress)")

    # 2. Rock Hazard (Eq 1)
    rock = row["f_rock"] * 100.0
    if rock <= 3.5:
        pros.append(f"Clean landing pad (rock abundance {rock:.2f}%)")
    elif rock <= 4.2:
        pros.append(f"Moderate boulder field ({rock:.2f}%)")
    else:
        cons.append(f"Higher boulder density ({rock:.2f}%, close to 5.0% cutoff; requires active hazard avoidance)")

    # 3. Solar Illumination Duty Cycle (Eq 1)
    illum = row["Phi_sol"] * 100.0
    if illum >= 96.0:
        pros.append(f"Exceptional solar duty cycle ({illum:.1f}% illumination, short eclipse)")
    elif illum >= 90.0:
        pros.append(f"Reliable solar power ({illum:.1f}%)")
    else:
        cons.append(f"Lower continuous sunlight ({illum:.1f}%, requires higher battery/RFC reserves)")

    # 4. Earth Visibility / LoS (Eq 1)
    dte = row["dte_visibility_fraction"] * 100.0
    if dte >= 90.0:
        pros.append(f"Direct-to-Earth line-of-sight ({dte:.1f}%, continuous comms)")
    elif dte >= 80.0:
        pros.append(f"Good direct communications ({dte:.1f}%)")
    else:
        cons.append(f"Limited direct Earth LoS ({dte:.1f}%, periodic telecom blackouts requiring orbital relay)")

    # 5. Horizon Obstruction (Eq 2)
    alpha_h = row["alpha_H_deg"]
    if alpha_h <= 27.0:
        pros.append(f"Broad open horizon (alpha_H = {alpha_h:.1f}°)")
    elif alpha_h > 30.0:
        cons.append(f"Higher crater rim horizon blockage (alpha_H = {alpha_h:.1f}°)")

    # 6. ISRU Hauling Energy & Cross-Check (Eq 3)
    e_haul = row["e_haul_j_kg"]
    dist = row["traverse_distance_km"]
    e_rank = row["energy_rank"]
    if e_haul <= 650.0:
        pros.append(f"Top-tier ISRU haul efficiency (#{e_rank}: {e_haul:.1f} J/kg across {dist:.1f} km)")
    elif e_haul <= 850.0:
        pros.append(f"Moderate haul energy (#{e_rank}: {e_haul:.1f} J/kg, {dist:.1f} km traverse)")
    else:
        cons.append(f"High ice haul energy (#{e_rank}: {e_haul:.1f} J/kg across {dist:.1f} km; higher battery drain on mining rovers)")

    # Cross-equation Tradeoff Flag:
    # If site is top 25% in terrain safety (Eq 1 & 2) but bottom 50% in haul energy (Eq 3)
    if slope <= 6.5 and e_haul > 900.0:
        cons.append(f"Tradeoff: Excellent landing terrain ({slope:.1f}°), but penalized by longer ice haul (#{e_rank})")
    elif e_haul <= 600.0 and slope > 7.0:
        cons.append(f"Tradeoff: Superb ice haul proximity (#{e_rank}), but requires landing on steeper terrain ({slope:.1f}°)")

    pros_str = "; ".join(pros) if pros else "Standard compliance"
    cons_str = "; ".join(cons) if cons else "No major red flags"

    return pros_str, cons_str


def main():
    print("=" * 70)
    print(" STEP 4: EQUATION 4 - MULTI-ATTRIBUTE UTILITY RANKING & TRADEOFF INDEX")
    print(" Dual-Perspective Analysis: Cross-referencing Eq 1/2 with Eq 3")
    print(" Output Directory: extraterrestrial_optimization/lunar/")
    print("=" * 70)

    # 1. Check and read separate inputs
    if not INPUT_EQ2_SURVIVORS.exists():
        print(f"❌ Error: {INPUT_EQ2_SURVIVORS} not found. Run step2_eq2_horizon_calculus.py first!")
        return
    if not INPUT_EQ3_ENERGY.exists():
        print(f"❌ Error: {INPUT_EQ3_ENERGY} not found. Run step3_eq3_hauling_energy.py first!")
        return

    df_terrain = pd.read_parquet(INPUT_EQ2_SURVIVORS)
    df_energy = pd.read_parquet(INPUT_EQ3_ENERGY)

    print(f"  • Reading Input 1 (Eq 1 & Eq 2 Terrain & Horizon): {len(df_terrain)} surviving sites")
    print(f"  • Reading Input 2 (Eq 3 Hauling Energy & Ranking): {len(df_energy)} energy-ranked sites")

    # Merge on site_id to combine the separate answers
    energy_cols_to_merge = [
        "site_id", "e_haul_j_kg", "energy_rank",
        "I_mafic", "I_hyd", "W_ice", "Gamma", "Delta_T_norm",
        "Theta_aeolian", "P_void", "R_rad"
    ]
    df = pd.merge(df_terrain, df_energy[energy_cols_to_merge], on="site_id")
    total_sites = len(df)
    print(f"  • Integrated {total_sites} verified candidate sites for dual cross-analysis.")

    # 2. Normalized Benefit Functions u^k in [0, 1]
    df["u_slope"] = df["mu_S"].apply(lambda s: max(0.0, min(1.0, 1.0 - (s / 10.0)**2)))
    df["u_rock"] = df["f_rock"].apply(lambda r: max(0.0, min(1.0, 1.0 - (r / 0.05)**1.5)))
    df["u_illum"] = df["Phi_sol"].apply(lambda p: max(0.0, min(1.0, (p - 0.80) / 0.20)))
    df["u_los"] = df["dte_visibility_fraction"].apply(lambda d: max(0.0, min(1.0, (d - 0.50) / 0.50)))

    # ISRU Hauling efficiency utility:
    e_min = df["e_haul_j_kg"].min()
    e_max = df["e_haul_j_kg"].max()
    denom = (e_max - e_min) if (e_max - e_min) > 0 else 1.0
    df["u_isru"] = df["e_haul_j_kg"].apply(lambda e: max(0.0, min(1.0, 1.0 - (e - e_min) / denom)))

    # Criteria Weights
    w_slope = 0.20
    w_rock = 0.20
    w_illum = 0.25
    w_los = 0.15
    w_isru = 0.20

    # Sensor resolution uncertainty penalty:
    lam = 0.5
    range_res = 50.0
    sum_w_sq = (w_slope**2 + w_rock**2 + w_illum**2 + w_los**2 + w_isru**2)

    def calc_u_base(row):
        benefit = (
            w_slope * row["u_slope"] +
            w_rock * row["u_rock"] +
            w_illum * row["u_illum"] +
            w_los * row["u_los"] +
            w_isru * row["u_isru"]
        )
        sigma = row["spatial_resolution_m"] if (row["spatial_resolution_m"] and not math.isnan(row["spatial_resolution_m"])) else 5.0
        penalty = lam * sum_w_sq * ((sigma / range_res) ** 2)
        return round(max(0.0, min(1.0, benefit - penalty)), 4)

    df["U_base"] = df.apply(calc_u_base, axis=1)

    # Re-rank by overall composite utility U_base
    df = df.sort_values(by="U_base", ascending=False).reset_index(drop=True)
    df["overall_rank"] = df.index + 1

    # Generate Engineering Pros and Cons for each site
    tradeoffs = [generate_tradeoff_analysis(row) for _, row in df.iterrows()]
    df["pros"] = [t[0] for t in tradeoffs]
    df["cons"] = [t[1] for t in tradeoffs]

    # Organize clean spreadsheet columns with canonical 12D physical parameters
    df["DeltaT_norm"] = df["Delta_T_norm"]
    spreadsheet_cols = [
        "overall_rank",
        "energy_rank",
        "site_id",
        "site_name",
        "target_region",
        "center_lat",
        "center_lon",
        "U_base",
        "e_haul_j_kg",
        "traverse_distance_km",
        "mu_S",
        "TRI",
        "f_rock",
        "I_mafic",
        "I_hyd",
        "W_ice",
        "Gamma",
        "Delta_T_norm",
        "Phi_sol",
        "Theta_aeolian",
        "P_void",
        "R_rad",
        "dte_visibility_fraction",
        "alpha_H_deg",
        "spatial_resolution_m",
        "pros",
        "cons"
    ]
    df_spreadsheet = df[spreadsheet_cols].copy()

    # Save CSV, Excel, and Parquet directly in lunar folder
    df_spreadsheet.to_csv(OUTPUT_CSV, index=False)
    df_spreadsheet.to_excel(OUTPUT_XLSX, index=False, engine="openpyxl")
    df.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy")

    # Generate Lunarbases_locations.md containing ALL rows
    md_rows = ""
    for _, r in df_spreadsheet.iterrows():
        md_rows += (
            f"| **{r['overall_rank']}** | #{r['energy_rank']} | `{r['site_id']}` | {r['target_region']} | "
            f"({r['center_lat']:.4f}°, {r['center_lon']:.4f}°) | **{r['U_base']:.4f}** | {r['e_haul_j_kg']:.1f} | "
            f"{r['traverse_distance_km']:.1f} | {r['mu_S']:.1f}° | {r['TRI']:.2f} | {r['f_rock']*100:.1f}% | "
            f"{r['I_hyd']:.3f} | {r['Delta_T_norm']:.3f} | {r['Theta_aeolian']:.2f} | {r['P_void']:.3f} | "
            f"{r['Phi_sol']*100:.1f}% | {r['dte_visibility_fraction']*100:.1f}% | {r['alpha_H_deg']:.1f}° | "
            f"**Pros:** {r['pros']}<br>**Cons:** {r['cons']} |\n"
        )

    md_content = rf"""# Complete Lunar Base Candidate Locations & Tradeoff Index
**Universal Spreadsheet File:** `Lunarbases_locations.csv`  
**Excel Workbook:** `Lunarbases_locations.xlsx`  
**High-Performance Columnar Store:** `Lunarbases_locations.parquet`  
**Total Surviving Candidates:** **{total_sites} sites** (Filtered through Eq 1 and Eq 2)  
**Location:** `extraterrestrial_optimization/lunar/`

---

## 🧭 Funnel Progression & Separate Input Synthesis
* **Input 1 (Eq 1 & Eq 2 Profile):** Evaluates terrain flatness, rock clearance, solar power, and horizon obstruction.
* **Input 2 (Eq 3 Profile):** Evaluates ISRU volatile hauling energy and ranks candidates from least energy to highest energy.
* **Eq 4 Dual Cross-Analysis:** Contrasts terrain safety against ice mining energy, capturing candidates that excel in Eq 1/2 but are penalized by distant ice deposits in Eq 3, or vice-versa.

---

## 📊 Complete Spreadsheet Table of ALL {total_sites} Surviving Lunar Base Locations

| Overall Rank | Energy Rank | Site ID | Region | Coordinates | $U_{{\text{{base}}}}$ Score | $E_{{\text{{haul}}}}$ (J/kg) | Dist (km) | Slope | TRI (m) | Rocks | $I_{{\text{{hyd}}}}$ | $\Delta T_{{\text{{norm}}}}$ | $\Theta_{{\text{{aeolian}}}}$ | $P_{{\text{{void}}}}$ | Sunlight | Earth LoS | Horizon | Tradeoffs & Engineering Cons |
| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
{md_rows}

---

## 📁 Downloadable Files
* **`Lunarbases_locations.csv`**: Universal tabular spreadsheet for Excel, Google Sheets, or Pandas.
* **`Lunarbases_locations.xlsx`**: Native Microsoft Excel workbook.
* **`Lunarbases_locations.parquet`**: Parquet store with all 49 physical and spatial attributes.
"""
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[FINAL SPREADSHEET GENERATED - {total_sites} SURVIVING CANDIDATES]")
    print(f"  • Universal CSV   : {OUTPUT_CSV}")
    print(f"  • Excel Workbook  : {OUTPUT_XLSX}")
    print(f"  • Parquet Store   : {OUTPUT_PARQUET}")
    print(f"  • Full Report     : {OUTPUT_MD}")
    print(f"\nAll {total_sites} surviving sites with their Eq 1-2 metrics, Eq 3 energy ranking, and Eq 4 composite ranking & cons are exported in the lunar folder.")


if __name__ == "__main__":
    main()
