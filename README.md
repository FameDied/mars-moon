# Complete Moon & Mars Scientific Planetary Database
**The Definitive Multidisciplinary Archive for Lunar and Martian Planetary Science & Landing Site Optimization**

---

## 🌌 Overview

This database constitutes a comprehensive, authoritative, multidisciplinary planetary database for **Earth's Moon** and **Mars** (along with the Martian moons **Phobos** and **Deimos**). It aggregates, harmonizes, and cross-indexes data from premier space agencies, planetary missions, and scientific institutions:
* **USGS Astrogeology Science Center / International Astronomical Union (IAU)**: Complete Gazetteer of Planetary Nomenclature with Uber H3 spatial indexing.
* **NASA Jet Propulsion Laboratory (JPL)**: Horizons Ephemerides & Dynamics System (DE441), Mars 2020 EDL Performance, and Surveyor landing telemetry.
* **NASA Goddard Space Flight Center (GSFC)**: National Space Science Data Center (NSSDC) Planetary Fact Sheets, LRO LOLA laser altimetry, and Diviner thermal radiometry.
* **NASA Johnson Space Center (JSC)**: Astromaterials Acquisition and Curation Office (Apollo Lunar Sample Database & Mars Meteorite Compendium).
* **NASA Planetary Data System (PDS) & SpatioTemporal Asset Catalog (STAC)**: Cloud-Optimized GeoTIFFs (COG), HiRISE DTMs, CRISM mineral parameter cubes, SHARAD SWIM ice overburden maps, and MOLA elevation grids.
* **CNSA, ISRO, ESA, Roscosmos, JAXA & Commercial CLPS Providers**: Chang'e 1–6, Chandrayaan 1–3, SLIM, Mars Express, ExoMars TGO, Intuitive Machines Nova-C, and Astrobotic Griffin.

The master database is housed in **SQLite 3 (`planetary_moon_mars.db`)** with **Full-Text Search (FTS5)**, **Uber H3 spatial indexing**, and **pre-computed Multi-Criteria Decision Analysis (MCDA)** scoring views. Every dataset is also independently exported in **CSV**, **JSON**, and **Apache Parquet (`.parquet`)** formats.

---

## 🚀 Key Upgrades & Core Innovations

### 1. 3-Sigma Landing Dispersion Ellipses & Uber H3 Spatial Grids
Spacecraft never land on a single zero-dimensional coordinate $(lat, lon)$. Atmospheric entry, guidance margins, retro-burn dispersion, and orbital inclination produce a **3-Sigma Dispersion Ellipse** parameterized by:
* **Semi-Major Axis ($a$)**: Dispersion along the entry corridor (km).
* **Semi-Minor Axis ($b$)**: Cross-track dispersion perpendicular to trajectory (km).
* **Approach Azimuth Angle ($\theta$)**: Orientation angle ($0^\circ - 360^\circ$ East of North) driven by incoming orbital inclination.

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

To enable spatial indexing across planetary spheres without heavyweight GIS dependencies (e.g. PostGIS, GDAL, GEOS), every named IAU feature, remote sensing raster, and candidate landing ellipse is indexed using the **Uber H3 Discrete Global Grid System at Resolution 6**:
* **Average Hexagon Area**: $\sim 36.1\text{ km}^2$
* **Average Edge Length**: $\sim 3.2\text{ km}$
* **Sub-Millisecond Spatial Joins**: Querying landing sites against regional named craters or co-located remote sensing rasters takes **$< 1.5\text{ ms}$** in pure SQLite using standard indexed `JOIN ... ON s.h3_index = r.h3_index`.

---

### 2. 500+ Official NASA Candidate Landing Sites Catalog
The candidate site database (`site_engineering_safety`) scales from small prototypes to **524 official NASA landing and exploration sites**:

