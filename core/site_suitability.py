#!/usr/bin/env python3
"""
Site Suitability & Engineering Constraint Masking Module (R2).

Implements:
1. Four hard engineering cutoffs (slope, rock abundance, polar illumination & LoS, cold trap proximity).
2. Non-linear S-curve Multi-Attribute Utility Theory (MAUT) marginal utility functions.
3. Composite utility scoring and Conservative Lower Confidence Bound (LCB) ranking under uncertainty.
4. Pareto dominance evaluation across multi-criteria candidate profiles.
5. Dual-tier masking: relational SQL candidate filtering and 2D vectorized NumPy raster spatial masking.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import math
import os
from pathlib import Path
import sqlite3
import numpy as np

# =============================================================================
# Constants & Default Engineering Thresholds
# =============================================================================

DEFAULT_DB_PATH = Path(
    os.getenv("PLANETARY_DB_PATH", Path(__file__).resolve().parent.parent / "planetary_moon_mars.db")
)

DEFAULT_THRESHOLDS = {
    "max_slope_deg": 10.0,
    "max_rock_abundance_pct": 5.0,
    "min_solar_illum_pct": 80.0,
    "min_earth_vis_pct": 50.0,
    "max_cold_trap_dist_km": 5.0,
    "lunar_polar_lat_cutoff": 80.0,
}

DEFAULT_UTILITY_WEIGHTS = {
    "slope": 0.25,
    "rock": 0.20,
    "illum": 0.25,
    "vis": 0.15,
    "cold_trap": 0.15,
}


def _validate_physical_inputs(
    slope_deg: float,
    rock_abundance_pct: float,
    solar_illum_pct: Optional[float] = None,
    earth_vis_pct: Optional[float] = None,
    cold_trap_dist_km: Optional[float] = None,
    latitude_deg: Optional[float] = None,
) -> None:
    """
    Validates physical parameter boundaries and domain ranges.
    Raises ValueError on NaN, Inf, or impossible physical values.
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
    if latitude_deg is not None:
        if math.isnan(latitude_deg) or math.isinf(latitude_deg):
            raise ValueError("Latitude cannot be NaN or Inf")


def check_hard_cutoffs(
    slope_deg: Union[float, Dict[str, Any]],
    rock_abundance_pct: Optional[float] = None,
    solar_illum_pct: Optional[float] = None,
    earth_vis_pct: Optional[float] = None,
    cold_trap_dist_km: Optional[float] = None,
    body: str = "Moon",
    latitude_deg: float = -85.0,
    **kwargs: Any,
) -> bool:
    """
    Evaluates the 4 R2 Hard Engineering Cutoffs:
    1. Slope <= 10.0 deg (tip-over stability limit at 5m baseline).
    2. Rock Abundance <= 5.0% (Diviner boulder strike hazard limit).
    3. Solar Illumination >= 80.0% AND Earth Visibility >= 50.0% (Lunar South Pole |lat| >= 80.0 deg).
    4. Proximity to Cold Trap <= 5.0 km (polar ice harvesting access, if specified).

    Accepts either individual parameter values or a candidate site dictionary as first argument.

    Raises:
        ValueError: If any parameter is NaN, Inf, or outside realistic physical domain bounds.

    Returns:
        bool: True if candidate satisfies all applicable cutoffs, False otherwise.
    """
    if isinstance(slope_deg, dict):
        site_dict = slope_deg
        body = site_dict.get("body", body)
        latitude_deg = site_dict.get("center_lat", site_dict.get("latitude_deg", latitude_deg))
        rock_abundance_pct = site_dict.get("rock_abundance_percent", site_dict.get("rock_abundance_pct", rock_abundance_pct))
        solar_illum_pct = site_dict.get("solar_illum_pct", site_dict.get("illumination", solar_illum_pct))
        dte = site_dict.get("earth_vis_pct", site_dict.get("dte_visibility_fraction", earth_vis_pct))
        if dte is not None and dte <= 1.0 and "earth_vis_pct" not in site_dict:
            earth_vis_pct = dte * 100.0
        else:
            earth_vis_pct = dte
        cold_trap_dist_km = site_dict.get("cold_trap_dist_km", cold_trap_dist_km)
        slope_val = float(site_dict.get("mean_slope_deg", site_dict.get("macro_slope_deg", site_dict.get("slope_deg", 0.0))))
    else:
        slope_val = float(slope_deg)

    if rock_abundance_pct is None:
        raise ValueError("Rock abundance percentage is required")

    rock_val = float(rock_abundance_pct)
    illum_val = float(solar_illum_pct) if solar_illum_pct is not None else None
    vis_val = float(earth_vis_pct) if earth_vis_pct is not None else None
    cold_val = float(cold_trap_dist_km) if cold_trap_dist_km is not None else None
    lat_val = float(latitude_deg) if latitude_deg is not None else -85.0

    _validate_physical_inputs(
        slope_deg=slope_val,
        rock_abundance_pct=rock_val,
        solar_illum_pct=illum_val,
        earth_vis_pct=vis_val,
        cold_trap_dist_km=cold_val,
        latitude_deg=lat_val,
    )

    # Cutoff 1: Slope <= 10.0 deg
    if slope_val > 10.0:
        return False

    # Cutoff 2: Rock abundance <= 5.0%
    if rock_val > 5.0:
        return False

    # Cutoff 3: Polar lunar illumination & Earth visibility
    is_lunar_polar = (str(body).strip().lower() == "moon" and abs(lat_val) >= 80.0)
    if is_lunar_polar:
        if illum_val is not None and illum_val < 80.0:
            return False
        if vis_val is not None and vis_val < 50.0:
            return False

    # Cutoff 4: Cold trap proximity <= 5.0 km
    if cold_val is not None and cold_val > 5.0:
        return False

    return True


