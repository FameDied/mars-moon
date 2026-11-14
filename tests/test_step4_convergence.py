"""
Unit & Integration Test Suite: Step 4 Cross-Planetary Convergence,
Split-Twin Optimization, 3-Tier Verification & Decision Scorecards

Verifies:
1. Master Extraterrestrial Targets dataset (extraterrestrial_targets.parquet, Top 5 Lunar + Top 5 Martian)
2. Master Earth Candidates dataset (earth_candidates.parquet)
3. Ground-Truth Geochemical Verification against authentic Apollo & Martian samples (Aitchison distance d_A)
4. Complementary Split-Twin Optimization (E1*, E2*)
5. Monte Carlo rank stability with 4-axis uncertainty error bars (±1.96σ)
6. Spatial contiguity verification (6-ring H3 cluster check)
7. Earth analog limit delta-vectors (gravity, vacuum, radiation, cryogenic)
8. CLI command 'python3 cli.py match' on individual targets, JSON output, and master matrix
"""

import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from analog_engine import (
    resolve_extraterrestrial_target,
    fetch_earth_candidates,
    match_target_pipeline,
    find_best_ground_truth_sample,
    optimize_complementary_split_twins,
    monte_carlo_rank_stability_test,
    spatial_contiguity_verification,
    compute_earth_analog_limit_delta,
    calculate_temporal_power_sizing,
    get_cospar_planetary_protection_flag,
    compute_three_hexagon_base_topology,
    compute_decomposed_4axis_scores,
    CANONICAL_12_KEYS,
    FEATURE_BOUNDS_12D,
    PROJECT_ROOT,
    DB_PATH,
)
from core.site_suitability import check_hard_cutoffs

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestStep4ExtraterrestrialTargetsParquet:
    def test_extraterrestrial_targets_exists_and_schema(self):
        root_p = ROOT_DIR / "extraterrestrial_targets.parquet"
        step1_p = ROOT_DIR / "extraterrestrial_optimization" / "extraterrestrial_targets.parquet"

        assert root_p.exists() or step1_p.exists(), "extraterrestrial_targets.parquet must exist"
        p = root_p if root_p.exists() else step1_p
        df = pd.read_parquet(p)

        assert len(df) == 10, f"Expected exactly 10 top targets (5 Lunar + 5 Martian), got {len(df)}"
        lunar = df[df["body"] == "Moon"]
        mars = df[df["body"] == "Mars"]
        assert len(lunar) == 5, f"Expected 5 Lunar targets, got {len(lunar)}"
        assert len(mars) == 5, f"Expected 5 Mars targets, got {len(mars)}"

    def test_target_engineering_gates_and_physics_vectors(self):
        p = ROOT_DIR / "extraterrestrial_targets.parquet"
        df = pd.read_parquet(p)

        for _, r in df.iterrows():
            # Engineering gate M_go must be 1 (PASS)
            assert int(r["m_go"]) == 1, f"Site {r['site_id']} must pass M_go engineering gate"
            # Survival utility U_base must be strictly positive
            assert float(r["U_base"]) > 0.5, f"Site {r['site_id']} U_base too low: {r['U_base']}"
            # ISRU hauling energy E_haul must be positive
            assert float(r["e_haul_j_kg"]) > 0.0, f"Site {r['site_id']} E_haul must be positive"

            # Check 12D physical state vector
            vec = r["vector_12d"]
            sig = r["sigma_12d"]
            assert len(vec) == 12, "vector_12d must have 12 dimensions"
            assert len(sig) == 12, "sigma_12d must have 12 dimensions"
            for val in sig:
                assert val > 0.0, f"Uncertainty sigma {val} must be strictly positive"


class TestStep4EarthCandidatesParquet:
    def test_earth_candidates_loading(self):
        candidates = fetch_earth_candidates()
        assert len(candidates) == 8, f"Expected 8 master Earth candidates, got {len(candidates)}"

        for c in candidates:
            assert "site_id" in c and c["site_id"].startswith("EARTH_ANALOG_")
            assert "site_name" in c and len(c["site_name"]) > 5
            assert "vector_12d" in c and len(c["vector_12d"]) == 12
            assert "sigma_12d" in c and len(c["sigma_12d"]) == 12
            assert "h3_res6" in c and len(c["h3_res6"]) > 5, "H3 res6 index must be populated"
            assert "p_novelty" in c and 0.15 <= c["p_novelty"] <= 1.0


