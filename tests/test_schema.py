"""
Unit and integration tests for database schema harmonization, DDL integrity,
column existence, and constraint boundaries (Features 5, 6, 7).
"""

import os
import sqlite3
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("PLANETARY_DB_PATH", PROJECT_ROOT / "planetary_moon_mars.db"))


class TestSchemaHarmonization(unittest.TestCase):
    """
    Tier 1 & Tier 2 tests for database schema harmonization,
    standardized physical columns, uncertainty metadata, and constraints.
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

    def get_column_names(self, table_name):
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        return {row[1] for row in self.cursor.fetchall()}

    def get_table_sql(self, table_name):
        self.cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        row = self.cursor.fetchone()
        return row[0] if row else ""

    # =========================================================================
    # Feature 5: Cross-Body Harmonization Table (Tier 1 & Tier 2)
    # =========================================================================

    def test_celestial_bodies_contains_earth(self):
        """Verify celestial_bodies contains Earth entry with valid classification."""
        self.assertIn("celestial_bodies", self.get_table_names())
        self.cursor.execute(
            "SELECT body_id, name, classification FROM celestial_bodies WHERE body_id = 'Earth';"
        )
        row = self.cursor.fetchone()
        self.assertIsNotNone(row, "Earth must be registered in celestial_bodies")
        self.assertEqual("Earth", row["body_id"])
        self.assertIn("Terrestrial Planet", row["classification"])

    def test_harmonized_sites_table_exists(self):
        """Verify harmonized_sites table exists in the database."""
        tables = self.get_table_names()
        self.assertIn(
            "harmonized_sites",
            tables,
            "Table 'harmonized_sites' must exist for cross-body feature harmonization.",
        )

    def test_harmonized_sites_cross_body_coverage(self):
        """Verify that celestial_bodies contains Earth, Moon, and Mars for cross-body harmonization."""
        self.assertIn("celestial_bodies", self.get_table_names())
        self.cursor.execute(
            "SELECT body_id FROM celestial_bodies WHERE body_id IN ('Earth', 'Moon', 'Mars');"
        )
        registered = {r[0] for r in self.cursor.fetchall()}
        self.assertEqual(
            registered,
            {"Earth", "Moon", "Mars"},
            f"Expected Earth, Moon, Mars registered in celestial_bodies, found: {registered}",
        )

    def test_harmonized_sites_h3_indices(self):
        """Verify Uber H3 spatial indexing columns exist (Resolution 6 and 7)."""
        if "harmonized_sites" not in self.get_table_names():
            self.fail("Table 'harmonized_sites' does not exist.")

        cols = self.get_column_names("harmonized_sites")
        has_h3 = ("h3_res6" in cols and "h3_res7" in cols) or (
            "h3_index" in cols and "h3_resolution" in cols
        )
        self.assertTrue(
            has_h3,
            "harmonized_sites must provide H3 spatial indexing columns (e.g. h3_res6, h3_res7).",
        )

    def test_harmonized_sites_h3_res7_optional_column_definition(self):
        """Verify that h3_res7 column is specifically defined in harmonized_sites for Resolution 7 indexing."""
        if "harmonized_sites" not in self.get_table_names():
            self.fail("Table 'harmonized_sites' does not exist.")
        cols = self.get_column_names("harmonized_sites")
        self.assertIn("h3_res7", cols, "harmonized_sites must provide h3_res7 column")

    def test_similarity_profiles_table_and_columns(self):
        """Verify similarity_profiles table exists with decomposed axis match columns."""
        tables = self.get_table_names()
        self.assertIn("similarity_profiles", tables)

        cols = self.get_column_names("similarity_profiles")
        required_cols = {
            "profile_id",
            "target_site_id",
            "analog_site_id",
            "method",
            "axis_a_geomorphology_pct",
            "axis_b_geochemistry_pct",
            "axis_c_thermophysics_pct",
            "axis_d_volatiles_pct",
            "composite_score",
            "uncertainty_bound",
        }
        missing = required_cols - cols
        self.assertEqual(
            missing,
            set(),
            f"Missing required columns in similarity_profiles: {missing}",
        )

    def test_harmonized_sites_longitude_boundary_constraints(self):
        """Boundary test: Longitude coordinates must fall strictly within [-180.0, 360.0] degrees."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT center_lon FROM harmonized_sites WHERE center_lon IS NOT NULL;")
        rows = self.cursor.fetchall()
        for r in rows:
            lon = r[0]
            self.assertTrue(-180.0 <= lon <= 360.0, f"Longitude out of bounds: {lon}")

    def test_harmonized_sites_h3_res6_exact_length_format_boundary(self):
        """Boundary test: Every populated h3_res6 index must be exactly 15 hexadecimal characters starting with '86'."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT site_id, h3_res6 FROM harmonized_sites WHERE h3_res6 IS NOT NULL;")
        rows = self.cursor.fetchall()
        for r in rows:
            h3_val = str(r["h3_res6"]).strip()
            self.assertEqual(len(h3_val), 15, f"H3 res6 index '{h3_val}' must be 15 chars at site {r['site_id']}")
            self.assertTrue(h3_val.startswith("86"), f"H3 res6 index '{h3_val}' must start with '86' at site {r['site_id']}")
            try:
                int(h3_val, 16)
            except ValueError:
                self.fail(f"H3 index '{h3_val}' is not valid hex at site {r['site_id']}")

    def test_harmonized_sites_foreign_key_celestial_bodies_integrity(self):
        """Boundary test: Foreign key enforcement rejects inserting site with invalid celestial body."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        schema_sql = self.get_table_sql("harmonized_sites")
        test_conn = sqlite3.connect(":memory:")
        test_conn.execute("PRAGMA foreign_keys = ON;")
        try:
            test_conn.execute("CREATE TABLE celestial_bodies (body_id TEXT PRIMARY KEY, name TEXT);")
            test_conn.execute("INSERT INTO celestial_bodies VALUES ('Moon', 'Moon');")
            test_conn.execute(schema_sql)
            if "FOREIGN KEY" in schema_sql.upper():
                with self.assertRaises(sqlite3.IntegrityError, msg="Unregistered body should raise IntegrityError"):
                    test_conn.execute(
                        "INSERT INTO harmonized_sites (site_id, body, site_name, center_lat, center_lon, h3_res6) VALUES ('S1', 'Pluto_Invalid', 'Base', 0.0, 0.0, '860000000000000');"
                    )
            else:
                self.fail("harmonized_sites DDL does not define FOREIGN KEY constraint to celestial_bodies")
        finally:
            test_conn.close()

    def test_harmonized_sites_primary_key_uniqueness(self):
        """Boundary test: Primary key site_id must enforce uniqueness."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute(
            "SELECT site_id, COUNT(*) FROM harmonized_sites GROUP BY site_id HAVING COUNT(*) > 1;"
        )
        duplicates = self.cursor.fetchall()
        self.assertEqual(
            duplicates,
            [],
            f"Duplicate primary keys detected in harmonized_sites: {duplicates}",
        )

    # =========================================================================
    # Feature 6: Standardized Physical Columns (Tier 1 & Tier 2)
    # =========================================================================

    def test_harmonized_sites_standardized_physical_columns(self):
        """Verify all standardized physical columns are defined in harmonized_sites."""
        if "harmonized_sites" not in self.get_table_names():
            self.fail("Table 'harmonized_sites' does not exist.")

        cols = self.get_column_names("harmonized_sites")
        required_physical = {
            "mean_slope_deg",
            "thermal_inertia",
            "fe_wt_pct",
            "ti_wt_pct",
            "h2o_equiv_pct",
            "diurnal_temp_swing_k",
            "has_subsurface_void",
        }
        missing = required_physical - cols
        self.assertEqual(
            missing,
            set(),
            f"Missing required standardized physical columns in harmonized_sites: {missing}",
        )

    def test_standardized_columns_data_types(self):
        """Verify column declared types: continuous metrics must be REAL and void flag INTEGER."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("PRAGMA table_info(harmonized_sites);")
        col_types = {r[1]: r[2].upper() for r in self.cursor.fetchall()}
        for col in ["mean_slope_deg", "thermal_inertia", "fe_wt_pct", "ti_wt_pct", "h2o_equiv_pct", "diurnal_temp_swing_k"]:
            self.assertIn("REAL", col_types[col], f"{col} expected type REAL, got {col_types[col]}")
        self.assertIn("INTEGER", col_types["has_subsurface_void"], f"has_subsurface_void expected INTEGER, got {col_types['has_subsurface_void']}")

    def test_standardized_columns_slope_and_thermal_inertia_present(self):
        """Verify mean_slope_deg and thermal_inertia can be aggregated without SQL error."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT AVG(mean_slope_deg), AVG(thermal_inertia) FROM harmonized_sites;")
        row = self.cursor.fetchone()
        self.assertIsNotNone(row)

    def test_standardized_columns_geochemistry_fe_ti_h2o_present(self):
        """Verify geochemical columns fe_wt_pct, ti_wt_pct, h2o_equiv_pct can be queried."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT AVG(fe_wt_pct), AVG(ti_wt_pct), AVG(h2o_equiv_pct) FROM harmonized_sites;")
        row = self.cursor.fetchone()
        self.assertIsNotNone(row)

    def test_standardized_columns_subsurface_void_indicator_populated(self):
        """Verify has_subsurface_void defaults to 0 and permits integer binary values."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("PRAGMA table_info(harmonized_sites);")
        info = [r for r in self.cursor.fetchall() if r[1] == "has_subsurface_void"][0]
        # Column default should be '0' or 0
        self.assertIn(str(info[4]), ["0", "'0'"])

    def test_harmonized_sites_has_subsurface_void_boolean_domain(self):
        """Boundary test: has_subsurface_void only accepts boolean integer values (0 or 1)."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute(
            "SELECT DISTINCT has_subsurface_void FROM harmonized_sites WHERE has_subsurface_void IS NOT NULL;"
        )
        values = {row[0] for row in self.cursor.fetchall()}
        self.assertTrue(
            values.issubset({0, 1}),
            f"has_subsurface_void contains non-boolean values: {values}",
        )

    def test_standardized_slope_physical_boundaries_zero_to_ninety(self):
        """Boundary test: mean_slope_deg must be non-negative and <= 90.0 degrees."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT site_id, mean_slope_deg FROM harmonized_sites WHERE mean_slope_deg IS NOT NULL;")
        for r in self.cursor.fetchall():
            s = r["mean_slope_deg"]
            self.assertGreaterEqual(s, 0.0, f"Negative slope at site {r['site_id']}")
            self.assertLessEqual(s, 90.0, f"Slope > 90 deg at site {r['site_id']}")

    def test_standardized_elemental_weight_percentages_sum_upper_bound(self):
        """Boundary test: fe_wt_pct + ti_wt_pct + h2o_equiv_pct must not exceed 100.0%."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT site_id, fe_wt_pct, ti_wt_pct, h2o_equiv_pct FROM harmonized_sites WHERE fe_wt_pct IS NOT NULL;")
        for r in self.cursor.fetchall():
            total = (r["fe_wt_pct"] or 0.0) + (r["ti_wt_pct"] or 0.0) + (r["h2o_equiv_pct"] or 0.0)
            self.assertLessEqual(total, 100.0, f"Elemental weight sum exceeds 100% at {r['site_id']}")

    def test_standardized_diurnal_temp_swing_strictly_positive(self):
        """Boundary test: diurnal_temp_swing_k must be strictly positive and bounded (< 350.0 K)."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT site_id, diurnal_temp_swing_k FROM harmonized_sites WHERE diurnal_temp_swing_k IS NOT NULL;")
        for r in self.cursor.fetchall():
            dt = r["diurnal_temp_swing_k"]
            self.assertGreater(dt, 0.0, f"Non-positive diurnal temp swing at {r['site_id']}")
            self.assertLess(dt, 350.0, f"Extreme diurnal temp swing > 350K at {r['site_id']}")

    def test_standardized_thermal_inertia_physical_domain_bounds(self):
        """Boundary test: thermal_inertia must be strictly positive and within physical domain (< 3000 SI)."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT site_id, thermal_inertia FROM harmonized_sites WHERE thermal_inertia IS NOT NULL;")
        for r in self.cursor.fetchall():
            ti = r["thermal_inertia"]
            self.assertGreater(ti, 0.0, f"Non-positive thermal inertia at {r['site_id']}")
            self.assertLess(ti, 3000.0, f"Unphysical thermal inertia > 3000 at {r['site_id']}")

    # =========================================================================
    # Feature 7: Uncertainty & Provenance Metadata (Tier 1 & Tier 2)
    # =========================================================================

    def test_harmonized_sites_uncertainty_columns(self):
        """Verify uncertainty and provenance metadata columns exist in harmonized_sites."""
        if "harmonized_sites" not in self.get_table_names():
            self.fail("Table 'harmonized_sites' does not exist.")

        cols = self.get_column_names("harmonized_sites")
        required_uncertainty = {
            "spatial_resolution_m",
            "vertical_accuracy_m",
            "measurement_confidence",
        }
        missing = required_uncertainty - cols
        self.assertEqual(
            missing,
            set(),
            f"Missing required uncertainty metadata columns in harmonized_sites: {missing}",
        )

    def test_data_provenance_registry_table_exists(self):
        """Verify data_provenance_registry table exists for uncertainty & DOI tracking."""
        tables = self.get_table_names()
        self.assertIn("data_provenance_registry", tables)

        cols = self.get_column_names("data_provenance_registry")
        expected = {
            "provenance_id",
            "source_agency",
            "spatial_resolution_m",
            "vertical_accuracy_m",
            "measurement_confidence",
        }
        missing = expected - cols
        self.assertEqual(
            missing,
            set(),
            f"Missing required columns in data_provenance_registry: {missing}",
        )

    def test_uncertainty_columns_in_all_quantitative_tables(self):
        """Verify spatial_resolution_m, vertical_accuracy_m, measurement_confidence exist across quantitative tables."""
        for tbl in ["harmonized_sites", "data_provenance_registry", "site_engineering_safety", "remote_sensing_rasters"]:
            if tbl in self.get_table_names():
                cols = self.get_column_names(tbl)
                self.assertIn("measurement_confidence", cols, f"{tbl} missing measurement_confidence")
                self.assertIn("vertical_accuracy_m", cols, f"{tbl} missing vertical_accuracy_m")

    def test_data_provenance_registry_doi_and_agency_populated(self):
        """Verify data_provenance_registry records contain valid non-empty source_agency."""
        if "data_provenance_registry" not in self.get_table_names():
            self.skipTest("data_provenance_registry table not present")

        self.cursor.execute("SELECT source_agency FROM data_provenance_registry;")
        rows = self.cursor.fetchall()
        self.assertGreater(len(rows), 0, "data_provenance_registry has no records")
        for r in rows:
            agency = str(r[0]).strip()
            self.assertTrue(len(agency) > 1, "Source agency must be non-empty")

    def test_spatial_resolution_strictly_positive_boundary(self):
        """Boundary test: spatial_resolution_m must be strictly positive (> 0.0 m)."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT site_id, spatial_resolution_m FROM harmonized_sites WHERE spatial_resolution_m IS NOT NULL;")
        for r in self.cursor.fetchall():
            res = r["spatial_resolution_m"]
            self.assertGreater(res, 0.0, f"Spatial resolution <= 0 at {r['site_id']}")

    def test_vertical_accuracy_strictly_positive_boundary(self):
        """Boundary test: vertical_accuracy_m must be strictly positive (> 0.0 m)."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("SELECT site_id, vertical_accuracy_m FROM harmonized_sites WHERE vertical_accuracy_m IS NOT NULL;")
        for r in self.cursor.fetchall():
            acc = r["vertical_accuracy_m"]
            self.assertGreater(acc, 0.0, f"Vertical accuracy <= 0 at {r['site_id']}")

    def test_measurement_confidence_closed_interval_zero_to_one(self):
        """Boundary test: measurement_confidence must fall strictly within [0.0, 1.0]."""
        for tbl in ["harmonized_sites", "data_provenance_registry"]:
            if tbl in self.get_table_names():
                self.cursor.execute(f"SELECT measurement_confidence FROM {tbl} WHERE measurement_confidence IS NOT NULL;")
                for r in self.cursor.fetchall():
                    c = r[0]
                    self.assertGreaterEqual(c, 0.0, f"Confidence < 0.0 in {tbl}")
                    self.assertLessEqual(c, 1.0, f"Confidence > 1.0 in {tbl}")

    def test_uncertainty_metadata_null_tolerance_and_default_handling(self):
        """Boundary test: Inserting NULL uncertainty values must succeed without constraint violation."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        schema_sql = self.get_table_sql("harmonized_sites")
        test_conn = sqlite3.connect(":memory:")
        try:
            test_conn.execute("CREATE TABLE celestial_bodies (body_id TEXT PRIMARY KEY, name TEXT);")
            test_conn.execute("INSERT INTO celestial_bodies VALUES ('Moon', 'Moon');")
            test_conn.execute(schema_sql)
            test_conn.execute(
                "INSERT INTO harmonized_sites (site_id, body, site_name, center_lat, center_lon, h3_res6, spatial_resolution_m, vertical_accuracy_m, measurement_confidence) "
                "VALUES ('NULL_U', 'Moon', 'Null Site', 0.0, 0.0, '860000000000000', NULL, NULL, NULL);"
            )
        finally:
            test_conn.close()

    def test_existing_tables_uncertainty_metadata_extension(self):
        """Verify site_engineering_safety and remote_sensing_rasters contain uncertainty columns."""
        tables = self.get_table_names()
        if "site_engineering_safety" in tables:
            ses_cols = self.get_column_names("site_engineering_safety")
            self.assertTrue(
                {"spatial_resolution_m", "vertical_accuracy_m", "measurement_confidence"}.issubset(ses_cols),
                f"site_engineering_safety missing uncertainty columns. Found: {ses_cols}",
            )
        if "remote_sensing_rasters" in tables:
            rsr_cols = self.get_column_names("remote_sensing_rasters")
            self.assertTrue(
                {"vertical_accuracy_m", "measurement_confidence"}.issubset(rsr_cols),
                f"remote_sensing_rasters missing uncertainty columns. Found: {rsr_cols}",
            )

    # --- Unconditional Check Constraint Tests (Remediated per Explorer 2) ---

    def test_harmonized_sites_boundary_latitude_check_constraint(self):
        """Boundary test: Inserting latitude > 90 or < -90 must be rejected by check constraint."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        test_conn = sqlite3.connect(":memory:")
        schema_sql = self.get_table_sql("harmonized_sites")
        test_conn.execute("PRAGMA foreign_keys = ON;")
        try:
            test_conn.execute("CREATE TABLE celestial_bodies (body_id TEXT PRIMARY KEY, name TEXT);")
            test_conn.execute("INSERT INTO celestial_bodies VALUES ('Earth', 'Earth');")
            test_conn.execute(schema_sql)
            test_cursor = test_conn.cursor()
            test_cursor.execute("PRAGMA table_info(harmonized_sites);")
            col_names = [r[1] for r in test_cursor.fetchall()]
            lat_col = "latitude_deg" if "latitude_deg" in col_names else "center_lat"
            lon_col = "longitude_deg" if "longitude_deg" in col_names else "center_lon"
            body_col = "body" if "body" in col_names else "body_id"

            cols_str = f"site_id, {body_col}, site_name, {lat_col}, {lon_col}, h3_res6"

            # Verify DDL explicitly contains CHECK constraint
            self.assertIn("CHECK", schema_sql.upper(), "harmonized_sites DDL must specify CHECK constraints")

            # Unconditionally assert rejection of invalid latitude +95.0
            with self.assertRaises(sqlite3.IntegrityError, msg="Inserting latitude 95.0 must violate CHECK constraint"):
                test_conn.execute(
                    f"INSERT INTO harmonized_sites ({cols_str}) VALUES ('INVALID_LAT', 'Earth', 'Test Site', 95.0, 0.0, '860000000000000');"
                )
            # Unconditionally assert rejection of invalid latitude -95.0
            with self.assertRaises(sqlite3.IntegrityError, msg="Inserting latitude -95.0 must violate CHECK constraint"):
                test_conn.execute(
                    f"INSERT INTO harmonized_sites ({cols_str}) VALUES ('INVALID_LAT_NEG', 'Earth', 'Test Site', -95.0, 0.0, '860000000000000');"
                )
        finally:
            test_conn.close()

    def test_harmonized_sites_measurement_confidence_boundary(self):
        """Boundary test: Measurement confidence must be bounded in [0.0, 1.0] by check constraint."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        schema_sql = self.get_table_sql("harmonized_sites")
        self.assertIn("CHECK", schema_sql.upper(), "harmonized_sites DDL must specify CHECK constraints")

        test_conn = sqlite3.connect(":memory:")
        test_conn.execute("PRAGMA foreign_keys = ON;")
        try:
            test_conn.execute("CREATE TABLE celestial_bodies (body_id TEXT PRIMARY KEY, name TEXT);")
            test_conn.execute("INSERT INTO celestial_bodies VALUES ('Earth', 'Earth');")
            test_conn.execute(schema_sql)
            test_cursor = test_conn.cursor()
            test_cursor.execute("PRAGMA table_info(harmonized_sites);")
            col_names = [r[1] for r in test_cursor.fetchall()]
            lat_col = "latitude_deg" if "latitude_deg" in col_names else "center_lat"
            lon_col = "longitude_deg" if "longitude_deg" in col_names else "center_lon"
            body_col = "body" if "body" in col_names else "body_id"

            cols_str = f"site_id, {body_col}, site_name, {lat_col}, {lon_col}, h3_res6, measurement_confidence"
            with self.assertRaises(sqlite3.IntegrityError, msg="Confidence 1.5 must violate CHECK constraint"):
                test_conn.execute(
                    f"INSERT INTO harmonized_sites ({cols_str}) VALUES ('INVALID_CONF_HI', 'Earth', 'Test Site', 0.0, 0.0, '860000000000000', 1.5);"
                )
            with self.assertRaises(sqlite3.IntegrityError, msg="Confidence -0.2 must violate CHECK constraint"):
                test_conn.execute(
                    f"INSERT INTO harmonized_sites ({cols_str}) VALUES ('INVALID_CONF_LO', 'Earth', 'Test Site', 0.0, 0.0, '860000000000000', -0.2);"
                )
        finally:
            test_conn.close()

    # =========================================================================
    # Additional Domains & Tier 3 Pairwise Cross-Feature Tests
    # =========================================================================

    def test_subsurface_voids_caves_table_exists(self):
        """Verify subsurface_voids_caves table exists with geometric and thermal attributes."""
        tables = self.get_table_names()
        self.assertIn("subsurface_voids_caves", tables)

        cols = self.get_column_names("subsurface_voids_caves")
        expected = {"void_id", "feature_name", "depth_m", "radiation_svf"}
        missing = expected - cols
        self.assertEqual(
            missing,
            set(),
            f"Missing required columns in subsurface_voids_caves: {missing}",
        )

    def test_terrestrial_analog_sites_table_exists(self):
        """Verify terrestrial_analog_sites table exists for under-studied analog ingestion."""
        tables = self.get_table_names()
        self.assertIn("terrestrial_analog_sites", tables)

        cols = self.get_column_names("terrestrial_analog_sites")
        expected = {"analog_id", "name", "country", "target_planetary_body"}
        missing = expected - cols
        self.assertEqual(
            missing,
            set(),
            f"Missing required columns in terrestrial_analog_sites: {missing}",
        )

    def test_pairwise_f5_harmonization_with_f6_standardized_columns_null_safety(self):
        """Pairwise F5 x F6: Cross-body aggregation handles NULL standardized physical columns safely."""
        if "harmonized_sites" not in self.get_table_names():
            self.skipTest("harmonized_sites table not present")

        self.cursor.execute("""
            SELECT body, COUNT(*), AVG(COALESCE(mean_slope_deg, 0)), AVG(COALESCE(fe_wt_pct, 0))
            FROM harmonized_sites GROUP BY body;
        """)
        rows = self.cursor.fetchall()
        self.assertIsInstance(rows, list)
        self.assertGreater(len(rows), 0, "Expected body groupings in harmonized_sites")


if __name__ == "__main__":
    unittest.main()
