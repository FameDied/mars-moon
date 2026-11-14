"""
Unit and integration tests for multi-dimensional similarity vector calculations,
decoupled physical axes (A, B, C, D), Cosine / Mahalanobis distance metrics,
min-max feature normalization, and Taylor-series uncertainty propagation (Features 1, 2, 8).
"""

import math
import os
import sqlite3
import unittest
from pathlib import Path
import numpy as np
from scipy.spatial.distance import mahalanobis

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("PLANETARY_DB_PATH", PROJECT_ROOT / "planetary_moon_mars.db"))

# Attempt dynamic import of production similarity engine.
# If core.similarity_engine is not yet available, standard reference mathematical
# formulas are used ONLY for algorithm invariant tests.
# Production module integration tests skip if the module is unbuilt.
try:
    import core.similarity_engine as sim_mod
    CORE_SIMILARITY_AVAILABLE = True
except ModuleNotFoundError as e:
    if e.name in ("core", "core.similarity_engine"):
        CORE_SIMILARITY_AVAILABLE = False
        sim_mod = None
    else:
        raise


# =============================================================================
# Authoritative Reference Mathematical Formulas (for Algorithm Invariants)
# =============================================================================

AXIS_FEATURE_BOUNDS = {
    # Axis A (Geomorphology)
    "mean_slope_deg": (0.0, 45.0),
    "tri_ruggedness": (0.0, 1.0),
    "rock_abundance_pct": (0.0, 30.0),
    # Axis B (Geochemistry & Mineralogy)
    "fe_wt_pct": (0.0, 30.0),
    "ti_wt_pct": (0.0, 5.0),
    "phyllosilicate_index": (0.0, 0.15),
    "sulfate_index": (0.0, 0.15),
    "olivine_index": (0.0, 0.25),
    # Axis C (Thermophysics)
    "diurnal_temp_swing_k": (0.0, 350.0),
    "thermal_inertia": (0.0, 2000.0),
    # Axis D (Volatiles & Aeolian)
    "h2o_equiv_pct": (0.0, 100.0),
    "wind_shear_mps": (0.0, 50.0),
    "dust_flux_g_m2_yr": (0.0, 1000.0),
}


def reference_min_max_normalize(val: float, f_min: float, f_max: float) -> float:
    """Clips and maps physical feature value to [0.0, 1.0]."""
    if f_max <= f_min:
        return 0.0
    return float(np.clip((val - f_min) / (f_max - f_min), 0.0, 1.0))


def reference_cosine_similarity_axis(
    u: np.ndarray, v: np.ndarray, zero_tol: float = 1e-15
) -> float:
    """
    Robust Normalized Cosine Similarity mapped to [0.0, 100.0]%.

    Guarantees per Explorer 2 specifications:
    - Scale invariance: S(u, c*u) = 100.0% for any c > 0 down to subnormal floats.
    - Zero distortion: avoids denominator epsilon regularizer corruption.
    - Overflow immunity: pre-scales by maximum magnitude to handle |u| >= 1e160 without NaN.
    - Strict bounds: returns float in [0.0, 100.0].
    """
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)

    if u.shape != v.shape:
        raise ValueError(f"Shape mismatch: {u.shape} vs {v.shape}")

    # Check for exact identical vectors (including all-zero vectors)
    if np.array_equal(u, v):
        return 100.0

    # Max-magnitude pre-scaling to prevent float64 overflow/underflow
    max_u = float(np.max(np.abs(u))) if u.size > 0 else 0.0
    max_v = float(np.max(np.abs(v))) if v.size > 0 else 0.0

    if max_u <= zero_tol or max_v <= zero_tol:
        return 0.0

    u_scaled = u / max_u
    v_scaled = v / max_v

    norm_u = float(np.linalg.norm(u_scaled))
    norm_v = float(np.linalg.norm(v_scaled))

    if norm_u <= zero_tol or norm_v <= zero_tol:
        return 0.0

    cos = np.dot(u_scaled / norm_u, v_scaled / norm_v)
    return float(np.clip(cos * 100.0, 0.0, 100.0))


def reference_regularized_covariance(
    data: np.ndarray, alpha: float = 0.15, eps_scale: float = 1e-5
) -> np.ndarray:
    """Ledoit-Wolf-style diagonal shrinkage to guarantee positive-definiteness."""
    X = np.asarray(data, dtype=float)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    n_samples, n_features = X.shape
    if n_samples <= 1:
        return np.eye(n_features) * 1.0
    cov = np.cov(X, rowvar=False)
    if n_features == 1:
        cov = np.array([[float(cov)]])
    diag_cov = np.diag(np.diag(cov))
    trace_val = max(float(np.trace(cov)), 1e-6)
    eps_eye = (eps_scale * (trace_val / n_features)) * np.eye(n_features)
    reg_cov = (1.0 - alpha) * cov + alpha * diag_cov + eps_eye
    return reg_cov