| Body | Catalog Category | Site Count | Description |
| :--- | :--- | :---: | :--- |
| **Moon** | **Artemis III 100m Candidate Pads** | **156** | All 13 official Artemis III candidate regions (Faustini Rim A, Peak Near Shackleton, Connecting Ridge, Connecting Ridge Ext, de Gerlache Rim 1 & 2, de Gerlache-Kocher Massif, Haworth, Malapert Massif, Leibnitz Beta Plateau, Nobile Rim 1 & 2, Amundsen Rim) decomposed into specific $100\text{m} \times 100\text{m}$ landing pads. |
| **Moon** | **CLPS Target Sites** | **30** | Commercial Lunar Payload Services targets: Gruithuisen Domes, Reiner Gamma, Schrödinger Basin, Lacus Mortis, Mons Latreille, Mare Crisium, Haworth PSR, etc. |
| **Moon** | **CxP Lunar Sortie Sites** | **50** | Constellation Program 50 globally distributed Lunar Sortie exploration sites. |
| **Moon** | **Lunar Science Exploration Sites** | **30** | Apollo 11–17 landmark bases, proposed Apollo 18–20 targets (Copernicus, Tycho, Marius Hills), and far-side/polar science outposts. |
| **Mars** | **Mars HLS2 Exploration Zones (EZs)** | **47** | All 47 official Human Landing Sites Study (HLS2) Exploration Zones submitted to NASA (Arcadia Planitia, Deuteronilus Mensae, Mawrth Vallis, Melas Chasma, Nili Fossae, etc.). |
| **Mars** | **Mars Candidate Landing Ellipses** | **23** | Mars 2020 Perseverance & ExoMars Rosalind Franklin final candidate ellipses (Midway, NE Syrtis, Columbia Hills, Oxia Planum, Aram Dorsum, Mawrth, Jezero, Gale). |
| **Mars** | **Mars Detailed Exploration Pads** | **188** | High-priority scientific pads (Arcadia Planitia pure slab ice pads, Olympia Undae gypsum dune pads, Hellas ultra-dense air pads, Olympus Mons basal scarps, etc.). |
| **Total** | **Official NASA Candidate Sites** | **524** | **Moon: 266 Sites \| Mars: 258 Sites** |

---

### 3. Multi-Criteria Decision Analysis (MCDA) Real-Time Scoring Engine
To resolve complex engineering and scientific trade-offs, SQLite pre-computes normalized scores ($0.0 - 100.0$) in the view `v_landing_site_pareto_ranks` across four core dimensions:

$$\text{MCDA Composite Score} = \frac{w_{saf} \cdot S_{EDL} + w_{com} \cdot S_{Comms} + w_{isru} \cdot S_{ISRU} + w_{sci} \cdot S_{Sci}}{w_{saf} + w_{com} + w_{isru} + w_{sci}}$$

```
                       ┌──────────────────────────────┐
                       │  v_landing_site_pareto_ranks │
                       └──────────────┬───────────────┘
                                      │
        ┌──────────────┬──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼
 ┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐
 │ EDL Safety  ││Comms/Survive││ISRU Resource││Science Return││ Pareto Rank │
 │ (Slope, Rock││(DTE, Shadow,││(Ice Depth,  ││(Diversity,   ││(Window Rank │
 │  MOLA, Masc)││ SVF, Therm) ││ WEH %, Min) ││ Astrobio, D)││ by Body)    │
 └─────────────┘└─────────────┘└─────────────┘└─────────────┘└─────────────┘
```

1. **EDL Safety Score ($S_{EDL}$)**:
   * Macro-slope penalty ($\le 15^\circ$ baseline)
   * Rock abundance penalty ($\le 15\%$ Diviner/THEMIS)
   * MOLA atmospheric density envelope ($\le -1,500\text{ m}$ for Mars aerodynamic aerobraking)
   * Atmospheric boundary layer wind shear ($\le 30\text{ m/s}$)
   * TRN optical texture entropy score ($0 - 100$)
   * GRAIL/MRO mascon gravity perturbation penalty ($\le 150\text{ mGal}$)
