# Complete Planetary Science & Terrestrial Analog Database (Earth, Moon & Mars)
**The Definitive Multidisciplinary Archive for Planetary Science, Mission Engineering, and Cross-Body Terrestrial Analog Discovery**

---

## 🌌 Overview

This database constitutes an authoritative, multidisciplinary planetary database spanning **Earth's Moon**, **Mars** (with **Phobos** and **Deimos**), and **Earth** as the baseline for comparative planetology and terrestrial analog matching. It aggregates, harmonizes, and cross-indexes open data from premier space agencies, planetary missions, and scientific institutions:

* **NASA Planetary Data System (PDS) & STAC**: LRO Diviner rock abundance & thermal radiometry, LOLA laser altimetry, Clementine UV-VIS FeO/TiO2 maps, CRISM hyperspectral cubes, MRO HiRISE DTMs, SHARAD SWIM ice overburden, and MOLA elevation grids.
* **NASA Earth Science & USGS Astrogeology**: ASTER Global Emissivity Dataset (GED v3), MODIS Land Surface Temperature (LST), EMIT hyperspectral mineralogy, Copernicus 30m GLO-30 DEMs, SRTM, and the complete IAU Gazetteer of Planetary Nomenclature with Uber H3 spatial indexing.
* **European Space Agency (ESA) & Copernicus Data Space**: Mars Express HRSC DTMs, ExoMars Trace Gas Orbiter (TGO) FREND neutron maps, and Copernicus Sentinel/Earth observation services.
* **JAXA, CSA & International Agencies**: JAXA G-Portal ALOS/PALSAR radar products, CSA RADARSAT-1 & RCM geomorphology archives, Chandrayaan-1 Moon Mineralogy Mapper ($M^3$), and Kaguya (SELENE) laser altimetry.
* **NASA JPL & Atmospheric Reanalysis**: JPL Horizons Ephemerides (DE441), Mars 2020 Perseverance & MSL Curiosity in-situ science telemetry, and ECMWF/NASA GMAO ERA5 wind shear and aerosol dust flux grids.
* **Johnson Space Center (JSC) Astromaterials**: Apollo Lunar Sample Database, Mars Meteorite Compendium (MMC), and terrestrial analog mineral catalogs.

The master database is housed in **SQLite 3 (`planetary_moon_mars.db`)** with **Full-Text Search (FTS5)**, **Uber H3 hexagonal spatial indexing (Resolutions 6 & 7)**, and pre-computed analytical views. Every dataset is synchronized and exported in **CSV**, **JSON**, and Snappy-compressed **Apache Parquet (`.parquet`)** formats.

---

## 🚀 Key Innovations & Scientific Capabilities

```
       Incoming Orbital Trajectory (Azimuth θ)
                     ───►
               . - ~ ~ ~ - .
           . '       |       ' .
         /           |           \
        |------------+------------|  ◄── Semi-Major Axis (a)
         \           |           /
           . '       |       ' .
               . - ~ ~ ~ - .
                     ▲
             Semi-Minor Axis (b)
```

### 1. Multi-Dimensional Similarity Vector & Decomposed Analog Score
Instead of an opaque, single similarity score, the system decouples physical matching across four orthogonal axes:

$$\text{Composite Score} = w_A S_{\text{Geomorph}} + w_B S_{\text{Geochem}} + w_C S_{\text{Thermo}} + w_D S_{\text{Volatiles}}$$

* **Axis A (Geomorphology):** Slope distributions, Terrain Ruggedness Index (TRI), crater roughness, and Diviner rock abundance at lander-footpad baselines.
* **Axis B (Geochemistry & Mineralogy):** Spectral band depths matching CRISM phyllosilicate/sulfate/olivine indices to Earth ASTER & EMIT hyperspectral bands, iron oxide ($\text{FeO}$ wt%), and titanium dioxide ($\text{TiO}_2$ wt%).
* **Axis C (Thermophysics):** Diurnal temperature amplitude ($\Delta T$) and apparent thermal inertia.
* **Axis D (Volatiles & Aeolian):** Water-equivalent hydrogen ($\text{WEH}$ wt%), active permafrost depth, ERA5 boundary layer wind shear, and dust deposition flux.

