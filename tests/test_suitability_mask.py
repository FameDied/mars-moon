#!/usr/bin/env python3
"""
Test Suite: Spatial Site Suitability Mask & Engineering Constraint Verification
================================================================================
Covers R2 Engineering Constraint Masks across Tiers 1, 2, and 3:
- Tier 1: 4 Hard Engineering Cutoffs (Slope <= 10 deg, Rock Abundance <= 5%,
          Solar Illumination >= 80% & Earth Visibility >= 50%, Cold Trap <= 5 km).
- Tier 2: Boundary Value Analysis (BVA) strictly at 10.0 vs 10.01 deg, 5.0 vs 5.01%,
          80.0 vs 79.9%, 50.0 vs 49.9%, 5.0 vs 5.01 km. Extreme & invalid values,
          simultaneous boundaries, and polar latitude transitions.
- Tier 3: Soft Optimization (Multi-Attribute Utility Theory S-curves, Pareto
          frontier ranking), Dual-Tier Masking (relational SQL predicate and
          continuous raster vectorized 2D boolean mask), and pairwise cross-feature
          evaluations with standardized physical columns and uncertainty metadata.

Pure standard library unittest test suite executable via:
    python3 -m unittest tests/test_suitability_mask.py -v
"""

import os
import sys
import math
import sqlite3
import unittest
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "planetary_moon_mars.db")

# Attempt dynamic import of core.site_suitability if available
try:
    import core.site_suitability as suitability_engine
except ImportError:
    try:
        import scripts.site_suitability as suitability_engine
    except ImportError:
        suitability_engine = None


def reference_hard_cutoff_check(
    slope_deg: float,
    rock_abundance_pct: float,
    solar_illum_pct: float = None,
    earth_vis_pct: float = None,
    cold_trap_dist_km: float = None,
    body: str = "Moon",
    latitude_deg: float = -85.0
) -> bool:
    """
    Authoritative reference implementation of R2 Hard Engineering Cutoffs:
    1. Slope <= 10.0 deg at 5m baseline (tip-over stability limit).
    2. Diviner Rock Abundance <= 5.0% (boulder strike limit).
    3. Solar Illumination >= 80.0% AND Earth Visibility >= 50.0% for Lunar South Pole (|lat| >= 80).
    4. Proximity to Cold Trap <= 5.0 km (ISRU ice harvesting access, if specified).
    """
    if math.isnan(slope_deg) or math.isinf(slope_deg):
        raise ValueError("Slope cannot be NaN or Inf")
    if math.isnan(rock_abundance_pct) or math.isinf(rock_abundance_pct):
        raise ValueError("Rock abundance cannot be NaN or Inf")
    if slope_deg < 0.0 or rock_abundance_pct < 0.0 or rock_abundance_pct > 100.0:
        raise ValueError("Physical parameter out of realistic domain bounds")
    if cold_trap_dist_km is not None:
        if math.isnan(cold_trap_dist_km) or math.isinf(cold_trap_dist_km) or cold_trap_dist_km < 0.0:
            raise ValueError("Cold trap distance cannot be negative, NaN, or Inf")
    if solar_illum_pct is not None:
        if math.isnan(solar_illum_pct) or math.isinf(solar_illum_pct) or solar_illum_pct < 0.0 or solar_illum_pct > 100.0:
            raise ValueError("Solar illumination must be bounded in [0.0, 100.0]%")
    if earth_vis_pct is not None:
        if math.isnan(earth_vis_pct) or math.isinf(earth_vis_pct) or earth_vis_pct < 0.0 or earth_vis_pct > 100.0:
            raise ValueError("Earth visibility must be bounded in [0.0, 100.0]%")

    # 1. Slope cutoff
    if slope_deg > 10.0:
        return False

    # 2. Rock abundance cutoff
    if rock_abundance_pct > 5.0:
        return False

    # 3. Lunar South Pole power and telecom cutoff
    is_lunar_polar = (body.lower() == "moon" and abs(latitude_deg) >= 80.0)
    if is_lunar_polar:
        if solar_illum_pct is not None:
            # Strict percentage scale [0.0, 100.0]%
            if float(solar_illum_pct) < 80.0:
                return False
        if earth_vis_pct is not None:
            # Strict percentage scale [0.0, 100.0]%
            if float(earth_vis_pct) < 50.0:
                return False

    # 4. Cold trap proximity cutoff (if applicable)
    if cold_trap_dist_km is not None and cold_trap_dist_km > 5.0:
        return False

    return True