2. **Survivability & Comms Score ($S_{Comms}$)**:
   * Direct-to-Earth (DTE) Deep Space Network line-of-sight visibility fraction ($0 - 100$)
   * Continuous night shadow eclipse penalty ($\le 354\text{ hours}$)
   * Topographic radiation shielding via Sky-View Factor ($1.0 - \text{SVF}$)
   * Surface thermal inertia stability ($50 - 600\text{ SI}$)
3. **ISRU Resource Score ($S_{ISRU}$)**:
   * Accessible water ice overburden depth ($\le 2.5\text{ m}$)
   * Water-Equivalent Hydrogen (WEH wt%)
   * Mineral feedstock abundance (Lunar ilmenite $\text{FeTiO}_3$ / Martian hydrated sulfates)
4. **Science Return Score ($S_{Sci}$)**:
   * Contact stratigraphic diversity count ($0 - 100$)
   * Astrobiology / biosignature sample return potential ($0 - 100$)
   * Rover trafficability and stand-off distance penalty ($\le 20\text{ km}$)

**Performance Benchmark**: Arbitrary dynamic weighting queries across all 524 candidate sites execute in **$1.2 - 1.8\text{ ms}$** in pure SQLite, enabling real-time slider updates in CLI, web, and hackathon frontends.

---

### 4. STAC-Compliant Remote Sensing Rasters (Cloud-Optimized GeoTIFFs)
NASA PDS, USGS Astrogeology, and OpenPlanetary are migrating to the **SpatioTemporal Asset Catalog (STAC)** standard. The `remote_sensing_rasters` table adheres to STAC specification:

* `stac_id`: Globally unique STAC identifier (e.g. `pds:mars:mars-mro-hirise-jezero-dtm`).
* `proj_epsg` / `iau_2015_wkt`: EPSG coordinate reference code (e.g. `104905` for Mars 2015 Sphere, `104904` for Moon 2015).
* `gsd_meters`: Ground Sampling Distance / spatial resolution in meters per pixel.
* `bbox_min_lon`, `bbox_min_lat`, `bbox_max_lon`, `bbox_max_lat`: STAC geographic bounding box.
* `cog_vsicurl_href`: Cloud-Optimized GeoTIFF or PDS endpoint formatted with GDAL's `/vsicurl/` network prefix.
* `no_data_value`: Sensor null/fill value.
* `h3_index`: Uber H3 spatial index at center coordinates.

Any planetary GIS scientist or Python developer can stream pixels directly from NASA/USGS S3 and HTTP endpoints in **QGIS** or **rasterio** without downloading multi-gigabyte files.

---

## 📊 Database Metrics & Contents

