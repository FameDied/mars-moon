# Complete Moon & Mars Scientific Planetary Database
**The Definitive Multidisciplinary Archive for Lunar and Martian Planetary Science**

---

## 🌌 Overview

This database constitutes a comprehensive, authoritative, multidisciplinary planetary database for **Earth's Moon** and **Mars** (along with the Martian moons **Phobos** and **Deimos**). It aggregates and harmonizes data from premier space agencies and scientific institutions:
* **USGS Astrogeology Science Center / International Astronomical Union (IAU)**: Gazetteer of Planetary Nomenclature.
* **NASA Jet Propulsion Laboratory (JPL)**: Horizons Ephemerides & Dynamics System (DE441).
* **NASA Goddard Space Flight Center (GSFC)**: National Space Science Data Center (NSSDC) Planetary Fact Sheets.
* **NASA Johnson Space Center (JSC)**: Astromaterials Acquisition and Curation Office (Apollo Lunar Sample Database & Mars Meteorite Compendium).
* **NASA Planetary Data System (PDS) & Centro de Astrobiología (CAB)**: InSight APSS, Curiosity REMS, and Perseverance MEDA weather stations.
* **CNSA, ISRO, ESA, Roscosmos & Private CLPS Missions**: Chang'e 1-6, Chandrayaan 1-3, SLIM, Mars Express, ExoMars TGO.

The master database is stored in **SQLite 3 (`planetary_moon_mars.db`)** with **Full-Text Search (FTS5)** and spatial indexing. Every dataset is also independently exported in **CSV**, **JSON**, and **Apache Parquet (`.parquet`)** formats.

---

## 📊 Database Metrics & Contents

| Table Name | Description | Records |
| :--- | :--- | :---: |
| `celestial_bodies` | Moon, Mars, Phobos, Deimos body registry & discovery histories | **4** |
| `physical_parameters` | Geodetic, bulk physical, gravity, optical, and thermal constants | **42** |
| `orbital_parameters` | Orbital elements, velocities, periods, and rotational dynamics | **55** |
| `ephemerides_2026` | High-precision JPL Horizons ephemerides (state vectors, magnitudes, distances) | **146** |
| `iau_planetary_features` | Complete IAU official named surface features (craters, maria, montes, valleys) | **11,139** |
| `missions_catalog` | All lunar and Martian missions (1958–present) with payloads & discoveries | **40** |
| `surface_landing_sites` | Precise coordinates, hardware status, and datums of all landers & impact sites | **23** |
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
| `remote_sensing_rasters` | Direct PDS/USGS/JAXA/ESA science rasters, DTMs, GeoTIFFs, and spectral cubes | **33** |
| `fts_planetary_search` | SQLite FTS5 unified search index across all features, samples, missions & rasters | **13,833** |
| **Total Database Records** | **Comprehensive Planetary Science Index** | **27,952** |

---

## 🗂️ Directory Architecture

```
NASA lol/
├── README.md                              <- Full documentation & schema manual
├── cli.py                                 <- Interactive Python CLI for querying & filtering
├── query_examples.py                      <- Standalone query demonstration suite
├── planetary_moon_mars.db                 <- Master SQLite 3 database with FTS5 search (10.9 MB)
├── data/
│   ├── raw/                               <- Downloaded raw archives from USGS and NASA
│   │   ├── usgs/                          <- Shapefiles & metadata (Moon & Mars nomenclature)
│   │   ├── nasa/                          <- NSSDC HTML fact sheets & JPL Horizons cards
│   │   └── jsc/                           <- Apollo sample HTML & Martian Meteorite Compendium XLS
│   ├── processed/
│   │   ├── csv/                           <- 17 tabular CSV exports (including remote_sensing_rasters.csv)
│   │   ├── json/                          <- 18 structured JSON files (including remote_sensing_rasters.json)
│   │   └── parquet/                       <- 17 Snappy-compressed Apache Parquet tables
│   └── maps/                              <- Authentic global shaded relief DEM maps
│       ├── luna_lola_global_topography.jpg
│       ├── mars_mola_global_topography.jpg
│       ├── mars_mola_surface_relief.jpg
│       └── mars_usgs_mola_colorhillshade.jpg
└── scripts/                               <- Modular ETL, scraper & database pipelines
    ├── 01_fetch_usgs_nomenclature.py
    ├── 02_fetch_nssdc_parameters.py
    ├── 03_fetch_jpl_horizons.py
    ├── 04_fetch_apollo_samples.py
    ├── 05_fetch_martian_meteorites.py
    ├── 06_fetch_weather_and_atmosphere.py
    ├── 07_fetch_missions_and_landings.py
    ├── 08_fetch_rover_targets_and_geology.py
    ├── 09_fetch_planetary_maps_and_media.py
    ├── 10_build_master_database.py
    └── 11_fetch_pds_usgs_remote_sensing_rasters.py
```

