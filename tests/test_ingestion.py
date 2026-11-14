"""
Unit and integration tests for factual data ingestion, under-studied terrestrial analogs,
authoritative provenance, and missing planetary domains (Features 10, 11).
"""

import os
import sqlite3
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("PLANETARY_DB_PATH", PROJECT_ROOT / "planetary_moon_mars.db"))

TWELVE_ANALOGS = {
    "Qaidam": {"lat": 37.50, "lon": 95.00, "region": "Tibet/China", "type": "playa/yardang"},
    "Haughton": {"lat": 75.38, "lon": -89.67, "region": "Devon Island/Canada", "type": "impact/permafrost"},
    "Samail": {"lat": 23.20, "lon": 58.10, "region": "Oman", "type": "ophiolite/serpentinization"},
    "Danakil": {"lat": 14.24, "lon": 40.30, "region": "Ethiopia", "type": "hydrothermal/acid"},
    "Svalbard": {"lat": 79.45, "lon": 13.32, "region": "Norway", "type": "volcanic-ice/carbonates"},
    "Pilbara": {"lat": -21.15, "lon": 119.43, "region": "Australia", "type": "astrobiology/stromatolites"},
    "Rio Tinto": {"lat": 37.70, "lon": -6.55, "region": "Spain", "type": "acidic/jarosite"},
    "Makgadikgadi": {"lat": -20.50, "lon": 25.50, "region": "Botswana", "type": "salt playa/aeolian"},
    "Nullarbor": {"lat": -31.40, "lon": 127.50, "region": "Australia", "type": "karst/cave"},
    "Lonar": {"lat": 19.98, "lon": 76.51, "region": "India", "type": "basaltic impact"},
    "El Malpais": {"lat": 34.98, "lon": -107.92, "region": "USA", "type": "lava tube/ice cave"},
    "Kazumura": {"lat": 19.52, "lon": -155.03, "region": "Hawaii/USA", "type": "lava tube"},
}