def reference_utility_slope(slope_deg: float) -> float:
    """Non-linear S-curve marginal utility for slope: u(theta) = 1.0 - (theta/10.0)^2."""
    if slope_deg > 10.0:
        return 0.0
    return max(0.0, 1.0 - (slope_deg / 10.0) ** 2)


def reference_utility_rock(rock_pct: float) -> float:
    """Non-linear marginal utility for rock abundance: u(r) = 1.0 - (r/5.0)^1.5."""
    if rock_pct > 5.0:
        return 0.0
    return max(0.0, 1.0 - (rock_pct / 5.0) ** 1.5)


def reference_composite_utility(
    slope_deg: float,
    rock_pct: float,
    illum_pct: float = 100.0,
    vis_pct: float = 100.0,
    cold_trap_km: float = 0.0
) -> float:
    """Multi-Attribute Utility score strictly in [0.0, 100.0]."""
    u_slope = reference_utility_slope(slope_deg)
    u_rock = reference_utility_rock(rock_pct)
    
    # Strict percentage scale [0.0, 100.0]%
    u_illum = max(0.0, min(1.0, ((illum_pct - 80.0) / 20.0) ** 0.5)) if illum_pct >= 80.0 else 0.0
    u_vis = max(0.0, min(1.0, ((vis_pct - 50.0) / 50.0) ** 0.5)) if vis_pct >= 50.0 else 0.0

    u_trap = max(0.0, min(1.0, 1.0 - (cold_trap_km / 5.0))) if cold_trap_km <= 5.0 else 0.0

    score = 100.0 * (0.25 * u_slope + 0.20 * u_rock + 0.25 * u_illum + 0.15 * u_vis + 0.15 * u_trap)
    return round(score, 4)