---

## 💻 Interactive Command-Line Interface (`cli.py`)

The workspace includes a command-line tool for instant data retrieval:

### 1. Unified Full-Text Search (Sub-millisecond)
Search across all 11,000+ features, samples, missions, landing sites, and science targets:
```bash
# Search for water ice detections across all missions and sensors
python3 cli.py search "water ice"

# Search for Apollo 11 artifacts and samples
python3 cli.py search "Apollo 11"

# Search for Perseverance delta samples
python3 cli.py search "Jezero delta"
```

### 2. IAU Planetary Features
Query official USGS/IAU nomenclature by body, type, diameter, or quadrangle:
```bash
# Find the largest craters on Mars
python3 cli.py features --body Mars --type Crater --min-diam 200

# Explore lunar volcanic maria
python3 cli.py features --body Moon --type Mare
```

### 3. Space Missions & Surface Landing Sites
```bash
# List all Mars missions launched by NASA or ESA
python3 cli.py missions --body Mars --agency NASA

# List all soft landers, rovers, and impact sites with coordinates
python3 cli.py sites
```

### 4. Lunar Samples & Martian Meteorites
```bash
# Query pristine Apollo 17 basalt samples over 500 grams
python3 cli.py samples --mission "Apollo 17" --rock-class Basalt --min-weight 500

# List rare Martian meteorites (Shergottites, Nakhlites, Chassignites)
python3 cli.py meteorites --classification Nakhlite
```

### 5. Physical Constants & Comparison Matrix
```bash
# Display comparative physical constants table (Moon vs Mars vs Earth)
python3 cli.py compare

# Inspect in-situ Martian surface weather logs
python3 cli.py weather

# Inspect polar and buried water ice reservoirs
python3 cli.py ice
```

### 6. Remote Sensing Rasters & Endpoints (`cli.py rasters`)
Direct endpoints, bounding boxes, and resolutions from NASA PDS, USGS Astrogeology ARD, JAXA DARTS, and ESA PSA:
```bash
# Query Lunar Digital Elevation Models (LOLA & Kaguya TC)
python3 cli.py rasters --body Moon --category "DEM"

# Query candidate Mars landing zone rasters (Jezero, Gale, Arcadia)
python3 cli.py rasters --target Jezero
python3 cli.py rasters --target Arcadia

# Query volatile & mineral detections (M3, CRISM, Odyssey GRS)
python3 cli.py rasters --category "Volatiles"

# Query thermal inertia and solar illumination maps
python3 cli.py rasters --category "Thermal"
```

---

## 🔬 Core Scientific Domains Covered

### 1. IAU Planetary Nomenclature
Contains all **11,139 official features** recognized by the International Astronomical Union:
* **The Moon (9,087 features)**: Craters, maria, montes, rimae, dorsa, catenae, and lacus.
* **Mars (2,052 features)**: Craters, chasmata (canyons), planitiae, tholi, valles, fossae, and mensae.
* Normalized coordinate networks (East Longitude and [-180, +180] longitude), bounding boxes, approval dates, USGS reference URLs, and biographical origins.

### 2. Returned Lunar Samples Catalog
Contains all **2,516 returned lunar sample specimens**:
* All **2,511 Apollo 11, 12, 14, 15, 16, and 17 samples** from the NASA JSC Curatorial Facility with sample IDs, weights in grams, pristine fractions (%), rock classes, subclasses, collection stations, and compendium links.
* Soviet **Luna 16, 20, and 24** drill cores from Mare Fecunditatis, Apollonius highlands, and Mare Crisium.
* Chinese **Chang'e 5** young basalts (2.03 Ga) from Northern Oceanus Procellarum and **Chang'e 6** historic far-side samples (1,935.3 g) from the South Pole-Aitken Basin.

