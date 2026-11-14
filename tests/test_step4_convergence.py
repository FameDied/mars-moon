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
    CANONICAL_12_KEYS,
    FEATURE_BOUNDS_12D,
    PROJECT_ROOT,
    DB_PATH,
)

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