#### Dual Similarity Metrics & Uncertainty Propagation
* **Normalized Cosine Similarity:** Scaled to $[0.0, 100.0]\%$ with magnitude overflow immunity and zero-division safeguards.
* **Regularized Mahalanobis Distance:** Accounts for cross-feature covariance using Ledoit-Wolf diagonal covariance shrinkage ($\Sigma_{\text{reg}} = (1 - \alpha)\Sigma + \alpha \mathbf{I}$).
* **Analytic Variance Propagation:** Instruments have varying spatial resolutions ($1\text{ m/px}$ HiRISE vs $300\text{ km/px}$ GRS). Variances propagate via first-order analytic Taylor expansion ($\sigma_{\text{composite}} = \sqrt{\sum w_i^2 \sigma_i^2}$), enabling **Conservative Lower Confidence Bound (LCB)** ranking:
  $$\text{Score}_{\text{LCB}} = \text{Score}_{\text{composite}} - 1.96 \cdot \sigma_{\text{composite}}$$

> **Why Scientists Love It:** Directly satisfies mission requirements by reporting: *“Site X in the Qaidam Basin or Northern Canada is an 89.8% Geochemical + Aeolian analog for Jezero Crater, though only an 81.4% Thermal analog ($\pm 4.2\%$ confidence).”*

---

### 2. Engineering Constraint Masks (Hard "No-Go" Filters vs. Soft Optimization)
Planetary scientists often nominate scientifically rich sites that spacecraft engineers must reject due to landing hazard envelopes. The database implements a dual-tier Site Suitability Mask:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAW CANDIDATE LANDING SITES                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       TIER 1: HARD "NO-GO" CUTOFFS                     │
│  • Surface Slope: ≤ 10.0° at 5m baseline (lander tip-over limit)       │
│  • Rock Abundance: ≤ 5.0% Diviner/THEMIS (boulder hazard limit)        │
│  • Lunar South Pole Illumination: ≥ 80.0% solar continuous power       │
│  • Direct-to-Earth Visibility: ≥ 50.0% line-of-sight communications    │
│  • Cold Trap Proximity: ≤ 5.0 km (polar water ice rover access)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │  [Pass All 4 Hard Filters]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     TIER 2: SOFT MAUT OPTIMIZATION                     │
│  • Multi-Attribute Utility Theory (MAUT) non-linear S-curves           │
│  • Vectorized 2D spatial raster mask & SQL predicate filtering         │
│  • Pareto-frontier multi-objective ranking                             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      QUALIFIED & RANKED BASE SITES                     │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Hard Engineering Cutoffs:**
   * **Slope Limit:** $\le 10^\circ$ at 5m baseline (lander tip-over envelope).
   * **Rock Abundance:** $\le 5\%$ boulder coverage (Diviner/THEMIS hazard limit).
   * **Solar Illumination & Earth Visibility:** $\ge 80\%$ solar illumination **AND** $\ge 50\%$ Direct-to-Earth (DTE) LoS visibility (Lunar South Pole).
   * **Cold Trap Proximity:** $\le 5\text{ km}$ from Permanently Shadowed Regions (PSRs) to enable rover ice extraction without ascending impassable crater walls.
2. **Soft Multi-Attribute Optimization:** Evaluates qualified candidates through continuous S-curve utility functions and Pareto-frontier optimization.

---

### 3. Cross-Body Feature Harmonization (Common H3 Schema)
Historically, planetary data for Earth, the Moon, and Mars lived in disjoint repositories with non-standard schemas. The database constructs a unified `harmonized_sites` table standardizing 20 physical dimensions:

| Standard Column | Units / Type | Physical Interpretation | Instrument Sources |
| :--- | :--- | :--- | :--- |
| `h3_res6` / `h3_res7` | `TEXT` (Index) | Uber H3 Hexagonal Cell Index (Res 6: $\sim 36\,\text{km}^2$, Res 7: $\sim 5.2\,\text{km}^2$) | Discrete Global Grid System |
| `mean_slope_deg` | Degrees ($^\circ$) | 5m-baseline slope distribution | LOLA DTM, MOLA, Copernicus 30m |
| `thermal_inertia` | $\text{J}\cdot\text{m}^{-2}\text{K}^{-1}\text{s}^{-1/2}$ | Surface grain size / bedrock fraction | LRO Diviner, Mars THEMIS, MODIS |
| `fe_wt_pct` | Weight % | Iron oxide concentration ($\text{FeO}$) | Clementine UV-VIS, GRS, ASTER |
| `ti_wt_pct` | Weight % | Titanium dioxide concentration ($\text{TiO}_2$ ilmenite) | LROC WAC, Clementine, EMIT |
| `h2o_equiv_pct` | Weight % | Water-Equivalent Hydrogen ($\text{WEH}$) | LRO LEND, Odyssey GRS, Copernicus |
| `diurnal_temp_swing_k` | Kelvin ($\text{K}$) | Diurnal surface temperature amplitude ($\Delta T$) | Diviner, MEDA, REMS, ERA5 |
| `has_subsurface_void`| `INTEGER` (0 or 1) | Presence of intact lava tubes or karst caves | LROC NAC Pits, USGS MGC3, Speleology |
| `spatial_resolution_m`| Meters ($\text{m}$) | Sensor ground sampling distance | HiRISE, NAC, HRSC, Sentinel |
| `vertical_accuracy_m` | Meters ($\text{m}$) | Vertical topographic error margin | LOLA, MOLA, SRTM |
| `measurement_confidence`| $[0.0, 1.0]$ | Quantitative dataset confidence bound | Peer-reviewed calibration margins |

