#!/usr/bin/env python3
"""
Physical Limit Delta-Vectors Module (R5).

Explicitly computes and formats physical delta-vectors (surface gravity ratio,
atmospheric pressure delta, and radiation dose multiplier) between candidate
terrestrial analogs and target Moon/Mars base locations.
"""

from typing import Any, Dict, Optional, Union
import math
import json

# =============================================================================
# Physical Constants & Ground-Truth Baselines
# =============================================================================

EARTH_G0 = 1.0                     # Standard Earth gravity (g0)
EARTH_KPA = 101.325                # Standard sea-level pressure (kPa)
EARTH_MSV_DAY = 0.006571           # 2.4 mSv/year terrestrial background (mSv/day)

MOON_G_RATIO = 0.1654              # 1.622 m/s^2 / 9.80665 m/s^2 (~0.165 g0)
MOON_G_DELTA_PCT = -83.5           # -83.46% relative to Earth
MOON_BASE_KPA = 0.0                # Hard vacuum exosphere
MOON_RAD_MULTIPLIER = 350.0        # Unshielded surface GCR/SPE dose multiplier (~2.3 mSv/day)

MARS_G_RATIO = 0.3795              # 3.721 m/s^2 / 9.80665 m/s^2 (~0.380 g0)
MARS_G_DELTA_PCT = -62.0           # -62.06% relative to Earth
MARS_BASE_KPA = 0.610              # Datum surface pressure (610 Pa)
MARS_SCALE_HEIGHT_M = 11100.0      # Barometric scale height (11.1 km)
MARS_RAD_MULTIPLIER = 180.0        # Unshielded surface GCR dose multiplier (~1.18 mSv/day)

VOID_ATTENUATION_FACTOR = 0.10     # Cave/subsurface void 90% overburden shielding


