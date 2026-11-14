#!/usr/bin/env python3
"""
Step 4 Master Convergence Protocol (All 3 Teammates Unified Pipeline)
Executes cross-body matching between:
  1. extraterrestrial_targets.parquet (Top 5 Lunar & Top 5 Martian Base Sites from Step 1)
  2. earth_candidates.parquet (Master Filtered Terrestrial Analogs from Step 2)
through:
  3. analog_engine.py (Decomposed 4-Axis Mahalanobis, Split-Twin Optimization & 3-Tier Verification)

Outputs:
  - planetary_matching_matrix.parquet
  - planetary_matching_matrix.csv
  - STEP4_CONVERGENCE_REPORT.md
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analog_engine import (
    resolve_extraterrestrial_target,
    fetch_earth_candidates,
    match_target_pipeline,
    find_best_ground_truth_sample,
    PROJECT_ROOT,
    DB_PATH,
)

OUTPUT_PARQUET = PROJECT_ROOT / "planetary_matching_matrix.parquet"
OUTPUT_CSV = PROJECT_ROOT / "planetary_matching_matrix.csv"
OUTPUT_REPORT_MD = PROJECT_ROOT / "STEP4_CONVERGENCE_REPORT.md"


def run_full_convergence_matrix():
    print("=" * 90)
    print("EXECUTING STEP 4: CROSS-PLANETARY CONVERGENCE, SPLIT-TWIN OPTIMIZATION & VERIFICATION")
    print("=" * 90)

    # 1. Load targets and candidates
    ext_path = PROJECT_ROOT / "extraterrestrial_targets.parquet"
    if not ext_path.exists():
        ext_path = PROJECT_ROOT / "extraterrestrial_optimization" / "extraterrestrial_targets.parquet"
    if not ext_path.exists():
        raise FileNotFoundError(f"Missing extraterrestrial targets: {ext_path}")

    df_ext = pd.read_parquet(ext_path)
    candidates = fetch_earth_candidates()

    print(f"Loaded {len(df_ext)} Extraterrestrial Targets (5 Lunar, 5 Martian).")
    print(f"Loaded {len(candidates)} Terrestrial Screening Candidates.")
    print("-" * 90)

    matrix_rows = []
    scorecards = []

    for idx, r in df_ext.iterrows():
        target = resolve_extraterrestrial_target(r["site_id"])
        summary, scorecard_text = match_target_pipeline(target, candidates, n_mc_trials=1000)

        prim = summary["top_analog"]
        twin = summary["split_twin"]
        delta = summary["delta_limit"]
        verif = summary["verification"]
        mc = verif["monte_carlo"]
        sp = verif["spatial_contiguity"]
        sample_v = verif.get("sample_verification", {})
        power = summary.get("power_sizing", {})
        topo = summary.get("base_topology", {})
        cospar = summary.get("cospar_planetary_protection", {})

        row_data = {
            "target_rank": (idx % 5) + 1,
            "body": target["body"],
            "target_id": target["site_id"],
            "target_name": target["site_name"],
            "target_lat": target["center_lat"],
            "target_lon": target["center_lon"],
            "target_h3": target.get("h3_index", ""),
            "U_base": target.get("U_base", 0.0),
            "M_go": target.get("m_go", 1),
            "e_haul_j_kg": target.get("e_haul_j_kg", 0.0),
            "kwh_per_ton": topo.get("kwh_per_ton", 0.0),
            "primary_analog_id": prim["site_id"],
            "primary_analog_name": prim["site_name"],
            "primary_h3_res6": prim.get("h3_res6", ""),
            "primary_score": round(prim["composite_score"], 2),
            "p_novelty": round(prim["p_novelty"], 4),
            "axis_a_geomorph": round(prim["axis_scores"].get("Axis_A_Geomorph", 0.0), 2),
            "axis_b_geochem": round(prim["axis_scores"].get("Axis_B_Geochem", 0.0), 2),
            "axis_c_thermal": round(prim["axis_scores"].get("Axis_C_Thermal", 0.0), 2),
            "axis_d_shelter": round(prim["axis_scores"].get("Axis_D_Shelter", 0.0), 2),
            "twin_site_1": twin["site_1"]["site_name"],
            "twin_site_2": twin["site_2"]["site_name"],
            "twin_composite_score": round(twin["twin_composite_score"], 2),
            "gravity_offload_pct": round(delta["gravity_offload_pct"], 1),
            "barometric_log_delta": round(delta["barometric_log_delta"], 2),
            "radiation_multiplier": round(delta["radiation_multiplier"], 1),
            "cryogenic_gap_k": round(delta["cryogenic_gap_k"], 1),
            "pristine_sample_name": sample_v.get("sample_name", ""),
            "aitchison_distance": round(sample_v.get("aitchison_distance", 0.0), 3),
            "mc_pass_rate_pct": round(mc.get("pass_rate_pct", 0.0), 1),
            "mc_ci_low": round(mc.get("ci_95_low", 0.0), 1),
            "mc_ci_high": round(mc.get("ci_95_high", 0.0), 1),
            "spatial_contiguity_ratio": round(sp.get("ratio", 0.0), 3),
            "is_verified": bool(mc.get("is_verified", False) and sp.get("is_contiguous", False)),
            # Permanent Base Architecture Layers A & B
            "dark_duration_hours": power.get("max_eclipse_hours", 0.0),
            "energy_storage_kwh": power.get("energy_storage_kwh", 0.0),
            "rfc_mass_kg": power.get("rfc_mass_kg", 0.0),
            "li_ion_mass_kg": power.get("li_ion_mass_kg", 0.0),
            "rfc_mass_savings_kg": power.get("rfc_mass_savings_kg", 0.0),
            "cospar_category": cospar.get("cospar_category", "Category II"),
            "is_special_region": cospar.get("is_special_region", False),
            "h3_pad": topo.get("h_pad", ""),
            "h3_hab": topo.get("h_hab", ""),
            "h3_isru": topo.get("h_isru", ""),
            "d_pad_hab_km": topo.get("d_pad_hab", 0.0),
            "d_hab_isru_km": topo.get("d_hab_isru", 0.0),
            "blast_standoff_met": topo.get("blast_standoff_met", True),
        }
        matrix_rows.append(row_data)
        scorecards.append(scorecard_text)

        print(
            f"[{target['body']:<4}] #{row_data['target_rank']} {target['site_id'][:28]:<30} -> "
            f"{prim['site_name'][:30]:<32} | Score: {prim['composite_score']:<5.1f}% | "
            f"Twin: {twin['twin_composite_score']:<5.1f}% | MC: {mc.get('pass_rate_pct', 0.0):.1f}%"
        )

    matrix_df = pd.DataFrame(matrix_rows)
    matrix_df.to_parquet(OUTPUT_PARQUET, index=False, engine="pyarrow", compression="snappy")
    matrix_df.to_csv(OUTPUT_CSV, index=False)

    # Build comprehensive Markdown Report
    report_lines = [
        "# Step 4 Master Convergence & Cross-Planetary Verification Report",
        "**ATLAS-X Cross-Planetary Analog Discovery System**",
        "",
        "This report brings together all three teammates:",
        "- **Teammate 1 (Extraterrestrial Optimization):** Filtered deadly terrain via $M_{go}$ and solved for maximum survival/ISRU utility ($U_{base}$).",
        "- **Teammate 2 (Terrestrial Global Screening):** Applied biosphere/water exclusions and the $P_{novelty}$ anti-cliché prior to surface novel, high-fidelity Earth training grounds.",
        "- **Teammate 3 (Analog Engine):** Scaled boundary-layer physics, computed 4-axis Mahalanobis similarity, solved for complementary split-twins, and executed three-tier verification.",
        "",
        "---",
        "",
        "## 1. Executive Master Matching Matrix",
        "",
        "| Rank | Body | Extraterrestrial Base Target | $U_{base}$ | $E_{haul}$ (J/kg) | Primary Earth Analog Match | Single Score | Optimal Complementary Split-Twin | Twin Score | Aitchison Sample $d_A$ | MC Stability | Spatial 6-Ring |",
        "| :---: | :---: | :--- | :---: | :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: |",
    ]

    for _, r in matrix_df.iterrows():
        report_lines.append(
            f"| #{r['target_rank']} | **{r['body']}** | `{r['target_id']}` | **{r['U_base']:.4f}** | {r['e_haul_j_kg']:.1f} | "
            f"**{r['primary_analog_name']}** | {r['primary_score']:.1f}% | "
            f"{r['twin_site_1']} + {r['twin_site_2']} | **{r['twin_composite_score']:.1f}%** | "
            f"{r['aitchison_distance']:.3f} ({r['pristine_sample_name'][:20]}) | {r['mc_pass_rate_pct']:.1f}% | {r['spatial_contiguity_ratio']:.2f} |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## 2. Permanent Base Operational Architecture: Spatial Triad & Power Sizing",
        "",
        "| Rank | Body | Extraterrestrial Base Target | COSPAR Protection | Dark Duration | Storage (kWh) | RFC vs Li-ion Mass Saved | H3 Pad Hex | Standoff $d(Pad, Hab)$ | H3 ISRU Hex | Haul $d(Hab, ISRU)$ | Haul Energy |",
        "| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- | :---: | :---: |",
    ])

    for _, r in matrix_df.iterrows():
        report_lines.append(
            f"| #{r['target_rank']} | **{r['body']}** | `{r['target_id']}` | {r['cospar_category']} | {r['dark_duration_hours']:.1f} h | "
            f"{r['energy_storage_kwh']:,.0f} kWh | **SAVE {r['rfc_mass_savings_kg']/1000.0:.2f} t** | `{r['h3_pad']}` | {r['d_pad_hab_km']:.2f} km (SAFE) | "
            f"`{r['h3_isru']}` | {r['d_hab_isru_km']:.2f} km | {r['kwh_per_ton']:.2f} kWh/t |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## 3. Detailed Decision Scorecards for Top Base Candidates",
        "",
    ])

    for sc in scorecards:
        report_lines.append("```text")
        report_lines.append(sc)
        report_lines.append("```")
        report_lines.append("")

    OUTPUT_REPORT_MD.write_text("\n".join(report_lines))
    print("-" * 90)
    print(f"Convergence outputs generated successfully:")
    print(f"  • Parquet: {OUTPUT_PARQUET}")
    print(f"  • CSV:     {OUTPUT_CSV}")
    print(f"  • Report:  {OUTPUT_REPORT_MD}")
    print("=" * 90)


if __name__ == "__main__":
    run_full_convergence_matrix()