| Table / View Name | Description | Records |
| :--- | :--- | :---: |
| `celestial_bodies` | Moon, Mars, Phobos, Deimos body registry & discovery histories | **4** |
| `physical_parameters` | Geodetic, bulk physical, gravity, optical, and thermal constants | **42** |
| `orbital_parameters` | Orbital elements, velocities, periods, and rotational dynamics | **55** |
| `ephemerides_2026` | High-precision JPL Horizons ephemerides (state vectors, magnitudes, distances) | **146** |
| `iau_planetary_features` | Official IAU Gazetteer surface features with Uber H3 spatial indexing | **11,138** |
| `missions_catalog` | All lunar and Martian missions (1958–present) with payloads & discoveries | **40** |
| `surface_landing_sites` | Coordinates, hardware status, and datums of all landers & impact sites | **23** |
| `lunar_samples_catalog` | Apollo 11–17, Luna 16/20/24, and Chang'e 5/6 returned extraterrestrial samples | **2,516** |
| `martian_meteorites_catalog` | NASA JSC Mars Meteorite Compendium (SNCs, ALH84001, Black Beauty, oxides) | **51** |
| `mars_surface_weather` | In-situ meteorological time-series (InSight, Curiosity REMS, Perseverance MEDA) | **12** |
| `atmospheric_profiles` | Atmospheric and exospheric structures, trace gases, isotopes, and radiation | **2** |
| `rover_science_targets` | MSL Curiosity & M2020 Perseverance drill cores, XRD/Raman, and cached tubes | **12** |
| `planetary_stratigraphy` | Chronostratigraphic epochs (Pre-Noachian to Amazonian; Pre-Nectarian to Copernican) | **10** |
| `internal_structure` | Core, mantle, and crustal geophysics based on Apollo & InSight SEIS seismology | **13** |
| `ice_reservoirs` | Polar cold traps, layered ice caps (NPLD/SPLD), and buried mid-latitude glaciers | **9** |
| `planetary_basemaps` | LOLA & MOLA global elevation models, shaded relief maps, and USGS rasters | **4** |
| `curated_imagery` | Curated NASA high-resolution imagery registry with direct CDN assets | **8** |
| `remote_sensing_rasters` | **STAC-Compliant** science rasters, DTMs, Cloud-Optimized GeoTIFFs, and cubes | **43** |
| `site_engineering_safety` | **524 Official NASA Candidate Sites** with 3-Sigma Ellipses & Uber H3 indexing | **524** |
| `lander_engineering_constraints` | Flight vehicle envelopes & 3-Sigma dispersion targets (Starship, Nova-C, Sky Crane) | **18** |
| `regolith_geotechnics_psi` | Soil mechanics (cohesion, friction angle, bearing capacity) & plume blast erosion | **9** |
| `telecom_relay_visibility` | Earth LoS libration angles, DSN visibility windows & Mars orbiter relay passes | **10** |
| `rock_hazard_sfd` | Rock Size-Frequency Distributions (SFD), Golombek q, tip-over probability & CPR | **10** |
| `fts_planetary_search` | SQLite FTS5 unified search index across all features, samples, missions & safety | **14,384** |
| `v_landing_site_pareto_ranks` | **MCDA Pre-Computed 4-Dimension Scoring View** with Pareto ranks | **524** |
| `v_lander_site_compatibility` | **Dynamic Vehicle-Site Compatibility Evaluation View** | **4,724** |
| **Total Table Records** | **Comprehensive Planetary Science, EDL Engineering & Multidisciplinary Safety Index** | **29,083** |

---

## 🗂️ Directory Architecture

```
NASA lol/
├── README.md                              <- Full documentation & schema manual
├── cli.py                                 <- Interactive Python CLI (safety, mcda, h3, rasters, landers)
├── query_examples.py                      <- 12 standalone query benchmarks (< 2ms MCDA & H3 joins)
├── planetary_moon_mars.db                 <- Master SQLite 3 database with FTS5 search (12.1 MB)
├── data/
│   ├── raw/                               <- Downloaded raw archives from USGS and NASA
│   │   ├── usgs/                          <- Shapefiles & metadata (Moon & Mars nomenclature)
│   │   ├── nasa/                          <- NSSDC HTML fact sheets & JPL Horizons cards
│   │   └── jsc/                           <- Apollo sample HTML & Martian Meteorite Compendium XLS
│   ├── processed/
│   │   ├── csv/                           <- Tabular CSV exports of all master tables
│   │   ├── json/                          <- Structured JSON exports of all master tables
│   │   └── parquet/                       <- Snappy-compressed Apache Parquet tables
│   └── maps/                              <- Authentic global shaded relief DEM maps
└── scripts/                               <- Modular ETL, scraper & database pipelines
    ├── 01_fetch_usgs_nomenclature.py      <- USGS nomenclature ingest + Uber H3 res 6 indexing
    ├── 02_fetch_nssdc_parameters.py
    ├── 03_fetch_jpl_horizons.py
    ├── 04_fetch_apollo_samples.py
    ├── 05_fetch_martian_meteorites.py
    ├── 06_fetch_weather_and_atmosphere.py
    ├── 07_fetch_missions_and_landings.py
    ├── 08_fetch_rover_targets_and_geology.py
    ├── 09_fetch_planetary_maps_and_media.py
    ├── 10_build_master_database.py        <- Master pipeline orchestrator & verification audit
    ├── 11_fetch_pds_usgs_remote_sensing_rasters.py <- STAC-compliant raster builder & COG links
    ├── 12_build_engineering_safety_and_edl.py      <- 524 site builder, MCDA engine, and FTS5 update
    └── candidate_sites_catalog.py         <- Official NASA catalog generator (Moon & Mars)
```