class TestStep4ThreeTierVerification:
    def test_tier1_ground_truth_geochemical_sample_mars(self):
        target = resolve_extraterrestrial_target("Jezero Crater", body="Mars")
        candidates = fetch_earth_candidates()
        best_cand = candidates[0]

        verif = find_best_ground_truth_sample(target, best_cand, db_path=DB_PATH)
        assert "sample_id" in verif
        assert "sample_name" in verif
        assert "aitchison_distance" in verif
        assert verif["aitchison_distance"] > 0.0, "Aitchison distance must be strictly positive"
        assert verif["is_verified"] is True, "Geochemical distance must pass simplex boundary"

    def test_tier1_ground_truth_geochemical_sample_moon(self):
        target = resolve_extraterrestrial_target("MOON_CLPS_GRIFFIN_VIPER_NOBILE", body="Moon")
        candidates = fetch_earth_candidates()
        best_cand = candidates[0]

        verif = find_best_ground_truth_sample(target, best_cand, db_path=DB_PATH)
        assert "APOLLO" in verif["sample_id"] or "VIPER" in verif["sample_id"]
        assert verif["aitchison_distance"] > 0.0

    def test_tier2_monte_carlo_rank_stability_and_axis_uncertainties(self):
        target = resolve_extraterrestrial_target("Jezero Crater")
        candidates = fetch_earth_candidates()

        mc = monte_carlo_rank_stability_test(
            target["vector_12d"],
            target["sigma_12d"],
            candidates,
            candidate_index=0,
            n_trials=300
        )
        assert mc["trials"] == 300
        assert 0.0 <= mc["pass_rate"] <= 1.0
        assert "axis_uncertainties" in mc
        for axis_name in ("Axis_A_Geomorph", "Axis_B_Geochem", "Axis_C_Thermal", "Axis_D_Shelter"):
            assert axis_name in mc["axis_uncertainties"]
            assert "ci_half_width" in mc["axis_uncertainties"][axis_name]
            assert mc["axis_uncertainties"][axis_name]["ci_half_width"] >= 0.0

    def test_tier3_spatial_contiguity_verification(self):
        res = spatial_contiguity_verification(center_score=75.0, neighbor_scores=[74.0, 73.5, 75.2, 74.8, 73.9, 74.5], contiguity_threshold=0.85)
        assert res["is_contiguous"] is True
        assert res["ratio"] >= 0.85


class TestStep4SplitTwinOptimization:
    def test_split_twin_coverage_maximization(self):
        target = resolve_extraterrestrial_target("Jezero Crater")
        candidates = fetch_earth_candidates()

        twin = optimize_complementary_split_twins(
            target["vector_12d"],
            target["sigma_12d"],
            candidates
        )
        assert "site_1" in twin
        assert "site_2" in twin
        assert twin["site_1"]["site_id"] != twin["site_2"]["site_id"], "Twin sites must be distinct"
        assert twin["twin_composite_score"] > 0.0
        assert len(twin["axis_coverage"]) == 4