def reference_mahalanobis_similarity_axis(
    u: np.ndarray, v: np.ndarray, inv_cov: np.ndarray = None
) -> float:
    """Monotonic inverse-decay Mahalanobis score mapped to [0.0, 100.0]%."""
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    diff = u - v
    dim = len(u)
    if inv_cov is None:
        inv_cov = np.eye(dim)
    try:
        d = mahalanobis(u, v, inv_cov)
    except Exception:
        d = np.sqrt(np.dot(diff, diff))
    score = 100.0 / (1.0 + float(d))
    return float(np.clip(score, 0.0, 100.0))


def reference_propagate_uncertainty_taylor(
    axis_scores: dict, conf_target: float, conf_analog: float, weights: dict = None
) -> float:
    """
    Analytic first-order Taylor series error variance propagation:
    sigma_S = sqrt( sum_k (w_k * S_k * Delta_C)^2 )
    where Delta_C = sqrt((1 - C_t)^2 + (1 - C_a)^2)
    """
    if weights is None:
        weights = {"axis_a": 0.25, "axis_b": 0.25, "axis_c": 0.25, "axis_d": 0.25}
    c_t = float(np.clip(conf_target, 0.0, 1.0))
    c_a = float(np.clip(conf_analog, 0.0, 1.0))
    delta_c = math.sqrt((1.0 - c_t) ** 2 + (1.0 - c_a) ** 2)

    var_sum = 0.0
    for axis, score in axis_scores.items():
        w = weights.get(axis, 0.25)
        sigma_k = float(score) * delta_c
        var_sum += (w * sigma_k) ** 2
    return float(math.sqrt(var_sum))


def reference_compute_conservative_score(composite_score: float, sigma: float) -> float:
    """95% single-sided Lower Confidence Bound (LCB) ranking: S - 1.645*sigma clipped to [0, 100]."""
    lcb = composite_score - 1.645 * sigma
    return float(max(0.0, min(100.0, lcb)))


# =============================================================================
# Test Class
# =============================================================================