---

## 💻 Interactive Command-Line Interface (`cli.py`)

The workspace includes a command-line interface for instant planetary data retrieval, live MCDA decision trade-offs, and spatial analysis:

### 1. Database Overview & Record Metrics
```bash
python3 cli.py stats
```

### 2. Multi-Criteria Decision Analysis (MCDA) Live Slider Engine (`cli.py mcda`)
Drag weights across EDL Safety, Survivability/Comms, ISRU, and Science Return:
```bash
# Balanced scoring for Lunar candidate sites (35% Safety, 25% Comms, 20% ISRU, 20% Science)
python3 cli.py mcda --body Moon --limit 10

# Judge prioritizing ISRU water extraction on Mars (50% ISRU, 30% Safety, 20% Science, 0% Comms)
python3 cli.py mcda --body Mars --weight-isru 50 --weight-safety 30 --weight-science 20 --weight-comms 0

# Filter Artemis III candidate landing pads specifically
python3 cli.py mcda --body Moon --category "Artemis III" --limit 5
```

### 3. Landing Site Safety & 3-Sigma Dispersion Envelopes (`cli.py safety`)
```bash
# Query Artemis III 100m landing pads with slopes <= 8° and rocks <= 5%
python3 cli.py safety --body Moon --category "Artemis III" --max-slope 8 --max-rocks 5

# Query Mars Exploration Zones with elevations <= -1500m MOLA and accessible ice
python3 cli.py safety --body Mars --max-elevation -1500 --has-ice --limit 10

# Filter by Uber H3 spatial index cell
python3 cli.py safety --h3 "86f291"
```

### 4. Sub-Millisecond Uber H3 Spatial Joins (`cli.py h3`)
Performs sub-millisecond GIS spatial joins between candidate landing ellipses, named IAU craters, and STAC remote sensing rasters in pure SQLite:
```bash
# Explore co-located named IAU features and STAC rasters on the Moon
python3 cli.py h3 --body Moon --limit 5

# Inspect spatial co-location on Mars (e.g. Jezero Delta or Gale Crater)
python3 cli.py h3 --body Mars --site "Jezero"
```

### 5. STAC-Compliant Remote Sensing Rasters (`cli.py rasters`)
Inspect Cloud-Optimized GeoTIFFs, EPSG projections, GSD, and vsicurl endpoints:
```bash
# Query high-resolution digital elevation models (DEMs)
python3 cli.py rasters --category "DEM" --limit 5

# Query Jezero Crater targeted rasters
python3 cli.py rasters --target Jezero
```

### 6. Flight Lander Engineering Envelopes (`cli.py landers`)
Inspect landing gear spans, touchdown mass, slope limits, and 3-sigma design targets:
```bash
# Query Lunar landers (Starship HLS, Nova-C, Blue Moon MK1, Chandrayaan-3, Apollo LM)
python3 cli.py landers --body Moon

# Query Mars EDL vehicles (Perseverance Sky Crane, InSight, ExoMars Rosalind Franklin)
python3 cli.py landers --body Mars
```

### 7. Dynamic Lander Vehicle vs Site Compatibility (`cli.py compat`)
Evaluate vehicle qualification status against candidate sites:
```bash
# Test SpaceX Starship HLS compatibility across lunar exploration sites
python3 cli.py compat --vehicle "Starship" --body Moon --limit 10

# Test Perseverance Sky Crane EDL compatibility across Mars Exploration Zones
python3 cli.py compat --vehicle "Perseverance" --body Mars --limit 10
```

### 8. Full-Text Search across the Master Archive (`cli.py search`)
```bash
# Search for water ice detections across all entities
python3 cli.py search "water ice"

# Search for Apollo 11 artifacts and samples
python3 cli.py search "Apollo 11"
```

---

## 🛠️ Python Programming Interface (API)