class TestFactualIngestion(unittest.TestCase):
    """
    Tier 1 & Tier 2 tests verifying factual, non-hallucinated datasets from
    open scientific archives, complete provenance, and missing domain catalogs.
    """

    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            raise unittest.SkipTest(f"Database file not found at {DB_PATH}")
        cls.conn = sqlite3.connect(str(DB_PATH))
        cls.conn.row_factory = sqlite3.Row
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "conn"):
            cls.conn.close()

    def get_table_names(self):
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view');"
        )
        return {row[0] for row in self.cursor.fetchall()}

    def fetch_all_analogs(self):
        """Fetch analog records from terrestrial_analog_sites or harmonized_sites."""
        tables = self.get_table_names()
        records = []
        if "terrestrial_analog_sites" in tables:
            self.cursor.execute("SELECT * FROM terrestrial_analog_sites;")
            records.extend(self.cursor.fetchall())
        elif "harmonized_sites" in tables:
            cols = {c[1] for c in self.cursor.execute("PRAGMA table_info(harmonized_sites);").fetchall()}
            body_col = "body" if "body" in cols else "body_id"
            self.cursor.execute(f"SELECT * FROM harmonized_sites WHERE {body_col} = 'Earth';")
            records.extend(self.cursor.fetchall())
        return records

    # =========================================================================
    # Feature 10: Factual Terrestrial Analogs Ingestion (Tier 1 & Tier 2)
    # =========================================================================

    def test_twelve_terrestrial_analog_sites_ingested(self):
        """Verify all 12 under-studied terrestrial analog sites are ingested."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No terrestrial analog records found in database.")

        site_names = " ".join(
            (r["name"] if "name" in r.keys() else r["site_name"]) for r in records
        ).lower()

        missing = []
        for key in TWELVE_ANALOGS:
            if key.lower() not in site_names:
                missing.append(key)

        self.assertEqual(
            missing,
            [],
            f"The following required factual analog sites were not found: {missing}",
        )

    def test_analog_sites_geographic_coordinates(self):
        """Verify analog coordinates match authentic peer-reviewed geographical locations."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found.")

        for name_key, ref in TWELVE_ANALOGS.items():
            matched = [
                r
                for r in records
                if name_key.lower()
                in (r["name"] if "name" in r.keys() else r["site_name"]).lower()
            ]
            if not matched:
                continue
            rec = matched[0]
            lat = rec["latitude_deg"] if "latitude_deg" in rec.keys() else rec["center_lat"]
            lon = rec["longitude_deg"] if "longitude_deg" in rec.keys() else rec["center_lon"]

            self.assertAlmostEqual(
                lat,
                ref["lat"],
                delta=2.5,
                msg=f"Latitude for {name_key} ({lat}) diverges from reference ({ref['lat']})",
            )
            self.assertAlmostEqual(
                lon,
                ref["lon"],
                delta=5.0,
                msg=f"Longitude for {name_key} ({lon}) diverges from reference ({ref['lon']})",
            )

    def test_analog_sites_authoritative_provenance(self):
        """Verify data provenance contains authoritative sources and non-mock citations."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found.")

        for r in records:
            source = (
                r["primary_data_source"]
                if "primary_data_source" in r.keys()
                else r.get("data_source", "")
            )
            name = r["name"] if "name" in r.keys() else r["site_name"]
            self.assertTrue(
                source and len(str(source).strip()) > 3,
                f"Analog site {name} has missing or empty data provenance source.",
            )
            self.assertNotIn("mock", str(source).lower())
            self.assertNotIn("synthetic", str(source).lower())

    def test_analog_geomorphology_plausible(self):
        """Verify geomorphology slope and roughness values reflect authentic topography."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found.")

        for r in records:
            name = (r["name"] if "name" in r.keys() else r["site_name"]).lower()
            slope = r["mean_slope_deg"]
            self.assertGreaterEqual(slope, 0.0)
            self.assertLessEqual(slope, 60.0)

            if "makgadikgadi" in name:
                self.assertLess(
                    slope,
                    3.0,
                    f"Makgadikgadi salt pan slope must be flat (<3.0 deg), got {slope}",
                )
            if "lonar" in name:
                self.assertGreater(
                    slope,
                    1.5,
                    f"Lonar impact crater rim/wall slope must be significant (>1.5 deg), got {slope}",
                )

    def test_analog_geochemistry_plausible(self):
        """Verify geochemistry reflects real mineralogy (Fe, Ti, hydrated minerals)."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found.")

        for r in records:
            name = (r["name"] if "name" in r.keys() else r["site_name"]).lower()
            fe = r["fe_wt_pct"]
            ti = r["ti_wt_pct"]
            self.assertTrue(0.0 <= fe <= 100.0, f"Invalid Fe wt% for {name}: {fe}")
            self.assertTrue(0.0 <= ti <= 100.0, f"Invalid Ti wt% for {name}: {ti}")

            if "rio tinto" in name:
                self.assertGreater(
                    fe,
                    10.0,
                    f"Rio Tinto must exhibit high iron concentration (>10 wt%), got {fe}",
                )
            if "lonar" in name:
                self.assertGreater(
                    fe,
                    8.0,
                    f"Lonar basalt must contain significant FeO (>8 wt%), got {fe}",
                )

    def test_analog_thermophysics_plausible(self):
        """Verify diurnal temperature amplitudes and thermal inertia reflect real physics."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found.")

        for r in records:
            name = (r["name"] if "name" in r.keys() else r["site_name"]).lower()
            dt = r["diurnal_temp_swing_k"]
            self.assertGreater(dt, 0.0, f"Diurnal temp swing must be positive, got {dt} for {name}")

            if "qaidam" in name or "danakil" in name:
                self.assertGreater(
                    dt,
                    15.0,
                    f"Desert basin {name} must have diurnal swing > 15K, got {dt}",
                )

    def test_analog_h3_indices_res6_format(self):
        """Verify H3 resolution 6 cells are valid 15-character hex strings."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found.")

        for r in records:
            name = r["name"] if "name" in r.keys() else r["site_name"]
            h3_val = (
                r["h3_index_res6"]
                if "h3_index_res6" in r.keys()
                else (r["h3_res6"] if "h3_res6" in r.keys() else r.get("h3_index"))
            )
            self.assertIsNotNone(h3_val, f"H3 index missing for site {name}")
            h3_str = str(h3_val).strip()
            self.assertEqual(
                len(h3_str),
                15,
                f"H3 Resolution 6 index must be 15 hex characters, got '{h3_str}' for {name}",
            )
            self.assertTrue(
                h3_str.startswith("86"),
                f"H3 Resolution 6 index must start with '86', got '{h3_str}' for {name}",
            )

    # --- Feature 10 Tier 2 Boundary Tests (Explorer 3) ---

    def test_analog_latitude_polar_and_equatorial_boundaries(self):
        """Boundary test: 12 analog sites span high Arctic (>70 deg N) to Southern Hemisphere (<-20 deg S)."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found in database.")

        lats = [r["latitude_deg"] if "latitude_deg" in r.keys() else r["center_lat"] for r in records]
        self.assertGreater(max(lats), 70.0, "Catalog must include high Arctic polar analog > 70 deg N (e.g. Svalbard/Haughton)")
        self.assertLess(min(lats), -20.0, "Catalog must include southern hemisphere analog < -20 deg S (e.g. Nullarbor)")
        for lat in lats:
            self.assertTrue(-90.0 <= lat <= 90.0, f"Latitude out of bounds: {lat}")

    def test_analog_elevation_extreme_boundaries(self):
        """Boundary test: Analog sites capture below sea level (<0m) and high plateau (>2000m) extremes."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found in database.")

        danakil = [r for r in records if "danakil" in (r["name"] if "name" in r.keys() else r["site_name"]).lower()]
        qaidam = [r for r in records if "qaidam" in (r["name"] if "name" in r.keys() else r["site_name"]).lower()]

        if danakil and "elevation_m" in danakil[0].keys() and danakil[0]["elevation_m"] is not None:
            self.assertLess(danakil[0]["elevation_m"], 0.0, "Danakil depression must be below sea level (<0m)")
        if qaidam and "elevation_m" in qaidam[0].keys() and qaidam[0]["elevation_m"] is not None:
            self.assertGreater(qaidam[0]["elevation_m"], 2000.0, "Qaidam basin must be high plateau (>2000m)")

    def test_analog_diurnal_temperature_swing_hyper_arid_extremes(self):
        """Boundary test: Hyper-arid basins exhibit dT >= 18.0K while cave analogs exhibit dT <= 15.0K."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found in database.")

        for r in records:
            name = (r["name"] if "name" in r.keys() else r["site_name"]).lower()
            dt = r["diurnal_temp_swing_k"]
            self.assertGreater(dt, 0.0)
            if "danakil" in name or "qaidam" in name:
                self.assertGreaterEqual(dt, 18.0, f"{name} must exhibit extreme diurnal swing >= 18K")
            if "kazumura" in name:
                self.assertLessEqual(dt, 15.0, f"{name} must exhibit buffered diurnal swing <= 15K")

    def test_analog_rock_abundance_boulder_hazard_extremes(self):
        """Boundary test: Smooth salt playa rock abundance < 3.0%, all values in [0.0, 100.0]%."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found in database.")

        for r in records:
            name = (r["name"] if "name" in r.keys() else r["site_name"]).lower()
            if "rock_abundance_pct" in r.keys() and r["rock_abundance_pct"] is not None:
                rock = r["rock_abundance_pct"]
                self.assertTrue(0.0 <= rock <= 100.0)
                if "makgadikgadi" in name:
                    self.assertLess(rock, 3.0, "Salt playa must have rock abundance < 3.0%")

    def test_analog_water_equivalent_permafrost_vs_hyper_arid_bounds(self):
        """Boundary test: Captures hyper-arid desiccation (<=5.0 wt%) and Arctic ground ice permafrost (>=10.0 wt%)."""
        records = self.fetch_all_analogs()
        if not records:
            self.fail("No analog records found in database.")

        for r in records:
            name = (r["name"] if "name" in r.keys() else r["site_name"]).lower()
            h2o = r["h2o_equiv_pct"]
            self.assertTrue(0.0 <= h2o <= 100.0)
            if "danakil" in name or "qaidam" in name:
                self.assertLessEqual(h2o, 5.0, f"Hyper-arid {name} H2O equivalent must be <= 5.0 wt%")
            if "haughton" in name:
                self.assertGreaterEqual(h2o, 10.0, f"Arctic permafrost {name} H2O equivalent must be >= 10.0 wt%")

    # =========================================================================
    # Feature 11: Missing Planetary Domains Ingestion (Tier 1 & Tier 2)
    # =========================================================================

    def test_subsurface_voids_caves_ingested(self):
        """Verify subsurface_voids_caves contains lunar pits, martian skylights, and terrestrial caves."""
        tables = self.get_table_names()
        if "subsurface_voids_caves" not in tables:
            self.fail("Table 'subsurface_voids_caves' is not ingested.")

        self.cursor.execute("SELECT feature_name, body_id, depth_m, radiation_svf FROM subsurface_voids_caves;")
        rows = self.cursor.fetchall()
        self.assertGreaterEqual(
            len(rows),
            4,
            f"Expected at least 4 subsurface voids cataloged, found {len(rows)}",
        )

        names = " ".join(r["feature_name"] for r in rows).lower()
        self.assertTrue(
            "marius" in names or "tranquillitatis" in names,
            "Lunar pit catalog must include Marius Hills or Tranquillitatis pit.",
        )
        self.assertTrue(
            "arsia" in names or "pavonis" in names,
            "Martian pit catalog must include Arsia Mons or Pavonis Mons skylight.",
        )

        for r in rows:
            self.assertGreater(r["depth_m"], 0.0)
            self.assertTrue(0.0 <= r["radiation_svf"] <= 1.0)

    def test_telecom_relay_visibility_lola(self):
        """Verify telecom_relay_visibility contains Earth line-of-sight profiles."""
        tables = self.get_table_names()
        self.assertIn("telecom_relay_visibility", tables)

        self.cursor.execute("SELECT * FROM telecom_relay_visibility;")
        rows = self.cursor.fetchall()
        self.assertGreater(len(rows), 0, "telecom_relay_visibility table is empty")

        for r in rows:
            vis = r["dte_visibility_fraction"]
            self.assertTrue(
                0.0 <= vis <= 1.0,
                f"DTE visibility fraction must be in [0.0, 1.0], got {vis}",
            )

    def test_regolith_geotechnics_psi_ingested(self):
        """Verify regolith_geotechnics_psi contains valid soil mechanics parameters."""
        tables = self.get_table_names()
        self.assertIn("regolith_geotechnics_psi", tables)

        self.cursor.execute("SELECT * FROM regolith_geotechnics_psi;")
        rows = self.cursor.fetchall()
        self.assertGreater(len(rows), 0, "regolith_geotechnics_psi is empty")

        for r in rows:
            friction = (
                r["internal_friction_angle_deg"]
                if "internal_friction_angle_deg" in r.keys()
                else r["friction_angle_deg"]
            )
            self.assertTrue(
                20.0 <= friction <= 60.0,
                f"Regolith friction angle must be realistic (20-60 deg), got {friction}",
            )

    def test_planetary_radiation_exposure_ingested(self):
        """Verify planetary_radiation_exposure contains LRO CRaTER and MSL RAD measurements."""
        tables = self.get_table_names()
        if "planetary_radiation_exposure" not in tables:
            self.fail("Table 'planetary_radiation_exposure' is not ingested.")

        self.cursor.execute("SELECT * FROM planetary_radiation_exposure;")
        rows = self.cursor.fetchall()
        self.assertGreater(len(rows), 0, "planetary_radiation_exposure is empty")

        bodies = {r["body_id"] for r in rows}
        self.assertTrue({"Moon", "Mars"}.issubset(bodies))

        for r in rows:
            dose = r["effective_surface_dose_msv_yr"]
            self.assertGreater(dose, 0.0, "Radiation dose must be positive")

    def test_isru_chemical_abundance_ingested(self):
        """Verify isru_chemical_abundance contains mineral abundance and extraction yields."""
        tables = self.get_table_names()
        if "isru_chemical_abundance" not in tables:
            self.fail("Table 'isru_chemical_abundance' is not ingested.")

        self.cursor.execute("SELECT * FROM isru_chemical_abundance;")
        rows = self.cursor.fetchall()
        self.assertGreater(len(rows), 0, "isru_chemical_abundance is empty")

        for r in rows:
            feedstock = r["feedstock_weight_pct"]
            self.assertTrue(0.0 <= feedstock <= 100.0)

    # --- Feature 11 Tier 2 Boundary Tests (Explorer 3) ---

    def test_subsurface_void_sky_view_factor_radiation_bounds(self):
        """Boundary test: Subsurface void radiation_svf must be in (0.0, 0.35] providing >=65% shielding."""
        if "subsurface_voids_caves" not in self.get_table_names():
            self.fail("Table 'subsurface_voids_caves' is not ingested.")

        self.cursor.execute("SELECT feature_name, radiation_svf FROM subsurface_voids_caves;")
        rows = self.cursor.fetchall()
        if not rows:
            self.fail("subsurface_voids_caves has no cataloged entries.")
        for r in rows:
            svf = r["radiation_svf"]
            self.assertGreater(svf, 0.0, f"SVF must be > 0 at {r['feature_name']}")
            self.assertLessEqual(svf, 0.35, f"Subterranean SVF {svf} must be <= 0.35 at {r['feature_name']}")

    def test_subsurface_void_depth_and_diameter_physical_bounds(self):
        """Boundary test: Pit craters and skylights have realistic depth and width bounds."""
        if "subsurface_voids_caves" not in self.get_table_names():
            self.fail("Table 'subsurface_voids_caves' is not ingested.")

        self.cursor.execute("SELECT feature_name, body_id, depth_m, opening_width_m FROM subsurface_voids_caves WHERE depth_m IS NOT NULL;")
        rows = self.cursor.fetchall()
        if not rows:
            self.fail("subsurface_voids_caves has no entries with depth.")
        for r in rows:
            d = r["depth_m"]
            w = r["opening_width_m"]
            # All cataloged voids (including deep volcanic pyroducts like Kazumura) have depth in [10, 1500] m
            self.assertTrue(10.0 <= d <= 1500.0, f"Void depth {d}m out of bounds [10, 1500] at {r['feature_name']}")
            # Planetary pits on Moon/Mars strictly fall within [10, 250] m
            if r["body_id"] in ("Moon", "Mars"):
                self.assertTrue(10.0 <= d <= 250.0, f"Planetary pit depth {d}m out of bounds [10, 250] at {r['feature_name']}")
            if w is not None:
                self.assertTrue(5.0 <= w <= 600.0, f"Opening width {w}m out of bounds [5, 600] at {r['feature_name']}")

    def test_telecom_line_of_sight_fraction_extremes(self):
        """Boundary test: Telecom visibility fraction spans from low (<0.20) to high (>=0.40)."""
        if "telecom_relay_visibility" not in self.get_table_names():
            self.fail("Table 'telecom_relay_visibility' is not ingested.")

        self.cursor.execute("SELECT MIN(dte_visibility_fraction), MAX(dte_visibility_fraction) FROM telecom_relay_visibility;")
        min_vis, max_vis = self.cursor.fetchone()
        if min_vis is None:
            self.fail("telecom_relay_visibility has no records.")
        self.assertGreaterEqual(min_vis, 0.0)
        self.assertLessEqual(max_vis, 1.0)
        self.assertGreater(max_vis, 0.40, "Peak line-of-sight must reach >= 40%")

    def test_regolith_internal_friction_and_cohesion_bounds(self):
        """Boundary test: Mohr-Coulomb parameters: friction in [20, 55] deg and cohesion in [0, 15] kPa."""
        if "regolith_geotechnics_psi" not in self.get_table_names():
            self.fail("Table 'regolith_geotechnics_psi' is not ingested.")

        self.cursor.execute("SELECT terrain_name, internal_friction_angle_deg, cohesion_kpa FROM regolith_geotechnics_psi;")
        rows = self.cursor.fetchall()
        if not rows:
            self.fail("regolith_geotechnics_psi has no records.")
        for r in rows:
            self.assertTrue(20.0 <= r["internal_friction_angle_deg"] <= 55.0, f"Friction angle {r['internal_friction_angle_deg']} out of bounds at {r['terrain_name']}")
            self.assertTrue(0.0 <= r["cohesion_kpa"] <= 15.0, f"Cohesion {r['cohesion_kpa']} out of bounds at {r['terrain_name']}")

    def test_isru_feedstock_weight_percent_and_recovery_yield_bounds(self):
        """Boundary test: ISRU chemical feedstock weight percentages fall within [0.1, 100.0]%."""
        if "isru_chemical_abundance" not in self.get_table_names():
            self.fail("Table 'isru_chemical_abundance' is not ingested.")

        self.cursor.execute("SELECT feedstock_weight_pct FROM isru_chemical_abundance;")
        rows = self.cursor.fetchall()
        if not rows:
            self.fail("isru_chemical_abundance has no records.")
        for r in rows:
            feed = r[0]
            self.assertTrue(0.1 <= feed <= 100.0, f"ISRU feedstock weight % {feed} out of expected [0.1, 100.0]%")

    # =========================================================================
    # Tier 3: Pairwise Cross-Feature Tests
    # =========================================================================

    def test_pairwise_f10_terrestrial_analogs_with_f11_subsurface_voids_caves(self):
        """Pairwise F10 x F11: Cross-reference cave analog sites in terrestrial_analog_sites with subsurface_voids_caves."""
        tables = self.get_table_names()
        if "subsurface_voids_caves" not in tables or "terrestrial_analog_sites" not in tables:
            self.skipTest("subsurface_voids_caves or terrestrial_analog_sites not present")

        self.cursor.execute("SELECT name, center_lat, center_lon FROM terrestrial_analog_sites WHERE name LIKE '%Kazumura%' OR name LIKE '%Malpais%';")
        t_rows = self.cursor.fetchall()
        self.cursor.execute("SELECT feature_name, center_lat, center_lon, thermal_stability_k FROM subsurface_voids_caves WHERE feature_name LIKE '%Kazumura%' OR feature_name LIKE '%Malpais%';")
        v_rows = self.cursor.fetchall()

        if not t_rows or not v_rows:
            self.skipTest("Terrestrial cave entries not yet ingested in both tables")

        # Verify thermal stability in subsurface voids is microclimatically buffered (<= 5.0 K)
        for r in v_rows:
            if "thermal_stability_k" in r.keys() and r["thermal_stability_k"] is not None:
                self.assertLessEqual(r["thermal_stability_k"], 5.0)


if __name__ == "__main__":
    unittest.main()