class TestSimilarityEngine(unittest.TestCase):
    """
    Comprehensive tests covering 4 decoupled physical axes, Cosine and Mahalanobis metrics,
    min-max feature normalization, Taylor series uncertainty propagation, and boundary cases.
    """

    def setUp(self):
        self.sample_target = {
            "site_id": "TARGET_LUNAR_RIDGE",
            "mean_slope_deg": 8.5,
            "tri_ruggedness": 0.15,
            "rock_abundance_pct": 3.2,
            "fe_wt_pct": 14.5,
            "ti_wt_pct": 2.1,
            "phyllosilicate_index": 0.05,
            "sulfate_index": 0.02,
            "diurnal_temp_swing_k": 220.0,
            "thermal_inertia": 450.0,
            "h2o_equiv_pct": 5.5,
            "wind_shear_mps": 0.0,
            "dust_flux_g_m2_yr": 0.0,
            "measurement_confidence": 0.95,
        }
        self.sample_analog = {
            "site_id": "ANALOG_HAUGHTON",
            "mean_slope_deg": 8.4,
            "tri_ruggedness": 0.14,
            "rock_abundance_pct": 3.0,
            "fe_wt_pct": 13.8,
            "ti_wt_pct": 1.9,
            "phyllosilicate_index": 0.04,
            "sulfate_index": 0.03,
            "diurnal_temp_swing_k": 18.0,
            "thermal_inertia": 850.0,
            "h2o_equiv_pct": 28.0,
            "wind_shear_mps": 12.0,
            "dust_flux_g_m2_yr": 50.0,
            "measurement_confidence": 0.90,
        }

    # --- Dispatch Helpers ---

    def call_cosine_similarity(self, u: np.ndarray, v: np.ndarray) -> float:
        if CORE_SIMILARITY_AVAILABLE and hasattr(sim_mod, "cosine_similarity_axis"):
            return sim_mod.cosine_similarity_axis(u, v)
        return reference_cosine_similarity_axis(u, v)

    def call_mahalanobis_similarity(self, u: np.ndarray, v: np.ndarray, inv_cov: np.ndarray = None) -> float:
        if CORE_SIMILARITY_AVAILABLE and hasattr(sim_mod, "mahalanobis_similarity_axis"):
            return sim_mod.mahalanobis_similarity_axis(u, v, inv_cov)
        return reference_mahalanobis_similarity_axis(u, v, inv_cov)

    def call_regularized_cov(self, data: np.ndarray, alpha: float = 0.15) -> np.ndarray:
        if CORE_SIMILARITY_AVAILABLE and hasattr(sim_mod, "regularized_covariance"):
            return sim_mod.regularized_covariance(data, alpha)
        return reference_regularized_covariance(data, alpha)

    def call_propagate_uncertainty(self, axis_scores: dict, conf_t: float, conf_a: float, weights: dict = None) -> float:
        if CORE_SIMILARITY_AVAILABLE and hasattr(sim_mod, "propagate_uncertainty_taylor"):
            return sim_mod.propagate_uncertainty_taylor(axis_scores, conf_t, conf_a, weights)
        return reference_propagate_uncertainty_taylor(axis_scores, conf_t, conf_a, weights)

    def call_conservative_score(self, composite_score: float = None, sigma: float = 0.0, comp_score: float = None) -> float:
        val = composite_score if composite_score is not None else comp_score
        if val is None:
            val = 0.0
        if CORE_SIMILARITY_AVAILABLE and hasattr(sim_mod, "compute_conservative_score"):
            return sim_mod.compute_conservative_score(val, sigma)
        return reference_compute_conservative_score(val, sigma)

    def call_compute_profile(self, target: dict, analog: dict, method: str = "cosine", weights: dict = None) -> dict:
        """Invokes production compute_similarity_profile. Skips if core.similarity_engine is not yet available."""
        if not CORE_SIMILARITY_AVAILABLE or not hasattr(sim_mod, "compute_similarity_profile"):
            self.skipTest("core.similarity_engine not yet available")
        return sim_mod.compute_similarity_profile(target, analog, method=method, weights=weights)

    # =========================================================================
    # Feature 1: Multi-Dimensional Similarity Vector (Cosine & Mahalanobis)
    # =========================================================================

    def test_axis_a_geomorphology_cosine_identical(self):
        """Identical geomorphology inputs must return 100.0% similarity."""
        u = np.array([0.2, 0.15, 0.03])
        v = np.array([0.2, 0.15, 0.03])
        score = self.call_cosine_similarity(u, v)
        self.assertAlmostEqual(score, 100.0, places=2)

    def test_axis_b_geochemistry_cosine_identical(self):
        """Identical geochemistry inputs must return 100.0% similarity."""
        u = np.array([0.15, 0.02, 0.05, 0.01])
        score = self.call_cosine_similarity(u, u)
        self.assertAlmostEqual(score, 100.0, places=2)

    def test_axis_c_thermophysics_cosine_identical(self):
        """Identical thermophysics inputs must return 100.0% similarity."""
        u = np.array([0.75, 0.25])
        score = self.call_cosine_similarity(u, u)
        self.assertAlmostEqual(score, 100.0, places=2)

    def test_axis_d_volatiles_cosine_identical(self):
        """Identical volatiles inputs must return 100.0% similarity."""
        u = np.array([0.05, 0.1, 0.01])
        score = self.call_cosine_similarity(u, u)
        self.assertAlmostEqual(score, 100.0, places=2)

    def test_mahalanobis_distance_identical_gives_100_percent(self):
        """When candidate equals target, Mahalanobis distance is 0, yielding 100% match."""
        u = np.array([0.5, 0.2, 0.8])
        score = self.call_mahalanobis_similarity(u, u)
        self.assertAlmostEqual(score, 100.0, places=2)

    def test_mahalanobis_distance_monotonicity(self):
        """Greater geometric separation under covariance must yield lower match score."""
        target = np.array([1.0, 1.0])
        close_analog = np.array([1.1, 1.05])
        far_analog = np.array([4.0, 5.0])
        score_close = self.call_mahalanobis_similarity(target, close_analog)
        score_far = self.call_mahalanobis_similarity(target, far_analog)
        self.assertGreater(score_close, score_far)

    def test_regularized_covariance_invertible(self):
        """Regularized covariance with diagonal shrinkage must be strictly positive definite."""
        collinear_data = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0], [4.0, 8.0]])
        reg_cov = self.call_regularized_cov(collinear_data, alpha=0.15)
        inv_cov = np.linalg.inv(reg_cov)
        self.assertEqual(inv_cov.shape, (2, 2))
        eigvals = np.linalg.eigvals(reg_cov)
        self.assertTrue(np.all(eigvals > 0), f"Covariance eigenvalues must be positive: {eigvals}")

    def test_orthogonal_features_produce_zero_cosine_score(self):
        """Completely orthogonal non-negative vectors must produce 0.0% cosine score."""
        u = np.array([1.0, 0.0, 0.0])
        v = np.array([0.0, 1.0, 0.0])
        score = self.call_cosine_similarity(u, v)
        self.assertAlmostEqual(score, 0.0, places=2)

    def test_all_scores_bounded_between_zero_and_hundred(self):
        """Scores must never exceed [0.0, 100.0]% even under random extreme vectors."""
        np.random.seed(42)
        for _ in range(30):
            u = np.random.uniform(0.0, 1000.0, size=4)
            v = np.random.uniform(0.0, 1000.0, size=4)
            score_cos = self.call_cosine_similarity(u, v)
            score_mah = self.call_mahalanobis_similarity(u, v)
            self.assertTrue(0.0 <= score_cos <= 100.0)
            self.assertTrue(0.0 <= score_mah <= 100.0)

    def test_zero_vector_handling_numerical_stability(self):
        """Zero vectors must not cause division-by-zero or NaN."""
        zero_vec = np.zeros(3)
        nonzero_vec = np.array([1.0, 2.0, 3.0])
        score_both_zero = self.call_cosine_similarity(zero_vec, zero_vec)
        self.assertEqual(score_both_zero, 100.0)
        score_one_zero = self.call_cosine_similarity(zero_vec, nonzero_vec)
        self.assertAlmostEqual(score_one_zero, 0.0, places=2)
        self.assertFalse(math.isnan(score_one_zero))

    def test_similarity_metric_symmetry(self):
        """Similarity metric must be symmetric: S(target, analog) == S(analog, target)."""
        u = np.array([3.2, 5.8, 1.1])
        v = np.array([2.9, 6.2, 0.9])
        score_uv = self.call_cosine_similarity(u, v)
        score_vu = self.call_cosine_similarity(v, u)
        self.assertAlmostEqual(score_uv, score_vu, places=4)

    def test_zero_variance_features_in_mahalanobis(self):
        """Datasets with constant zero-variance features must not crash regularizer."""
        data_zero_var = np.array([[5.0, 1.0], [5.0, 2.0], [5.0, 3.0]])
        reg_cov = self.call_regularized_cov(data_zero_var)
        inv_cov = np.linalg.inv(reg_cov)
        score = self.call_mahalanobis_similarity(np.array([5.0, 1.5]), np.array([5.0, 2.5]), inv_cov)
        self.assertTrue(0.0 <= score <= 100.0)

    # Explorer 2 Mathematical Fixes: Denominator Epsilon Distortion & Pre-Scaling
    def test_cosine_similarity_small_magnitude_scale_invariance(self):
        """Small identical vectors [5e-9] must evaluate to 100.0% without epsilon regularizer crushing."""
        u_small = np.array([5e-9, 5e-9, 5e-9])
        score = self.call_cosine_similarity(u_small, u_small)
        self.assertAlmostEqual(score, 100.0, places=2, msg=f"Small magnitude vector similarity crushed to {score}%")

    def test_cosine_similarity_extreme_magnitude_overflow_immunity(self):
        """Extreme magnitude vectors [1e160] must compute without IEEE-754 overflow or NaN."""
        u_large = np.array([1e160, 2e160, 3e160])
        score = self.call_cosine_similarity(u_large, u_large)
        self.assertFalse(math.isnan(score))
        self.assertAlmostEqual(score, 100.0, places=2)

    def test_min_max_feature_normalization_astrobiological_discrimination(self):
        """Min-max feature normalization prevents elemental weight dominance over spectral bands."""
        axis_b_bounds = [(0.0, 30.0), (0.0, 5.0), (0.0, 0.15), (0.0, 0.15), (0.0, 0.25)]

        def norm_vec(raw):
            return np.array([
                reference_min_max_normalize(val, b[0], b[1])
                for val, b in zip(raw, axis_b_bounds)
            ], dtype=float)

        jezero_norm = norm_vec([15.2, 1.1, 0.085, 0.045, 0.090])
        pilbara_norm = norm_vec([18.4, 0.6, 0.075, 0.020, 0.010])
        zero_bands_norm = norm_vec([15.2, 1.1, 0.0, 0.0, 0.0])

        score_pilbara = self.call_cosine_similarity(jezero_norm, pilbara_norm)
        score_zero_bands = self.call_cosine_similarity(jezero_norm, zero_bands_norm)

        self.assertGreater(score_pilbara, 85.0, "Pilbara must show premier astrobiological match")
        self.assertLess(score_zero_bands, 70.0, "Zero spectral bands must be significantly penalized")
        self.assertGreater(score_pilbara, score_zero_bands, "Authentic analog must outscore zero-band candidate")

    # =========================================================================
    # Feature 2: Decomposed Analog Match Percentages (Tier 1 & Tier 2)
    # =========================================================================

    def test_compute_similarity_profile_decomposed_keys(self):
        """Profile calculation must produce decomposed percentages across all 4 axes."""
        profile = self.call_compute_profile(self.sample_target, self.sample_analog, method="cosine")
        expected_keys = {
            "axis_a_pct", "axis_b_pct", "axis_c_pct", "axis_d_pct",
            "composite_score", "uncertainty_sigma", "conservative_score",
        }
        self.assertTrue(expected_keys.issubset(profile.keys()))
        for key in ["axis_a_pct", "axis_b_pct", "axis_c_pct", "axis_d_pct", "composite_score"]:
            val = profile[key]
            self.assertTrue(0.0 <= val <= 100.0, f"{key} value {val} out of bounds [0, 100]")

    def test_decomposed_percentage_individual_axis_ranges(self):
        """All four decomposed axis percentages must evaluate strictly in [0.0, 100.0]%."""
        profile = self.call_compute_profile(self.sample_target, self.sample_analog, method="cosine")
        for axis in ["axis_a_pct", "axis_b_pct", "axis_c_pct", "axis_d_pct"]:
            val = profile[axis]
            self.assertIsInstance(val, float)
            self.assertGreaterEqual(val, 0.0, f"{axis} score {val} < 0.0")
            self.assertLessEqual(val, 100.0, f"{axis} score {val} > 100.0")

    def test_decomposed_composite_score_weighted_sum_consistency(self):
        """composite_score must equal weighted linear combination sum(w_k * axis_pct_k)."""
        w_custom = {"axis_a": 0.40, "axis_b": 0.30, "axis_c": 0.20, "axis_d": 0.10}
        p = self.call_compute_profile(self.sample_target, self.sample_analog, weights=w_custom)
        expected = round(sum(p[f"axis_{k}_pct"] * w_custom[f"axis_{k}"] for k in ["a", "b", "c", "d"]), 2)
        self.assertAlmostEqual(p["composite_score"], expected, delta=0.05)

    def test_decomposed_profile_table_schema_mapping(self):
        """Profile output must map cleanly to similarity_profiles SQLite table columns."""
        profile = self.call_compute_profile(self.sample_target, self.sample_analog)
        required_cols = [
            "axis_a_geomorphology_pct", "axis_b_geochemistry_pct",
            "axis_c_thermophysics_pct", "axis_d_volatiles_pct",
            "composite_score", "uncertainty_bound",
        ]
        row_dict = {
            "axis_a_geomorphology_pct": profile["axis_a_pct"],
            "axis_b_geochemistry_pct": profile["axis_b_pct"],
            "axis_c_thermophysics_pct": profile["axis_c_pct"],
            "axis_d_volatiles_pct": profile["axis_d_pct"],
            "composite_score": profile["composite_score"],
            "uncertainty_bound": profile["uncertainty_sigma"],
        }
        for col in required_cols:
            self.assertIn(col, row_dict)
            self.assertFalse(math.isnan(row_dict[col]))

    def test_decomposed_ranking_order_consistency(self):
        """Close geomorphic analog must rank higher on Axis A than a divergent geomorphic analog."""
        flat_analog = dict(self.sample_analog)
        flat_analog["mean_slope_deg"] = 0.1
        flat_analog["tri_ruggedness"] = 0.01

        p_close = self.call_compute_profile(self.sample_target, self.sample_analog)
        p_flat = self.call_compute_profile(self.sample_target, flat_analog)
        self.assertGreater(p_close["axis_a_pct"], p_flat["axis_a_pct"])

    def test_decomposed_zero_match_lower_bound_zero_percent(self):
        """Orthogonal features across all axes must yield 0.0% scores (BVA lower bound)."""
        t_ortho = {
            "mean_slope_deg": 10.0, "tri_ruggedness": 0.0, "rock_abundance_pct": 0.0,
            "fe_wt_pct": 10.0, "ti_wt_pct": 0.0, "phyllosilicate_index": 0.0, "sulfate_index": 0.0,
            "diurnal_temp_swing_k": 100.0, "thermal_inertia": 0.0,
            "h2o_equiv_pct": 5.0, "wind_shear_mps": 0.0, "dust_flux_g_m2_yr": 0.0,
        }
        a_ortho = {
            "mean_slope_deg": 0.0, "tri_ruggedness": 0.5, "rock_abundance_pct": 15.0,
            "fe_wt_pct": 0.0, "ti_wt_pct": 5.0, "phyllosilicate_index": 0.1, "sulfate_index": 0.1,
            "diurnal_temp_swing_k": 0.0, "thermal_inertia": 500.0,
            "h2o_equiv_pct": 0.0, "wind_shear_mps": 15.0, "dust_flux_g_m2_yr": 50.0,
        }
        p = self.call_compute_profile(t_ortho, a_ortho, method="cosine")
        for axis in ["axis_a_pct", "axis_b_pct", "axis_c_pct", "axis_d_pct"]:
            self.assertAlmostEqual(p[axis], 0.0, places=1)
        self.assertAlmostEqual(p["composite_score"], 0.0, places=1)

    def test_decomposed_identical_match_upper_bound_hundred_percent(self):
        """Self-comparison must yield strictly 100.0% on all 4 axes and composite score."""
        for method in ["cosine", "mahalanobis"]:
            p = self.call_compute_profile(self.sample_target, self.sample_target, method=method)
            self.assertAlmostEqual(p["axis_a_pct"], 100.0, places=1)
            self.assertAlmostEqual(p["axis_b_pct"], 100.0, places=1)
            self.assertAlmostEqual(p["axis_c_pct"], 100.0, places=1)
            self.assertAlmostEqual(p["axis_d_pct"], 100.0, places=1)
            self.assertAlmostEqual(p["composite_score"], 100.0, places=1)

    def test_decomposed_single_axis_zero_other_axes_hundred(self):
        """Axis decoupling: when one axis matches 0% and three match 100%, composite is 75%."""
        analog_mixed = dict(self.sample_target)
        # Make Axis D completely orthogonal
        analog_mixed["h2o_equiv_pct"] = 0.0
        analog_mixed["wind_shear_mps"] = 25.0
        target_mod = dict(self.sample_target)
        target_mod["h2o_equiv_pct"] = 5.0
        target_mod["wind_shear_mps"] = 0.0

        p = self.call_compute_profile(target_mod, analog_mixed, method="cosine")
        self.assertAlmostEqual(p["axis_a_pct"], 100.0, places=1)
        self.assertAlmostEqual(p["axis_b_pct"], 100.0, places=1)
        self.assertAlmostEqual(p["axis_c_pct"], 100.0, places=1)
        self.assertAlmostEqual(p["axis_d_pct"], 0.0, places=1)
        self.assertAlmostEqual(p["composite_score"], 75.0, places=1)

    def test_decomposed_extreme_scaling_invariance(self):
        """Multiplication by positive scalars must not alter cosine similarity match percentages."""
        u = np.array([0.2, 0.15, 0.03])
        v = np.array([0.25, 0.10, 0.04])
        base_score = self.call_cosine_similarity(u, v)
        for alpha in [1e-5, 10.0, 1e4, 1e6]:
            scaled_score = self.call_cosine_similarity(u * alpha, v * alpha)
            self.assertAlmostEqual(scaled_score, base_score, places=3)

    def test_axis_decoupling_orthogonality(self):
        """Modifying Axis B alone must NOT alter Axis A, C, or D match percentages."""
        target = dict(self.sample_target)
        analog_1 = dict(self.sample_analog)
        analog_2 = dict(self.sample_analog)

        # Alter ONLY geochemistry in analog_2
        analog_2["fe_wt_pct"] = 99.0
        analog_2["ti_wt_pct"] = 50.0

        p1 = self.call_compute_profile(target, analog_1)
        p2 = self.call_compute_profile(target, analog_2)

        self.assertEqual(p1["axis_a_pct"], p2["axis_a_pct"])
        self.assertEqual(p1["axis_c_pct"], p2["axis_c_pct"])
        self.assertEqual(p1["axis_d_pct"], p2["axis_d_pct"])
        self.assertNotEqual(p1["axis_b_pct"], p2["axis_b_pct"])

    def test_custom_axis_weights(self):
        """Custom axis weighting must govern composite score proportionally."""
        weights = {"axis_a": 1.0, "axis_b": 0.0, "axis_c": 0.0, "axis_d": 0.0}
        profile = self.call_compute_profile(self.sample_target, self.sample_analog, weights=weights)
        self.assertAlmostEqual(profile["composite_score"], profile["axis_a_pct"], places=1)

    # =========================================================================
    # Feature 8: Uncertainty Bound Propagation (Tier 1 & Tier 2)
    # =========================================================================

    def test_taylor_series_uncertainty_propagation(self):
        """Imperfect confidence levels must yield positive uncertainty sigma."""
        scores = {"axis_a": 80.0, "axis_b": 75.0, "axis_c": 60.0, "axis_d": 50.0}
        sigma = self.call_propagate_uncertainty(scores, conf_t=0.90, conf_a=0.85)
        self.assertGreater(sigma, 0.0)

    def test_conservative_ranking_lower_bound(self):
        """Conservative score must be lower than or equal to nominal composite score."""
        comp_score = 85.0
        sigma = 6.2
        conservative = self.call_conservative_score(comp_score, sigma)
        self.assertLessEqual(conservative, comp_score)
        self.assertAlmostEqual(conservative, comp_score - 1.645 * sigma, places=1)

    def test_uncertainty_propagation_taylor_formula_exactness(self):
        """propagate_uncertainty_taylor must match analytic formula sqrt(sum((w_k * S_k * Delta_C)^2))."""
        scores = {"axis_a": 80.0, "axis_b": 70.0, "axis_c": 60.0, "axis_d": 50.0}
        w = {"axis_a": 0.25, "axis_b": 0.25, "axis_c": 0.25, "axis_d": 0.25}
        c_t, c_a = 0.90, 0.80
        delta_c = math.sqrt((1.0 - c_t) ** 2 + (1.0 - c_a) ** 2)
        expected_sigma = math.sqrt(sum((w[k] * scores[k] * delta_c) ** 2 for k in scores))
        actual_sigma = self.call_propagate_uncertainty(scores, c_t, c_a, weights=w)
        self.assertAlmostEqual(actual_sigma, expected_sigma, places=3)

    def test_conservative_lcb_ranking_inversion_prevention(self):
        """Lower Confidence Bound (S - 1.645*sigma) properly penalizes high-uncertainty sites."""
        lcb_high_variance = self.call_conservative_score(composite_score=85.0, sigma=10.0)  # 85 - 16.45 = 68.55
        lcb_low_variance = self.call_conservative_score(composite_score=78.0, sigma=2.0)   # 78 - 3.29 = 74.71
        self.assertGreater(lcb_low_variance, lcb_high_variance)

    def test_uncertainty_sigma_in_similarity_profile_output(self):
        """Profile output must contain uncertainty_sigma and conservative_score."""
        p = self.call_compute_profile(self.sample_target, self.sample_analog)
        self.assertIn("uncertainty_sigma", p)
        self.assertIn("conservative_score", p)
        self.assertGreaterEqual(p["uncertainty_sigma"], 0.0)
        self.assertTrue(0.0 <= p["conservative_score"] <= 100.0)

    def test_uncertainty_propagation_perfect_confidence_zero_sigma(self):
        """When confidences are 1.0, propagated uncertainty sigma is exactly 0.0."""
        scores = {"axis_a": 90.0, "axis_b": 85.0, "axis_c": 75.0, "axis_d": 80.0}
        sigma = self.call_propagate_uncertainty(scores, conf_t=1.0, conf_a=1.0)
        self.assertAlmostEqual(sigma, 0.0, places=4)
        conservative = self.call_conservative_score(82.5, sigma)
        self.assertAlmostEqual(conservative, 82.5, places=4)

    def test_uncertainty_propagation_zero_confidence_maximum_sigma(self):
        """Low confidence bounds (C=0.01) compute numerically stable maximum uncertainty."""
        scores = {"axis_a": 100.0, "axis_b": 100.0, "axis_c": 100.0, "axis_d": 100.0}
        sigma = self.call_propagate_uncertainty(scores, conf_t=0.01, conf_a=0.01)
        self.assertFalse(math.isnan(sigma))
        self.assertGreater(sigma, 50.0)
        conservative = self.call_conservative_score(100.0, sigma)
        self.assertGreaterEqual(conservative, 0.0)

    def test_uncertainty_propagation_zero_similarity_scores(self):
        """When similarity scores are 0.0, propagated uncertainty sigma is 0.0."""
        scores_zero = {"axis_a": 0.0, "axis_b": 0.0, "axis_c": 0.0, "axis_d": 0.0}
        sigma = self.call_propagate_uncertainty(scores_zero, conf_t=0.5, conf_a=0.5)
        self.assertAlmostEqual(sigma, 0.0, places=4)

    def test_conservative_score_clipping_at_zero(self):
        """When S - 1.645*sigma is negative, conservative score clips cleanly to 0.0."""
        score_clipped = self.call_conservative_score(comp_score=15.0, sigma=20.0)
        self.assertEqual(score_clipped, 0.0)

    def test_uncertainty_propagation_single_axis_dominant_variance(self):
        """When weight is concentrated on single axis, sigma equals single-axis standard deviation."""
        w = {"axis_a": 1.0, "axis_b": 0.0, "axis_c": 0.0, "axis_d": 0.0}
        scores = {"axis_a": 80.0, "axis_b": 60.0, "axis_c": 40.0, "axis_d": 20.0}
        c_t, c_a = 0.9, 0.8
        expected = scores["axis_a"] * math.sqrt((1.0 - c_t) ** 2 + (1.0 - c_a) ** 2)
        actual = self.call_propagate_uncertainty(scores, c_t, c_a, weights=w)
        self.assertAlmostEqual(actual, expected, places=3)

    # =========================================================================
    # Tier 3: Pairwise Cross-Feature Tests
    # =========================================================================

    def test_pairwise_f1_similarity_vector_with_f5_harmonized_sites(self):
        """Pairwise F1 x F5: Compute similarity profile directly from harmonized_sites DB records."""
        if not DB_PATH.exists():
            self.skipTest(f"Database not found at {DB_PATH}")

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='harmonized_sites';")
        if not cursor.fetchone():
            conn.close()
            self.skipTest("harmonized_sites table not present")

        cursor.execute("SELECT * FROM harmonized_sites WHERE body='Moon' LIMIT 1;")
        moon_row = cursor.fetchone()
        cursor.execute("SELECT * FROM harmonized_sites WHERE body='Earth' LIMIT 1;")
        earth_row = cursor.fetchone()
        conn.close()

        if not moon_row or not earth_row:
            self.skipTest("Insufficient records in harmonized_sites to evaluate cross-body pair")

        target_dict = dict(moon_row)
        analog_dict = dict(earth_row)

        profile = self.call_compute_profile(target_dict, analog_dict, method="cosine")
        self.assertTrue(all(0.0 <= profile[f"axis_{k}_pct"] <= 100.0 for k in ["a", "b", "c", "d"]))
        self.assertTrue(0.0 <= profile["composite_score"] <= 100.0)

    def test_pairwise_f8_uncertainty_propagation_with_f2_decomposed_percentages(self):
        """Pairwise F8 x F2: Changing measurement confidence scales sigma without corrupting axis percentages."""
        t_high = dict(self.sample_target, measurement_confidence=0.99)
        a_high = dict(self.sample_analog, measurement_confidence=0.95)
        t_low = dict(self.sample_target, measurement_confidence=0.40)
        a_low = dict(self.sample_analog, measurement_confidence=0.35)

        p_high = self.call_compute_profile(t_high, a_high)
        p_low = self.call_compute_profile(t_low, a_low)

        self.assertAlmostEqual(p_high["axis_a_pct"], p_low["axis_a_pct"], delta=0.1)
        self.assertAlmostEqual(p_high["axis_b_pct"], p_low["axis_b_pct"], delta=0.1)
        self.assertGreater(p_low["uncertainty_sigma"], p_high["uncertainty_sigma"])
        self.assertLess(p_low["conservative_score"], p_high["conservative_score"])

    def test_pairwise_f1_similarity_with_f2_decomposed_weights(self):
        """Pairwise F1 x F2: Metric choice (Cosine vs Mahalanobis) alters axis percentages and composite score."""
        p_cos = self.call_compute_profile(self.sample_target, self.sample_analog, method="cosine")
        p_mah = self.call_compute_profile(self.sample_target, self.sample_analog, method="mahalanobis")

        self.assertEqual(p_cos["method"], "cosine")
        self.assertEqual(p_mah["method"], "mahalanobis")
        self.assertTrue(0.0 <= p_cos["composite_score"] <= 100.0)
        self.assertTrue(0.0 <= p_mah["composite_score"] <= 100.0)

    def test_pairwise_f1_similarity_with_f8_uncertainty_penalty(self):
        """Pairwise F1 x F8: Equal composite scores with divergent confidences produce different conservative scores."""
        scores = {"axis_a": 80.0, "axis_b": 80.0, "axis_c": 80.0, "axis_d": 80.0}
        sigma_high = self.call_propagate_uncertainty(scores, conf_t=0.95, conf_a=0.95)
        sigma_low = self.call_propagate_uncertainty(scores, conf_t=0.60, conf_a=0.60)

        conservative_high = self.call_conservative_score(80.0, sigma_high)
        conservative_low = self.call_conservative_score(80.0, sigma_low)

        self.assertGreater(conservative_high, conservative_low)


if __name__ == "__main__":
    unittest.main()
