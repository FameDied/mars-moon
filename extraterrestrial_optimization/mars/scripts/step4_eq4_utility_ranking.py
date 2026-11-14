#!/usr/bin/env python3
"""
Step 4: Equation 4 - Multi-Attribute Utility Score (U_base) & Comprehensive Tradeoff Index [MARS]

Reads SEPARATELY:
  1. extraterrestrial_optimization/mars/eq2_horizon_sites.parquet (Terrain, atmospheric depth & horizon profile from Eq 1 & 2)
  2. extraterrestrial_optimization/mars/eq3_energy_ranked_sites.parquet (ISRU hauling work & energy rank from Eq 3)

Performs Dual-Perspective Cross-Analysis:
  - Contrasts Terrain/Atmospheric Safety (Eq 1 & 2) vs ISRU Mining Efficiency (Eq 3)
  - Identifies sites that are champions in Eq 1 & 2 but low in Eq 3, and vice versa.
  - Computes composite U_base score with sensor resolution penalty:
    U_base(x) = M_go(x) * [ sum(w_k * u^k(x)) - lambda * sum(w_k^2 * (sigma_k / Range_k)^2) ]
  - Generates comprehensive tradeoffs, pros & cons for every site.

Outputs (in mars folder when executed):
  Marsbases_locations.csv (universal spreadsheet)
  Marsbases_locations.xlsx (formatted Excel workbook)
  Marsbases_locations.parquet (high-performance columnar store)
  Marsbases_locations.md (complete readable Markdown report with ALL rows)
"""

import math
from pathlib import Path
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
MARS_DIR = SCRIPTS_DIR.parent

# Separate inputs as requested:
INPUT_EQ2_SURVIVORS = MARS_DIR / "eq2_horizon_sites.parquet"  # Eq 1 & Eq 2 surviving profile
INPUT_EQ3_ENERGY = MARS_DIR / "eq3_energy_ranked_sites.parquet"   # Eq 3 hauling work & energy rank

OUTPUT_CSV = MARS_DIR / "Marsbases_locations.csv"
OUTPUT_XLSX = MARS_DIR / "Marsbases_locations.xlsx"
OUTPUT_PARQUET = MARS_DIR / "Marsbases_locations.parquet"
OUTPUT_MD = MARS_DIR / "Marsbases_locations.md"