# Hard cutoff function aliases
is_site_suitable = check_hard_cutoffs
passes_hard_mask = check_hard_cutoffs
evaluate_hard_cutoffs = check_hard_cutoffs


# =============================================================================
# Marginal Utility Functions (MAUT S-Curves)
# =============================================================================

def utility_slope(slope_deg: float) -> float:
    """
    Non-linear S-curve marginal utility for slope:
    u(theta) = 1.0 - (theta / 10.0)^2 for 0.0 <= theta <= 10.0, else 0.0.
    """
    s = float(slope_deg)
    if s > 10.0:
        return 0.0
    if s < 0.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (s / 10.0) ** 2))


compute_slope_utility = utility_slope


def utility_rock(rock_pct: float) -> float:
    """
    Non-linear marginal utility for rock abundance:
    u(r) = 1.0 - (r / 5.0)^1.5 for 0.0 <= r <= 5.0, else 0.0.
    """
    r = float(rock_pct)
    if r > 5.0:
        return 0.0
    if r < 0.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (r / 5.0) ** 1.5))


compute_rock_utility = utility_rock


def utility_illumination(illum_pct: float) -> float:
    """
    Concave square-root marginal utility for polar solar illumination:
    u(I) = ((I - 80.0) / 20.0)^0.5 for 80.0 <= I <= 100.0, else 0.0.
    """
    i = float(illum_pct)
    if i < 80.0:
        return 0.0
    return max(0.0, min(1.0, ((min(100.0, i) - 80.0) / 20.0) ** 0.5))


def utility_visibility(vis_pct: float) -> float:
    """
    Concave square-root marginal utility for Earth line-of-sight visibility:
    u(V) = ((V - 50.0) / 50.0)^0.5 for 50.0 <= V <= 100.0, else 0.0.
    """
    v = float(vis_pct)
    if v < 50.0:
        return 0.0
    return max(0.0, min(1.0, ((min(100.0, v) - 50.0) / 50.0) ** 0.5))


def utility_cold_trap(cold_trap_km: float) -> float:
    """
    Linear proximity decay utility for ISRU cold trap access:
    u(d) = 1.0 - (d / 5.0) for 0.0 <= d <= 5.0, else 0.0.
    """
    d = float(cold_trap_km)
    if d > 5.0:
        return 0.0
    if d < 0.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (d / 5.0)))


