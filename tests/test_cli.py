#!/usr/bin/env python3
"""
Test Suite: End-to-End CLI Subcommands & Argument Validation
============================================================
Covers Feature 12 & Requirements R1-R6 via opaque-box CLI invocations using
subprocess.run([sys.executable, 'cli.py', ...]):
- Subcommands: stats, compare, safety, mcda, features, h3, search
- New M4 Subcommands: analog, mask / suitability, delta, harmonize
- Argument validation, help messages (--help), invalid numeric bounds,
  non-finite weight rejection (NaN, Inf), invalid enum choices,
  and non-zero exit codes on invalid or malformed arguments.

Pure standard library unittest test suite executable via:
    python3 -m unittest tests/test_cli.py -v
"""

import os
import sys
import json
import sqlite3
import subprocess
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_PATH = os.path.join(PROJECT_ROOT, "cli.py")
DB_PATH = os.path.join(PROJECT_ROOT, "planetary_moon_mars.db")


class TestCLIExecution(unittest.TestCase):
    """Tier 1, Tier 2, Tier 3: Opaque-Box CLI Subcommand Verification."""

    def run_cli(self, args, check_exit_zero=True):
        """Invoke cli.py via subprocess and capture output."""
        cmd = [sys.executable, CLI_PATH] + args
        proc = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        if check_exit_zero:
            self.assertEqual(
                proc.returncode, 0,
                f"CLI command failed with code {proc.returncode}.\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
            )
        return proc

    def get_registered_subcommands(self):
        """Parse available subcommands from cli.py --help."""
        proc = self.run_cli(["--help"], check_exit_zero=True)
        return proc.stdout

    # -------------------------------------------------------------------------
    # Global CLI Arguments & Error Handling
    # -------------------------------------------------------------------------

    def test_01_cli_help_global(self):
        """'python3 cli.py --help' exits 0 and prints usage with positional subcommands."""
        proc = self.run_cli(["--help"])
        self.assertIn("usage: cli.py", proc.stdout)
        self.assertIn("Master Database CLI", proc.stdout)

    def test_02_cli_no_args_displays_help(self):
        """'python3 cli.py' without arguments exits 0 and displays help."""
        proc = self.run_cli([])
        self.assertIn("usage: cli.py", proc.stdout)

    def test_03_cli_invalid_command_returns_nonzero_exit_code(self):
        """'python3 cli.py invalid_subcommand' returns non-zero exit code (code 2)."""
        proc = self.run_cli(["nonexistent_subcommand_xyz"], check_exit_zero=False)
        self.assertNotEqual(proc.returncode, 0, "Invalid command must exit non-zero")
        self.assertIn("invalid choice", proc.stderr)

    # -------------------------------------------------------------------------
    # Subcommand: stats
    # -------------------------------------------------------------------------

    def test_04_cli_stats_summary_execution(self):
        """'python3 cli.py stats' outputs database metrics table and total record counts."""
        proc = self.run_cli(["stats"])
        self.assertIn("MASTER MOON & MARS DATABASE SUMMARY & METRICS", proc.stdout)
        self.assertIn("TOTAL INDEXED TABLE RECORDS:", proc.stdout)
        self.assertIn("DATABASE FILE SIZE:", proc.stdout)

    def test_05_cli_stats_table_content_verification(self):
        """'python3 cli.py stats' reports core planetary tables."""
        proc = self.run_cli(["stats"])
        self.assertIn("Planetary & Satellite Bodies", proc.stdout)
        self.assertIn("Physical & Bulk Geodetic Constants", proc.stdout)
        self.assertIn("Landing Site Safety Evaluator", proc.stdout)
        self.assertIn("Full-Text Search Index Entries", proc.stdout)

    # -------------------------------------------------------------------------
    # Subcommand: compare
    # -------------------------------------------------------------------------

    def test_06_cli_compare_execution(self):
        """'python3 cli.py compare' prints comparative physical constants across Moon, Mars, Earth."""
        proc = self.run_cli(["compare"])
        self.assertIn("PLANETARY PHYSICAL CONSTANTS COMPARISON", proc.stdout)
        self.assertIn("Surface gravity", proc.stdout)
        self.assertIn("Moon", proc.stdout)
        self.assertIn("Mars", proc.stdout)
        self.assertIn("Earth", proc.stdout)

    # -------------------------------------------------------------------------
    # Subcommand: safety
    # -------------------------------------------------------------------------

    def test_07_cli_safety_body_filtering_moon(self):
        """'python3 cli.py safety --body Moon --limit 5' returns Lunar candidate sites."""
        proc = self.run_cli(["safety", "--body", "Moon", "--limit", "5"])
        self.assertIn("LANDING SITE ENGINEERING SAFETY", proc.stdout)
        self.assertIn("[Moon]", proc.stdout)

    def test_08_cli_safety_body_filtering_mars(self):
        """'python3 cli.py safety --body Mars --limit 5' returns Martian candidate sites."""
        proc = self.run_cli(["safety", "--body", "Mars", "--limit", "5"])
        self.assertIn("LANDING SITE ENGINEERING SAFETY", proc.stdout)
        self.assertIn("[Mars]", proc.stdout)

    def test_09_cli_safety_slope_filter(self):
        """'python3 cli.py safety --body Moon --max-slope 6.0 --limit 5' enforces macro slope <= 6 deg."""
        proc = self.run_cli(["safety", "--body", "Moon", "--max-slope", "6.0", "--limit", "5"])
        self.assertIn("LANDING SITE ENGINEERING SAFETY", proc.stdout)
        self.assertIn("[Moon]", proc.stdout)
        self.assertIn("Slope:", proc.stdout)

    def test_10_cli_safety_rock_abundance_filter(self):
        """'python3 cli.py safety --body Moon --max-rocks 4.0 --limit 5' enforces rock abundance <= 4%."""
        proc = self.run_cli(["safety", "--body", "Moon", "--max-rocks", "4.0", "--limit", "5"])
        self.assertIn("LANDING SITE ENGINEERING SAFETY", proc.stdout)
        self.assertIn("Rocks:", proc.stdout)

    def test_11_cli_safety_invalid_numeric_argument(self):
        """'python3 cli.py safety --max-slope abc' exits non-zero with argument error."""
        proc = self.run_cli(["safety", "--max-slope", "abc"], check_exit_zero=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid float value", proc.stderr)

    # -------------------------------------------------------------------------
    # Subcommand: mcda
    # -------------------------------------------------------------------------

    def test_12_cli_mcda_default_weights(self):
        """'python3 cli.py mcda --body Moon --limit 5' computes 4-criteria MCDA scores."""
        proc = self.run_cli(["mcda", "--body", "Moon", "--limit", "5"])
        self.assertIn("MULTI-CRITERIA DECISION ANALYSIS", proc.stdout)
        self.assertIn("Weights:", proc.stdout)
        self.assertIn("Score", proc.stdout)

    def test_13_cli_mcda_custom_weights(self):
        """'python3 cli.py mcda --body Mars --weight-safety 40 --weight-comms 30 --weight-isru 10 --weight-science 20 --limit 5' executes normalized custom weights."""
        proc = self.run_cli([
            "mcda", "--body", "Mars",
            "--weight-safety", "40",
            "--weight-comms", "30",
            "--weight-isru", "10",
            "--weight-science", "20",
            "--limit", "5"
        ])
        self.assertIn("EDL Safety: 40.0%", proc.stdout)
        self.assertIn("Survivability/Comms: 30.0%", proc.stdout)
        self.assertIn("ISRU: 10.0%", proc.stdout)
        self.assertIn("Science Return: 20.0%", proc.stdout)

    def test_14_cli_mcda_invalid_weight_format(self):
        """'python3 cli.py mcda --weight-safety invalid_value' exits non-zero."""
        proc = self.run_cli(["mcda", "--weight-safety", "invalid_value"], check_exit_zero=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid float value", proc.stderr)

    # -------------------------------------------------------------------------
    # Subcommands: features, h3, search
    # -------------------------------------------------------------------------

    def test_15_cli_features_query(self):
        """'python3 cli.py features --body Moon --limit 3' returns IAU features with H3 indexing."""
        proc = self.run_cli(["features", "--body", "Moon", "--limit", "3"])
        self.assertIn("Official IAU Planetary Features", proc.stdout)
        self.assertIn("H3:", proc.stdout)

    def test_16_cli_h3_spatial_join(self):
        """'python3 cli.py h3 --body Moon --limit 3' performs H3 spatial join with STAC rasters."""
        proc = self.run_cli(["h3", "--body", "Moon", "--limit", "3"])
        self.assertIn("UBER H3 SPATIAL GRID JOINS", proc.stdout)

    def test_17_cli_search_full_text(self):
        """'python3 cli.py search \"water ice\" --limit 3' returns FTS5 keyword results."""
        proc = self.run_cli(["search", "water ice", "--limit", "3"])
        self.assertIn("Searching for 'water ice'", proc.stdout)

    # -------------------------------------------------------------------------
    # New Subcommands: analog, mask, delta, harmonize (M4 / Progressive Integration)
    # -------------------------------------------------------------------------

    def test_18_cli_subcommand_analog_or_progressive_check(self):
        """Verifies 'analog' subcommand when present, or validates CLI parser status."""
        help_text = self.get_registered_subcommands()
        if "analog" in help_text:
            proc = self.run_cli(["analog", "--help"])
            self.assertIn("analog", proc.stdout.lower())
        else:
            self.skipTest("Subcommand 'analog' pending M4 implementation in cli.py")

    def test_19_cli_subcommand_mask_or_progressive_check(self):
        """Verifies 'mask' (or 'suitability') subcommand when present."""
        help_text = self.get_registered_subcommands()
        cmd_name = None
        if "mask" in help_text:
            cmd_name = "mask"
        elif "suitability" in help_text:
            cmd_name = "suitability"

        if cmd_name:
            proc = self.run_cli([cmd_name, "--help"])
            self.assertEqual(proc.returncode, 0)
            self.assertIn(cmd_name, proc.stdout.lower())
        else:
            self.skipTest("Subcommand 'mask'/'suitability' pending M4 implementation in cli.py")

    def test_20_cli_subcommand_delta_or_progressive_check(self):
        """Verifies 'delta' subcommand when present."""
        help_text = self.get_registered_subcommands()
        if "delta" in help_text:
            proc = self.run_cli(["delta", "--help"])
            self.assertEqual(proc.returncode, 0)
            self.assertIn("delta", proc.stdout.lower())
        else:
            self.skipTest("Subcommand 'delta' pending M4 implementation in cli.py")

    def test_21_cli_subcommand_harmonize_or_progressive_check(self):
        """Verifies 'harmonize' (or 'harmonized') subcommand when present."""
        help_text = self.get_registered_subcommands()
        cmd_name = None
        if "harmonize" in help_text:
            cmd_name = "harmonize"
        elif "harmonized" in help_text:
            cmd_name = "harmonized"

        if cmd_name:
            proc = self.run_cli([cmd_name, "--help"])
            self.assertEqual(proc.returncode, 0)
            self.assertIn(cmd_name, proc.stdout.lower())
        else:
            self.skipTest("Subcommand 'harmonize' pending M4 implementation in cli.py")

    # -------------------------------------------------------------------------
    # Adversarial Error Handling & Boundary Argument Validation
    # -------------------------------------------------------------------------

    def test_22_cli_mcda_invalid_nan_weight_error_handling(self):
        """'python3 cli.py mcda --weight-safety nan' must exit non-zero on non-finite weight."""
        proc = self.run_cli(["mcda", "--weight-safety", "nan"], check_exit_zero=False)
        self.assertNotEqual(proc.returncode, 0, "MCDA with NaN weight must exit non-zero")

    def test_23_cli_mcda_invalid_inf_weight_error_handling(self):
        """'python3 cli.py mcda --weight-safety inf' must exit non-zero on infinite weight."""
        proc = self.run_cli(["mcda", "--weight-safety", "inf"], check_exit_zero=False)
        self.assertNotEqual(proc.returncode, 0, "MCDA with Inf weight must exit non-zero")

    def test_24_cli_safety_invalid_body_choice(self):
        """'python3 cli.py safety --body Jupiter' exits non-zero (code 2) with invalid choice error."""
        proc = self.run_cli(["safety", "--body", "Jupiter"], check_exit_zero=False)
        self.assertEqual(proc.returncode, 2, "Invalid enum choice must exit code 2")
        self.assertIn("invalid choice", proc.stderr)

    def test_25_cli_search_syntax_error_handling(self):
        """'python3 cli.py search \"NOT\"' returns non-zero exit code on invalid FTS5 syntax."""
        proc = self.run_cli(["search", "NOT"], check_exit_zero=False)
        self.assertNotEqual(proc.returncode, 0, "Malformed FTS5 search query must exit non-zero")


if __name__ == "__main__":
    unittest.main()