### 3. Martian Meteorites (SNCs & Ancient Crust)
Directly ingested from the **NASA JSC Mars Meteorite Compendium**:
* 51 meteorite specimens spanning Basaltic Shergottites, Olivine-Phyric Shergottites, Lherzolites, Nakhlites, Chassignites, Orthopyroxenite (**ALH84001**, 4.09 Ga ancient crust), and Polymict Breccias (**NWA 7034 / "Black Beauty"**).
* Complete geochemical major oxide assays (SiO2, TiO2, Al2O3, FeO, MnO, CaO, MgO, Na2O, K2O, P2O5) and rare-earth trace elements (ppm).

### 4. Space Exploration Missions & Surface Hardware
* Complete registry of 40 landmark Moon and Mars missions from 1958 to 2026 across NASA, USSR/Roscosmos, ESA, ISRO, CNSA, JAXA, and commercial CLPS providers.
* Surface coordinate registry of 23 landing, rover egress, and impact sites (e.g. Tranquillity Base, Shiv Shakti Point, Bradbury Landing, Octavia E. Butler Landing, Three Forks Sample Depot) including surface hardware inventories.

### 5. In-Situ Rover Science Drill Targets
* **Curiosity (MSL)**: John Klein, Cumberland, Windjana, Confidence Hills, Buckskin, Kilmarie, Mary Anning (mudstones, clay-bearing units, tridymite, organic sulfur compounds, and K-Ar geochronology).
* **Perseverance (Mars 2020)**: Montdenier, Salette, Swift Run, Bearwallow, Cheyava Falls (delta-front organic detections, olivine cumulates, "leopard spots" redox alteration halos, sealed sample cache tubes).

### 6. Geophysics, Internal Structure & Stratigraphy
* InSight SEIS and Apollo Passive Seismic Experiment models: core radiuses (Mars liquid Fe-Ni-S core: ~1,830 km; Moon core: ~330 km outer liquid + ~240 km inner solid), crustal thicknesses, and mantle partial-melt zones.
* Chronostratigraphy:
  * **Moon**: Pre-Nectarian, Nectarian, Early Imbrian, Late Imbrian, Eratosthenian, Copernican.
  * **Mars**: Pre-Noachian, Noachian, Hesperian, Amazonian.

### 7. Polar & Subsurface Water Ice Reservoirs
* Lunar permanently shadowed cold traps (Cabeus, Shackleton, Faustini, Shoemaker, Hermite crater at 26 K).
* Martian North (NPLD) and South (SPLD) polar layered deposits (1.6 million km³ ice each), mid-latitude lobate debris aprons (SHARAD radar >80% purity), and the Medusae Fossae Formation.

### 8. Remote Sensing Scientific Rasters & Endpoints
Integrated direct download endpoints across four critical planetary domains:
1. **Digital Elevation Models (DEM/DHM)**:
   * **Moon**: LRO LOLA Cylindrical Global DEM (128 ppd, ~237 m), LOLA South Pole Polar Stereographic DEM (20 m/pix, 80°S-90°S), LOLA EDR Altimeter laser profile tracks, JAXA Kaguya TC Seamless DTM v2.0 (8.42 m/pix), and USGS Astrogeology Kaguya TC Polar Cloud-Optimized GeoTIFF (10.3 m/pix).
   * **Mars**: MGS MOLA MEGDR Global Topography (128 ppd, 463 m/pix), MOLA South Polar Stereographic Model (512 ppd, 115 m/pix), and Mars Express HRSC Multi-line Stereo Level 4 DTMs (50 m/pix) and Nadir Orthoimages.
2. **High-Resolution Imagery & Slope Maps**:
   * **Moon (Polar Regions)**: LROC NAC Shackleton Connecting Ridge DTM (3.5 m) & Slope Angle Map (0°-90°), Malapert Massif Summit DTM (4.0 m) & Slope Map, and Faustini Crater Sub-Meter Polar Orthomosaics (1.0 m/pix).
   * **Mars (Candidate Landing Zones)**: HiRISE DTMs (1.0 m/pix) and Color Relief Orthos for **Jezero Crater** (Perseverance), **Gale Crater** (Curiosity Mount Sharp traverse), and **Arcadia Planitia** (shallow sheet ice); controlled CTX regional mosaics (6.0 m) and geoid-adjusted DTMs (20 m).