def generate_mars_tradeoff_analysis(row):
    """
    Cross-analyzes Eq 1 & 2 findings against Eq 3 energy ranking.
    Articulates specific pros, cons, and tradeoffs for each candidate site on Mars.
    """
    pros = []
    cons = []

    # 1. Slope & Terrain (Eq 1 & 2)
    slope = row["mu_S"]
    if slope <= 4.5:
        pros.append(f"Very flat terrain ({slope:.1f}° slope, minimal tip-over hazard)")
    elif slope <= 7.0:
        pros.append(f"Manageable landing slope ({slope:.1f}°)")
    else:
        cons.append(f"Steeper incline ({slope:.1f}° slope, higher landing gear lateral stress)")

    # 2. Rock Hazard (Eq 1)
    rock = row["f_rock"] * 100.0
    if rock <= 3.0:
        pros.append(f"Clean landing ellipse (rock abundance {rock:.2f}%)")
    elif rock <= 4.2:
        pros.append(f"Moderate boulder field ({rock:.2f}%)")
    else:
        cons.append(f"Higher boulder density ({rock:.2f}%, close to 5.0% hazard limit; requires active hazard avoidance)")

    # 3. Elevation & Atmospheric Deceleration Column (z_MOLA) (Eq 1)
    elev = row["elevation_mola_m"]
    if elev <= -3500.0:
        pros.append(f"Deep atmospheric entry column ({elev:.0f}m MOLA; excellent parachute deceleration mass)")
    elif elev <= -2500.0:
        pros.append(f"Good aerodynamic braking margin ({elev:.0f}m MOLA)")
    else:
        cons.append(f"Higher landing elevation ({elev:.0f}m MOLA; thinner atmospheric column, narrow parachute margin)")

    # 4. Latitude & Thermal Winter (Eq 1)
    lat = row["center_lat"]
    if abs(lat) <= 20.0:
        pros.append(f"Equatorial zone ({lat:.1f}° lat; benign thermal winter and high annual solar flux)")
    elif abs(lat) <= 35.0:
        pros.append(f"Sub-tropical latitude ({lat:.1f}° lat)")
    else:
        cons.append(f"Mid-to-high latitude ({lat:.1f}° lat; severe winter dust storms and reduced solar power)")

    # 5. Wind Shear & Aeolian Transport (Eq 1 & 12D Vector)
    wind = row["wind_shear_mps"] if (row.get("wind_shear_mps") is not None and not math.isnan(row.get("wind_shear_mps", 0))) else 10.0
    if wind <= 8.0:
        pros.append(f"Low wind shear ({wind:.1f} m/s; minimal dust abrasion)")
    elif wind > 18.0:
        cons.append(f"High aeolian wind shear ({wind:.1f} m/s; severe dust deposition on solar arrays)")

    # 6. Horizon Obstruction (Eq 2)
    alpha_h = row["alpha_H_deg"]
    if alpha_h <= 20.0:
        pros.append(f"Wide open horizon (alpha_H = {alpha_h:.1f}°)")
    elif alpha_h > 26.0:
        cons.append(f"High crater rim / canyon obstruction (alpha_H = {alpha_h:.1f}°)")

    # 7. ISRU Hauling Energy & Cross-Check (Eq 3)
    e_haul = row["e_haul_j_kg"]
    dist = row["traverse_distance_km"]
    e_rank = row["energy_rank"]
    if e_haul <= 1200.0:
        pros.append(f"Top-tier ISRU haul efficiency (#{e_rank}: {e_haul:.1f} J/kg across {dist:.1f} km)")
    elif e_haul <= 2000.0:
        pros.append(f"Moderate haul energy (#{e_rank}: {e_haul:.1f} J/kg, {dist:.1f} km traverse)")
    else:
        cons.append(f"High ice haul energy (#{e_rank}: {e_haul:.1f} J/kg across {dist:.1f} km; high rover energy expenditure)")

    # Cross-equation Tradeoff Flag:
    # If site is top 25% in terrain safety (Eq 1 & 2) but bottom 50% in haul energy (Eq 3)
    if slope <= 5.0 and e_haul > 2200.0:
        cons.append(f"Tradeoff: Extremely safe flat terrain ({slope:.1f}°), but penalized by distant ice deposit (#{e_rank})")
    elif e_haul <= 1000.0 and slope > 6.5:
        cons.append(f"Tradeoff: Outstanding ice mining proximity (#{e_rank}), but requires landing on steeper terrain ({slope:.1f}°)")

    pros_str = "; ".join(pros) if pros else "Standard compliance"
    cons_str = "; ".join(cons) if cons else "No major red flags"

    return pros_str, cons_str


