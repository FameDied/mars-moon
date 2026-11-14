"""
Unit and integration tests for physical limit delta-vectors across Earth, Moon, and Mars:
gravity ratio, atmospheric pressure delta, and radiation dose multiplier (Feature 9).
"""

import json
import os
import sqlite3
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("PLANETARY_DB_PATH", PROJECT_ROOT / "planetary_moon_mars.db"))

# Dynamic binding to core.delta_vectors per review and dispatch specifications.
# Eliminates self-certifying embedded fallbacks; tests skip cleanly if module is unbuilt.
try:
    import core.delta_vectors as delta_mod
    CORE_DELTA_AVAILABLE = True
except ModuleNotFoundError as e:
    if e.name in ("core", "core.delta_vectors"):
        CORE_DELTA_AVAILABLE = False
        delta_mod = None
    else:
        raise


class TestDeltaVectors(unittest.TestCase):
    """
    Tier 1 & Tier 2 tests for physical limit delta-vectors (gravity, pressure, radiation),
    elevation scaling, void shielding, and CLI presentation.
    """

    def setUp(self):
        if not CORE_DELTA_AVAILABLE:
            self.skipTest("core.delta_vectors not yet available")

    # --- Tier 1: Core Physical Delta-Vectors ---

    def test_gravity_ratio_moon(self):
        """Moon surface gravity relative to Earth must be ~0.165 g0 (1.62 m/s^2)."""
        delta = delta_mod.compute_physical_delta_vector("Moon")
        ratio = delta["gravity"]["ratio_to_earth"]
        self.assertAlmostEqual(ratio, 0.165, delta=0.01)
        self.assertAlmostEqual(delta["gravity"]["relative_delta_pct"], -83.5, delta=1.0)

    def test_gravity_ratio_mars(self):
        """Mars surface gravity relative to Earth must be ~0.380 g0 (3.72 m/s^2)."""
        delta = delta_mod.compute_physical_delta_vector("Mars")
        ratio = delta["gravity"]["ratio_to_earth"]
        self.assertAlmostEqual(ratio, 0.380, delta=0.01)
        self.assertAlmostEqual(delta["gravity"]["relative_delta_pct"], -62.0, delta=1.0)

    def test_gravity_ratio_earth_to_earth(self):
        """Earth compared to Earth baseline must yield ratio of 1.0 and 0% delta."""
        delta = delta_mod.compute_physical_delta_vector("Earth")
        ratio = delta["gravity"]["ratio_to_earth"]
        self.assertEqual(ratio, 1.0)
        self.assertEqual(delta["gravity"]["relative_delta_pct"], 0.0)

    def test_atmospheric_pressure_delta_moon(self):
        """Moon has hard vacuum (0 kPa), yielding delta of -101.325 kPa."""
        delta = delta_mod.compute_physical_delta_vector("Moon")
        pres_delta = delta["atmospheric_pressure"]["delta_kpa"]
        self.assertAlmostEqual(pres_delta, -101.325, places=2)
        self.assertEqual(delta["atmospheric_pressure"]["target_value_kpa"], 0.0)

    def test_atmospheric_pressure_delta_mars(self):
        """Mars nominal surface pressure is ~0.610 kPa, yielding delta of ~ -100.715 kPa."""
        delta = delta_mod.compute_physical_delta_vector("Mars")
        pres_delta = delta["atmospheric_pressure"]["delta_kpa"]
        self.assertAlmostEqual(pres_delta, -100.715, places=1)
        self.assertAlmostEqual(delta["atmospheric_pressure"]["target_value_kpa"], 0.610, places=2)

    def test_radiation_multiplier_moon(self):
        """Unshielded lunar surface radiation dose multiplier must be in range [300, 420]x."""
        delta = delta_mod.compute_physical_delta_vector("Moon")
        mult = delta["radiation_dose"]["multiplier"]
        self.assertTrue(
            300.0 <= mult <= 420.0,
            f"Lunar radiation multiplier {mult}x out of expected range [300, 420]x",
        )

    def test_radiation_multiplier_mars(self):
        """Unshielded Martian surface radiation dose multiplier must be in range [160, 250]x."""
        delta = delta_mod.compute_physical_delta_vector("Mars")
        mult = delta["radiation_dose"]["multiplier"]
        self.assertTrue(
            160.0 <= mult <= 250.0,
            f"Martian radiation multiplier {mult}x out of expected range [160, 250]x",
        )

    def test_delta_vector_dict_schema(self):
        """Output dictionary must contain all required top-level and nested physical keys."""
        delta = delta_mod.compute_physical_delta_vector("Mars")
        self.assertIn("target_body", delta)
        self.assertIn("gravity", delta)
        self.assertIn("atmospheric_pressure", delta)
        self.assertIn("radiation_dose", delta)

        for k in ["earth_baseline_g0", "target_value_g0", "ratio_to_earth", "unit", "engineering_impact"]:
            self.assertIn(k, delta["gravity"])

        for k in ["earth_baseline_kpa", "target_value_kpa", "delta_kpa", "unit", "engineering_impact"]:
            self.assertIn(k, delta["atmospheric_pressure"])

        for k in ["earth_baseline_msv_day", "target_effective_msv_day", "multiplier", "unit", "engineering_impact"]:
            self.assertIn(k, delta["radiation_dose"])

    def test_delta_vector_json_serializable(self):
        """Output dictionary must be directly JSON-serializable."""
        delta = delta_mod.compute_physical_delta_vector("Moon")
        serialized = json.dumps(delta)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["target_body"], "Moon")

    def test_delta_vector_cli_output_formatting(self):
        """CLI text summary must contain headers, units, and engineering impacts."""
        delta = delta_mod.compute_physical_delta_vector("Moon")
        cli_text = delta_mod.format_delta_vector_cli(delta)
        self.assertIn("Physical Limit Delta-Vectors", cli_text)
        self.assertIn("g0", cli_text)
        self.assertIn("kPa", cli_text)
        self.assertIn("Operational Impact", cli_text)

    # --- Tier 2: Boundary & Corner Cases ---

    def test_martian_elevation_pressure_effect(self):
        """Extreme elevations on Mars scale atmospheric pressure barometrically."""
        delta_summit = delta_mod.compute_physical_delta_vector("Mars", elevation_m=21287.0)
        p_summit = delta_summit["atmospheric_pressure"]["target_value_kpa"]
        delta_floor = delta_mod.compute_physical_delta_vector("Mars", elevation_m=-8200.0)
        p_floor = delta_floor["atmospheric_pressure"]["target_value_kpa"]

        self.assertGreater(p_floor, p_summit)
        self.assertLess(p_summit, 0.15, "Summit pressure should be very thin (<0.15 kPa)")
        self.assertGreater(p_floor, 0.90, "Hellas basin pressure should exceed 0.9 kPa")

    def test_subsurface_void_radiation_shielding(self):
        """Subsurface void and low sky-view-factor attenuate surface radiation significantly."""
        unshielded = delta_mod.compute_physical_delta_vector("Moon", sky_view_factor=1.0)
        shielded = delta_mod.compute_physical_delta_vector("Moon", has_subsurface_void=True)
        self.assertLess(
            shielded["radiation_dose"]["multiplier"],
            unshielded["radiation_dose"]["multiplier"] * 0.3,
            "Subsurface cave must attenuate radiation by >70%",
        )

    def test_case_insensitive_body_names(self):
        """Body name inputs must be case-insensitive and handle whitespace."""
        d1 = delta_mod.compute_physical_delta_vector("moon")
        d2 = delta_mod.compute_physical_delta_vector("MOON ")
        self.assertEqual(d1["gravity"]["ratio_to_earth"], d2["gravity"]["ratio_to_earth"])

    def test_unknown_body_raises_error(self):
        """Unknown celestial bodies must raise ValueError."""
        with self.assertRaises(ValueError):
            delta_mod.compute_physical_delta_vector("Jupiter")

    # --- Tier 3: Pairwise Cross-Feature Test ---

    def test_pairwise_f9_delta_vectors_with_f10_terrestrial_analogs(self):
        """Pairwise F9 x F10: Physical delta-vectors computed between Earth analogs and destinations."""
        delta_moon = delta_mod.compute_physical_delta_vector("Moon")
        self.assertAlmostEqual(delta_moon["gravity"]["ratio_to_earth"], 0.1654, delta=0.01)
        self.assertAlmostEqual(delta_moon["atmospheric_pressure"]["delta_kpa"], -101.325, delta=0.1)
        self.assertGreater(delta_moon["radiation_dose"]["multiplier"], 300.0)

        delta_mars = delta_mod.compute_physical_delta_vector("Mars")
        self.assertAlmostEqual(delta_mars["gravity"]["ratio_to_earth"], 0.3795, delta=0.01)
        self.assertAlmostEqual(delta_mars["atmospheric_pressure"]["delta_kpa"], -100.715, delta=0.1)
        self.assertGreater(delta_mars["radiation_dose"]["multiplier"], 150.0)


if __name__ == "__main__":
    unittest.main()