3. **Resource & Volatiles Distribution**:
   * **Moon**: Lunar Prospector Epithermal & Thermal Neutron Spectrometer maps (0.5°/pix, water-equivalent hydrogen proxy); Chandrayaan-1 Moon Mineralogy Mapper (M3) Level 2 calibrated surface reflectance hypercubes (85 continuous bands, 430-3000 nm, 140 m/pix) detecting the 2.8-3.0 µm OH/H2O absorption features across sunlit regolith and permanently shadowed polar craters.
   * **Mars**: Mars Odyssey GRS/MONS Global Water-Equivalent Hydrogen (WEH wt%) maps (300 km/pix, detecting up to 50-70 wt% ice poleward of 60°); MRO CRISM MTRDR summary parameter cubes (18 m/pix) containing targeted indices `SINDEX` (sulfates), `BD1900` (water), `BD2100` (monohydrated sulfates), and `D2300` (phyllosilicates) at Jezero Crater and Gale Crater.
4. **Thermal & Illumination Regimes**:
   * **Moon**: LRO Diviner Polar Cumulative Product (PCP) seasonal bolometric brightness temperatures (240 m/pix, identifying cryogenic micro cold-traps < 40 K); LRO LOLA South Pole Solar Visibility & Illumination maps (240 m/pix, mapping Peaks of Eternal Light with > 85-92% annual sunlight).
   * **Mars**: 2001 Mars Odyssey THEMIS geodetically controlled daytime and nighttime infrared mosaics (100 m/pix) across **Syrtis Major (Jezero)**, **Aeolis (Gale)**, **Diacria**, and **Arcadia Planitia**, providing direct proxies for surface thermal inertia, dust mantling, and bedrock induration.

---

## 🛠️ Python Programming Interface (API)

```python
import sqlite3
import pandas as pd

# Connect to the master database
conn = sqlite3.connect("planetary_moon_mars.db")

# Example 1: Read Apollo 17 samples into a pandas DataFrame
df_apollo = pd.read_sql_query("""
    SELECT sample_id, rock_class, rock_subclass, weight_grams, pristine_percent 
    FROM lunar_samples_catalog 
    WHERE mission = 'Apollo 17' AND weight_grams > 500
    ORDER BY weight_grams DESC;
""", conn)
print(df_apollo.head())

# Example 2: Sub-millisecond Full-Text Search
df_search = pd.read_sql_query("""
    SELECT entity_type, title, category, content 
    FROM fts_planetary_search 
    WHERE fts_planetary_search MATCH 'perchlorate'
    LIMIT 10;
""", conn)
print(df_search)

# Example 3: Stream Cloud-Optimized GeoTIFFs (COGs) with Rasterio & GDAL (No full download needed)
# import rasterio
# cog_url = "https://astrogeo-ard.s3-us-west-2.amazonaws.com/moon/kaguya/terrain_camera/usgs_dtms_v2/TC2W2B0_01_07536S736E2606__TC1W2B0_01_07536S733E2605/TC2W2B0_01_07536S736E2606__TC1W2B0_01_07536S733E2605-DEM.tif"
# with rasterio.open(f"/vsicurl/{cog_url}") as src:
#     print(f"Profile: {src.profile}, CRS: {src.crs}, Resolution: {src.res}")
#     window_data = src.read(1, window=((0, 500), (0, 500)))

# Example 4: Load directly from Apache Parquet
# df_rasters = pd.read_parquet("data/processed/parquet/remote_sensing_rasters.parquet")
# df_features = pd.read_parquet("data/processed/parquet/iau_features.parquet")
```

---

## 📜 Credible Sources & Primary References
1. **USGS Astrogeology Science Center**: *Gazetteer of Planetary Nomenclature*, Working Group for Planetary System Nomenclature (WGPSN), International Astronomical Union (IAU).
2. **NASA GSFC NSSDC**: Planetary Fact Sheets, Dr. David R. Williams (NASA Goddard Space Flight Center).
3. **NASA JPL Horizons System**: Solar System Dynamics Group, Ephemeris DE441 / SSD API.
4. **NASA JSC Astromaterials Curation**: *Apollo Lunar Sample Database* & *Mars Meteorite Compendium (MMC)*, Curatorial Facility, Johnson Space Center.
5. **NASA PDS Geosciences Node / CAB**: InSight Mars Weather Service (APSS), MSL REMS, Mars 2020 MEDA.
6. **LROC & MRO Teams**: Lunar Reconnaissance Orbiter Camera (ASU) and HiRISE/CTX (University of Arizona / JPL).

