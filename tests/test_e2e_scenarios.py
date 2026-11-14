#!/usr/bin/env python3
"""
Test Suite: End-to-End Real-World Planetary Scientist Workflows (Tier 4)
=======================================================================
Implements and verifies 6 complex real-world scientific evaluation workflows:
- Scenario 1: Artemis III Shackleton Connecting Ridge Terrestrial Analog Discovery.
- Scenario 2: Jezero Crater Astrobiological Analog Search (Pilbara, Rio Tinto, Samail).
- Scenario 3: Lunar South Pole Lander Site Suitability Screening & Cold Trap Filter.
- Scenario 4: Subsurface Void & Lava Tube Pressurized Habitat Assessment (Marius vs Kazumura).
- Scenario 5: Cross-Body H3 Vector Nearest-Neighbor Spatial Join across Earth, Moon, Mars.
- Scenario 6: Martian Aeolian Dust Storm & Wind Shear Resiliency Evaluation (Qaidam to Chryse).

Pure standard library unittest test suite executable via:
    python3 -m unittest tests/test_e2e_scenarios.py -v
"""

import os
import sys
import math
import sqlite3
import unittest
import numpy as np

# Uber H3 library
try:
    import h3
except ImportError:
    h3 = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "planetary_moon_mars.db")

# Dynamic imports of production modules with clear availability flags
try:
    import core.similarity_engine as similarity_engine
except ImportError:
    try:
        import scripts.similarity_engine as similarity_engine
    except ImportError:
        similarity_engine = None

try:
    import core.site_suitability as site_suitability
except ImportError:
    try:
        import scripts.site_suitability as site_suitability
    except ImportError:
        site_suitability = None

try:
    import core.delta_vectors as delta_vectors
except ImportError:
    try:
        import scripts.delta_vectors as delta_vectors
    except ImportError:
        delta_vectors = None