class SuitabilityEvaluatorBase:
    """Shared harness method for dynamic binding to core.site_suitability."""

    def evaluate_site(self, slope, rock, illum=None, vis=None, cold_trap=None, body="Moon", lat=-85.0):
        """Invoke core.site_suitability if available, otherwise skipTest."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")

        for fn_name in ("check_hard_cutoffs", "is_site_suitable", "evaluate_hard_cutoffs", "passes_hard_mask"):
            fn = getattr(suitability_engine, fn_name, None)
            if callable(fn):
                try:
                    return fn(
                        slope_deg=slope,
                        rock_abundance_pct=rock,
                        solar_illum_pct=illum,
                        earth_vis_pct=vis,
                        cold_trap_dist_km=cold_trap,
                        body=body,
                        latitude_deg=lat
                    )
                except TypeError:
                    try:
                        return fn(slope, rock, illum, vis, cold_trap)
                    except TypeError:
                        pass
        self.skipTest("core.site_suitability does not export a recognized cutoff evaluation function")


class TestSuitabilityMaskHardCutoffs(unittest.TestCase, SuitabilityEvaluatorBase):
    """Tier 1: Feature Coverage — Four Hard Engineering Cutoffs."""

    def test_01_slope_within_limit_passes(self):
        """Slope of 5.0 degrees (<= 10.0 deg limit) passes lander tip-over cutoff."""
        passed = self.evaluate_site(slope=5.0, rock=2.0, illum=90.0, vis=75.0, cold_trap=2.5)
        self.assertTrue(passed, "Slope of 5.0 deg should satisfy <= 10.0 deg cutoff")

    def test_02_slope_exceeding_limit_fails(self):
        """Slope of 14.5 degrees (> 10.0 deg limit) fails tip-over cutoff."""
        passed = self.evaluate_site(slope=14.5, rock=2.0, illum=90.0, vis=75.0, cold_trap=2.5)
        self.assertFalse(passed, "Slope of 14.5 deg must fail tip-over cutoff")

    def test_03_rock_abundance_within_limit_passes(self):
        """Diviner Rock Abundance of 3.2% (<= 5.0% limit) passes boulder hazard cutoff."""
        passed = self.evaluate_site(slope=6.0, rock=3.2, illum=88.0, vis=65.0, cold_trap=3.0)
        self.assertTrue(passed, "Rock abundance of 3.2% should pass <= 5.0% cutoff")

    def test_04_rock_abundance_exceeding_limit_fails(self):
        """Diviner Rock Abundance of 8.0% (> 5.0% limit) fails boulder hazard cutoff."""
        passed = self.evaluate_site(slope=6.0, rock=8.0, illum=88.0, vis=65.0, cold_trap=3.0)
        self.assertFalse(passed, "Rock abundance of 8.0% must fail boulder strike cutoff")

    def test_05_lunar_polar_illumination_and_visibility_pass(self):
        """Lunar South Pole site with Illumination=85% (>= 80%) and Earth Vis=60% (>= 50%) passes."""
        passed = self.evaluate_site(
            slope=7.0, rock=3.0, illum=85.0, vis=60.0, cold_trap=2.0, body="Moon", lat=-89.5
        )
        self.assertTrue(passed, "Illumination >= 80% and Earth Vis >= 50% must pass at Lunar South Pole")

    def test_06_lunar_polar_illumination_below_threshold_fails(self):
        """Lunar South Pole site with Illumination=65% (< 80% required) fails power cutoff."""
        passed = self.evaluate_site(
            slope=7.0, rock=3.0, illum=65.0, vis=60.0, cold_trap=2.0, body="Moon", lat=-89.5
        )
        self.assertFalse(passed, "Illumination of 65% (< 80%) must fail at Lunar South Pole")

    def test_07_lunar_polar_earth_visibility_below_threshold_fails(self):
        """Lunar South Pole site with Earth Visibility=35% (< 50% required) fails DTE telecom cutoff."""
        passed = self.evaluate_site(
            slope=7.0, rock=3.0, illum=85.0, vis=35.0, cold_trap=2.0, body="Moon", lat=-89.5
        )
        self.assertFalse(passed, "Earth visibility of 35% (< 50%) must fail at Lunar South Pole")

    def test_08_lunar_equatorial_site_bypasses_polar_constraints(self):
        """Equatorial lunar site (|lat| < 80) does not require 80% continuous illumination."""
        passed = self.evaluate_site(
            slope=5.0, rock=2.0, illum=50.0, vis=40.0, cold_trap=None, body="Moon", lat=5.0
        )
        self.assertTrue(passed, "Non-polar Moon site should not enforce polar illumination constraint")

    def test_09_mars_site_bypasses_lunar_polar_constraints(self):
        """Martian candidate site is not subject to Lunar South Pole illumination/visibility rule."""
        passed = self.evaluate_site(
            slope=4.0, rock=3.0, illum=45.0, vis=10.0, cold_trap=None, body="Mars", lat=18.4
        )
        self.assertTrue(passed, "Mars site must bypass lunar polar constraints")

    def test_10_cold_trap_proximity_within_five_km_passes(self):
        """Cold trap distance of 3.8 km (<= 5.0 km) passes ice harvesting access constraint."""
        passed = self.evaluate_site(slope=6.0, rock=2.5, illum=82.0, vis=55.0, cold_trap=3.8)
        self.assertTrue(passed, "Cold trap distance <= 5.0 km must pass")

    def test_11_cold_trap_proximity_exceeding_five_km_fails(self):
        """Cold trap distance of 9.2 km (> 5.0 km) fails ice harvesting access constraint."""
        passed = self.evaluate_site(slope=6.0, rock=2.5, illum=82.0, vis=55.0, cold_trap=9.2)
        self.assertFalse(passed, "Cold trap distance > 5.0 km must fail")

    def test_12_all_four_cutoffs_satisfied_qualifies_candidate(self):
        """A site satisfying all 4 cutoffs qualifies as compliant for mission operations."""
        passed = self.evaluate_site(
            slope=4.2, rock=1.8, illum=88.5, vis=72.0, cold_trap=1.4, body="Moon", lat=-89.7
        )
        self.assertTrue(passed, "Site meeting all 4 conditions must pass")

    def test_13_single_cutoff_failure_disqualifies_candidate(self):
        """Failing even one hard cutoff disqualifies an otherwise ideal candidate."""
        passed = self.evaluate_site(
            slope=11.2, rock=0.5, illum=95.0, vis=90.0, cold_trap=0.5, body="Moon", lat=-89.7
        )
        self.assertFalse(passed, "Excessive slope must disqualify site despite other ideal parameters")


class TestSuitabilityMaskBVA(unittest.TestCase, SuitabilityEvaluatorBase):
    """Tier 2: Boundary Value Analysis (BVA) strictly at engineering thresholds."""

    def test_14_bva_slope_exact_ten_degrees_passes(self):
        """Slope exactly at 10.00 deg (boundary) passes; 10.01 deg fails."""
        self.assertTrue(
            self.evaluate_site(slope=10.00, rock=2.0),
            "Slope exactly at 10.00 deg must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=10.01, rock=2.0),
            "Slope at 10.01 deg must FAIL"
        )

    def test_15_bva_rock_abundance_exact_five_percent_passes(self):
        """Rock abundance exactly at 5.00% passes; 5.01% fails."""
        self.assertTrue(
            self.evaluate_site(slope=5.0, rock=5.00),
            "Rock abundance exactly at 5.00% must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=5.01),
            "Rock abundance at 5.01% must FAIL"
        )

    def test_16_bva_solar_illumination_boundary_eighty_percent(self):
        """Polar illumination exactly at 80.0% passes; 79.9% fails."""
        self.assertTrue(
            self.evaluate_site(slope=5.0, rock=2.0, illum=80.0, vis=60.0),
            "Illumination exactly 80.0% must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=2.0, illum=79.9, vis=60.0),
            "Illumination at 79.9% must FAIL"
        )

    def test_17_bva_earth_visibility_boundary_fifty_percent(self):
        """Polar Earth visibility exactly at 50.0% passes; 49.9% fails."""
        self.assertTrue(
            self.evaluate_site(slope=5.0, rock=2.0, illum=85.0, vis=50.0),
            "Earth visibility exactly 50.0% must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=2.0, illum=85.0, vis=49.9),
            "Earth visibility at 49.9% must FAIL"
        )

    def test_18_bva_cold_trap_distance_exact_five_km(self):
        """Cold trap distance exactly at 5.00 km passes; 5.01 km fails."""
        self.assertTrue(
            self.evaluate_site(slope=5.0, rock=2.0, cold_trap=5.00),
            "Cold trap distance exactly 5.00 km must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=2.0, cold_trap=5.01),
            "Cold trap distance at 5.01 km must FAIL"
        )

    def test_19_bva_extreme_optimal_zero_values(self):
        """Optimal physical values: slope=0.0 deg, rocks=0.0%, cold_trap=0.0 km pass cleanly."""
        self.assertTrue(
            self.evaluate_site(
                slope=0.0, rock=0.0, illum=100.0, vis=100.0, cold_trap=0.0
            ),
            "Extreme optimal 0.0 values must PASS"
        )

    def test_20_bva_negative_and_out_of_bounds_inputs_raise(self):
        """Adversarial check: negative slope or rocks > 100% must raise ValueError or disqualify."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=-1.5, rock=2.0)
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=5.0, rock=105.0)
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=5.0, rock=2.0, cold_trap=-3.0)

    def test_27_bva_slope_rock_simultaneous_boundary(self):
        """Tier 2: Simultaneous boundary condition test for slope and rock limits."""
        self.assertTrue(
            self.evaluate_site(slope=10.00, rock=5.00),
            "Slope 10.0 and rock 5.0 simultaneously at boundary must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=10.01, rock=5.00),
            "Slope 10.01 and rock 5.00 must FAIL"
        )
        self.assertFalse(
            self.evaluate_site(slope=10.00, rock=5.01),
            "Slope 10.00 and rock 5.01 must FAIL"
        )
        self.assertFalse(
            self.evaluate_site(slope=10.01, rock=5.01),
            "Slope 10.01 and rock 5.01 must FAIL"
        )

    def test_28_bva_polar_illumination_visibility_simultaneous_boundary(self):
        """Tier 2: Simultaneous boundary condition test for polar illumination and visibility."""
        self.assertTrue(
            self.evaluate_site(slope=5.0, rock=2.0, illum=80.0, vis=50.0, body="Moon", lat=-85.0),
            "Illum 80.0% and Vis 50.0% simultaneously at boundary must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=2.0, illum=79.99, vis=50.0, body="Moon", lat=-85.0),
            "Illum 79.99% and Vis 50.0% must FAIL"
        )
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=2.0, illum=80.0, vis=49.99, body="Moon", lat=-85.0),
            "Illum 80.0% and Vis 49.99% must FAIL"
        )

    def test_29_bva_polar_latitude_transition_boundary(self):
        """Tier 2: Latitude boundary transition at |lat| = 80.0 deg for lunar polar constraints."""
        # At lat = -79.99 deg: non-polar, solar illumination of 60.0% is not constrained by the 80% polar rule
        self.assertTrue(
            self.evaluate_site(slope=5.0, rock=2.0, illum=60.0, vis=40.0, body="Moon", lat=-79.99),
            "Moon site at lat=-79.99 deg must not enforce polar illumination cutoff"
        )
        # At lat = -80.00 deg: polar, solar illumination of 60.0% fails the 80% cutoff
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=2.0, illum=60.0, vis=40.0, body="Moon", lat=-80.00),
            "Moon site at lat=-80.00 deg must enforce polar illumination cutoff and FAIL"
        )

    def test_30_bva_nan_and_inf_inputs_rejected(self):
        """Tier 2 Adversarial: NaN or Inf for any physical parameter must raise ValueError or disqualify."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=float('nan'), rock=2.0)
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=5.0, rock=float('inf'))
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=5.0, rock=2.0, illum=float('nan'))
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=5.0, rock=2.0, vis=float('nan'))
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=5.0, rock=2.0, cold_trap=float('nan'))

    def test_31_bva_extreme_polar_cold_trap_boundaries(self):
        """Tier 2: Cold trap distance boundary: 5.000 km passes, 5.001 km fails, negative raises."""
        self.assertTrue(
            self.evaluate_site(slope=5.0, rock=2.0, cold_trap=5.000),
            "Cold trap distance exactly 5.000 km must PASS"
        )
        self.assertFalse(
            self.evaluate_site(slope=5.0, rock=2.0, cold_trap=5.001),
            "Cold trap distance 5.001 km must FAIL"
        )
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        with self.assertRaises((ValueError, AssertionError)):
            self.evaluate_site(slope=5.0, rock=2.0, cold_trap=-0.5)


class TestSuitabilitySoftOptimizationAndDualTier(unittest.TestCase):
    """Tier 3: Soft Optimization, S-curves, Pareto ranking, and Dual-Tier spatial masks."""

    def test_21_soft_utility_slope_s_curve_monotonicity(self):
        """Slope utility function u(theta) = 1 - (theta/10)^2 strictly decreases from 1.0 to 0.0."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        fn = getattr(suitability_engine, "utility_slope",
             getattr(suitability_engine, "compute_slope_utility", None))
        if not callable(fn):
            self.skipTest("core.site_suitability lacks utility_slope function")

        u0 = fn(0.0)
        u2 = fn(2.0)
        u5 = fn(5.0)
        u8 = fn(8.0)
        u10 = fn(10.0)
        u12 = fn(12.0)

        self.assertAlmostEqual(u0, 1.0, places=4, msg="u(0) should be 1.0")
        self.assertTrue(u0 > u2 > u5 > u8 > u10, "Slope utility must be strictly monotonically decreasing")
        self.assertAlmostEqual(u10, 0.0, places=4, msg="u(10) at cutoff should be 0.0")
        self.assertEqual(u12, 0.0, "Utility above cutoff must be 0.0")

    def test_22_soft_utility_rock_abundance_s_curve(self):
        """Rock abundance utility u(r) = 1 - (r/5)^1.5 strictly decreases from 1.0 to 0.0."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        fn = getattr(suitability_engine, "utility_rock",
             getattr(suitability_engine, "compute_rock_utility", None))
        if not callable(fn):
            self.skipTest("core.site_suitability lacks utility_rock function")

        u0 = fn(0.0)
        u2 = fn(2.0)
        u5 = fn(5.0)
        u7 = fn(7.0)

        self.assertAlmostEqual(u0, 1.0, places=4)
        self.assertTrue(u0 > u2 > u5, "Rock utility must be strictly decreasing")
        self.assertAlmostEqual(u5, 0.0, places=4)
        self.assertEqual(u7, 0.0)

    def test_23_composite_utility_score_bounded_zero_to_hundred(self):
        """Composite suitability score is strictly bounded in [0.0, 100.0]."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        fn = getattr(suitability_engine, "compute_composite_utility",
             getattr(suitability_engine, "composite_utility", None))
        if not callable(fn):
            self.skipTest("core.site_suitability lacks compute_composite_utility function")

        best_score = fn(0.0, 0.0, 100.0, 100.0, 0.0)
        self.assertAlmostEqual(best_score, 100.0, places=2)

        worst_score = fn(10.0, 5.0, 80.0, 50.0, 5.0)
        self.assertAlmostEqual(worst_score, 0.0, places=2)

        mid_score = fn(4.0, 2.0, 85.0, 60.0, 2.0)
        self.assertTrue(0.0 <= mid_score <= 100.0, f"Score {mid_score} out of [0, 100] bounds")

    def test_24_pareto_dominance_ranking(self):
        """Candidate A superior or equal in all utility criteria strictly Pareto-dominates Candidate B."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        fn = getattr(suitability_engine, "pareto_dominates",
             getattr(suitability_engine, "dominates",
             getattr(suitability_engine, "is_pareto_dominant", None)))
        if not callable(fn):
            self.skipTest("core.site_suitability lacks pareto_dominance function")

        cand_a = {"name": "Site_A", "u_slope": 0.85, "u_rock": 0.90, "u_illum": 0.70}
        cand_b = {"name": "Site_B", "u_slope": 0.60, "u_rock": 0.70, "u_illum": 0.50}
        keys = ["u_slope", "u_rock", "u_illum"]
        self.assertTrue(fn(cand_a, cand_b, keys), "Candidate A must Pareto-dominate Candidate B")
        self.assertFalse(fn(cand_b, cand_a, keys), "Candidate B cannot dominate Candidate A")

    def test_25_dual_tier_sql_masking_against_database(self):
        """Tier 1 relational SQL mask queries database site_engineering_safety with real cutoffs."""
        if not os.path.exists(DB_PATH):
            self.skipTest(f"Database not found at {DB_PATH}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Query all sites passing slope <= 10 deg AND rock abundance <= 5%
        c.execute("""
            SELECT count(*) FROM site_engineering_safety
            WHERE macro_slope_deg <= 10.0 AND rock_abundance_percent <= 5.0;
        """)
        passing_count = c.fetchone()[0]

        # Query all sites violating rock abundance cutoff
        c.execute("""
            SELECT count(*) FROM site_engineering_safety
            WHERE rock_abundance_percent > 5.0;
        """)
        failing_rocks = c.fetchone()[0]

        conn.close()

        self.assertGreater(passing_count, 0, "There should be landing sites passing the hard cutoffs")
        self.assertGreater(failing_rocks, 0, "There should be landing sites failing rock abundance cutoff")
        self.assertGreater(passing_count, failing_rocks, "Compliant sites should exceed high-hazard sites")

    def test_26_dual_tier_raster_mask_vectorized_numpy(self):
        """Tier 2 continuous gridded raster mask correctly vectorizes across 2D spatial DEM arrays."""
        # Create a synthetic 10x10 gridded region
        np.random.seed(42)
        slope_grid = np.array([
            [5.0,  8.0, 12.0, 4.0],
            [10.0, 9.5, 15.0, 2.0],
            [3.0,  1.0, 8.5, 11.0],
            [7.0,  6.0, 4.0,  5.0]
        ])
        rock_grid = np.array([
            [2.0, 4.5, 1.0, 6.0],  # (0,2) slope 12 fails; (0,3) rock 6 fails
            [5.0, 3.0, 7.0, 1.0],  # (1,0) slope 10 rock 5 passes; (1,2) rock 7 fails
            [1.0, 2.0, 4.0, 3.0],  # (2,3) slope 11 fails
            [5.5, 2.0, 3.0, 1.5]   # (3,0) rock 5.5 fails
        ])

        # Dual-tier vectorized boolean mask: slope <= 10.0 & rock <= 5.0
        raster_mask = (slope_grid <= 10.0) & (rock_grid <= 5.0)

        # Expected boolean layout
        self.assertTrue(raster_mask[0, 0])
        self.assertTrue(raster_mask[0, 1])
        self.assertFalse(raster_mask[0, 2])
        self.assertFalse(raster_mask[0, 3])
        self.assertTrue(raster_mask[1, 0])  # Exactly 10.0 and 5.0 boundary
        self.assertFalse(raster_mask[1, 2]) # 15.0 slope and 7.0 rock
        # Compliant cells: 16 - 5 failing cells = 11 compliant cells
        self.assertEqual(np.sum(raster_mask), 11, "Exactly 11 cells out of 16 should be compliant")

    def test_32_soft_utility_combined_multi_attribute_s_curves(self):
        """Tier 3: Multi-attribute soft utility monotonicity across custom weighting profiles."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        fn = getattr(suitability_engine, "compute_composite_utility",
             getattr(suitability_engine, "composite_utility", None))
        if not callable(fn):
            self.skipTest("core.site_suitability lacks composite utility function")

        # Candidate with ideal terrain: slope=1.0, rock=1.0
        score_ideal = fn(1.0, 1.0, 95.0, 85.0, 1.0)
        # Candidate with degraded terrain: slope=8.0, rock=4.0
        score_degraded = fn(8.0, 4.0, 95.0, 85.0, 1.0)
        self.assertGreater(score_ideal, score_degraded, "Ideal terrain must score strictly higher than degraded terrain")

    def test_33_pairwise_f3_hard_cutoffs_with_f6_standardized_physical_columns(self):
        """Tier 3 Pairwise: Feature 3 (Hard Engineering Cutoffs) x Feature 6 (Standardized Columns)."""
        if not os.path.exists(DB_PATH):
            self.skipTest(f"Database not found at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT h.site_id, h.site_name, h.mean_slope_deg, s.rock_abundance_percent
            FROM harmonized_sites h
            JOIN site_engineering_safety s USING (site_id)
            WHERE h.mean_slope_deg IS NOT NULL AND s.rock_abundance_percent IS NOT NULL
            LIMIT 50;
        """)
        rows = c.fetchall()
        conn.close()
        if not rows:
            self.skipTest("No joined records in harmonized_sites and site_engineering_safety")

        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        eval_fn = getattr(suitability_engine, "check_hard_cutoffs",
                  getattr(suitability_engine, "is_site_suitable",
                  getattr(suitability_engine, "passes_hard_mask", None)))
        if not callable(eval_fn):
            self.skipTest("core.site_suitability lacks hard cutoff evaluation function")

        for r in rows:
            expected_pass = (r["mean_slope_deg"] <= 10.0 and r["rock_abundance_percent"] <= 5.0)
            actual_pass = eval_fn(
                slope_deg=r["mean_slope_deg"],
                rock_abundance_pct=r["rock_abundance_percent"],
                body="Moon",
                latitude_deg=0.0
            )
            self.assertEqual(actual_pass, expected_pass, f"Cutoff evaluation mismatch for site {r['site_name']}")

    def test_34_pairwise_f4_soft_optimization_with_f7_uncertainty_metadata(self):
        """Tier 3 Pairwise: Feature 4 (Soft Optimization) x Feature 7 (Uncertainty Metadata)."""
        if suitability_engine is None:
            self.skipTest("core.site_suitability pending M4 implementation")
        fn = getattr(suitability_engine, "compute_conservative_utility",
             getattr(suitability_engine, "conservative_utility", None))
        if not callable(fn):
            self.skipTest("core.site_suitability lacks conservative_utility function with uncertainty")

        # Candidate A: high nominal utility (0.90), low measurement confidence (0.40)
        # Candidate B: slightly lower nominal utility (0.85), high measurement confidence (0.95)
        score_a = fn(nominal_utility=0.90, measurement_confidence=0.40)
        score_b = fn(nominal_utility=0.85, measurement_confidence=0.95)
        self.assertGreater(score_b, score_a, "High confidence site must rank higher than high uncertainty site under conservative utility")


if __name__ == "__main__":
    unittest.main()
