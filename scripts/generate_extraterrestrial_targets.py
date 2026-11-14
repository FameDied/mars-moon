#!/usr/bin/env python3
"""
Generate Extraterrestrial Targets Parquet (Top 5 Lunar & Top 5 Martian Base Sites)
Step 1 Master Synthesis: Combines the top 5 Lunar and top 5 Martian base sites
filtered by Hard Engineering Constraints (M_go), curvature-corrected horizon calculus,
and ISRU hauling energy, outputting extraterrestrial_targets.parquet with their canonical
z_T and sigma_T 12-dimensional vectors.
"""

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LUNAR_PARQUET = PROJECT_ROOT / "extraterrestrial_optimization" / "lunar" / "Lunarbases_locations.parquet"
MARS_PARQUET = PROJECT_ROOT / "extraterrestrial_optimization" / "mars" / "Marsbases_locations.parquet"

OUTPUT_ROOT_PARQUET = PROJECT_ROOT / "extraterrestrial_targets.parquet"
OUTPUT_STEP1_PARQUET = PROJECT_ROOT / "extraterrestrial_optimization" / "extraterrestrial_targets.parquet"
OUTPUT_CSV = PROJECT_ROOT / "extraterrestrial_targets.csv"
OUTPUT_MD = PROJECT_ROOT / "extraterrestrial_targets.md"

G_MOON = 1.62000
G_MARS = 3.72076
P_MOON = 1e-10
P_MARS = 610.0
T_MIN_MOON = 35.0
T_MIN_MARS = 145.0

CANONICAL_12_KEYS = [
    "mu_S", "TRI", "f_rock",
    "I_mafic", "I_hyd", "W_ice",
    "Gamma", "DeltaT_norm", "Phi_sol",
    "Theta_aeolian", "P_void", "R_rad"
]


def build_targets_table() -> pd.DataFrame:
    lunar_df = pd.read_parquet(LUNAR_PARQUET)
    mars_df = pd.read_parquet(MARS_PARQUET)

    top_lunar = lunar_df.sort_values(by="U_base", ascending=False).head(5).copy()
    top_mars = mars_df.sort_values(by="U_base", ascending=False).head(5).copy()

    top_lunar["body"] = "Moon"
    top_lunar["g_body"] = G_MOON
    top_lunar["p_atm_pa"] = P_MOON
    top_lunar["t_min_k"] = T_MIN_MOON

    top_mars["body"] = "Mars"
    top_mars["g_body"] = G_MARS
    top_mars["p_atm_pa"] = P_MARS
    top_mars["t_min_k"] = T_MIN_MARS

    combined = pd.concat([top_lunar, top_mars], ignore_index=True)

    # Ensure canonical columns
    if "DeltaT_norm" not in combined.columns and "Delta_T_norm" in combined.columns:
        combined["DeltaT_norm"] = combined["Delta_T_norm"]

    vector_12d_list = []
    sigma_12d_list = []

    for _, row in combined.iterrows():
        res_m = float(row.get("spatial_resolution_m", 5.0) or 5.0)
        res_factor = max(0.5, res_m / 5.0)

        mu_s = float(row["mu_S"])
        tri = float(row["TRI"])
        f_rock = float(row["f_rock"])
        i_mafic = float(row["I_mafic"])
        i_hyd = float(row["I_hyd"])
        w_ice = float(row["W_ice"])
        gamma = float(row["Gamma"])
        d_t_norm = float(row.get("DeltaT_norm", row.get("Delta_T_norm", 0.5)))
        phi_sol = float(row["Phi_sol"])
        theta_aeolian = float(row["Theta_aeolian"])
        p_void = float(row["P_void"])
        r_rad = float(row["R_rad"])

        vec = [
            mu_s, tri, f_rock,
            i_mafic, i_hyd, w_ice,
            gamma, d_t_norm, phi_sol,
            theta_aeolian, p_void, r_rad
        ]

        sig = [
            round(mu_s * 0.08 + 0.1 * res_factor, 3),
            round(tri * 0.08 + 0.1 * res_factor, 3),
            round(0.005 + 0.005 * res_factor, 4),
            round(i_mafic * 0.06 + 0.2, 3),
            round(0.01 * res_factor, 4),
            round(max(0.1, w_ice * 0.08), 3),
            round(gamma * 0.05 + 5.0, 2),
            round(0.03, 3),
            round(0.02, 3),
            round(0.002, 4),
            round(0.05, 3),
            round(max(5.0, r_rad * 0.05), 2),
        ]

        vector_12d_list.append(vec)
        sigma_12d_list.append(sig)

    combined["vector_12d"] = vector_12d_list
    combined["sigma_12d"] = sigma_12d_list

    return combined


def main():
    df = build_targets_table()

    # Save outputs
    df.to_parquet(OUTPUT_ROOT_PARQUET, index=False, engine="pyarrow", compression="snappy")
    df.to_parquet(OUTPUT_STEP1_PARQUET, index=False, engine="pyarrow", compression="snappy")
    
    # Exclude complex vector columns for simple CSV export
    csv_cols = [c for c in df.columns if c not in ("vector_12d", "sigma_12d")]
    df[csv_cols].to_csv(OUTPUT_CSV, index=False)

    # Generate Markdown documentation
    md_lines = [
        "# Top 10 Extraterrestrial Base Sites (5 Lunar + 5 Martian)",
        "Mathematically selected via Hard Engineering Constraints ($M_{go}$), Horizon Calculus, and ISRU Hauling Optimization ($U_{base}$).",
        "",
        "| Rank | Body | Site ID | Site Name | Region | Coordinates | $U_{base}$ | $E_{haul}$ (J/kg) | $M_{go}$ | Slope | Sunlight | Rocks |",
        "| :---: | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for idx, r in df.iterrows():
        rank = (idx % 5) + 1
        md_lines.append(
            f"| #{rank} | **{r['body']}** | `{r['site_id']}` | {r['site_name']} | {r['target_region']} | "
            f"({r['center_lat']:.3f}°, {r['center_lon']:.3f}°) | **{r['U_base']:.4f}** | {r['e_haul_j_kg']:.1f} | "
            f"PASS ({int(r['m_go'])}) | {r['mu_S']:.1f}° | {r['Phi_sol']*100:.1f}% | {r['f_rock']*100:.1f}% |"
        )

    OUTPUT_MD.write_text("\n".join(md_lines) + "\n")
    print(f"Generated extraterrestrial targets: {len(df)} sites (5 Lunar, 5 Martian).")
    print(f"  Root:  {OUTPUT_ROOT_PARQUET}")
    print(f"  Step1: {OUTPUT_STEP1_PARQUET}")


if __name__ == "__main__":
    main()