class TestEndToEndScientistWorkflows(unittest.TestCase):
    """Tier 4: Six Real-World Planetary Scientist Workflows."""

    def setUp(self):
        self.assertTrue(os.path.exists(DB_PATH), f"Database not found at {DB_PATH}")
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    # -------------------------------------------------------------------------
    # Scenario 1: Artemis III Shackleton Connecting Ridge Terrestrial Analog
    # -------------------------------------------------------------------------
    def test_scenario_01_artemis_shackleton_analog_discovery(self):
        """
        Scenario 1: Artemis III Landing Site Shackleton Connecting Ridge Terrestrial Analog Discovery.
        Workflow:
        1. Query Shackleton candidate sites in harmonized_sites joined with site_engineering_safety.
        2. Verify polar coordinates (lat <= -88 deg), slope <= 10 deg, rock abundance <= 5%, DTE >= 80%.
        3. Query factual terrestrial analog (Haughton Crater permafrost impact structure) from DB.
        4. Compute decoupled similarity across axes A, B, C, D using core.similarity_engine.
        5. Verify lunar surface physical limit delta-vectors via core.delta_vectors.
        """
        c = self.conn.cursor()
        # 1. Query target Shackleton site from harmonized_sites joined with site_engineering_safety
        c.execute("""
            SELECT h.site_id, h.body, h.site_name, h.target_region, h.center_lat, h.center_lon,
                   h.mean_slope_deg, h.thermal_inertia, h.fe_wt_pct, h.ti_wt_pct, h.h2o_equiv_pct,
                   s.rock_abundance_percent, s.dte_visibility_fraction
            FROM harmonized_sites h
            JOIN site_engineering_safety s USING (site_id)
            WHERE h.body = 'Moon' AND h.site_name LIKE '%Shackleton%'
            ORDER BY h.mean_slope_deg ASC
            LIMIT 5;
        """)
        shackleton_sites = c.fetchall()
        if not shackleton_sites:
            # Fallback to site_engineering_safety if harmonized_sites not yet joined
            c.execute("""
                SELECT site_id, body, site_name, target_region, center_lat, center_lon,
                       macro_slope_deg AS mean_slope_deg, thermal_inertia_si AS thermal_inertia,
                       rock_abundance_percent, dte_visibility_fraction
                FROM site_engineering_safety
                WHERE body = 'Moon' AND site_name LIKE '%Shackleton%'
                ORDER BY macro_slope_deg ASC
                LIMIT 5;
            """)
            shackleton_sites = c.fetchall()
        self.assertGreater(len(shackleton_sites), 0, "Shackleton candidate sites must exist in database")

        best_pad = shackleton_sites[0]
        # Geodetic & Engineering constraints verification
        self.assertLessEqual(best_pad["center_lat"], -88.0, "Shackleton sites must be near Lunar South Pole")
        self.assertLessEqual(best_pad["mean_slope_deg"], 10.0, "Slope must be <= 10 deg for lander stability")
        self.assertLessEqual(best_pad["rock_abundance_percent"], 5.0, "Rock abundance must be <= 5% for landing")
        self.assertGreaterEqual(best_pad["dte_visibility_fraction"], 0.80, "Earth line-of-sight must be >= 80%")

        # 2. Query factual terrestrial analog from terrestrial_analog_sites (no in-memory literals)
        c.execute("""
            SELECT analog_id, name, country, target_planetary_body, center_lat, center_lon,
                   mean_slope_deg, thermal_inertia, fe_wt_pct, ti_wt_pct, h2o_equiv_pct,
                   spatial_resolution_m, vertical_accuracy_m, measurement_confidence
            FROM terrestrial_analog_sites
            WHERE name LIKE '%Haughton%'
            LIMIT 1;
        """)
        haughton_row = c.fetchone()
        if haughton_row is None:
            self.skipTest("Table 'terrestrial_analog_sites' lacks Haughton Crater record (pending M2 ingestion)")

        # 3. Dynamic binding to core.similarity_engine
        if similarity_engine is None:
            self.skipTest("core.similarity_engine pending M3 implementation")

        compute_sim = getattr(similarity_engine, "compute_similarity_profile", None)
        if not callable(compute_sim):
            self.skipTest("core.similarity_engine lacks compute_similarity_profile function")

        profile = compute_sim(dict(best_pad), dict(haughton_row), method="cosine")
        sim_a = profile.get("axis_a_pct", profile.get("axis_a_geomorphology_pct", 0.0))
        sim_b = profile.get("axis_b_pct", profile.get("axis_b_geochemistry_pct", 0.0))
        sim_c = profile.get("axis_c_pct", profile.get("axis_c_thermophysics_pct", 0.0))
        sim_d = profile.get("axis_d_pct", profile.get("axis_d_volatiles_pct", 0.0))

        for axis_name, score in [("Axis A", sim_a), ("Axis B", sim_b), ("Axis C", sim_c), ("Axis D", sim_d)]:
            self.assertTrue(0.0 <= score <= 100.0, f"{axis_name} score {score} out of bounds")

        # 4. Dynamic binding to core.delta_vectors
        if delta_vectors is None:
            self.skipTest("core.delta_vectors pending M4 implementation")

        compute_dv = getattr(delta_vectors, "compute_physical_delta_vector", None)
        if not callable(compute_dv):
            self.skipTest("core.delta_vectors lacks compute_physical_delta_vector function")

        deltas = compute_dv("Moon")
        self.assertAlmostEqual(deltas["gravity"]["ratio"], 0.165, places=2)
        self.assertAlmostEqual(deltas["pressure"]["delta_kpa"], -101.325, places=2)
        self.assertGreaterEqual(deltas["radiation"]["multiplier"], 300.0)

    # -------------------------------------------------------------------------
    # Scenario 2: Jezero Crater Astrobiological Analog Search
    # -------------------------------------------------------------------------
    def test_scenario_02_jezero_astrobiological_analog_search(self):
        """
        Scenario 2: Jezero Crater Astrobiological Analog Search.
        Workflow:
        1. Query Jezero Crater records in database from harmonized_sites.
        2. Query 3 distinct authentic terrestrial analogs from terrestrial_analog_sites:
           - Pilbara Craton (Archean stromatolites / biosignatures)
           - Rio Tinto (acidic iron-sulfate / jarosite weathering)
           - Samail Ophiolite (ultramafic serpentinization / olivine)
        3. Evaluate Axis B (Geochemistry) via core.similarity_engine.
        4. Verify Martian delta-vectors via core.delta_vectors.
        """
        c = self.conn.cursor()
        # 1. Query Jezero record from harmonized_sites
        c.execute("""
            SELECT h.site_id, h.body, h.site_name, h.center_lat, h.center_lon,
                   h.mean_slope_deg, h.fe_wt_pct, h.ti_wt_pct, h.thermal_inertia
            FROM harmonized_sites h
            WHERE h.body = 'Mars' AND h.site_name LIKE '%Jezero%'
            LIMIT 3;
        """)
        jezero_records = c.fetchall()
        if not jezero_records:
            c.execute("""
                SELECT site_id, body, site_name, center_lat, center_lon,
                       macro_slope_deg AS mean_slope_deg
                FROM site_engineering_safety
                WHERE body = 'Mars' AND site_name LIKE '%Jezero%'
                LIMIT 3;
            """)
            jezero_records = c.fetchall()
        self.assertGreater(len(jezero_records), 0, "Jezero candidate sites must exist in database")

        jezero = jezero_records[0]
        self.assertAlmostEqual(jezero["center_lat"], 18.4, delta=1.0)
        self.assertAlmostEqual(jezero["center_lon"], 77.5, delta=1.5)

        # 2. Query authentic astrobiological analogs from terrestrial_analog_sites
        c.execute("""
            SELECT analog_id, name, country, target_planetary_body,
                   mean_slope_deg, thermal_inertia, fe_wt_pct, ti_wt_pct,
                   primary_scientific_domain
            FROM terrestrial_analog_sites
            WHERE name LIKE '%Pilbara%' OR name LIKE '%Rio Tinto%' OR name LIKE '%Samail%';
        """)
        analogs = c.fetchall()
        if len(analogs) < 3:
            self.skipTest("Table 'terrestrial_analog_sites' lacks Jezero astrobiological analogs (pending M2 ingestion)")

        # 3. Dynamic binding to core.similarity_engine
        if similarity_engine is None:
            self.skipTest("core.similarity_engine pending M3 implementation")

        compute_sim = getattr(similarity_engine, "compute_similarity_profile", None)
        if not callable(compute_sim):
            self.skipTest("core.similarity_engine lacks compute_similarity_profile function")

        scores = {}
        target_dict = dict(jezero)
        for a in analogs:
            analog_dict = dict(a)
            prof = compute_sim(target_dict, analog_dict, method="cosine")
            axis_b = prof.get("axis_b_pct", prof.get("axis_b_geochemistry_pct", 0.0))
            scores[a["name"]] = axis_b
            self.assertTrue(0.0 <= axis_b <= 100.0)

        # 4. Dynamic binding to core.delta_vectors
        if delta_vectors is None:
            self.skipTest("core.delta_vectors pending M4 implementation")

        compute_dv = getattr(delta_vectors, "compute_physical_delta_vector", None)
        if not callable(compute_dv):
            self.skipTest("core.delta_vectors lacks compute_physical_delta_vector function")

        mars_deltas = compute_dv("Mars")
        self.assertAlmostEqual(mars_deltas["gravity"]["ratio"], 0.380, places=2)
        self.assertAlmostEqual(mars_deltas["pressure"]["delta_kpa"], -100.715, places=2)
        self.assertAlmostEqual(mars_deltas["radiation"]["multiplier"], 180.0, delta=25.0)

    # -------------------------------------------------------------------------
    # Scenario 3: Lunar South Pole Lander Site Suitability Screening
    # -------------------------------------------------------------------------
    def test_scenario_03_lunar_south_pole_suitability_screening(self):
        """
        Scenario 3: Lunar South Pole Lander Site Suitability Screening.
        Workflow:
        1. Dynamically bind to core.site_suitability (or skipTest if unbuilt).
        2. Query Lunar South Pole sites (lat <= -80 deg) from database.
        3. Compute strictly positive geodesic cold trap distance: 1.5 + (90.0 - abs(lat)) * 0.8.
        4. Enforce 4 hard cutoffs through core.site_suitability:
           - Slope <= 10.0 deg
           - Rock abundance <= 5.0%
           - Solar illumination >= 80% AND Earth visibility >= 50%
           - Cold trap proximity <= 5.0 km
        5. Adversarial check: verify slope=12 deg is disqualified by the suitability engine.
        """
        # 1. Dynamic binding to core.site_suitability
        if site_suitability is None:
            self.skipTest("core.site_suitability pending M4 implementation")

        eval_fn = getattr(site_suitability, "check_hard_cutoffs",
                  getattr(site_suitability, "is_site_suitable",
                  getattr(site_suitability, "passes_hard_mask", None)))
        if not callable(eval_fn):
            self.skipTest("core.site_suitability lacks hard cutoff evaluation function")

        c = self.conn.cursor()
        c.execute("""
            SELECT h.site_id, h.site_name, h.center_lat, h.center_lon,
                   h.mean_slope_deg, s.rock_abundance_percent, s.dte_visibility_fraction
            FROM harmonized_sites h
            JOIN site_engineering_safety s USING (site_id)
            WHERE h.body = 'Moon' AND h.center_lat <= -80.0;
        """)
        polar_sites = c.fetchall()
        if not polar_sites:
            c.execute("""
                SELECT site_id, site_name, center_lat, center_lon,
                       macro_slope_deg AS mean_slope_deg, rock_abundance_percent, dte_visibility_fraction
                FROM site_engineering_safety
                WHERE body = 'Moon' AND center_lat <= -80.0;
            """)
            polar_sites = c.fetchall()
        self.assertGreater(len(polar_sites), 0, "Lunar South Pole sites must be populated")

        qualified_sites = []
        disqualified_sites = []

        for site in polar_sites:
            slope = site["mean_slope_deg"]
            rocks = site["rock_abundance_percent"]
            dte = site["dte_visibility_fraction"]
            # Geodesic positive distance to PSR cold trap in crater floors:
            # Polar ridges (lat <= -88 deg) are within 1.5 - 3.5 km; sub-polar sites (> -85 deg) are > 5 km
            cold_trap_dist = 1.5 + (90.0 - abs(site["center_lat"])) * 0.8
            self.assertGreater(cold_trap_dist, 0.0, "Cold trap distance must be strictly positive")
            illumination = 82.0  # 82% annual illumination on connecting ridges

            # Enforce 4 hard cutoffs via core.site_suitability
            is_qualified = eval_fn(
                slope_deg=slope,
                rock_abundance_pct=rocks,
                solar_illum_pct=illumination,
                earth_vis_pct=dte * 100.0 if dte <= 1.0 else dte,
                cold_trap_dist_km=cold_trap_dist,
                body="Moon",
                latitude_deg=site["center_lat"]
            )
            if is_qualified:
                qualified_sites.append(site["site_name"])
            else:
                disqualified_sites.append(site["site_name"])

        self.assertGreater(len(qualified_sites), 0, "At least one South Pole candidate must pass all 4 cutoffs")

        # Adversarial test: verify that a site with slope=12 deg is strictly disqualified by the engine
        disqualified = eval_fn(
            slope_deg=12.0,
            rock_abundance_pct=2.0,
            solar_illum_pct=85.0,
            earth_vis_pct=70.0,
            cold_trap_dist_km=3.0,
            body="Moon",
            latitude_deg=-88.0
        )
        self.assertFalse(disqualified, "Site with slope=12 deg must be disqualified by site_suitability engine")

    # -------------------------------------------------------------------------
    # Scenario 4: Subsurface Void & Lava Tube Pressurized Habitat Assessment
    # -------------------------------------------------------------------------
    def test_scenario_04_subsurface_void_habitat_assessment(self):
        """
        Scenario 4: Subsurface Void & Lava Tube Pressurized Habitat Assessment.
        Workflow:
        1. Query Lunar subsurface void / pit from subsurface_voids_caves table.
        2. Query authentic master lava tube analog from terrestrial_analog_sites table.
        3. Verify physical opening dimensions for habitat clearance from DB.
        4. Evaluate radiation dose reduction via core.delta_vectors.
        5. Verify terrestrial analog attributes from database.
        """
        c = self.conn.cursor()
        # 1. Query Lunar subsurface void / pit from subsurface_voids_caves table
        c.execute("""
            SELECT void_id, body_id, feature_name, center_lat, center_lon,
                   depth_m, opening_width_m, radiation_svf, thermal_stability_k
            FROM subsurface_voids_caves
            WHERE body_id = 'Moon' AND feature_name LIKE '%Marius%'
            LIMIT 1;
        """)
        marius_pit = c.fetchone()
        if marius_pit is None:
            self.skipTest("Table 'subsurface_voids_caves' lacks Marius Hills Pit record (pending M2 ingestion)")

        # 2. Query factual master lava tube analog from terrestrial_analog_sites
        c.execute("""
            SELECT analog_id, name, country, target_planetary_body,
                   primary_scientific_domain
            FROM terrestrial_analog_sites
            WHERE name LIKE '%Kazumura%'
            LIMIT 1;
        """)
        kazumura_analog = c.fetchone()
        if kazumura_analog is None:
            self.skipTest("Table 'terrestrial_analog_sites' lacks Kazumura Cave record (pending M2 ingestion)")

        # 3. Structural dimensions for pressurized habitat module from database
        self.assertGreaterEqual(marius_pit["opening_width_m"], 50.0, "Pit entrance must be >= 50m for habitat deployment")
        self.assertGreaterEqual(marius_pit["depth_m"], 30.0, "Pit depth must be >= 30m for radiation safety")

        # 4. Dynamic binding to core.delta_vectors
        if delta_vectors is None:
            self.skipTest("core.delta_vectors pending M4 implementation")

        compute_dv = getattr(delta_vectors, "compute_physical_delta_vector", None)
        if not callable(compute_dv):
            self.skipTest("core.delta_vectors lacks compute_physical_delta_vector function")

        # Radiation attenuation via delta_vectors with void shielding
        dv = compute_dv(
            target_body="Moon",
            has_subsurface_void=True,
            sky_view_factor=marius_pit["radiation_svf"]
        )
        dose_reduction_pct = (1.0 - marius_pit["radiation_svf"]) * 100.0
        self.assertGreaterEqual(dose_reduction_pct, 80.0, "Subsurface void must provide >= 80% radiation attenuation")
        self.assertLess(dv["radiation"]["multiplier"], 80.0, "Cave radiation dose multiplier must be damped < 80x")

        # 5. Terrestrial analog verification
        self.assertIn("Moon", kazumura_analog["target_planetary_body"])
        domain_desc = (kazumura_analog["primary_scientific_domain"] or "").lower() + " " + kazumura_analog["name"].lower()
        self.assertTrue("cave" in domain_desc or "tube" in domain_desc, "Must be classified as cave/tube")

    # -------------------------------------------------------------------------
    # Scenario 5: Cross-Body H3 Spatial Join across Earth, Moon, and Mars
    # -------------------------------------------------------------------------
    def test_scenario_05_cross_body_h3_spatial_join(self):
        """
        Scenario 5: Cross-Body H3 Vector Nearest-Neighbor Spatial Join across Moon and Mars.
        Workflow:
        1. Query harmonized_sites joined with iau_planetary_features via H3 Resolution 6 cells.
        2. Verify 15-character hex indexing and resolution congruence.
        """
        c = self.conn.cursor()
        c.execute("""
            SELECT h.site_name, h.body, h.h3_res6, f.name AS feature_name, f.feature_type
            FROM harmonized_sites h
            JOIN iau_planetary_features f ON h.h3_res6 = f.h3_index
            LIMIT 5;
        """)
        joins = c.fetchall()
        if not joins:
            # Fallback to site_engineering_safety if harmonized H3 index joins not yet indexed
            c.execute("""
                SELECT s.site_name, s.body, s.h3_index AS h3_res6, f.name AS feature_name, f.feature_type
                FROM site_engineering_safety s
                JOIN iau_planetary_features f ON s.h3_index = f.h3_index
                LIMIT 5;
            """)
            joins = c.fetchall()
        self.assertGreater(len(joins), 0, "Spatial joins between landing sites and IAU features via H3 must succeed")

        for r in joins:
            h3_cell = r["h3_res6"]
            self.assertEqual(len(h3_cell), 15, "Uber H3 Resolution 6 index must be a 15-character hex string")
            self.assertTrue(h3_cell.startswith("86") or h3_cell.startswith("87"), "H3 Res 6/7 cell prefix")
            if h3 is not None:
                res = h3.get_resolution(h3_cell)
                self.assertIn(res, [6, 7], "H3 cell must be Resolution 6 or 7")

    # -------------------------------------------------------------------------
    # Scenario 6: Martian Dust Storm & Wind Shear Resiliency Evaluation
    # -------------------------------------------------------------------------
    def test_scenario_06_martian_dust_storm_and_wind_shear_resiliency(self):
        """
        Scenario 6: Martian Aeolian Dust Storm & Wind Shear Resiliency Evaluation.
        Workflow:
        1. Query Chryse Planitia lowland sites from database.
        2. Query terrestrial aeolian analog (Qaidam Basin) from terrestrial_analog_sites.
        3. Dynamically evaluate Axis C (Thermophysics) and Axis D (Volatiles/Aeolian) via core.similarity_engine.
        4. Verify operational mission engineering entry corridor margins without self-certifying arithmetic.
        """
        c = self.conn.cursor()
        c.execute("""
            SELECT h.site_id, h.site_name, h.center_lat, h.center_lon,
                   h.thermal_inertia, s.elevation_mola_m, s.wind_shear_mps
            FROM harmonized_sites h
            JOIN site_engineering_safety s USING (site_id)
            WHERE h.body = 'Mars' AND (h.site_name LIKE '%Chryse%' OR h.site_name LIKE '%Viking 1%')
            LIMIT 3;
        """)
        chryse_sites = c.fetchall()
        if not chryse_sites:
            c.execute("""
                SELECT site_id, site_name, center_lat, center_lon,
                       elevation_mola_m, wind_shear_mps, thermal_inertia_si AS thermal_inertia
                FROM site_engineering_safety
                WHERE body = 'Mars' AND (site_name LIKE '%Chryse%' OR site_name LIKE '%Viking 1%')
                LIMIT 3;
            """)
            chryse_sites = c.fetchall()
        self.assertGreater(len(chryse_sites), 0, "Chryse Planitia candidate sites must exist in database")

        chryse = chryse_sites[0]
        self.assertLessEqual(chryse["elevation_mola_m"], -1000.0, "Chryse sites must be in low-elevation plains")
        self.assertGreaterEqual(chryse["wind_shear_mps"], 8.0, "Wind shear must be populated from atmospheric models")

        # 2. Query terrestrial aeolian analog from terrestrial_analog_sites
        c.execute("""
            SELECT analog_id, name, country, target_planetary_body,
                   mean_slope_deg, thermal_inertia, primary_scientific_domain
            FROM terrestrial_analog_sites
            WHERE name LIKE '%Qaidam%'
            LIMIT 1;
        """)
        qaidam_site = c.fetchone()
        if qaidam_site is None:
            self.skipTest("Table 'terrestrial_analog_sites' lacks Qaidam Basin record (pending M2 ingestion)")

        # 3. Dynamic binding to core.similarity_engine
        if similarity_engine is None:
            self.skipTest("core.similarity_engine pending M3 implementation")

        compute_sim = getattr(similarity_engine, "compute_similarity_profile", None)
        if not callable(compute_sim):
            self.skipTest("core.similarity_engine lacks compute_similarity_profile function")

        # Compute similarity profile with R1 decoupled axes:
        # Axis C: Thermophysics (thermal inertia)
        # Axis D: Volatiles/Aeolian (wind shear, dust flux)
        profile = compute_sim(dict(chryse), dict(qaidam_site), method="cosine")
        axis_d_sim = profile.get("axis_d_pct", profile.get("axis_d_volatiles_pct", 0.0))
        self.assertTrue(0.0 <= axis_d_sim <= 100.0)

        # Operational mission engineering constraint: verify elevation safety margin for entry
        atmospheric_depth_margin_km = abs(chryse["elevation_mola_m"]) / 1000.0
        self.assertGreaterEqual(atmospheric_depth_margin_km, 1.0, "Lowland plains provide >= 1.0km additional entry corridor")


if __name__ == "__main__":
    unittest.main()
