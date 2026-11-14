# ATLAS-X Software Requirements Verification Matrix (SRVM)
**Standard:** NASA NPR 7150.2D (*NASA Software Engineering Requirements*)  
**Software Classification:** Class D (Mission Support & Scientific Analysis Software)  
**Traceability Mandates:** SWE-052 (Bidirectional Traceability), SWE-064 (Design to Code), SWE-065 (Verification & Testing)  
**Document Identifier:** ATLAS-X-VRM-2026-001  
**Baseline Date:** 2026-11-14  
**Project:** ATLAS-X (Automated Terrestrial & Lunar/Martian Analog System)

---

## 1. Verification Method Legend
In accordance with NASA NPR 7150.2D Section 5.3, verification of software requirements is accomplished through one or more of four formal verification methods:
- **[T] Test:** Verification via automated execution of unit, integration, or regression test suites with defined inputs and quantitative pass/fail assertions.
- **[A] Analysis:** Verification via theoretical mathematical models, physical limit bounds, algorithmic proofs, or statistical covariance shrinkage.
- **[D] Demonstration:** Verification via observable execution of user interfaces, CLI commands, and automated data pipelines.
- **[I] Inspection:** Verification via visual audit of source code, relational database schema (DDL), tabular exports, or metadata files.

---

## 2. Requirements Traceability Matrix (REQ-01 through REQ-04)

| Req ID | Requirement Statement & Description | NPR 7150.2D Mandate | Method | Primary Test Suite | Key Test Cases & Verification Assertions | Status |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **REQ-01** | **Factual Planetary & Terrestrial Dataset Ingestion**<br>Ingest 12 peer-reviewed, under-studied Earth analog sites with authentic coordinates and DOIs; ingest 6 missing planetary domains (subsurface voids/caves, telecom LoS visibility, regolith geotechnics, radiation exposure, ISRU chemistry); maintain authoritative non-mock provenance from NASA PDS, USGS, and ESA archives. | `SWE-052`<br>`SWE-065` | **T, I** | `tests/test_ingestion.py`<br>*(23 tests)* | • `test_twelve_terrestrial_analog_sites_ingested`: All 12 authentic analogs present.<br>• `test_analog_sites_geographic_coordinates`: Coordinates match literature within ±2.5° lat, ±5.0° lon.<br>• `test_analog_sites_authoritative_provenance`: Zero mock/synthetic data sources.<br>• `test_subsurface_voids_caves_ingested`: Depth > 0, SVF in [0.0, 0.35].<br>• `test_telecom_relay_visibility_lola`: DTE visibility fraction in [0.0, 1.0].<br>• `test_regolith_geotechnics_psi_ingested`: Internal friction angle in [20°, 60°].<br>• `test_planetary_radiation_exposure_ingested`: Surface dose > 0 mSv/yr.<br>• `test_isru_chemical_abundance_ingested`: Feedstock wt% in [0.1, 100.0]%. | **VERIFIED**<br>*(23/23 Pass)* |
| **REQ-02** | **Multi-Dimensional Decoupled Similarity Engine**<br>Compute decomposed analog similarity scores across 4 decoupled physical axes: Axis A (Geomorphology), Axis B (Geochemistry), Axis C (Thermophysics), Axis D (Volatiles/Aeolian); implement Normalized Cosine Similarity $[0, 100]\%$ with zero/overflow immunity and Ledoit-Wolf Regularized Mahalanobis Distance; propagate analytic Taylor series sensor uncertainties to compute Lower Confidence Bound (LCB) ranking. | `SWE-052`<br>`SWE-064`<br>`SWE-065` | **T, A** | `tests/test_similarity.py`<br>*(40 tests)* | • `test_axis_a_geomorphology_cosine_identical` to `test_axis_d_volatiles_cosine_identical`: Exact identical vectors return 100.0%.<br>• `test_all_scores_bounded_between_zero_and_hundred`: Strict [0, 100]% bounds.<br>• `test_regularized_covariance_invertible`: Ledoit-Wolf shrinkage ensures positive definite covariance.<br>• `test_cosine_similarity_small_magnitude_scale_invariance`: Subnormal float resilience.<br>• `test_taylor_series_uncertainty_propagation`: First-order Taylor error propagation.<br>• `test_conservative_ranking_lower_bound`: Score_LCB = Score - 1.96 * sigma prevents ranking inversion. | **VERIFIED**<br>*(40/40 Pass)* |
| **REQ-03** | **Dual-Tier Spatial Site Suitability Masking**<br>Implement dual-tier engineering constraint evaluation: Tier 1 enforces 4 hard "no-go" cutoffs (Slope $\le 10^\circ$, Rock Abundance $\le 5\%$, Lunar South Pole Solar Illumination $\ge 80\%$ & DTE Visibility $\ge 50\%$, Cold Trap Distance $\le 5\text{ km}$); Tier 2 Boundary Value Analysis (BVA) strictly at cutoff boundaries; Tier 3 soft optimization via Multi-Attribute Utility Theory (MAUT) non-linear S-curves, Pareto-frontier ranking, and relational SQL / continuous 2D raster boolean masks. | `SWE-052`<br>`SWE-065` | **T, A** | `tests/test_suitability_mask.py`<br>*(34 tests)* | • `test_01_slope_within_limit_passes` to `test_13_single_cutoff_failure_disqualifies_candidate`: 4 hard cutoffs strictly qualify/disqualify.<br>• `test_14_bva_slope_exact_ten_degrees_passes` to `test_20_bva_negative_and_out_of_bounds_inputs_raise`: Strict BVA (10.0° vs 10.01°, 5.0% vs 5.01%, 80.0% vs 79.9%, 5.0 vs 5.01 km).<br>• `test_21_soft_utility_slope_s_curve_monotonicity`: S-curve monotonicity.<br>• `test_24_pareto_dominance_ranking`: Strict Pareto frontier dominance.<br>• `test_25_dual_tier_sql_masking_against_database`: SQL predicate filtering.<br>• `test_26_dual_tier_raster_mask_vectorized_numpy`: 2D spatial raster masking. | **VERIFIED**<br>*(34/34 Pass)* |
| **REQ-04** | **Cross-Body Physical Limit Delta-Vectors**<br>Quantify planetary physical deltas between Earth baseline and target extraterrestrial landing sites: Surface gravity ratios ($0.165g$ Moon, $0.380g$ Mars); atmospheric pressure differentials ($-101.325\text{ kPa}$ Moon vacuum, $-100.715\text{ kPa}$ Mars); radiation dose multipliers ($180\times-200\times$) with subterranean lava tube basalt attenuation ($0.10\times$ transmission factor / $90\%$ reduction). | `SWE-052`<br>`SWE-064`<br>`SWE-065` | **T, A** | `tests/test_delta_vectors.py`<br>*(15 tests)* | • `test_gravity_ratio_moon`: Ratio $0.165 \pm 0.005$, delta $-83.5\%$.<br>• `test_gravity_ratio_mars`: Ratio $0.380 \pm 0.005$, delta $-62.0\%$.<br>• `test_atmospheric_pressure_delta_moon`: Vacuum limit $-101.325\text{ kPa}$.<br>• `test_atmospheric_pressure_delta_mars`: Delta $-100.715\text{ kPa}$.<br>• `test_radiation_multiplier_moon`: Lunar dose multiplier $\approx 180\times$.<br>• `test_radiation_multiplier_mars`: Martian dose multiplier $\approx 180-200\times$.<br>• `test_subsurface_void_radiation_shielding`: Attenuation factor $0.10\times$ verified. | **VERIFIED**<br>*(15/15 Pass)* |

