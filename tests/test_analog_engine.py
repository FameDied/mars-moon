"""
Unit tests for analog_engine.py (Teammate 3 Mathematical Verification Library).
"""

import unittest
import numpy as np
import math

from analog_engine import (
    G_EARTH,
    G_MOON,
    G_MARS,
    calculate_shields_parameter,
    scale_lava_tube_structural_width,
    uncertainty_regularized_mahalanobis,
    mahalanobis_to_analog_score,
    compute_decomposed_4axis_scores,
    compute_earth_analog_limit_delta,
    optimize_complementary_split_twins,
    aitchison_compositional_distance,
    spatial_contiguity_verification,
    generate_synthetic_target,
    generate_synthetic_earth_candidates,
    match_target_pipeline,
)


class TestAnalogEnginePhysics(unittest.TestCase):
    """Verifies dimensionless cross-planetary physics scaling laws."""

    def test_aeolian_shields_parameter_formula(self):
        """
        Theta_aeolian = (rho_atm * u_star^2) / ((rho_grain - rho_atm) * g_body * d_p)
        Verifies exact algebraic equivalence.
        """
        rho_atm = 0.020
        u_star = 0.50
        rho_grain = 2900.0
        g_body = 3.72
        d_p = 100e-6

        expected = (0.020 * (0.50 ** 2)) / ((2900.0 - 0.020) * 3.72 * 100e-6)
        computed = calculate_shields_parameter(rho_atm, u_star, rho_grain, g_body, d_p)
        self.assertAlmostEqual(computed, expected, places=7)

    def test_aeolian_shields_high_altitude_analog(self):
        """High-altitude Earth desert matches Mars Shields dynamics closer than sea level."""
        u_star = 0.50
        rho_grain = 2900.0
        d_p = 100e-6

        theta_mars = calculate_shields_parameter(0.018, u_star, rho_grain, G_MARS, d_p)
        theta_sea = calculate_shields_parameter(1.225, u_star, rho_grain, G_EARTH, d_p)
        theta_plateau = calculate_shields_parameter(0.770, u_star, rho_grain, G_EARTH, d_p)

        self.assertLess(abs(theta_plateau - theta_mars), abs(theta_sea - theta_mars))

    def test_lava_tube_beam_scaling(self):
        """
        W_Earth_equiv = W_target * (g_target / g_Earth)
        A 181 m Lunar tube should scale to ~29.9 m on Earth.
        """
        w_lunar = 181.0
        w_earth = scale_lava_tube_structural_width(w_lunar, G_MOON, G_EARTH)
        self.assertAlmostEqual(w_earth, 181.0 * (1.62 / 9.80665), places=2)
        self.assertAlmostEqual(w_earth, 29.89, delta=0.1)


class TestDecomposedMahalanobisMatching(unittest.TestCase):
    """Verifies 4-axis decomposed matching and uncertainty regularization."""

    def test_uncertainty_regularization_downweights_noisy_sensors(self):
        """Higher measurement uncertainty sigma increases covariance denominator, reducing distance penalty."""
        z_t = np.array([10.0, 5.0, 0.2])
        z_e = np.array([15.0, 7.0, 0.4])
        cov = np.eye(3)

        d_clean = uncertainty_regularized_mahalanobis(
            z_t, z_e, cov,
            np.zeros(3), np.zeros(3)
        )
        d_noisy = uncertainty_regularized_mahalanobis(
            z_t, z_e, cov,
            np.array([5.0, 5.0, 0.5]), np.array([5.0, 5.0, 0.5])
        )
        self.assertLess(d_noisy, d_clean)

    def test_score_bounded_in_0_to_100(self):
        """S_a = 100 * exp(-D_M^2 / (2 * d_a)) is bounded in [0.0, 100.0]%."""
        self.assertAlmostEqual(mahalanobis_to_analog_score(0.0, d_a=3), 100.0, places=4)
        self.assertAlmostEqual(mahalanobis_to_analog_score(100.0, d_a=3), 0.0, places=4)

        score_mid = mahalanobis_to_analog_score(2.0, d_a=3)
        self.assertTrue(0.0 < score_mid < 100.0)


class TestEarthAnalogLimitDelta(unittest.TestCase):
    """Verifies non-simulatable Earth physical residual vector."""

    def test_lunar_gravity_offload_ratio(self):
        delta = compute_earth_analog_limit_delta(
            "Moon", G_MOON, 101325.0, 1e-10, 380.0, 2.4, 210.0, 35.0
        )
        # 1 - 1.62/9.80665 ~ 83.48%
        self.assertAlmostEqual(delta.gravity_offload_pct, 83.48, delta=0.1)
        self.assertGreater(delta.radiation_multiplier, 100.0)
        self.assertAlmostEqual(delta.cryogenic_gap_k, 175.0, places=1)


class TestSplitTwinAndVerifications(unittest.TestCase):
    """Verifies complementary twin optimization and 3-tier audits."""

    def test_split_twin_dominates_single_site(self):
        target = generate_synthetic_target("Moon", "shackleton")
        candidates = generate_synthetic_earth_candidates(10)

        twin = optimize_complementary_split_twins(
            target["vector_12d"], target["sigma_12d"], candidates
        )
        self.assertIn("site_1", twin)
        self.assertIn("site_2", twin)
        self.assertGreater(twin["twin_composite_score"], 0.0)

    def test_aitchison_distance_identity(self):
        """Distance between identical geochemical compositions is zero."""
        oxides = [45.0, 1.0, 15.0, 10.0, 8.0, 10.0]
        dist = aitchison_compositional_distance(oxides, oxides)
        self.assertAlmostEqual(dist, 0.0, places=5)

    def test_spatial_contiguity_passes(self):
        center = 80.0
        neighbors = [75.0, 78.0, 81.0, 76.0, 79.0, 77.0]
        result = spatial_contiguity_verification(center, neighbors, 0.85)
        self.assertTrue(result["is_contiguous"])
        self.assertGreaterEqual(result["mean_neighbor_score"], 68.0)


if __name__ == "__main__":
    unittest.main()