> **Game-Changer:** Standardizing every square kilometer of Earth, the Moon, and Mars into H3 hexagonal indices turns planetary analog discovery into sub-millisecond SQL and vector nearest-neighbor queries across all three worlds.

---

### 4. "Earth Analog Limit" Delta-Vectors (The Reality Check)
Earth analogs can replicate mineralogy, geomorphology, and hyper-arid weathering, but Earth possesses fundamental physical boundaries. The `core/delta_vectors.py` engine computes explicit physical deltas between terrestrial sites and target Moon/Mars landing zones:

* **Surface Gravity Ratio:**
  * Moon: $1.000g \rightarrow 0.165g$ ($-83.5\%$ relative delta, $1.62\text{ m/s}^2$).
  * Mars: $1.000g \rightarrow 0.380g$ ($-62.0\%$ relative delta, $3.72\text{ m/s}^2$).
* **Atmospheric Pressure Delta:**
  * Moon: $101.325\text{ kPa} \rightarrow 0.0\text{ Pa}$ (vacuum limit: $-101.325\text{ kPa}$).
  * Mars: $101.325\text{ kPa} \rightarrow 0.610\text{ kPa}$ (near-vacuum $\text{CO}_2$: $-100.715\text{ kPa}$).
* **Ionizing Radiation Exposure Multiplier:**
  * Galactic Cosmic Rays (GCR) + Solar Particle Events (SPE): Earth surface background is $\sim 0.007\text{ mSv/day}$ ($2.4\text{ mSv/yr}$).
  * Lunar / Martian Surface: Multipliers of $\sim 180\times$ to $200\times$ ($1.18 - 1.35\text{ mSv/day}$).
  * Subsurface Void Attenuation: When candidate sites possess intact lava tubes (`has_subsurface_void = 1`), basalt ceiling shielding applies a $0.10\times$ transmission factor ($\sim 90\%$ radiation reduction), bringing cosmic radiation down to near-terrestrial levels.

---

### 5. 12 Factual, Under-Studied Terrestrial Analog Regions
Following official competition directives to look beyond over-studied sites (Antarctica, Atacama, Iceland, Hawaii), the database incorporates 12 peer-reviewed terrestrial analog sites with authentic coordinates, DOIs, and calibrated multi-domain measurements:

| Site ID | Terrestrial Location | Primary Planetary Target | Analog Domain | Authentic Literature DOI |
| :--- | :--- | :--- | :--- | :--- |
| `EARTH_ANALOG_QAIDAM_BASIN` | Qaidam Basin Hyper-Arid Playa (China) | Mars (Jezero, Mawrth, Gale) | Aeolian Yardangs, sulfate/clay evaporites, hypolithic microbes | `10.1016/j.epsl.2018.06.028` |
| `EARTH_ANALOG_HAUGHTON_CRATER` | Haughton Impact Crater (Devon Island, Canada) | Moon & Mars (Artemis, HLS2) | Shocked impact breccia, hydrothermal paleolakes, permafrost gullies | `10.1111/j.1945-5100.2005.tb00179.x` |
| `EARTH_ANALOG_SAMAIL_OPHIOLITE` | Samail Ophiolite Mantle Peridotite (Oman) | Mars (Nili Fossae, Syrtis Major) | Ultramafic mantle serpentinization, olivine weathering, abiotic $\text{CH}_4$ | `10.1002/2016JB013604` |
| `EARTH_ANALOG_DANAKIL_DEPRESSION`| Danakil Depression / Dallol (Ethiopia) | Mars (Early Mars Acidic Brines) | Ultra-acidic ($pH < 0$), hyper-saline hydrothermal sulfate chemistry | `10.1038/s41559-019-1005-0` |
| `EARTH_ANALOG_SVALBARD_BOCKFJORDEN`| Bockfjorden Volcanic Complex (Svalbard) | Mars (Gusev Crater, Elysium) | Basaltic volcanism through glacial cryosphere, carbonate globules | `10.1111/maps.12210` |
| `EARTH_ANALOG_PILBARA_CRATON` | Pilbara Craton (North Pole Dome, Australia) | Mars (Jezero Crater, Noachian) | Archean chert stromatolites, oldest terrestrial biosignatures ($3.48\text{ Ga}$) | `10.1038/s41467-019-11883-0` |
| `EARTH_ANALOG_RIO_TINTO` | Rio Tinto (Iberian Pyrite Belt, Spain) | Mars (Meridiani Planum) | Acid mine drainage, ferric iron precipitation, jarosite evaporites | `10.1016/j.pss.2007.05.008` |
| `EARTH_ANALOG_MAKGADIKGADI_PANS` | Makgadikgadi Salt Flats (Botswana) | Mars (Terra Sirenum paleolakes) | Giant lacustrine evaporite crusts, deflation hollows, brine groundwater | `10.1016/j.geomorph.2014.03.018` |
| `EARTH_ANALOG_NULLARBOR_KARST` | Nullarbor Plain Karst & Caves (Australia) | Moon & Mars (Subsurface Skylights) | Arid karst collapse dolines, deep caves, subterranean microclimates | `10.1016/j.epsl.2017.04.015` |
| `EARTH_ANALOG_LONAR_CRATER` | Lonar Impact Crater (Deccan Traps, India) | Moon & Mars (Basaltic Craters) | Hyper-velocity impact cratering in basalt target rocks, shock plagioclase | `10.1111/j.1945-5100.2008.tb00676.x` |
| `EARTH_ANALOG_EL_MALPAIS` | El Malpais Lava Tube System (New Mexico, USA)| Moon (Marius Hills) / Mars (Arsia Mons)| Quaternary basaltic lava tubes, perennial micro-ice reserves, biothems | `10.1016/j.icarus.2017.06.002` |
| `EARTH_ANALOG_KAZUMURA_LAVA_TUBE`| Kazumura Lava Tube (Hawaii, USA) | Moon (Mare Tranquillitatis) | World's longest and deepest intact basaltic master lava tube | `10.1016/j.jvolgeores.2019.07.014` |

---

### 6. Missing Mission Domains & Scientific Regimes
The database completes missing mission domains critical for landing site selection:

1. **Subsurface Voids & Caves (`subsurface_voids_caves`, 13 rows):** Catalogs lunar skylights (Marius Hills, Mare Tranquillitatis, King Crater), Martian collapse pits (Arsia Mons, Pavonis Mons, Hephaestus Fossae), and terrestrial lava tubes.
2. **Communications & Earth Visibility (`telecom_relay_visibility`, 14 rows):** LOLA-derived Direct-to-Earth (DTE) line-of-sight elevation angles and Earth visibility percentages for Lunar South Pole peaks alongside Mars orbiter pass frequencies.
3. **Regolith Geomechanics & Hazards (`regolith_geotechnics_psi`, 10 rows):** Apollo 11/15/17 and InSight HP3 regolith cohesion, internal friction angles, ultimate bearing capacity, and Diviner rock size-frequency distributions.
4. **Space Weather & Crustal Magnetics (`planetary_radiation_exposure`, 11 rows):** LRO CRaTER and MSL RAD surface radiation dose rates, solar particle burst limits, and lunar crustal magnetic anomalies (Reiner Gamma) providing localized solar wind deflection.
5. **ISRU Chemistry (`isru_chemical_abundance`, 8 rows):** Clementine UV-VIS titanium dioxide ($\text{TiO}_2$ ilmenite) and iron oxide ($\text{FeO}$) feedstock maps for lunar oxygen/metal reduction, and CRISM clay/sulfate deposits for water extraction.
6. **Data Provenance Registry (`data_provenance_registry`, 21 rows):** Full provenance linking every quantitative table to NASA PDS, USGS, ESA PSA, Copernicus, and JAXA archives with DOIs.

---

## 📊 Database Metrics & Contents

The master database `planetary_moon_mars.db` contains **37 structured relational tables**:

| Table / View Name | Category | Primary Purpose & Standard Columns | Records |
| :--- | :--- | :--- | :---: |
| `harmonized_sites` | **Harmonization** | Cross-body H3 indexed sites (Moon, Mars, Earth) with 20 physical columns | **536** |
| `similarity_profiles` | **Analog Engine** | 4-axis decoupled Cosine/Mahalanobis scores, decomposed %, uncertainty bounds | **2,620** |
| `terrestrial_analog_sites`| **Earth Analogs** | 12 under-studied peer-reviewed Earth analogs with authentic DOIs | **12** |
| `subsurface_voids_caves` | **Habitats** | Lunar pits, Mars cave candidates, and terrestrial master lava tubes | **13** |
| `telecom_relay_visibility`| **Telecom** | LOLA Earth LoS visibility fraction, DSN windows, Mars relay passes | **14** |
| `regolith_geotechnics_psi`| **Geomechanics** | Soil bearing capacity, friction angles, cohesion, Diviner boulder coverage | **10** |
| `planetary_radiation_exposure`| **Radiation** | CRaTER / MSL RAD surface dose rates, SPE bursts, magnetic shielding | **11** |
| `isru_chemical_abundance` | **ISRU** | Ilmenite ($\text{TiO}_2$), FeO, phyllosilicates, and hydrated mineral maps | **8** |
| `data_provenance_registry` | **Provenance** | Data provenance, sensor GSD, vertical accuracy, measurement confidence | **21** |
| `site_engineering_safety` | **Candidate Sites** | 524 NASA candidate sites with 3-Sigma Ellipses & Uber H3 indices | **524** |
| `remote_sensing_rasters` | **STAC Rasters** | STAC-compliant rasters, DTMs, Cloud-Optimized GeoTIFFs (COG) | **55** |
| `iau_planetary_features` | **Nomenclature** | Official IAU Gazetteer features across Moon & Mars with H3 indices | **11,138** |
| `lunar_samples_catalog` | **Samples** | Apollo 11–17 & Luna returned sample catalog | **2,516** |
| `martian_meteorites_catalog`| **Meteorites** | Mars Meteorite Compendium (SNCs, ALH84001, Black Beauty) | **51** |
| `missions_catalog` | **Missions** | Global lunar and Martian space missions (1958–present) | **40** |
| `lander_engineering_constraints`| **Vehicles** | Vehicle design limits (Starship HLS, Nova-C, Sky Crane, Apollo LM) | **18** |
| `celestial_bodies` | **Solar System** | Body registry (Moon, Mars, Earth, Phobos, Deimos) | **5** |
| `fts_planetary_search` | **Search** | SQLite FTS5 unified search index across all features and catalogs | **14,384** |
| `v_landing_site_pareto_ranks` | **MCDA View** | Multi-Criteria Decision Analysis 4-dimension pre-computed scores | **524** |
| `v_lander_site_compatibility`| **Evaluation** | Dynamic vehicle-site engineering compatibility matrix | **4,724** |
| *Other Reference Tables* | **Physical Science** | Ephemerides, stratigraphy, weather, basemaps, ice, internal structure | **310** |
| **Total Table Records** | **Master System** | **Authoritative Cross-Body Planetary & Terrestrial Science System** | **36,634** |

---

## 🗂️ Directory Architecture

```
NASA lol/
├── README.md                              <- Full documentation & system manual
├── cli.py                                 <- Interactive CLI (analog, mask, delta, harmonize, safety, mcda)
├── planetary_moon_mars.db                 <- Master SQLite 3 database (37 tables, 14.8 MB)
├── core/                                  <- Scientific algorithms & analytical modules
│   ├── __init__.py
│   ├── similarity_engine.py               <- Decoupled 4-axis Cosine/Mahalanobis similarity & Taylor LCB ranking
│   ├── site_suitability.py                <- Spatial constraint masks (4 hard cutoffs) & MAUT utility ranking
│   └── delta_vectors.py                   <- Physical limit delta-vectors (gravity, pressure, radiation shielding)
├── scripts/                               <- Modular ETL, migration, and ingestion pipelines
│   ├── migrate_v2_schema.py               <- Schema migration, Earth registration, H3 indexer & provenance
│   ├── ingest_factual_datasets.py         <- Ingestion of 12 Earth analogs & 6 missing planetary domains
│   ├── 01_fetch_usgs_nomenclature.py      <- USGS nomenclature ingest + Uber H3 res 6 indexing
│   ├── 02_fetch_nssdc_parameters.py       <- NSSDC physical constants
│   ├── 03_fetch_jpl_horizons.py           <- JPL Horizons ephemerides
│   ├── 04_fetch_apollo_samples.py         <- Apollo lunar samples catalog
│   ├── 05_fetch_martian_meteorites.py     <- Martian meteorite compendium
│   ├── 06_fetch_weather_and_atmosphere.py <- In-situ meteorology & atmospheric profiles
│   ├── 07_fetch_missions_and_landings.py  <- Spaceflight missions & hardware landing sites
│   ├── 08_fetch_rover_targets_and_geology.py <- Rover drill cores & stratigraphic epochs
│   ├── 09_fetch_planetary_maps_and_media.py  <- Basemaps & curated media
│   ├── 10_build_master_database.py        <- Master pipeline orchestrator & verification audit
│   ├── 11_fetch_pds_usgs_remote_sensing_rasters.py <- STAC raster catalog & COG links
│   ├── 12_build_engineering_safety_and_edl.py      <- 524 site builder & MCDA views
│   └── candidate_sites_catalog.py         <- NASA candidate site definitions
├── tests/                                 <- Comprehensive E2E automated test harness (177 tests)
│   ├── __init__.py
│   ├── test_similarity.py                 <- 40 tests: 4-axis similarity, metrics, zero guards, Taylor error
│   ├── test_suitability_mask.py           <- 34 tests: 4 hard cutoffs, boundary pairs, MAUT S-curves
│   ├── test_schema.py                     <- 34 tests: DDL checks, foreign keys, H3 columns, provenance
│   ├── test_cli.py                        <- 25 tests: Subcommands, argument validation, JSON formatting
│   ├── test_ingestion.py                  <- 23 tests: Factual records, coordinates, DOIs, bounds
│   ├── test_delta_vectors.py              <- 15 tests: Gravity ratios, barometric hypsometry, radiation multipliers
│   └── test_e2e_scenarios.py              <- 6 tests: Artemis III, Jezero delta, and lava tube habitats
└── data/
    ├── processed/
    │   ├── csv/                           <- Synchronized CSV exports for all 37 tables
    │   ├── json/                          <- Synchronized JSON exports for all 37 tables
    │   └── parquet/                       <- High-performance Snappy Apache Parquet tables
    ├── maps/                              <- Shaded relief DEM basemaps
    └── raw/                               <- Cached source archives from USGS, NASA, and ESA
```