---

## 3. Supporting Software Verification Suites

| Verification Scope | NPR 7150.2D Mandate | Method | Test Suite | Test Count | Status |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **Database Schema & DDL Integrity** | `SWE-052`, `SWE-064` | **T, I** | `tests/test_schema.py` | 34 tests | **VERIFIED** (Pass) |
| **Unified Command-Line Interface (CLI)** | `SWE-065` | **T, D** | `tests/test_cli.py` | 25 tests | **VERIFIED** (Pass) |
| **End-to-End Real-World Mission Scenarios** | `SWE-065` | **T, D** | `tests/test_e2e_scenarios.py` | 6 tests | **VERIFIED** (Pass) |
| **Analog Engine Algorithmic Integrity** | `SWE-052`, `SWE-064` | **T, A** | `tests/test_analog_engine.py` | 9 tests | **VERIFIED** (Pass) |
| **Step 2 Terrestrial Screening Pipeline** | `SWE-052`, `SWE-065` | **T, A, D** | `tests/test_terrestrial_pipeline.py` | 15 tests | **VERIFIED** (Pass) |
| **Step 4 Cross-Planetary Convergence & Split-Twin Engine** | `SWE-052`, `SWE-065` | **T, A, D** | `tests/test_step4_convergence.py` | 12 tests | **VERIFIED** (Pass) |
| **Cumulative Project Test Harness** | `SWE-065` | **T** | `tests/` *(10 test modules)* | **213 tests** | **100% PASS** |

---

## 4. Test Execution & Compliance Summary
- **Execution Command:** `pytest tests/` (or `python3 -m unittest discover tests -v`)
- **Total Tests Collected:** 213
- **Total Tests Passed:** 213
- **Failures / Errors:** 0
- **Skipped Tests:** 0
- **Execution Elapsed Time:** 6.33 seconds
- **Verification Conclusion:** All software requirements REQ-01 through REQ-04 and supporting system suites meet 100% compliance criteria under NASA NPR 7150.2D.