def main():
    print("=" * 70)
    print(" STEP 4: EQUATION 4 - MULTI-ATTRIBUTE UTILITY RANKING & TRADEOFF INDEX [MARS]")
    print(" Dual-Perspective Analysis: Cross-referencing Eq 1/2 with Eq 3")
    print(" Output Directory: extraterrestrial_optimization/mars/")
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

    print(f"  • Reading Input 1 (Eq 1 & Eq 2 Terrain, Atmosphere & Horizon): {len(df_terrain)} surviving sites")
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

    # 2. Normalized Benefit Functions u^k in [0, 1] for Mars:
    df["u_slope"] = df["mu_S"].apply(lambda s: max(0.0, min(1.0, 1.0 - (s / 10.0)**2)))
    df["u_rock"] = df["f_rock"].apply(lambda r: max(0.0, min(1.0, 1.0 - (r / 0.05)**1.5)))
    df["u_elev"] = df["elevation_mola_m"].apply(lambda z: max(0.0, min(1.0, (abs(z) - 2000.0) / 4500.0)))
    df["u_sol"] = df["Phi_sol"].apply(lambda p: max(0.0, min(1.0, p / 0.50)))

    # ISRU Hauling efficiency utility:
    e_min = df["e_haul_j_kg"].min()
    e_max = df["e_haul_j_kg"].max()
    denom = (e_max - e_min) if (e_max - e_min) > 0 else 1.0
    df["u_isru"] = df["e_haul_j_kg"].apply(lambda e: max(0.0, min(1.0, 1.0 - (e - e_min) / denom)))

    # Criteria Weights for Mars base selection:
    w_elev = 0.25
    w_slope = 0.20
    w_rock = 0.20
    w_sol = 0.15
    w_isru = 0.20

    # Sensor resolution uncertainty penalty (HiRISE 0.25-1m vs CTX vs MOLA):
    lam = 0.5
    range_res = 50.0
    sum_w_sq = (w_elev**2 + w_slope**2 + w_rock**2 + w_sol**2 + w_isru**2)

    def calc_u_base(row):
        benefit = (
            w_elev * row["u_elev"] +
            w_slope * row["u_slope"] +
            w_rock * row["u_rock"] +
            w_sol * row["u_sol"] +
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
    tradeoffs = [generate_mars_tradeoff_analysis(row) for _, row in df.iterrows()]
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
        "elevation_mola_m",
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
        "wind_shear_mps",
        "alpha_H_deg",
        "spatial_resolution_m",
        "pros",
        "cons"
    ]
    df_spreadsheet = df[spreadsheet_cols].copy()

    # Save CSV, Excel, and Parquet directly in mars folder
    df_spreadsheet.to_csv(OUTPUT_CSV, index=False)
    df_spreadsheet.to_excel(OUTPUT_XLSX, index=False, engine="openpyxl")
    df.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy")

    # Generate Marsbases_locations.md containing ALL rows
    md_rows = ""
    for _, r in df_spreadsheet.iterrows():
        md_rows += (
            f"| **{r['overall_rank']}** | #{r['energy_rank']} | `{r['site_id']}` | {r['target_region']} | "
            f"({r['center_lat']:.2f}°, {r['center_lon']:.2f}°) | **{r['U_base']:.4f}** | {r['e_haul_j_kg']:.1f} | "
            f"{r['elevation_mola_m']:.0f}m | {r['mu_S']:.1f}° | {r['TRI']:.2f} | {r['f_rock']*100:.1f}% | "
            f"{r['I_hyd']:.3f} | {r['Delta_T_norm']:.3f} | {r['Theta_aeolian']:.2f} | {r['P_void']:.3f} | "
            f"{r['wind_shear_mps']:.1f} m/s | {r['alpha_H_deg']:.1f}° | "
            f"**Pros:** {r['pros']}<br>**Cons:** {r['cons']} |\n"
        )

    md_content = rf"""# Complete Mars Base Candidate Locations & Tradeoff Index
**Universal Spreadsheet File:** `Marsbases_locations.csv`  
**Excel Workbook:** `Marsbases_locations.xlsx`  
**High-Performance Columnar Store:** `Marsbases_locations.parquet`  
**Total Surviving Candidates:** **{total_sites} sites** (Filtered through Eq 1 and Eq 2)  
**Location:** `extraterrestrial_optimization/mars/`

---

## 🧭 Funnel Progression & Separate Input Synthesis (Mars)
* **Input 1 (Eq 1 & Eq 2 Profile):** Evaluates landing slope, rock hazard, atmospheric aerobraking column ($z_{{\text{{MOLA}}}} \le -2000\text{{ m}}$), latitude bounds, and horizon obstruction.
* **Input 2 (Eq 3 Profile):** Evaluates volatile hauling work with $g_{{\text{{Mars}}}} = 3.721\text{{ m/s}}^2$ and ranks candidates from least energy to highest energy.
* **Eq 4 Dual Cross-Analysis:** Contrasts atmospheric and terrain safety against ice mining energy, highlighting tradeoffs (e.g. sites with excellent landing safety but distant ice reserves).

---

## 📊 Complete Spreadsheet Table of ALL {total_sites} Surviving Mars Base Locations

| Overall Rank | Energy Rank | Site ID | Region | Coordinates | $U_{{\text{{base}}}}$ Score | $E_{{\text{{haul}}}}$ (J/kg) | Elevation ($z_{{\text{{MOLA}}}}$) | Slope | TRI (m) | Rocks | $I_{{\text{{hyd}}}}$ | $\Delta T_{{\text{{norm}}}}$ | $\Theta_{{\text{{aeolian}}}}$ | $P_{{\text{{void}}}}$ | Wind Shear | Horizon | Tradeoffs & Engineering Cons |
| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
{md_rows}

---

## 📁 Downloadable Files
* **`Marsbases_locations.csv`**: Universal tabular spreadsheet for Excel, Google Sheets, or Pandas.
* **`Marsbases_locations.xlsx`**: Native Microsoft Excel workbook.
* **`Marsbases_locations.parquet`**: Parquet store with all 49 physical and spatial attributes.
"""
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[FINAL SPREADSHEET GENERATED - {total_sites} SURVIVING CANDIDATES]")
    print(f"  • Universal CSV   : {OUTPUT_CSV}")
    print(f"  • Excel Workbook  : {OUTPUT_XLSX}")
    print(f"  • Parquet Store   : {OUTPUT_PARQUET}")
    print(f"  • Full Report     : {OUTPUT_MD}")
    print(f"\nAll {total_sites} surviving sites with their Eq 1-2 metrics, Eq 3 energy ranking, and Eq 4 composite ranking & cons are exported in the mars folder.")


if __name__ == "__main__":
    main()