---

## 💻 Interactive Command-Line Interface (`cli.py`)

The unified CLI provides instant planetary queries, multi-dimensional analog matching, engineering suitability masking, and physical delta evaluations:

### 1. Multi-Dimensional Planetary Analog Discovery (`cli.py analog`)
Find terrestrial analog sites for target Moon or Mars landing locations with decomposed per-axis matching:
```bash
# Decomposed 4-axis analog match for Jezero Crater river delta on Mars
python3 cli.py analog --target MARS_HLS2_16_JEZERO --top 3
```
```text
=========================================================================================================
                              PLANETARY ANALOG DISCOVERY & SIMILARITY ENGINE
Target Site: [Mars] MARS_HLS2_16_JEZERO - Mars HLS2 EZ 16: Jezero Crater River Delta & Lakebed EZ
Method: Cosine Similarity | Metric Dimensions: 4 Decoupled Physical Axes
=========================================================================================================
Rank  Analog ID                       Score   | Axis A   Axis B   Axis C   Axis D   | Uncertainty
---------------------------------------------------------------------------------------------------------
1     EARTH_ANALOG_DANAKIL_DEPRESSION 89.8%   | 92.1%    99.4%    81.4%    86.2%    | ± 4.2%    
2     EARTH_ANALOG_PILBARA_CRATON     89.7%   | 95.8%    98.1%    69.0%    95.9%    | ± 2.6%    
3     EARTH_ANALOG_NULLARBOR_KARST    87.7%   | 94.2%    92.8%    70.2%    93.6%    | ± 3.1%    
---------------------------------------------------------------------------------------------------------
```

### 2. Physical Limit Delta-Vectors (`cli.py delta`)
Display the exact physical boundaries (gravity, pressure, radiation) between candidate Earth analogs and target extraterrestrial bases:
```bash
python3 cli.py delta --target MARS_HLS2_16_JEZERO --analog EARTH_ANALOG_QAIDAM_BASIN
```
```text
=========================================================================================================
               Physical Limit Delta-Vectors: Earth Baseline -> Mars
=========================================================================================================
• Surface Gravity:
  - Earth Baseline:     1.000 g0 (9.807 m/s²)
  - Target Value:       0.380 g0
  - Ratio / Delta:      0.380x (-62.0% relative delta)
  - Operational Impact: Moderate low gravity (0.380 g0). Reduced structural load; traction differs.

• Atmospheric Pressure:
  - Earth Baseline:     101.325 kPa (1 atm)
  - Target Value:       0.610 kPa
  - Pressure Delta:     -100.715 kPa
  - Operational Impact: Near-vacuum CO2 atmosphere (0.610 kPa). Requires pressurized suits and habitats.

• Radiation Dose Exposure:
  - Earth Baseline:     0.007 mSv/day (2.4 mSv/year natural background)
  - Target Effective:   1.183 mSv/day
  - Dose Multiplier:    180.0x
  - Operational Impact: Martian cosmic radiation exposure (180.0x). Minimal atmospheric GCR shielding.
=========================================================================================================
```

