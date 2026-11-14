"""
Unit Test Suite: Terrestrial Analog Screening Pipeline
and Integration with ATLAS-X analog_engine.py

Verifies:
1. Step 1: Biosphere, Anthropogenic & Geopolitical Mask (Wolf Amendment & ITAR filtering)
2. Step 2: Apparent Thermal Inertia & Lapse-Rate Temperature Swing
3. Step 3: Continuum-Removed Spectral Absorption Depth, Cave Proximity, & 12D Vectors
4. Step 4: Anti-Cliche Spatial Novelty Prior & Master Earth Candidates Ranking
5. Integration: Full end-to-end execution of analog_engine.match_target_pipeline with Earth candidates
"""

import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from analog_engine import (
    fetch_earth_candidates,
    fetch_terrestrial_candidates_from_db,
    generate_synthetic_target,
    match_target_pipeline,
    DB_PATH,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
TERRESTRIAL_DIR = ROOT_DIR / "terrestrial_screening"


class TestTerrestrialStep1BiosphereMask:
    def test_step1_outputs_exist(self):
        passed_csv = TERRESTRIAL_DIR / "eq1_passed_earth_sites.csv"
        passed_parquet = TERRESTRIAL_DIR / "eq1_passed_earth_sites.parquet"
        elim_csv = TERRESTRIAL_DIR / "eq1_eliminated_earth_sites.csv"

        assert passed_csv.exists(), "Step 1 passed CSV missing"
        assert passed_parquet.exists(), "Step 1 passed Parquet missing"
        assert elim_csv.exists(), "Step 1 eliminated CSV missing"

    def test_geopolitical_exclusion_wolf_amendment(self):
        elim_df = pd.read_csv(TERRESTRIAL_DIR / "eq1_eliminated_earth_sites.csv")
        # Check that Qaidam Basin (China) was eliminated due to Wolf Amendment / ITAR
        assert not elim_df.empty, "Step 1 should eliminate at least one site"
        china_elim = elim_df[elim_df["country"].str.lower().str.contains("china")]
        assert len(china_elim) >= 1, "Qaidam Basin in China must be eliminated by NASA Wolf Amendment"
        assert "Wolf Amendment" in str(china_elim.iloc[0]["elimination_reason"])

    def test_dynamic_ndvi_and_environmental_bounds(self):
        passed_df = pd.read_parquet(TERRESTRIAL_DIR / "eq1_passed_earth_sites.parquet")
        assert len(passed_df) == 11, f"Expected 11 passed sites, got {len(passed_df)}"
        for _, row in passed_df.iterrows():
            ndvi = float(row["ndvi_est"])
            assert 0.015 <= ndvi < 0.12, f"NDVI {ndvi} out of dry analog bounds for {row['site_name']}"
            assert int(row["water_mask"]) == 0, "Water mask must be 0 for land site"
            assert int(row["night_lights"]) == 0, "Night lights must be 0 for remote analog"
            assert float(row["mean_slope_deg"]) <= 45.0, "Slope must be <= 45 degrees"


class TestTerrestrialStep2ThermalInertia:
    def test_step2_outputs_exist(self):
        passed_parquet = TERRESTRIAL_DIR / "eq2_thermal_earth_sites.parquet"
        assert passed_parquet.exists(), "Step 2 passed Parquet missing"

    def test_thermal_inertia_physical_bounds(self):
        df = pd.read_parquet(TERRESTRIAL_DIR / "eq2_thermal_earth_sites.parquet")
        assert len(df) == 11, "All 11 non-China arid sites should pass thermal requirements"
        for _, row in df.iterrows():
            gamma = float(row["Gamma"])
            assert 50.0 <= gamma <= 2200.0, f"Gamma {gamma} outside physical thermal inertia bounds"
            albedo = float(row["albedo"])
            assert 0.08 <= albedo <= 0.45, f"Albedo {albedo} outside physical rock bounds"
            t_mean = float(row["t_mean_k"])
            assert 250.0 <= t_mean <= 315.0, f"T_mean {t_mean} outside terrestrial bounds"
            assert "DeltaT_norm" in row, "Missing DeltaT_norm alias"
            assert "Delta_T_norm" in row, "Missing Delta_T_norm alias"


class TestTerrestrialStep3Spectral12DVector:
    def test_step3_outputs_exist(self):
        passed_parquet = TERRESTRIAL_DIR / "eq3_spectral_12d_earth_sites.parquet"
        assert passed_parquet.exists(), "Step 3 passed Parquet missing"

    def test_spectral_hydration_band_depth(self):
        df = pd.read_parquet(TERRESTRIAL_DIR / "eq3_spectral_12d_earth_sites.parquet")
        assert len(df) == 11, "All 11 sites should pass Step 3"
        for _, row in df.iterrows():
            i_hyd = float(row["I_hyd"])
            assert 0.005 <= i_hyd <= 1.0, f"Hydration band depth {i_hyd} out of bounds"
            i_mafic = float(row["I_mafic"])
            assert i_mafic > 0.0, f"Mafic index {i_mafic} must be positive"

    def test_dynamic_oxide_simplex(self):
        df = pd.read_parquet(TERRESTRIAL_DIR / "eq3_spectral_12d_earth_sites.parquet")
        oxide_keys = ["SiO2", "TiO2", "Al2O3", "FeO", "MgO", "CaO"]
        for _, row in df.iterrows():
            total = sum(float(row[k]) for k in oxide_keys)
            assert pytest.approx(total, rel=1e-2) == 100.0, f"Oxide sum {total} != 100%"
            for k in oxide_keys:
                assert float(row[k]) > 0.0, f"Oxide {k} must be strictly positive"

    def test_subsurface_void_accessibility(self):
        df = pd.read_parquet(TERRESTRIAL_DIR / "eq3_spectral_12d_earth_sites.parquet")
        # El Malpais and Kazumura are genuine lava tube systems with voids
        malpais = df[df["analog_id"] == "EARTH_ANALOG_EL_MALPAIS"]
        assert not malpais.empty
        assert float(malpais.iloc[0]["P_void"]) >= 0.85, "El Malpais must have high P_void"


class TestTerrestrialStep4NoveltyPriorAndMasterCatalog:
    def test_step4_master_outputs_exist(self):
        assert (TERRESTRIAL_DIR / "earth_candidates.csv").exists()
        assert (TERRESTRIAL_DIR / "earth_candidates.parquet").exists()
        assert (TERRESTRIAL_DIR / "earth_candidates.xlsx").exists()
        assert (TERRESTRIAL_DIR / "earth_candidates.md").exists()
        assert (TERRESTRIAL_DIR / "eq4_cliche_eliminated_sites.csv").exists()

    def test_cliche_elimination_precision(self):
        elim_df = pd.read_csv(TERRESTRIAL_DIR / "eq4_cliche_eliminated_sites.csv")
        elim_ids = set(elim_df["analog_id"].tolist())
        # Haughton (HMP station), Rio Tinto (station), and Kazumura (HI-SEAS Mauna Loa) are cliches
        assert "EARTH_ANALOG_HAUGHTON_CRATER" in elim_ids, "Haughton Crater must be eliminated as over-studied"
        assert "EARTH_ANALOG_RIO_TINTO" in elim_ids, "Rio Tinto must be eliminated as over-studied"
        assert "EARTH_ANALOG_KAZUMURA_LAVA_TUBE" in elim_ids, "Kazumura must be eliminated due to HI-SEAS proximity"

    def test_surviving_candidates_novelty_and_completeness(self):
        df = pd.read_parquet(TERRESTRIAL_DIR / "earth_candidates.parquet")
        assert len(df) == 8, f"Expected exactly 8 novel Earth training grounds, got {len(df)}"
        # All surviving candidates should have Novelty >= 0.35
        for _, row in df.iterrows():
            assert float(row["P_novelty"]) >= 0.35, f"Site {row['site_name']} has novelty < 0.35"
            assert float(row["dist_to_famous_km"]) >= 250.0, f"Site {row['site_name']} too close to famous station"


class TestTerrestrialAnalogEngineIntegration:
    def test_fetch_earth_candidates(self):
        candidates = fetch_earth_candidates()
        assert len(candidates) == 8, f"Expected 8 candidates loaded from Earth candidates parquet, got {len(candidates)}"
        for c in candidates:
            assert "vector_12d" in c
            assert len(c["vector_12d"]) == 12
            assert "sigma_12d" in c
            assert len(c["sigma_12d"]) == 12
            assert "oxides" in c
            assert len(c["oxides"]) == 6
            assert pytest.approx(np.sum(c["oxides"]), rel=1e-2) == 100.0
            assert c["p_novelty"] >= 0.35
            assert c["p_pa"] > 0
            assert c["t_min_k"] > 0

    def test_e2e_match_target_pipeline_mars_jezero(self):
        target = generate_synthetic_target("Mars", "jezero")
        candidates = fetch_earth_candidates()
        summary, scorecard = match_target_pipeline(target, candidates, n_mc_trials=500)

        assert summary["target"]["site_name"] == "Jezero Crater Delta (Mars)"
        assert summary["top_analog"]["site_id"] in [c["site_id"] for c in candidates]
        assert summary["top_analog"]["composite_score"] > 50.0
        assert summary["verification"]["monte_carlo"]["is_verified"] is True
        assert summary["verification"]["spatial_contiguity"]["is_contiguous"] is True
        assert summary["verification"]["aitchison_distance"] > 0.0
        assert "PLANETARY DECISION SCORECARD" in scorecard

    def test_e2e_match_target_pipeline_moon_shackleton(self):
        target = generate_synthetic_target("Moon", "shackleton")
        candidates = fetch_earth_candidates()
        summary, scorecard = match_target_pipeline(target, candidates, n_mc_trials=500)

        assert summary["target"]["site_name"] == "Shackleton Connecting Ridge (Moon)"
        assert summary["top_analog"]["site_id"] in [c["site_id"] for c in candidates]
        assert summary["top_analog"]["composite_score"] > 35.0
        assert summary["verification"]["monte_carlo"]["is_verified"] is True
        assert summary["verification"]["spatial_contiguity"]["is_contiguous"] is True
        assert summary["verification"]["aitchison_distance"] > 0.0
        assert "PLANETARY DECISION SCORECARD" in scorecard