class TestStep4CLIMatchCommand:
    def test_cli_match_jezero_crater(self):
        cmd = [sys.executable, str(ROOT_DIR / "cli.py"), "match", "--target", "Jezero Crater", "--trials", "200"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
        assert res.returncode == 0, f"CLI match failed: {res.stderr}"
        out = res.stdout

        assert "PLANETARY DECISION SCORECARD" in out
        assert "TARGET EXTRATERRESTRIAL BASE SUMMARY" in out
        assert "PRIMARY TERRESTRIAL ANALOG" in out
        assert "DECOMPOSED 4-AXIS SIMILARITY BREAKDOWN" in out
        assert "COMPLEMENTARY 'SPLIT-TWIN' ANALOG OPTIMIZATION" in out
        assert "THE 'EARTH ANALOG LIMIT' DELTA-VECTOR" in out
        assert "THREE-TIER SCIENTIFIC VERIFICATION AUDIT" in out
        assert "Closest Matching Pristine Sample" in out

    def test_cli_match_moon_nobile(self):
        cmd = [sys.executable, str(ROOT_DIR / "cli.py"), "match", "--target", "MOON_CLPS_GRIFFIN_VIPER_NOBILE", "--trials", "200"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
        assert res.returncode == 0, f"CLI match failed: {res.stderr}"
        out = res.stdout
        assert "MOON_CLPS_GRIFFIN_VIPER_NOBILE" in out
        assert "Moon" in out

    def test_cli_match_json_output(self):
        cmd = [sys.executable, str(ROOT_DIR / "cli.py"), "match", "--target", "Jezero Crater", "--trials", "100", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
        assert res.returncode == 0, f"CLI match JSON failed: {res.stderr}"

        data = json.loads(res.stdout)
        assert "target" in data
        assert "top_analog" in data
        assert "split_twin" in data
        assert "delta_limit" in data
        assert "verification" in data
        assert "scorecard_text" in data

    def test_cli_match_all_matrix(self):
        cmd = [sys.executable, str(ROOT_DIR / "cli.py"), "match", "--target", "all"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
        assert res.returncode == 0, f"CLI match all failed: {res.stderr}"
        out = res.stdout
        assert "STEP 4 MASTER CROSS-PLANETARY MATCHING MATRIX" in out
        assert "MOON_CLPS_GRIFFIN_VIPER_NOBILE" in out
        assert "MARS_PAD_HELLAS_DEEP_FLOOR_12" in out


class TestStep4PermanentBaseLayers:
    def test_temporal_power_sizing_moon(self):
        power = calculate_temporal_power_sizing("Moon", max_eclipse_hours=102.5, base_power_kw=25.0)
        assert power["body"] == "Moon"
        assert power["energy_storage_kwh"] == 2562.5
        assert power["rfc_mass_kg"] < power["li_ion_mass_kg"]
        assert power["mass_savings_pct"] == pytest.approx(60.0, abs=0.5)
        assert power["rfc_mass_savings_kg"] > 8500.0  # Saves ~8.5 metric tons

    def test_temporal_power_sizing_mars_dust_storm(self):
        power = calculate_temporal_power_sizing("Mars", dust_storm_tau=3.0)
        assert power["body"] == "Mars"
        assert power["solar_reduction_pct"] >= 90.0
        assert power["kilopower_units"] == 2
        assert power["kilopower_total_mass_kg"] == 3000.0

    def test_cospar_planetary_protection_classification(self):
        # Moon polar cold trap with volatiles
        cospar_moon = get_cospar_planetary_protection_flag("LUNAR_PAD_NOBILE_01", "Moon", center_lat=-85.2, water_ice_pct=5.5)
        assert cospar_moon["cospar_category"] == "Category II*"
        assert cospar_moon["is_special_region"] is False

        # Mars accessible ice deposit
        cospar_mars_ice = get_cospar_planetary_protection_flag("MARS_PAD_HELLAS_ICE_01", "Mars", center_lat=-38.94, water_ice_pct=25.0)
        assert "Category IVb" in cospar_mars_ice["cospar_category"]
        assert cospar_mars_ice["is_special_region"] is True
        assert "< 0.03" in cospar_mars_ice["bioburden_limit"]

        # Mars dry surface
        cospar_mars_dry = get_cospar_planetary_protection_flag("MARS_PAD_GALE_01", "Mars", center_lat=-4.5, water_ice_pct=0.5)
        assert cospar_mars_dry["cospar_category"] == "Category IVa"
        assert cospar_mars_dry["is_special_region"] is False

    def test_three_hexagon_base_topology(self):
        target = resolve_extraterrestrial_target("Jezero Crater")
        topo = compute_three_hexagon_base_topology(target, h3_resolution=7)

        assert "h_pad" in topo and "h_hab" in topo and "h_isru" in topo
        assert topo["blast_standoff_met"] is True, "Plume blast standoff must be met (>= 1.5 km)"
        assert topo["d_pad_hab"] >= 1.5, f"Pad-Hab standoff {topo['d_pad_hab']} km must be >= 1.5 km"
        assert topo["d_hab_isru"] > 0.0
        assert "ascii_diagram" in topo and len(topo["ascii_diagram"]) > 50

    def test_jezero_axis_b_geochemistry_score_is_calibrated(self):
        """
        Verifies that Axis B for Jezero Crater is physically calibrated to continuum-removed
        band depth, scoring ~40-75% against terrestrial hydrothermal suites rather than 0.12%.
        """
        target = resolve_extraterrestrial_target("Jezero Crater")
        candidates = fetch_earth_candidates()

        danakil = next(c for c in candidates if "DANAKIL" in c["site_id"])
        scores_4axis = compute_decomposed_4axis_scores(
            target["vector_12d"],
            danakil["vector_12d"],
            target["sigma_12d"],
            danakil["sigma_12d"]
        )
        axis_b_score = scores_4axis["Axis_B_Geochem"]["score"]
        assert 40.0 <= axis_b_score <= 80.0, f"Axis B score {axis_b_score:.2f}% must be in realistic [40, 80]% range, not 0.12%"

    def test_mars_latitude_cutoff_relaxation_55_degrees(self):
        """
        Verifies that relaxing Mars latitude cutoff to 55 deg allows high-latitude NASA SWIM ice
        candidates (e.g. Utopia Planitia at 46.8 deg) to qualify, but disqualifies them at 45 deg.
        """
        # Site at latitude 46.8 deg
        utopia_site = {
            "body": "Mars",
            "center_lat": 46.76,
            "center_lon": 110.05,
            "slope_deg": 1.4,
            "rock_abundance_pct": 2.1,
            "solar_illum_pct": 98.3,
            "earth_vis_pct": 70.0,
            "cold_trap_dist_km": 0.0,
        }
        # Passes with 55 deg cutoff
        assert check_hard_cutoffs(utopia_site, max_lat_deg=55.0) is True
        # Fails with legacy 45 deg cutoff
        assert check_hard_cutoffs(utopia_site, max_lat_deg=45.0) is False

    def test_cli_topology_command(self):
        cmd = [sys.executable, str(ROOT_DIR / "cli.py"), "topology", "--target", "Jezero Crater", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
        assert res.returncode == 0, f"CLI topology failed: {res.stderr}"

        data = json.loads(res.stdout)
        assert "base_topology" in data
        assert "power_sizing" in data
        assert "cospar_protection" in data
        assert data["base_topology"]["blast_standoff_met"] is True