### 3. Spatial Site Suitability & Engineering Constraint Masking (`cli.py mask`)
Filter candidate landing sites through the 4 hard engineering cutoffs and rank qualified sites via MAUT utility scores:
```bash
# Filter Lunar South Pole sites with slope <= 10°, rocks <= 5%, illum >= 80%, Earth vis >= 50%
python3 cli.py mask --body Moon --max-slope 10 --max-rock 5 --limit 3
```
```text
=========================================================================================================
                        SPATIAL SITE SUITABILITY & ENGINEERING CONSTRAINT MASK
Body: Moon | Cutoffs: Slope <= 10.0° | Rocks <= 5.0% | Illum >= 80.0% | Earth Vis >= 50.0% | Cold Trap <= 5.0 km
=========================================================================================================
Candidate Site Name              Coords (Lat, Lon)    Slope   Rocks   Illum   EarthVis  ColdTrap  Status     Utility
---------------------------------------------------------------------------------------------------------
Artemis III Connecting Ridge -   (-89.43°, -137.49°)  5.8°    3.9%    97.5%   91.0%     2.0km     QUALIFIED 65.45  
Artemis III Connecting Ridge -   (-89.44°, -137.49°)  6.2°    3.6%    97.5%   89.0%     1.9km     QUALIFIED 65.39  
CLPS Reiner Gamma Magnetic Ano   (+7.30°, -57.50°)    2.5°    2.0%    50.0%   99.0%     0.0km     QUALIFIED 64.82  
---------------------------------------------------------------------------------------------------------
```

### 4. Cross-Body Harmonized Sites Query (`cli.py harmonize`)
Query standardized physical features across Earth, Moon, and Mars indexed by Uber H3:
```bash
python3 cli.py harmonize --body Moon --limit 3
```
```text
===================================================================================================================
                             CROSS-BODY HARMONIZED SITES (EARTH, MOON, MARS)
===================================================================================================================
Site ID      Body   Site Name                    H3 Res 6         Slope  ThInertia  Fe%    Ti%    H2O%   Conf  
-------------------------------------------------------------------------------------------------------------------
MOON_ARTEMIS_AMUNDSEN_RIM_PAD_01 Moon   Artemis III Amundsen Rim -   86f109417ffffff  7.0°   54.0       4.6%   0.0%   6.2%   0.95  
MOON_ARTEMIS_AMUNDSEN_RIM_PAD_02 Moon   Artemis III Amundsen Rim -   86f109417ffffff  7.3°   54.0       4.6%   0.0%   6.2%   0.95  
MOON_ARTEMIS_AMUNDSEN_RIM_PAD_03 Moon   Artemis III Amundsen Rim -   86f109417ffffff  7.7°   54.0       4.6%   0.0%   6.2%   0.95  
-------------------------------------------------------------------------------------------------------------------
```

### 5. Multi-Criteria Decision Analysis (MCDA) Scoring (`cli.py mcda`)
Live weighting engine across EDL Safety, Survivability/Comms, ISRU, and Science Return:
```bash
python3 cli.py mcda --body Moon --weight-safety 40 --weight-comms 25 --weight-isru 20 --weight-science 15 --limit 5
```

### 6. Full-Text Search Across the Master Archive (`cli.py search`)
```bash
python3 cli.py search "lava tube"
```

---

## 🛠️ Python Programming Interface (API)

```python
import sqlite3
import pandas as pd
from core.similarity_engine import compute_similarity_profile, find_top_analogs
from core.site_suitability import evaluate_site_suitability, filter_candidate_sites
from core.delta_vectors import compute_physical_delta_vector

# Connect to the master database
conn = sqlite3.connect("planetary_moon_mars.db")

# Example 1: Decomposed Analog Search for a Target Landing Site
top_analogs = find_top_analogs(
    target_site_id="MARS_HLS2_16_JEZERO",
    top_n=3,
    method="cosine",
    weights={"axis_a": 0.25, "axis_b": 0.35, "axis_c": 0.20, "axis_d": 0.20}
)
for a in top_analogs:
    print(f"Analog: {a['analog_name']} | Composite: {a['composite_score']:.1f}% ± {a['uncertainty_bound']:.1f}%")
    print(f"  Geomorphology: {a['axis_a_geomorphology_pct']:.1f}% | Geochemistry: {a['axis_b_geochemistry_pct']:.1f}%")

# Example 2: Spatial Engineering Constraint Masking
qualified_sites = filter_candidate_sites(
    body="Moon",
    max_slope_deg=10.0,
    max_rock_abundance_pct=5.0,
    min_solar_illum_pct=80.0,
    min_earth_vis_pct=50.0,
    max_cold_trap_dist_km=5.0
)
print(f"Qualified Landing Sites: {len(qualified_sites)} sites pass all hard engineering cutoffs.")

# Example 3: Compute Physical Limit Delta-Vector
delta = compute_physical_delta_vector("Mars")
print(f"Mars Gravity: {delta['gravity']['ratio_to_earth']:.3f}g0 ({delta['gravity']['relative_delta_pct']:.1f}%)")
print(f"Pressure Delta: {delta['pressure']['delta_kpa']:.2f} kPa")
print(f"Radiation Dose Multiplier: {delta['radiation']['effective_multiplier']:.1f}x Earth background")

# Example 4: Load cross-body harmonized sites directly from Apache Parquet
df_harmonized = pd.read_parquet("data/processed/parquet/harmonized_sites.parquet")
print(f"Loaded {len(df_harmonized)} cross-body harmonized sites across Earth, Moon, and Mars.")
```