# =============================================================================
# Composite & Conservative Utility Scoring
# =============================================================================

def compute_composite_utility(
    slope_deg: float,
    rock_pct: float,
    illum_pct: float = 100.0,
    vis_pct: float = 100.0,
    cold_trap_km: float = 0.0,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Multi-Attribute Utility score strictly bounded in [0.0, 100.0].
    Score = 100.0 * (w_slope * u_slope + w_rock * u_rock + w_illum * u_illum + w_vis * u_vis + w_trap * u_trap)
    Rounded to 4 decimal places.
    """
    w = dict(DEFAULT_UTILITY_WEIGHTS)
    if weights:
        w.update(weights)

    total_w = sum(w.values())
    if total_w <= 0.0:
        total_w = 1.0

    w_slope = w["slope"] / total_w
    w_rock = w["rock"] / total_w
    w_illum = w["illum"] / total_w
    w_vis = w["vis"] / total_w
    w_trap = w["cold_trap"] / total_w

    u_s = utility_slope(slope_deg)
    u_r = utility_rock(rock_pct)
    u_i = utility_illumination(illum_pct)
    u_v = utility_visibility(vis_pct)
    u_t = utility_cold_trap(cold_trap_km)

    score = 100.0 * (w_slope * u_s + w_rock * u_r + w_illum * u_i + w_vis * u_v + w_trap * u_t)
    clamped_score = max(0.0, min(100.0, score))
    return round(clamped_score, 4)


composite_utility = compute_composite_utility


def pareto_dominates(
    cand_a: Dict[str, Any],
    cand_b: Dict[str, Any],
    keys: Optional[List[str]] = None,
) -> bool:
    """
    Determines whether candidate A strictly Pareto-dominates candidate B across given criteria keys:
    Returns True iff all(A[k] >= B[k]) and any(A[k] > B[k]).
    """
    if keys is None:
        keys = [k for k in cand_a if k in cand_b and isinstance(cand_a[k], (int, float))]

    if not keys:
        return False

    all_ge = all(cand_a[k] >= cand_b[k] for k in keys)
    any_gt = any(cand_a[k] > cand_b[k] for k in keys)
    return all_ge and any_gt


dominates = pareto_dominates
is_pareto_dominant = pareto_dominates


def compute_conservative_utility(
    nominal_utility: float,
    measurement_confidence: float = 1.0,
) -> float:
    """
    Computes uncertainty-penalized conservative utility score:
    U_conservative = nominal_utility * measurement_confidence
    Ensures high-confidence candidate outranks high-uncertainty candidate.
    """
    conf = max(0.0, min(1.0, float(measurement_confidence)))
    return round(float(nominal_utility) * conf, 4)


conservative_utility = compute_conservative_utility


# =============================================================================
# Comprehensive Site Evaluator
# =============================================================================

def evaluate_site_suitability(
    site_data: Dict[str, Any],
    body: str = "Moon",
) -> Dict[str, Any]:
    """
    Performs full site suitability assessment for a candidate landing site.

    Returns structured summary dictionary with:
    - is_suitable (bool)
    - failed_constraints (List[str])
    - passed_constraints (List[str])
    - utility_score (float)
    - conservative_utility_score (float)
    - utilities (Dict[str, float])
    - raw_parameters (Dict[str, Any])
    """
    body_val = site_data.get("body", body)
    lat_val = float(site_data.get("center_lat", site_data.get("latitude_deg", -85.0)))
    slope_val = float(site_data.get("mean_slope_deg", site_data.get("macro_slope_deg", site_data.get("slope_deg", 0.0))))
    rock_val = float(site_data.get("rock_abundance_percent", site_data.get("rock_abundance_pct", 0.0)))
    
    dte = site_data.get("earth_vis_pct", site_data.get("dte_visibility_fraction", None))
    if dte is not None and dte <= 1.0 and "earth_vis_pct" not in site_data:
        vis_val = float(dte) * 100.0
    elif dte is not None:
        vis_val = float(dte)
    else:
        vis_val = 50.0

    illum = site_data.get("solar_illum_pct", site_data.get("illumination", None))
    if illum is not None:
        illum_val = float(illum)
    else:
        illum_val = 82.0 if (str(body_val).lower() == "moon" and abs(lat_val) >= 80.0) else 100.0

    cold = site_data.get("cold_trap_dist_km", None)
    if cold is not None:
        cold_val = float(cold)
    else:
        cold_val = (1.5 + (90.0 - abs(lat_val)) * 0.8) if (str(body_val).lower() == "moon" and abs(lat_val) >= 80.0) else 0.0

    confidence = float(site_data.get("measurement_confidence", 1.0))

    # Evaluate cutoffs
    failed = []
    passed = []

    if slope_val <= 10.0:
        passed.append("slope_deg <= 10.0")
    else:
        failed.append(f"slope_deg ({slope_val:.2f}) > 10.0")

    if rock_val <= 5.0:
        passed.append("rock_abundance_pct <= 5.0")
    else:
        failed.append(f"rock_abundance_pct ({rock_val:.2f}) > 5.0")

    is_lunar_polar = (str(body_val).lower() == "moon" and abs(lat_val) >= 80.0)
    if is_lunar_polar:
        if illum_val >= 80.0:
            passed.append("solar_illum_pct >= 80.0")
        else:
            failed.append(f"solar_illum_pct ({illum_val:.2f}%) < 80.0%")

        if vis_val >= 50.0:
            passed.append("earth_vis_pct >= 50.0")
        else:
            failed.append(f"earth_vis_pct ({vis_val:.2f}%) < 50.0%")

    if cold_val is not None:
        if cold_val <= 5.0:
            passed.append("cold_trap_dist_km <= 5.0")
        else:
            failed.append(f"cold_trap_dist_km ({cold_val:.2f} km) > 5.0 km")

    is_suitable = len(failed) == 0

    # Utilities
    u_s = utility_slope(slope_val)
    u_r = utility_rock(rock_val)
    u_i = utility_illumination(illum_val)
    u_v = utility_visibility(vis_val)
    u_t = utility_cold_trap(cold_val)

    util_score = compute_composite_utility(slope_val, rock_val, illum_val, vis_val, cold_val)
    conservative_score = compute_conservative_utility(util_score, confidence)

    return {
        "site_id": site_data.get("site_id", "UNKNOWN"),
        "site_name": site_data.get("site_name", "Unknown Site"),
        "body": body_val,
        "is_suitable": is_suitable,
        "failed_constraints": failed,
        "passed_constraints": passed,
        "utility_score": util_score,
        "conservative_utility_score": conservative_score,
        "utilities": {
            "u_slope": round(u_s, 4),
            "u_rock": round(u_r, 4),
            "u_illum": round(u_i, 4),
            "u_vis": round(u_v, 4),
            "u_cold_trap": round(u_t, 4),
        },
        "raw_parameters": {
            "slope_deg": slope_val,
            "rock_abundance_pct": rock_val,
            "solar_illum_pct": illum_val,
            "earth_vis_pct": vis_val,
            "cold_trap_dist_km": cold_val,
            "measurement_confidence": confidence,
            "center_lat": lat_val,
            "center_lon": site_data.get("center_lon", 0.0),
        },
    }


# =============================================================================
# Vectorized 2D Raster Spatial Mask
# =============================================================================

def create_raster_mask(
    slope_grid: np.ndarray,
    rock_grid: np.ndarray,
    max_slope: float = 10.0,
    max_rock: float = 5.0,
    illum_grid: Optional[np.ndarray] = None,
    min_illum: float = 80.0,
    vis_grid: Optional[np.ndarray] = None,
    min_vis: float = 50.0,
) -> np.ndarray:
    """
    Vectorized NumPy continuous gridded raster mask:
    Returns boolean 2D array where True indicates all engineering thresholds are satisfied.
    """
    mask = (slope_grid <= max_slope) & (rock_grid <= max_rock)
    if illum_grid is not None:
        mask = mask & (illum_grid >= min_illum)
    if vis_grid is not None:
        mask = mask & (vis_grid >= min_vis)
    return mask


# =============================================================================
# Database Candidate Ranking & SQL Filtering
# =============================================================================

def filter_candidate_sites(
    db_path: Union[str, Path] = DEFAULT_DB_PATH,
    body: str = "Moon",
    constraints: Optional[Dict[str, float]] = None,
    apply_soft_ranking: bool = True,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Queries harmonized_sites and site_engineering_safety in SQLite database,
    enforces 4 hard engineering cutoffs, calculates soft MAUT utility rankings,
    and returns a sorted list of compliant landing candidates.
    """
    c_map = dict(DEFAULT_THRESHOLDS)
    if constraints:
        c_map.update(constraints)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT 
            h.site_id,
            h.body,
            h.site_name,
            h.target_region,
            h.center_lat,
            h.center_lon,
            h.h3_res6,
            h.mean_slope_deg,
            s.rock_abundance_percent,
            s.dte_visibility_fraction,
            s.max_eclipse_hours,
            h.measurement_confidence
        FROM harmonized_sites h
        LEFT JOIN site_engineering_safety s USING (site_id)
        WHERE LOWER(h.body) = LOWER(?)
    """
    cursor.execute(query, (body,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        row_dict = dict(r)
        slope = row_dict["mean_slope_deg"] if row_dict.get("mean_slope_deg") is not None else 0.0
        rock = row_dict["rock_abundance_percent"] if row_dict.get("rock_abundance_percent") is not None else 0.0
        lat = row_dict["center_lat"]

        dte = row_dict.get("dte_visibility_fraction")
        vis = (float(dte) * 100.0) if (dte is not None and dte <= 1.0) else (float(dte) if dte is not None else 50.0)

        # Derived illumination
        max_eclipse = row_dict.get("max_eclipse_hours")
        if max_eclipse is not None and max_eclipse > 0:
            illum = max(0.0, min(100.0, 100.0 * (1.0 - float(max_eclipse) / 708.7)))
        elif str(body).lower() == "moon" and abs(lat) >= 80.0:
            illum = 82.0
        else:
            illum = 100.0

        # Cold trap distance
        if str(body).lower() == "moon" and abs(lat) >= 80.0:
            cold_trap = 1.5 + (90.0 - abs(lat)) * 0.8
        else:
            cold_trap = 0.0

        eval_input = {
            "site_id": row_dict["site_id"],
            "site_name": row_dict["site_name"],
            "body": row_dict["body"],
            "center_lat": lat,
            "center_lon": row_dict["center_lon"],
            "mean_slope_deg": slope,
            "rock_abundance_pct": rock,
            "solar_illum_pct": illum,
            "earth_vis_pct": vis,
            "cold_trap_dist_km": cold_trap,
            "measurement_confidence": row_dict.get("measurement_confidence") or 1.0,
        }

        # Check cutoffs against custom thresholds if specified
        is_qual = check_hard_cutoffs(
            slope_deg=slope,
            rock_abundance_pct=rock,
            solar_illum_pct=illum,
            earth_vis_pct=vis,
            cold_trap_dist_km=cold_trap,
            body=body,
            latitude_deg=lat,
        )

        # Further filter against custom thresholds if tighter than defaults
        if is_qual:
            if slope > c_map.get("max_slope_deg", 10.0):
                is_qual = False
            elif rock > c_map.get("max_rock_abundance_pct", 5.0):
                is_qual = False
            elif str(body).lower() == "moon" and abs(lat) >= 80.0:
                if illum < c_map.get("min_solar_illum_pct", 80.0):
                    is_qual = False
                elif vis < c_map.get("min_earth_vis_pct", 50.0):
                    is_qual = False
            if cold_trap > c_map.get("max_cold_trap_dist_km", 5.0):
                is_qual = False

        if is_qual:
            assessment = evaluate_site_suitability(eval_input, body=body)
            results.append(assessment)

    if apply_soft_ranking:
        results.sort(key=lambda x: (x["conservative_utility_score"], x["utility_score"]), reverse=True)

    if limit is not None and limit > 0:
        results = results[:limit]

    return results