```python
import sqlite3
import pandas as pd

# Connect to the master database
conn = sqlite3.connect("planetary_moon_mars.db")

# Example 1: Multi-Criteria Decision Analysis (MCDA) Live Slider Query (< 2 ms)
df_mcda = pd.read_sql_query("""
    SELECT site_name, body, catalog_category,
           ROUND(
               (edl_safety_score * 0.40 + survivability_comms_score * 0.25 + isru_resource_score * 0.20 + science_return_score * 0.15), 2
           ) AS custom_score,
           edl_safety_score, survivability_comms_score, isru_resource_score, science_return_score,
           ellipse_semi_major_km, ellipse_semi_minor_km, approach_azimuth_deg, h3_index
    FROM v_landing_site_pareto_ranks
    WHERE body = 'Moon'
    ORDER BY custom_score DESC
    LIMIT 10;
""", conn)
print(df_mcda)

# Example 2: Sub-Millisecond Pure SQLite Uber H3 Spatial Join
df_h3_join = pd.read_sql_query("""
    SELECT s.site_name, s.body, s.catalog_category, s.h3_index,
           f.clean_name AS iau_feature, f.feature_type, f.diameter_km
    FROM site_engineering_safety s
    JOIN iau_planetary_features f ON s.h3_index = f.h3_index
    WHERE s.body = 'Moon'
    LIMIT 10;
""", conn)
print(df_h3_join)

# Example 3: Stream Cloud-Optimized GeoTIFF (COG) via rasterio & /vsicurl/
# import rasterio
# cur = conn.cursor()
# cur.execute("SELECT cog_vsicurl_href, stac_id FROM remote_sensing_rasters WHERE stac_id = 'pds:mars:mars-mro-hirise-jezero-dtm';")
# cog_href, stac_id = cur.fetchone()
# with rasterio.open(cog_href) as src:
#     print(f"STAC ID: {stac_id} | Shape: {src.shape} | Bounds: {src.bounds} | Res: {src.res}")
#     # Sample a 512x512 pixel window under the landing ellipse in milliseconds without downloading the full DTM!
#     window_data = src.read(1, window=((1000, 1512), (1000, 1512)))

# Example 4: Load high-performance Apache Parquet exports
df_parquet_safety = pd.read_parquet("data/processed/parquet/site_engineering_safety.parquet")
print(f"Loaded {len(df_parquet_safety)} candidate landing sites from Parquet.")
```

---

## 📜 Credible Sources & Primary References

1. **USGS Astrogeology Science Center**: *Gazetteer of Planetary Nomenclature*, Working Group for Planetary System Nomenclature (WGPSN), International Astronomical Union (IAU).
2. **NASA GSFC NSSDC**: Planetary Fact Sheets, Dr. David R. Williams (NASA Goddard Space Flight Center).
3. **NASA JPL Horizons System**: Solar System Dynamics Group, Ephemeris DE441 / SSD API.
4. **NASA JSC Astromaterials Curation**: *Apollo Lunar Sample Database* & *Mars Meteorite Compendium (MMC)*, Curatorial Facility, Johnson Space Center.
5. **NASA Planetary Data System (PDS) & STAC**: Geosciences, Imaging, and Cartography Nodes; Cloud-Optimized GeoTIFFs (COG).
6. **LROC & MRO Teams**: Lunar Reconnaissance Orbiter Camera (ASU) and HiRISE/CTX (University of Arizona / JPL).
7. **NASA Human Landing Sites Study (HLS2)**: First Landing Site / Exploration Zone Workshop for Human Missions to the Surface of Mars.
8. **NASA Artemis Program**: Artemis III Candidate Landing Regions and LROC/LOLA candidate landing pad evaluations.
9. **NASA GRAIL & MRO Gravity Teams**: GRAIL JGL1500P Lunar Gravity Model & MRO GMM-3 Martian Gravity Field.
10. **InSight SEIS Team & CAB**: Mars Interior Structure and InSight / Curiosity / Perseverance in-situ meteorological records.
11. **Uber H3**: H3: A Hexagonal Hierarchical Spatial Index, open-source discrete global grid system.