def compute_physical_delta_vector(
    target_body: Optional[Union[str, Dict[str, Any]]] = None,
    analog_site: Optional[Dict[str, Any]] = None,
    target_site: Optional[Dict[str, Any]] = None,
    elevation_m: Optional[float] = None,
    has_subsurface_void: Optional[Union[bool, int]] = None,
    sky_view_factor: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes physical limit delta-vectors (gravity, atmospheric pressure, radiation dose)
    between Earth analogs and destination celestial bodies (Moon, Mars, Earth).

    Args:
        target_body: Celestial body name ('Moon', 'Mars', 'Earth') or candidate site dictionary.
        analog_site: Optional terrestrial analog site dictionary.
        target_site: Optional candidate landing site dictionary.
        elevation_m: Surface elevation in meters relative to planetary datum (for barometric scaling).
        has_subsurface_void: True/1 if site is located in or adjacent to a lava tube/cave.
        sky_view_factor: Fractional exposure to open sky [0.0, 1.0]. Attenuates radiation.

    Returns:
        JSON-serializable dictionary with gravity, pressure, and radiation delta-vectors.
    """
    # Extract body if target_body is a dictionary or target_site is provided
    body_str = None
    if isinstance(target_body, dict):
        target_site = target_body
        body_val = target_site.get("body")
        if body_val is None:
            body_val = target_site.get("body_id")
        if body_val is not None:
            body_str = str(body_val).strip()
            if not body_str:
                raise ValueError("Unknown celestial body: ''")
        else:
            body_str = "Moon"
    elif target_body is not None:
        body_str = str(target_body).strip()
        if not body_str:
            raise ValueError("Unknown celestial body: ''")
    elif target_site is not None:
        body_val = target_site.get("body")
        if body_val is None:
            body_val = target_site.get("body_id")
        if body_val is not None:
            body_str = str(body_val).strip()
            if not body_str:
                raise ValueError("Unknown celestial body: ''")
        else:
            body_str = "Moon"
    else:
        body_str = "Moon"

    if not body_str:
        body_str = "Moon"

    # Canonicalize body name
    norm_body = body_str.strip().lower()
    if norm_body in ("moon", "luna"):
        canon_body = "Moon"
    elif norm_body in ("mars", "ares"):
        canon_body = "Mars"
    elif norm_body in ("earth", "terra"):
        canon_body = "Earth"
    else:
        raise ValueError(f"Unknown celestial body: {body_str}")

    # Extract site attributes if provided in target_site (avoid falsy zero masking)
    if target_site:
        if elevation_m is None:
            elev = target_site.get("elevation_m")
            elevation_m = elev if elev is not None else target_site.get("elevation_mola_m")
        if has_subsurface_void is None:
            has_subsurface_void = target_site.get("has_subsurface_void")
        if sky_view_factor is None:
            svf = target_site.get("sky_view_factor")
            sky_view_factor = svf if svf is not None else target_site.get("radiation_svf")

    # 1. Surface Gravity Vector
    if canon_body == "Moon":
        g_ratio = MOON_G_RATIO
        g_delta_pct = MOON_G_DELTA_PCT
        g_target = MOON_G_RATIO
        g_impact = (
            "Extreme low gravity (0.165 g0). Greatly reduced traction, risk of high-center-of-mass "
            "rover tip-over, reduced structural weight requirements, reduced hydrostatic fluid pressure."
        )
    elif canon_body == "Mars":
        g_ratio = MARS_G_RATIO
        g_delta_pct = MARS_G_DELTA_PCT
        g_target = MARS_G_RATIO
        g_impact = (
            "Moderate low gravity (0.380 g0). Reduced structural load; mobility mechanics differ "
            "substantially from terrestrial tire/soil traction models."
        )
    else:  # Earth
        g_ratio = 1.0
        g_delta_pct = 0.0
        g_target = 1.0
        g_impact = "Earth baseline standard gravity (1.000 g0)."

    gravity_dict = {
        "earth_baseline_g0": float(EARTH_G0),
        "target_value_g0": round(float(g_target), 4),
        "ratio_to_earth": round(float(g_ratio), 4),
        "relative_delta_pct": round(float(g_delta_pct), 2),
        "unit": "g0",
        "engineering_impact": g_impact,
        "ratio": round(float(g_ratio), 4),
        "delta": round(float(g_delta_pct) / 100.0, 4),
    }

    # 2. Atmospheric Pressure Vector & Hypsometric Scaling
    if canon_body == "Moon":
        p_target = MOON_BASE_KPA
        p_delta = round(p_target - EARTH_KPA, 4)
        p_impact = (
            "Hard vacuum (0.0 kPa, delta = -101.325 kPa). Zero convective cooling, severe cold-welding risk, "
            "full spacesuit and habitat structural pressurization requirement, no aerodynamic braking."
        )
    elif canon_body == "Mars":
        if elevation_m is not None:
            # Barometric hypsometric formula: P(z) = P0 * exp(-z / H)
            exponent = -float(elevation_m) / MARS_SCALE_HEIGHT_M
            if exponent > 100.0:
                p_calc = float("inf")
            else:
                try:
                    p_calc = MARS_BASE_KPA * math.exp(exponent)
                except OverflowError:
                    p_calc = float("inf")
            p_target = max(0.0, float(p_calc))
        else:
            p_target = MARS_BASE_KPA
        p_delta = round(p_target - EARTH_KPA, 4)
        p_impact = (
            f"Near-vacuum CO2 atmosphere ({p_target:.3f} kPa, delta = {p_delta:.3f} kPa). "
            "Negligible aerodynamic lift, insufficient for human respiration, requires pressurized suits and airtight habitats."
        )
    else:  # Earth
        p_target = EARTH_KPA
        p_delta = 0.0
        p_impact = "Earth sea-level atmospheric baseline (101.325 kPa)."

    pressure_dict = {
        "earth_baseline_kpa": float(EARTH_KPA),
        "target_value_kpa": round(float(p_target), 4),
        "delta_kpa": round(float(p_delta), 4),
        "unit": "kPa",
        "engineering_impact": p_impact,
    }

    # 3. Radiation Dose Exposure Vector & Subsurface Attenuation
    # Determine attenuation factor
    if sky_view_factor is not None:
        svf_clamped = max(0.0, min(1.0, float(sky_view_factor)))
        attenuation = svf_clamped
    elif bool(has_subsurface_void):
        attenuation = VOID_ATTENUATION_FACTOR
    else:
        attenuation = 1.0

    if canon_body == "Moon":
        unshielded_mult = MOON_RAD_MULTIPLIER
        eff_mult = unshielded_mult * attenuation
        eff_dose = EARTH_MSV_DAY * eff_mult
        r_impact = (
            f"Surface cosmic radiation exposure ({eff_mult:.1f}x Earth baseline). "
            "Unfiltered GCR and acute SPE solar storms require >= 2-3m regolith shielding or habitat burial."
        )
    elif canon_body == "Mars":
        unshielded_mult = MARS_RAD_MULTIPLIER
        eff_mult = unshielded_mult * attenuation
        eff_dose = EARTH_MSV_DAY * eff_mult
        r_impact = (
            f"Martian cosmic radiation exposure ({eff_mult:.1f}x Earth baseline). "
            "Weak atmosphere provides minimal GCR shielding; SPE solar particle events require active shielding or regolith cover."
        )
    else:  # Earth
        unshielded_mult = 1.0
        eff_mult = 1.0 * attenuation
        eff_dose = EARTH_MSV_DAY * eff_mult
        r_impact = "Earth natural background radiation baseline (~0.007 mSv/day)."

    radiation_dict = {
        "earth_baseline_msv_day": round(float(EARTH_MSV_DAY), 6),
        "target_effective_msv_day": round(float(eff_dose), 5),
        "multiplier": round(float(eff_mult), 2),
        "unit": "multiplier / mSv/day",
        "engineering_impact": r_impact,
    }

    result = {
        "target_body": canon_body,
        "gravity": gravity_dict,
        "atmospheric_pressure": pressure_dict,
        "radiation_dose": radiation_dict,
        # Shorthand aliases for downstream scientific workflows
        "pressure": pressure_dict,
        "radiation": radiation_dict,
    }

    return result


def format_delta_vector_cli(delta: Dict[str, Any]) -> str:
    """
    Formats physical limit delta-vector dictionary into a human-readable CLI summary table.
    Ensures all required tokens ('Physical Limit Delta-Vectors', 'g0', 'kPa', 'Operational Impact')
    are present.
    """
    body = delta.get("target_body", "Target Body")
    grav = delta.get("gravity", {})
    pres = delta.get("atmospheric_pressure", delta.get("pressure", {}))
    rad = delta.get("radiation_dose", delta.get("radiation", {}))

    lines = [
        "=========================================================================================================",
        f"               Physical Limit Delta-Vectors: Earth Baseline -> {body}",
        "=========================================================================================================",
        "• Surface Gravity:",
        f"  - Earth Baseline:     {grav.get('earth_baseline_g0', 1.0):.3f} g0 (9.807 m/s²)",
        f"  - Target Value:       {grav.get('target_value_g0', 0.0):.3f} g0",
        f"  - Ratio / Delta:      {grav.get('ratio_to_earth', grav.get('ratio', 0.0)):.3f}x ({grav.get('relative_delta_pct', 0.0):+.1f}% relative delta)",
        f"  - Operational Impact: {grav.get('engineering_impact', 'Significant alteration of mobility mechanics.')}",
        "",
        "• Atmospheric Pressure:",
        f"  - Earth Baseline:     {pres.get('earth_baseline_kpa', 101.325):.3f} kPa (1 atm)",
        f"  - Target Value:       {pres.get('target_value_kpa', 0.0):.3f} kPa",
        f"  - Pressure Delta:     {pres.get('delta_kpa', -101.325):.3f} kPa",
        f"  - Operational Impact: {pres.get('engineering_impact', 'Requires hermetic pressure sealing.')}",
        "",
        "• Radiation Dose Exposure:",
        f"  - Earth Baseline:     {rad.get('earth_baseline_msv_day', 0.007):.3f} mSv/day (2.4 mSv/year natural background)",
        f"  - Target Effective:   {rad.get('target_effective_msv_day', 0.0):.3f} mSv/day",
        f"  - Dose Multiplier:    {rad.get('multiplier', 1.0):.1f}x",
        f"  - Operational Impact: {rad.get('engineering_impact', 'Requires regolith or cave overburden shielding.')}",
        "=========================================================================================================",
    ]
    return "\n".join(lines)