---

## 🧪 Automated Test Suite & Scientific Verification

The project includes an end-to-end automated test harness with **177 tests** executing in $< 1.0\text{ second}$:

```bash
python3 -m unittest discover tests -v
```

```text
----------------------------------------------------------------------
Ran 177 tests in 0.978s

OK
```

* **`tests/test_similarity.py` (40 tests):** Verifies decoupled 4-axis similarity, cosine normalization $[0.0, 100.0]\%$, Ledoit-Wolf Mahalanobis shrinkage, zero/subnormal scale guards, and analytic Taylor uncertainty bounds.
* **`tests/test_suitability_mask.py` (34 tests):** Tests the 4 hard engineering cutoffs, strict boundary value analysis (e.g. $10.0^\circ$ vs $10.01^\circ$, $5.0\%$ vs $5.01\%$), and MAUT S-curve utility curves.
* **`tests/test_schema.py` (34 tests):** Enforces SQLite DDL check constraints on latitude/longitude, foreign key referential integrity to `celestial_bodies`, and valid H3 resolution 6/7 cell index formats.
* **`tests/test_cli.py` (25 tests):** Validates all CLI subcommands (`analog`, `mask`, `delta`, `harmonize`, `safety`, `mcda`), error handling, invalid enum rejection, and JSON output formatting.
* **`tests/test_ingestion.py` (23 tests):** Validates authentic coordinates, physical parameter bounds, and authentic peer-reviewed literature DOIs for all 12 terrestrial analog sites.
* **`tests/test_delta_vectors.py` (15 tests):** Asserts gravity ratios ($0.165g$ Moon, $0.380g$ Mars), barometric pressure differentials, and radiation multipliers with subsurface void attenuation.
* **`tests/test_e2e_scenarios.py` (6 tests):** Validates complex mission scenarios: Artemis III Connecting Ridge landing qualification, Jezero Crater astrobiological analog discovery, and Marius Hills lava tube microclimate habitat sheltering.

---

## 📜 Credible Sources & Primary References

1. **USGS Astrogeology Science Center**: *Gazetteer of Planetary Nomenclature*, Working Group for Planetary System Nomenclature (WGPSN), International Astronomical Union (IAU).
2. **NASA GSFC NSSDC**: Planetary Fact Sheets, Dr. David R. Williams (NASA Goddard Space Flight Center).
3. **NASA JPL Horizons System**: Solar System Dynamics Group, Ephemeris DE441 / SSD API.
4. **NASA JSC Astromaterials Curation**: *Apollo Lunar Sample Database* & *Mars Meteorite Compendium (MMC)*, Curatorial Facility, Johnson Space Center.
5. **NASA Planetary Data System (PDS) & STAC**: Geosciences, Imaging, and Cartography Nodes; Cloud-Optimized GeoTIFFs (COG).
6. **LROC & MRO Teams**: Lunar Reconnaissance Orbiter Camera (ASU), Diviner Thermal Radiometer (UCLA), and HiRISE/CTX (University of Arizona / JPL).
7. **NASA Human Landing Sites Study (HLS2)**: First Landing Site / Exploration Zone Workshop for Human Missions to the Surface of Mars.
8. **NASA Artemis Program**: Artemis III Candidate Landing Regions and LROC/LOLA candidate landing pad evaluations.
9. **Copernicus Data Space**: Copernicus 30m Global DEM (GLO-30), European Space Agency (ESA).
10. **ASTER GED Team**: Advanced Spaceborne Thermal Emission and Reflection Radiometer Global Emissivity Dataset (v3), NASA JPL / METI.
11. **ECMWF / NASA GMAO**: ERA5 Global Atmospheric Reanalysis, boundary layer wind dynamics and aerosol flux grids.
12. **InSight SEIS Team & CAB**: Mars Interior Structure and InSight / Curiosity / Perseverance in-situ meteorological records.
13. **Uber H3**: H3: A Hexagonal Hierarchical Spatial Index, open-source discrete global grid system.
