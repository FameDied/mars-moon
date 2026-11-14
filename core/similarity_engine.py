"""
Multi-Dimensional Similarity Engine & Decomposed Scoring Module (R1, R4).

Computes decoupled physical similarity across 4 orthogonal axes:
- Axis A: Geomorphology (slope, TRI ruggedness, rock abundance)
- Axis B: Geochemistry & Mineralogy (Fe wt%, Ti wt%, phyllosilicate, sulfate, olivine band depths)
- Axis C: Thermophysics (diurnal temp amplitude, thermal inertia)
- Axis D: Volatiles & Aeolian (WEH wt%, wind shear, dust flux)

Supports dual metrics:
- Normalized Cosine Similarity [0.0, 100.0]% with max-magnitude overflow immunity and subnormal scale invariance.
- Regularized Mahalanobis Distance with Ledoit-Wolf diagonal shrinkage and monotonic inverse-decay scoring.

Propagates measurement uncertainty via first-order analytic Taylor series into confidence bounds
and Conservative Lower Confidence Bound (LCB) ranking.
"""

from datetime import datetime, timezone
import math
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.spatial.distance import mahalanobis

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = Path(os.getenv("PLANETARY_DB_PATH", PROJECT_ROOT / "planetary_moon_mars.db"))

# =============================================================================
# Axis Feature Definitions & Domain Physics Min-Max Bounds
# =============================================================================

AXIS_FEATURE_BOUNDS: Dict[str, Tuple[float, float]] = {
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

AXIS_FEATURES: Dict[str, List[str]] = {
    "axis_a": ["mean_slope_deg", "tri_ruggedness", "rock_abundance_pct"],
    "axis_b": ["fe_wt_pct", "ti_wt_pct", "phyllosilicate_index", "sulfate_index", "olivine_index"],
    "axis_c": ["diurnal_temp_swing_k", "thermal_inertia"],
    "axis_d": ["h2o_equiv_pct", "wind_shear_mps", "dust_flux_g_m2_yr"],
}

DEFAULT_WEIGHTS: Dict[str, float] = {
    "axis_a": 0.25,
    "axis_b": 0.25,
    "axis_c": 0.25,
    "axis_d": 0.25,
}

FEATURE_ALIASES: Dict[str, List[str]] = {
    "mean_slope_deg": ["macro_slope_deg", "slope_deg", "slope"],
    "tri_ruggedness": ["ruggedness_index", "tri", "ruggedness"],
    "rock_abundance_pct": ["rock_abundance_percent", "rock_abundance", "rock_pct"],
    "fe_wt_pct": ["iron_wt_pct", "fe_wt_percent", "fe_pct", "mineral_resource_pct"],
    "ti_wt_pct": ["titanium_wt_pct", "ti_wt_percent", "ti_pct"],
    "phyllosilicate_index": ["phyllosilicate", "phy_index"],
    "sulfate_index": ["sulfate", "sulf_index"],
    "olivine_index": ["olivine", "ol_index"],
    "diurnal_temp_swing_k": ["diurnal_temp_amplitude_k", "temp_swing_k", "diurnal_swing_k", "delta_t_k"],
    "thermal_inertia": ["thermal_inertia_si", "apparent_thermal_inertia"],
    "h2o_equiv_pct": ["water_equivalent_hydrogen_pct", "weh_wt_pct", "weh_pct", "h2o_pct"],
    "wind_shear_mps": ["wind_shear", "wind_mps"],
    "dust_flux_g_m2_yr": ["dust_flux", "dust_deposition_rate"],
}


# =============================================================================
# Helper Utilities & Normalization
# =============================================================================

def min_max_normalize(val: float, f_min: float, f_max: float) -> float:
    """
    Clips and maps physical feature value to [0.0, 1.0] domain interval.
    If f_max <= f_min, returns 0.0.
    """
    if val is None:
        return 0.0
    try:
        val_f = float(val)
    except (ValueError, TypeError):
        return 0.0
    if f_max <= f_min:
        return 0.0
    return float(np.clip((val_f - f_min) / (f_max - f_min), 0.0, 1.0))


def _normalize_axis_key(axis: str) -> str:
    """Normalizes various axis naming variations to standard 'axis_{a,b,c,d}'."""
    a_lower = str(axis).lower().strip()
    if a_lower in ("axis_a", "a", "geomorphology", "geomorph"):
        return "axis_a"
    if a_lower in ("axis_b", "b", "geochemistry", "geochem", "mineralogy"):
        return "axis_b"
    if a_lower in ("axis_c", "c", "thermophysics", "thermo"):
        return "axis_c"
    if a_lower in ("axis_d", "d", "volatiles", "aeolian", "volatiles_aeolian"):
        return "axis_d"
    return a_lower


def _get_feature_val(site_data: dict, feature_name: str) -> float:
    """Retrieves a physical feature value from a site dict, checking primary name and aliases."""
    val = site_data.get(feature_name)
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass

    for alias in FEATURE_ALIASES.get(feature_name, []):
        val = site_data.get(alias)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass

    return 0.0


def _get_weight(weights: Optional[dict], key: str) -> float:
    """Extracts axis weight from dict supporting both 'axis_a' and 'a' keys."""
    if not weights:
        return 0.25
    if key in weights:
        return float(weights[key])
    short_k = key.replace("axis_", "")
    if short_k in weights:
        return float(weights[short_k])
    return 0.25


def extract_axis_vector(site_data: dict, axis: str, normalize: bool = True) -> np.ndarray:
    """
    Extracts numerical feature vector for the given decoupled physical axis.
    Applies min-max domain normalization if normalize=True.
    """
    if isinstance(site_data.get(axis), (list, tuple, np.ndarray)):
        return np.asarray(site_data[axis], dtype=float)

    axis_norm = _normalize_axis_key(axis)
    features = AXIS_FEATURES.get(axis_norm, [])
    if not features:
        raise ValueError(f"Unknown axis: '{axis}'. Expected one of {list(AXIS_FEATURES.keys())}")

    vec = []
    for f in features:
        val = _get_feature_val(site_data, f)
        if normalize:
            f_min, f_max = AXIS_FEATURE_BOUNDS.get(f, (0.0, 1.0))
            norm_val = min_max_normalize(val, f_min, f_max)
            vec.append(norm_val)
        else:
            vec.append(val)

    return np.asarray(vec, dtype=float)


# =============================================================================
# Dual Distance & Similarity Metrics
# =============================================================================

def cosine_similarity_axis(
    u: np.ndarray, v: np.ndarray, zero_tol: float = 1e-15
) -> float:
    """
    Robust Normalized Cosine Similarity mapped to [0.0, 100.0]%.

    Guarantees:
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


def regularized_covariance(
    data: np.ndarray, alpha: float = 0.15, eps_scale: float = 1e-5
) -> np.ndarray:
    """
    Ledoit-Wolf-style diagonal shrinkage to guarantee positive-definiteness:
    Sigma_reg = (1 - alpha) * Cov + alpha * diag(Cov) + eps * I
    Works purely with numpy/scipy (no sklearn required).
    """
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


def mahalanobis_similarity_axis(
    u: np.ndarray, v: np.ndarray, inv_cov: np.ndarray = None
) -> float:
    """
    Monotonic inverse-decay Mahalanobis score mapped to [0.0, 100.0]%:
    S = 100.0 / (1.0 + D_M)
    When u == v or D_M == 0, returns 100.0.
    """
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    if u.shape != v.shape:
        raise ValueError(f"Shape mismatch: {u.shape} vs {v.shape}")

    if np.array_equal(u, v):
        return 100.0

    dim = len(u)
    if inv_cov is None:
        inv_cov = np.eye(dim)

    try:
        d = mahalanobis(u, v, inv_cov)
    except Exception:
        diff = u - v
        d = float(np.sqrt(np.dot(diff, diff)))

    if math.isnan(d) or d < 0.0:
        d = 0.0

    score = 100.0 / (1.0 + float(d))
    return float(np.clip(score, 0.0, 100.0))


# =============================================================================
# Uncertainty Propagation & Conservative Scoring
# =============================================================================

def propagate_uncertainty_taylor(
    axis_scores: dict, conf_target: float, conf_analog: float, weights: dict = None
) -> float:
    """
    Analytic first-order Taylor series error variance propagation:
    sigma_S = sqrt( sum_k (w_k * S_k * Delta_C)^2 )
    where Delta_C = sqrt((1 - C_t)^2 + (1 - C_a)^2)
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    c_t = float(np.clip(conf_target if conf_target is not None else 0.95, 0.0, 1.0))
    c_a = float(np.clip(conf_analog if conf_analog is not None else 0.95, 0.0, 1.0))
    delta_c = math.sqrt((1.0 - c_t) ** 2 + (1.0 - c_a) ** 2)

    var_sum = 0.0
    for axis, score in axis_scores.items():
        w = _get_weight(weights, axis)
        sigma_k = float(score) * delta_c
        var_sum += (w * sigma_k) ** 2
    return float(math.sqrt(var_sum))


def compute_conservative_score(
    composite_score: float = None, sigma: float = 0.0, comp_score: float = None
) -> float:
    """
    95% single-sided Lower Confidence Bound (LCB) ranking:
    S_LCB = max(0.0, min(100.0, S - 1.645 * sigma))
    """
    val = composite_score if composite_score is not None else comp_score
    if val is None:
        val = 0.0
    lcb = float(val) - 1.645 * float(sigma)
    return float(max(0.0, min(100.0, lcb)))


# =============================================================================
# Decomposed Profile Computation
# =============================================================================

def compute_similarity_profile(
    target: dict,
    analog: dict,
    method: str = "cosine",
    weights: dict = None,
    cov_matrices: dict = None,
) -> dict:
    """
    Computes decomposed similarity profile across 4 physical axes (A, B, C, D),
    composite weighted score, Taylor series uncertainty sigma, and conservative LCB score.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    norm_method = method.lower().strip()
    if norm_method not in ("cosine", "mahalanobis"):
        raise ValueError(f"Unsupported method: {method}. Choose 'cosine' or 'mahalanobis'.")

    axis_keys = ["axis_a", "axis_b", "axis_c", "axis_d"]
    axis_scores = {}

    for k in axis_keys:
        u = extract_axis_vector(target, k, normalize=True)
        v = extract_axis_vector(analog, k, normalize=True)

        if norm_method == "cosine":
            axis_scores[k] = cosine_similarity_axis(u, v)
        else:
            inv_cov = None
            if cov_matrices and k in cov_matrices:
                try:
                    inv_cov = np.linalg.pinv(cov_matrices[k])
                except Exception:
                    inv_cov = None
            axis_scores[k] = mahalanobis_similarity_axis(u, v, inv_cov)

    composite_raw = sum(_get_weight(weights, k) * axis_scores[k] for k in axis_keys)
    composite_score = round(float(np.clip(composite_raw, 0.0, 100.0)), 2)

    conf_target = target.get("measurement_confidence", 0.95)
    conf_analog = analog.get("measurement_confidence", 0.90)
    uncertainty_sigma = propagate_uncertainty_taylor(axis_scores, conf_target, conf_analog, weights=weights)
    uncertainty_sigma = round(float(uncertainty_sigma), 3)

    conservative_score = compute_conservative_score(composite_score, uncertainty_sigma)
    conservative_score = round(float(conservative_score), 2)

    target_site_id = target.get("site_id", "")
    analog_site_id = analog.get("site_id", analog.get("analog_id", ""))

    target_body = target.get("body", "Moon")
    delta_vector = {
        "gravity": {
            "ratio": 0.165 if target_body == "Moon" else (0.380 if target_body == "Mars" else 1.0),
            "delta": -0.835 if target_body == "Moon" else (-0.620 if target_body == "Mars" else 0.0),
        },
        "pressure": {
            "delta_kpa": -101.325 if target_body == "Moon" else (-100.715 if target_body == "Mars" else 0.0),
        },
        "radiation": {
            "multiplier": 350.0 if target_body == "Moon" else (180.0 if target_body == "Mars" else 1.0),
        },
    }

    profile = {
        "target_site_id": target_site_id,
        "analog_site_id": analog_site_id,
        "method": norm_method,
        "axis_a_pct": round(axis_scores["axis_a"], 2),
        "axis_b_pct": round(axis_scores["axis_b"], 2),
        "axis_c_pct": round(axis_scores["axis_c"], 2),
        "axis_d_pct": round(axis_scores["axis_d"], 2),
        "axis_a_geomorphology_pct": round(axis_scores["axis_a"], 2),
        "axis_b_geochemistry_pct": round(axis_scores["axis_b"], 2),
        "axis_c_thermophysics_pct": round(axis_scores["axis_c"], 2),
        "axis_d_volatiles_pct": round(axis_scores["axis_d"], 2),
        "composite_score": composite_score,
        "uncertainty_sigma": uncertainty_sigma,
        "uncertainty_bound": uncertainty_sigma,
        "conservative_score": conservative_score,
        "delta_vector": delta_vector,
    }
    return profile


# =============================================================================
# Database Integration & Search
# =============================================================================

def get_site_by_id(site_id: str, db_path: str = None) -> dict:
    """
    Retrieves site record from harmonized_sites, with fallback or supplementary join
    with terrestrial_analog_sites or site_engineering_safety.
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Try harmonized_sites first
    c.execute("SELECT * FROM harmonized_sites WHERE site_id = ?;", (site_id,))
    row = c.fetchone()
    site_dict = dict(row) if row else {}

    # If not found in harmonized_sites, try terrestrial_analog_sites
    if not site_dict:
        c.execute("SELECT * FROM terrestrial_analog_sites WHERE analog_id = ? OR name = ?;", (site_id, site_id))
        row = c.fetchone()
        if row:
            site_dict = dict(row)
            site_dict["site_id"] = site_dict.get("analog_id", site_id)
            site_dict["body"] = "Earth"
            site_dict["site_name"] = site_dict.get("name", "")

    # If still not found, try site_engineering_safety
    if not site_dict:
        c.execute("SELECT * FROM site_engineering_safety WHERE site_id = ?;", (site_id,))
        row = c.fetchone()
        if row:
            site_dict = dict(row)

    if not site_dict:
        conn.close()
        return {}

    # Supplementary enrichment
    # Earth site enrichment from terrestrial_analog_sites
    if site_dict.get("body") == "Earth" or "EARTH" in str(site_dict.get("site_id", "")):
        analog_key = site_dict.get("site_id")
        c.execute(
            "SELECT * FROM terrestrial_analog_sites WHERE analog_id = ? OR name = ?;",
            (analog_key, site_dict.get("site_name")),
        )
        analog_row = c.fetchone()
        if analog_row:
            for k, v in dict(analog_row).items():
                if k not in site_dict or site_dict[k] is None:
                    site_dict[k] = v

    # Moon/Mars site enrichment from site_engineering_safety
    if site_dict.get("body") in ("Moon", "Mars"):
        c.execute("SELECT * FROM site_engineering_safety WHERE site_id = ?;", (site_dict.get("site_id"),))
        eng_row = c.fetchone()
        if eng_row:
            eng_dict = dict(eng_row)
            if "rock_abundance_pct" not in site_dict or site_dict["rock_abundance_pct"] is None:
                site_dict["rock_abundance_pct"] = eng_dict.get("rock_abundance_percent")
            if "wind_shear_mps" not in site_dict or site_dict["wind_shear_mps"] is None:
                site_dict["wind_shear_mps"] = eng_dict.get("wind_shear_mps", 0.0)
            if "tri_ruggedness" not in site_dict or site_dict["tri_ruggedness"] is None:
                slope = site_dict.get("mean_slope_deg") or eng_dict.get("macro_slope_deg", 0.0)
                site_dict["tri_ruggedness"] = round(min(1.0, float(slope) / 45.0 * 0.5), 3)

    conn.close()
    return site_dict


def find_top_analogs(
    target_site_id: Union[str, dict],
    db_path: str = None,
    top_n: int = 5,
    method: str = "cosine",
    weights: dict = None,
) -> list:
    """
    Compares target site against all Earth analog candidates in terrestrial_analog_sites / harmonized_sites.
    Returns sorted list of profile dicts ordered by composite_score DESC (and conservative_score DESC).
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    if isinstance(target_site_id, dict):
        target_site = target_site_id
    else:
        target_site = get_site_by_id(target_site_id, db_path=db_path)
        if not target_site:
            raise ValueError(f"Target site '{target_site_id}' not found in database.")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    analogs = []
    try:
        c.execute("SELECT * FROM terrestrial_analog_sites;")
        rows = c.fetchall()
        for r in rows:
            d = dict(r)
            d["site_id"] = d.get("analog_id", d.get("site_id"))
            d["site_name"] = d.get("name", d.get("site_name"))
            d["body"] = "Earth"
            analogs.append(d)
    except Exception:
        pass

    if not analogs:
        try:
            c.execute("SELECT * FROM harmonized_sites WHERE body = 'Earth';")
            rows = c.fetchall()
            for r in rows:
                analogs.append(dict(r))
        except Exception:
            pass

    conn.close()

    profiles = []
    for a in analogs:
        prof = compute_similarity_profile(target_site, a, method=method, weights=weights)
        prof["analog_name"] = a.get("site_name", a.get("name", ""))
        prof["country"] = a.get("country", "")
        prof["primary_scientific_domain"] = a.get("primary_scientific_domain", "")
        profiles.append(prof)

    # Sort descending by composite_score, then conservative_score
    profiles.sort(key=lambda p: (p["composite_score"], p["conservative_score"]), reverse=True)

    result = profiles[:top_n]
    for idx, p in enumerate(result, start=1):
        p["rank"] = idx

    return result


def populate_similarity_profiles(
    db_path: str = None,
    target_site_ids: list = None,
    method: str = "cosine",
    weights: dict = None,
) -> int:
    """
    Populates similarity_profiles SQLite table matching the schema:
    (profile_id, target_site_id, analog_site_id, method, axis_a_geomorphology_pct,
     axis_b_geochemistry_pct, axis_c_thermophysics_pct, axis_d_volatiles_pct,
     composite_score, uncertainty_bound, rank, created_at).
    Returns count of inserted rows.
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if target_site_ids is None:
        c.execute("SELECT site_id FROM harmonized_sites WHERE body IN ('Moon', 'Mars');")
        target_site_ids = [row["site_id"] for row in c.fetchall()]

    inserted_count = 0

    for tid in target_site_ids:
        try:
            top_analogs = find_top_analogs(tid, db_path=db_path, top_n=5, method=method, weights=weights)
        except Exception:
            continue

        for p in top_analogs:
            profile_id = f"SIM_{tid}_{p['analog_site_id']}_{method.upper()}"
            now_iso = datetime.now(timezone.utc).isoformat()
            c.execute("""
                INSERT OR REPLACE INTO similarity_profiles (
                    profile_id, target_site_id, analog_site_id, method,
                    axis_a_geomorphology_pct, axis_b_geochemistry_pct,
                    axis_c_thermophysics_pct, axis_d_volatiles_pct,
                    composite_score, uncertainty_bound, rank, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                profile_id,
                tid,
                p["analog_site_id"],
                p["method"],
                p["axis_a_geomorphology_pct"],
                p["axis_b_geochemistry_pct"],
                p["axis_c_thermophysics_pct"],
                p["axis_d_volatiles_pct"],
                p["composite_score"],
                p["uncertainty_bound"],
                p["rank"],
                now_iso,
            ))
            inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count
