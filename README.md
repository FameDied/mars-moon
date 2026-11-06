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

| Table / View Name | Description | Records |
| :--- | :--- | :---: |
| `celestial_bodies` | Moon, Mars, Phobos, Deimos body registry & discovery histories | **4** |
| `physical_parameters` | Geodetic, bulk physical, gravity, optical, and thermal constants | **42** |
| `orbital_parameters` | Orbital elements, velocities, periods, and rotational dynamics | **55** |
| `ephemerides_2026` | High-precision JPL Horizons ephemerides (state vectors, magnitudes, distances) | **146** |
| `iau_planetary_features` | Complete IAU official named surface features (craters, maria, montes, valleys) | **11,138** |
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
| `remote_sensing_rasters` | Direct PDS/USGS/JAXA/ESA science rasters, DTMs, GeoTIFFs, and spectral cubes | **43** |
| `site_candidate_matrix` | Comprehensive 43-parameter engineering, environmental & operational trade-space table | **57** |
| `site_engineering_safety` | Upgraded 44-column multi-domain site safety table (GNC, tectonics, cryo, dust, radiation, COSPAR, ISRU) | **57** |
| `lander_engineering_constraints` | Flight vehicle envelopes (Starship, Nova-C, Sky Crane, Apollo LM) & EDL limits | **18** |
| `v_lander_site_compatibility` | Dynamic evaluation join view matching landers to candidate exploration zones | **522** |
| `regolith_geotechnics_psi` | Soil mechanics (cohesion, friction angle, bearing capacity) & plume blast erosion | **9** |
| `telecom_relay_visibility` | Earth LoS libration angles, DSN visibility windows & Mars orbiter relay passes | **10** |
| `rock_hazard_sfd` | Rock Size-Frequency Distributions (SFD), Golombek q, tip-over probability & CPR | **10** |
| `v_site_gnc_optical_gravity` | **Domain 1 View**: TRN visual entropy, glare risk, GRAIL/MRO Bouguer & free-air gravity | **57** |
| `v_site_active_tectonics_seismology` | **Domain 2 View**: Lobate fault scarps, shallow moonquake/marsquake PGA & landslides | **57** |
| `v_site_power_cryo_thermal` | **Domain 3 View**: Worst-case continuous night (18.6-yr cycle), min winter temp, thermal plunge | **57** |
| `v_site_dust_charging_magnetics` | **Domain 4 View**: Crustal magnetic fields, terminator voltage (-200V to -4000V), dust levitation | **57** |
| `v_site_radiation_topographic_shielding` | **Domain 5 View**: Sky-View Factor (SVF 0-2π sr), annual GCR dose, albedo neutrons, lava tubes | **57** |
| `v_site_mars_atmospheric_dynamics` | **Domain 6 View**: MCD v5.3 99% gusts, mesoscale wind shear, dust optical depth, dust deposition | **57** |
| `v_site_planetary_protection_heritage` | **Domain 7 View**: COSPAR category (II, IVa, IVb, Special Region), historic buffers, plume risk | **57** |
| `v_site_isru_feedstock_toxicity` | **Domain 8 View**: Ilmenite TiO2, FeO, Solar Wind He-3, bound H2O, ClO4- perchlorates | **57** |
| `v_site_traverse_science_paradox` | **Domain 9 View**: Distance to science, Bekker-Wong rover traverse energy, epoch diversity | **57** |
| `fts_planetary_search` | SQLite FTS5 unified search index across all features, samples, missions & safety | **13,993** |
| **Total Database Records** | **Comprehensive Planetary Science, EDL Engineering & Multidisciplinary Safety Index** | **28,795** |

---

## 🗂️ Directory Architecture

```
NASA lol/
├── README.md                              <- Full documentation & schema manual
├── cli.py                                 <- Interactive Python CLI for querying & filtering
├── query_examples.py                      <- Standalone query demonstration suite
├── planetary_moon_mars.db                 <- Master SQLite 3 database with FTS5 search (11.9 MB)
├── data/
│   ├── raw/                               <- Downloaded raw archives from USGS and NASA
│   │   ├── usgs/                          <- Shapefiles & metadata (Moon & Mars nomenclature)
│   │   ├── nasa/                          <- NSSDC HTML fact sheets & JPL Horizons cards
│   │   └── jsc/                           <- Apollo sample HTML & Martian Meteorite Compendium XLS
│   ├── processed/
│   │   ├── csv/                           <- 32 tabular CSV exports (including 9 domain views, safety & landers)
│   │   ├── json/                          <- 33 structured JSON files (including 9 domain views, safety & landers)
│   │   └── parquet/                       <- 32 Snappy-compressed Apache Parquet tables
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
    ├── 11_fetch_pds_usgs_remote_sensing_rasters.py
    └── 12_build_engineering_safety_and_edl.py
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

### 7. Landing Site Engineering Safety Evaluator (`cli.py safety`)
Evaluate candidate landing zones across 9 specialized engineering, environmental & scientific views, or generate full vehicle-site dossiers:
```bash
# 1. Physical safety summary (slope, elevation, rocks, DTE LoS comms, ice overburden, plume scour)
python3 cli.py safety --body Moon --max-slope 10 --max-rocks 5 --min-dte 0.70
python3 cli.py safety --body Mars --max-elevation -1500 --max-slope 5 --max-rocks 7

# 2. GNC & Optical Navigation: TRN visual entropy & GRAIL/MRO gravity anomalies
python3 cli.py safety --view gnc --min-trn 0.70

# 3. Active Tectonics & Seismic Hazard: Lobate thrust scarps & Peak Ground Acceleration (PGA)
python3 cli.py safety --view tectonics --max-pga 0.20

# 4. Power & Cryogenic Survival: Worst-case continuous night hours (18.6-yr cycle) & thermal drop
python3 cli.py safety --view thermal --max-night-hours 120 --min-temp 80

# 5. Dust Levitation & Surface Charging: Crustal magnetic anomalies & terminator potential
python3 cli.py safety --view dust

# 6. Topographic Radiation Shielding: Sky-View Factor (SVF 0 to 2π sr) & annual GCR doses
python3 cli.py safety --view radiation --max-radiation 350

# 7. Mars Atmospheric Dynamics: MCD 99% gusts, vertical wind shear & dust deposition
python3 cli.py safety --view atmosphere

# 8. Legal, Heritage & Planetary Protection: COSPAR categories & historic Apollo/Luna buffers
python3 cli.py safety --view protection --cospar "Category IVb"

# 9. ISRU Feedstock & Chemical Toxicity: Ilmenite TiO2, FeO, Solar Wind He-3 & ClO4- perchlorates
python3 cli.py safety --view isru --min-tio2 5.0 --min-he3 10.0

# 10. Science-vs-Safety Paradox: Rover traverse energy (Wh/km), stand-off distance & diversity
python3 cli.py safety --view science --max-dist-science 5.0 --min-diversity 3

# 11. Complete 9-Domain Full Flight Specification Dossier for candidate landing zones
python3 cli.py safety --view all --site "Shackleton"
python3 cli.py safety --view all --site "Jezero"
```

### 8. Flight Vehicle Engineering Envelopes (`cli.py landers`)
Query engineering envelopes across prominent lunar and Martian landers:
```bash
# Inspect lunar landers (Starship HLS, Nova-C, Blue Moon MK1/MK2, Apollo LM, Chandrayaan-3)
python3 cli.py landers --body Moon

# Query Mars EDL vehicle systems (Perseverance Sky Crane, InSight, Viking, Airbags)
python3 cli.py landers --body Mars
```

### 9. Regolith Geotechnics & Plume-Surface Interaction (`cli.py geotechnics`)
Query soil mechanics, internal friction angle ($\phi$), cohesion ($c$), bearing capacity, and blast scour:
```bash
# Inspect all lunar and Martian geotechnical terrains
python3 cli.py geotechnics

# Filter by candidate terrain
python3 cli.py geotechnics --terrain "Permafrost"
```

### 10. Direct-to-Earth (DTE) LoS & Orbiter Relay Windows (`cli.py telecom`)
Query Earth line-of-sight elevation angles and Mars orbiter relay passes:
```bash
# Inspect telecommunication profiles across Moon and Mars
python3 cli.py telecom

# Filter by high Earth visibility fraction (>= 80%)
python3 cli.py telecom --min-dte 0.80
```

### 11. Rock Size-Frequency Distribution & Boulder Hazards (`cli.py hazards`)
Query Diviner/THEMIS rock abundance ($k$), mean rock height, exponential SFD slope ($q$), and tip-over risks:
```bash
# Inspect rock hazard parameters across landmark sites
python3 cli.py hazards

# Filter for low-hazard landing sites (< 5% rock abundance)
python3 cli.py hazards --max-rocks 5.0
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

### 9. Direct Line-of-Sight (LoS) Earth & DSN Telecommunications Visibility
* **Lunar South Pole Libration & Horizon Obscuration**: Models Earth elevation angles across the 18.6-year lunar precessional cycle against LOLA 20 m/pixel polar horizon masks. High ridge crests (Malapert Massif >94%, Shackleton Connecting Ridge >86%, de Gerlache rim >84%) provide continuous line-of-sight to NASA's Deep Space Network (DSN Goldstone, Madrid, Canberra), whereas crater floors (Cabeus, Shackleton PSR, Haworth) lie in permanent RF comms shadow (0.00 visibility fraction), requiring dedicated relay orbiters (e.g., ESA Lunar Pathfinder, Lunar Gateway).
* **Mars Orbiter Relay Pass Windows**: Quantifies daily UHF Proximity-1 overflight contacts for landed surface assets across MRO (3:00 PM sun-synchronous), ExoMars TGO (400 km circular), Mars Odyssey, and MAVEN. Features pass frequencies (4.8 to 6.1 passes/sol), average pass durations (11.8 to 13.5 minutes), and daily data return envelopes (240 to 520 Mbit/sol), accounting for terrain masking and biennial solar conjunction blackouts.

### 10. Hazard Density: Rock Size-Frequency Distribution (SFD) & Crater Roughness
* **Sub-Resolution Boulders vs Macro-Slope**: 20 m/pixel LOLA or 50 m/pixel HRSC DEMs resolve macro-slope, but 1–2 meter tall lander legs are vulnerable to boulders $>0.5 - 1.0\text{ m}$ causing vehicle puncture or tip-over.
* **Empirical SFD Parameterization**: Integrates fractional rock abundance ($k$ or $R_{area} \%$) derived from **LRO Diviner Lunar Radiometer Experiment** (Channels 6, 7, 8 nocturnal radiance) for the Moon and **MGS TES / Mars Odyssey THEMIS** thermal infrared deconvolution for Mars. Includes Golombek exponential decay slope exponents ($q$), cumulative boulder densities ($N_{>0.5m}$ and $N_{>1.0m}$ per m²), lander tip-over probabilities, and radar Circular Polarization Ratios (CPR). Benchmark threshold: $R_{area} \le 7.0\%$ is required for safe landing operations.

### 11. Landing Dynamics & Entry, Descent, and Landing (EDL) Envelopes
* **Flight Vehicle Constraints (`lander_engineering_constraints`)**: Detailed aerospace envelopes for 18 flight systems: SpaceX Starship HLS, Intuitive Machines Nova-C, Blue Origin Blue Moon MK1 & MK2, Astrobotic Griffin / VIPER, Apollo Lunar Module, Surveyor, Chang'e 5/6, Chandrayaan-3 Vikram, SLIM, Mars 2020 Perseverance Sky Crane, MSL Curiosity Sky Crane, InSight, Viking Landers 1 & 2, Mars Pathfinder, MER Spirit/Opportunity, ExoMars Rosalind Franklin, and Tianwen-1 Zhurong.
* **Mars EDL Atmospheric Scale Height Datum Constraint**: Supersonic parachute deployment and aerodynamic aerobraking deceleration require sufficient atmospheric column density ($m_{air} = \int \rho \, dz$). Landing sites must sit at elevations **$\le -1,500\text{ m}$ to $-2,000\text{ m}$ below the MOLA datum** (e.g. Jezero Delta at $-2,530\text{ m}$, Gale Crater at $-4,500\text{ m}$, Arcadia Planitia at $-4,280\text{ m}$, Oxia Planum at $-3,050\text{ m}$). High plateaus (e.g. Olympus Mons at $+21,287\text{ m}$ or Tharsis volcanic rises) are physically disqualified for parachute landing systems due to thin air (~0.5 mbar).

### 12. Regolith Geotechnics & Plume-Surface Interaction (PSI)
* **Soil Mechanics & Bearing Capacity**: Quantifies regolith bulk density ($\rho = 1.15 - 1.65\text{ g/cm}^3$), porosity ($38 - 62\%$), cohesion ($c = 0.10 - 1.80\text{ kPa}$), and internal friction angle ($\phi = 32^\circ - 43.5^\circ$) based on Apollo core tubes, penetrometer measurements, Viking surface samplers, and InSight HP3 mole penetration. Calculates ultimate bearing capacity ($q_{ult} = 15 - 110\text{ kPa}$) using Terzaghi's bearing capacity formulation.
* **Dust Mantling & THEMIS Fine Thermal Inertia**: Incorporates THEMIS fine-component thermal inertia ($I_{fine}$) and Diviner thermal inertia. Low thermal inertia ($<100\text{ J m}^{-2}\text{ K}^{-1}\text{ s}^{-1/2}$) identifies deep, unconsolidated airfall dust mantles with severe scouring and sinkage risks. High thermal inertia ($>250\text{ SI}$) indicates armored duricrust and pebble pavement.
* **Rocket Plume Scouring & Blast Ejecta**: Parameterizes gas-surface shear velocity thresholds ($u_{*th}$), viscous erosion rates ($2.1 - 22.0\text{ kg/m}^2\text{s}$), and Plume Scour Risk Indexes ($0.0 - 1.0$) to evaluate sensor brownout, regolith trenching, and high-velocity horizontal sandblasting of nearby landing pads.

### 13. Upgraded Schema: `site_engineering_safety` (44 Multi-Domain Parameters)
Integrates pre-computed physical terrain safety constraints, GNC optical/gravity metrics, active tectonic hazards, cryogenic night limits, electrostatic dust levitation, topographic radiation shielding, Mars atmospheric dynamics, COSPAR/heritage protections, ISRU feedstocks, and rover traverse science costs:
```sql
CREATE TABLE site_engineering_safety (
    feature_id INTEGER PRIMARY KEY,
    body TEXT NOT NULL,
    site_name TEXT NOT NULL,
    center_lat REAL,
    center_lon REAL,
    
    -- Base Physical & Geodetic Terrain Parameters
    macro_slope_deg REAL,                      -- LOLA/MOLA DEM macro-slope (<= 10 deg safe)
    elevation_mola_m REAL,                     -- LOLA / MOLA elevation (< -1500m required for Mars EDL)
    rock_abundance_percent REAL,               -- Diviner / THEMIS rock abundance (< 7% safe)
    dte_visibility_fraction REAL,              -- Direct-to-Earth DSN line-of-sight (0.0 to 1.0)
    ice_overburden_depth_m REAL,               -- SHARAD / CRISM / Diviner (< 1.0m accessible)
    plume_scour_risk_index REAL,               -- Viscous erosion / sensor brownout risk (0.0 to 1.0)
    
    -- Domain 1: GNC & Optical Navigation
    trn_visual_entropy_score REAL,             -- 0.0 (featureless/blind) to 1.0 (ideal LVS correlation)
    solar_incidence_glare_risk TEXT,           -- 'Low', 'Moderate', 'High', 'Severe' (Zero-phase opposition surge)
    free_air_gravity_anomaly_mgal REAL,        -- GRAIL JGL1500P / MRO GMM-3 free-air gravity (mGal)
    bouguer_gravity_anomaly_mgal REAL,         -- Bouguer gravity anomaly (mascon crustal loading)
    local_vertical_deflection_arcsec REAL,     -- Astro-geodetic vertical plumb-line deflection (arcsec)
    
    -- Domain 2: Active Tectonics & Seismic Hazard
    nearest_fault_scarp_dist_km REAL,          -- Distance to youngest lobate thrust scarp or Cerberus graben
    peak_ground_acceleration_pga_g REAL,       -- Modeled Peak Ground Acceleration (g) from M5.5 moonquakes
    landslide_runout_susceptibility TEXT,      -- 'Low', 'Moderate', 'High', 'Extreme'
    
    -- Domain 3: Power & Cryogenic Survival
    max_continuous_night_hours REAL,           -- Worst-case single continuous eclipse duration over 18.6-yr cycle
    min_winter_bolometric_temp_k REAL,         -- Diviner / TES minimum winter surface temperature (K)
    diurnal_thermal_shock_k_per_hr REAL,       -- Sunset cooling rate (K/hr) driving vehicle thermal fatigue
    
    -- Domain 4: Electrostatic Dust Levitation & Surface Charging
    crustal_magnetic_field_nt REAL,            -- LP / Kaguya / MGS crustal remanent magnetic field (nT)
    terminator_surface_potential_v REAL,       -- Day/night terminator electrostatic potential (-200V to -4000V)
    electrostatic_dust_levitation_risk TEXT,   -- 'Low', 'Moderate', 'High', 'Extreme'
    
    -- Domain 5: Radiation Shielding via Topographic Sky-View Factor (SVF)
    sky_view_factor_steradians REAL,           -- Topographic horizon sky exposure (0.0 to 2π sr = 6.283 sr)
    gcr_dose_equivalent_msv_yr REAL,           -- CRaTER / MSL RAD annual Galactic Cosmic Ray dose (mSv/yr)
    albedo_neutron_flux REAL,                  -- Relative secondary albedo neutron flux from high-Ti/Fe soils
    nearest_lava_tube_skylight_km REAL,        -- Proximity to natural subsurface lava tube radiation shelter
    
    -- Domain 6: Mars Atmospheric Dynamics & Dust Storms
    mcd_99pct_wind_gust_ms REAL,               -- Mars Climate Database v5.3 99th percentile wind gust (m/s)
    vertical_wind_shear_s_inv REAL,            -- Atmospheric boundary layer vertical wind shear (s⁻¹)
    climatological_dust_optical_depth_tau REAL,-- Climatological column dust optical depth (tau)
    annual_dust_deposition_rate_microns_sol REAL, -- Solar panel dust obscuration rate (microns/sol)
    
    -- Domain 7: Legal, Heritage & Planetary Protection Keep-Out Zones (COSPAR)
    cospar_planetary_protection_cat TEXT,      -- 'Category II', 'Category IVa', 'Category IVb', 'Special Region'
    heritage_exclusion_buffer_km REAL,         -- Radial buffer around historic artifacts (Apollo 11-17, Luna)
    plume_orbital_contamination_risk TEXT,     -- 'Low', 'Moderate', 'High', 'Critical'
    
    -- Domain 8: ISRU Feedstock & Chemical Toxicity
    fe_o_wt_pct REAL,                          -- Soil Iron Oxide content (wt%)
    ti_o2_ilmenite_wt_pct REAL,                -- Clementine / LRO WAC Ilmenite feedstock for carbothermal O2 (wt%)
    helium3_ppb REAL,                          -- Solar wind implanted Helium-3 abundance (ppb)
    perchlorate_toxicity_wt_pct REAL,          -- Soil toxic perchlorate ClO4- concentration (wt%)
    hydrated_mineral_bound_h2o_wt_pct REAL,    -- Thermally extractable water in hydrated clays/sulfates (wt%)
    
    -- Domain 9: The Science-vs-Safety Paradox & Trafficability
    distance_to_primary_science_km REAL,       -- Stand-off distance from safe landing flat to primary outcrop
    rover_traverse_energy_wh_per_km REAL,      -- Bekker-Wong soil sinkage + slope traverse energy cost (Wh/km)
    contact_stratigraphic_diversity_count INTEGER, -- Number of distinct geologic epochs within 10 km radius
    
    FOREIGN KEY(feature_id) REFERENCES iau_planetary_features(feature_id)
);
```

### 14. The 9 Multidisciplinary Planetary Engineering & Science Domains

The database provides 9 dedicated relational views and standardized datasets covering critical planetary exploration challenges:

#### Domain 1: GNC & Optical Navigation (`v_site_gnc_optical_gravity`)
* **Terrain Relative Navigation (TRN) Texture Entropy**: Modern autonomous landers (Perseverance Lander Vision System, Intuitive Machines Nova-C, Astrobotic Griffin, Starship HLS) capture real-time optical descent imagery and correlate surface features against pre-loaded orbital DEMs. Sites with low entropy (`trn_visual_entropy_score` $< 0.40$), featureless dust mantles, or extreme shadow dropout suffer optical correlation failure.
* **Solar Glare & Opposition Surge**: Low-elevation grazing sunlight near the lunar poles causes zero-phase opposition surge glare and blinding forward scatter (`solar_incidence_glare_risk`).
* **Mascons & Gravity Perturbations**: Subsurface mass concentrations (mascons) produce severe gravity anomalies mapped by **NASA GRAIL (JGL1500P)** for the Moon and **MRO (GMM-3)** for Mars (`free_air_gravity_anomaly_mgal`, `bouguer_gravity_anomaly_mgal`), generating local vertical plumb-line deflections (`local_vertical_deflection_arcsec`) exceeding 50–90 arcseconds that corrupt inertial guidance navigation filters if uncompensated.

#### Domain 2: Active Tectonics & Seismic Hazard (`v_site_active_tectonics_seismology`)
* **LROC Lobate Thrust Fault Scarps**: High-resolution LROC imagery identified thousands of geologically young (< 50 Ma) thrust faults formed as the lunar interior cools and contracts.
* **Shallow Moonquakes & Marsquakes**: Apollo Passive Seismic Experiment recorded shallow moonquakes reaching Magnitude 5.5 that lasted over 10 to 15 minutes due to the zero-attenuation, fractured crystalline regolith.
* **Seismic Risk & Landslide Runout**: Proximity to scarps (`nearest_fault_scarp_dist_km` $\le 5\text{ km}$, e.g. Apollo 17 near the Lee-Lincoln scarp) incurs high Peak Ground Acceleration (`peak_ground_acceleration_pga_g` up to $0.48\text{ g}$) and catastrophic crater-wall landslide runout hazards. On Mars, InSight SEIS confirmed active seismicity along the Cerberus Fossae graben system.

#### Domain 3: Power & Cryogenic Survival (`v_site_power_cryo_thermal`)
* **Continuous Shadow vs Annual Sunlight**: Spacecraft power architects size secondary batteries and thermal heaters for the single longest continuous blackout, not average annual illumination. Sites with >85% annual sunlight (e.g. Shackleton rim) still endure 54 to 96 hours of continuous eclipse during lunar nodal tilt extremes (`max_continuous_night_hours`). Equatorial sites endure 354.4 hours (14.7 Earth days), while polar cold traps (Cabeus, Hermite) reside in perpetual darkness (>163,000 hours).
* **Cryogenic Limits & Diurnal Thermal Shock**: Deep PSR floors plunge to $26 - 40\text{ K}$ (`min_winter_bolometric_temp_k`), requiring Radioisotope Heater Units (RHUs). The sunset temperature drop rate (`diurnal_thermal_shock_k_per_hr` up to $24.5\text{ K/hr}$) induces severe mechanical thermal fatigue on solar array substrates and lander landing gear.

#### Domain 4: Dust Levitation & Surface Charging (`v_site_dust_charging_magnetics`)
* **Photoemission & Plasma Wake Charging**: Solar UV and solar wind plasma induce strong photoelectric charging (+V) on sunlit surfaces, while crossing the day/night terminator or Earth's magnetotail charges regolith to large negative potentials (`terminator_surface_potential_v` from $-200\text{ V}$ down to $-4,000\text{ V}$).
* **Electrostatic Dust Levitation**: Micron-scale abrasive glass shards levitate tens of meters above the surface, adhering electrostatically to spacesuit fabrics, radiator panels, and optical sensors.
* **Crustal Magnetic Shielding**: Lunar magnetic swirls (e.g. Reiner Gamma at $240\text{ nT}$) and Martian crustal remanent magnetic fields locally deflect solar wind ions, forming miniature protective magnetospheres that reduce charging and weathering.

#### Domain 5: Radiation Shielding via Topographic Sky-View Factor (`v_site_radiation_topographic_shielding`)
* **Topographic Horizon Occlusion**: Deep impact craters and grabens naturally shield surface crews from Galactic Cosmic Rays (GCR) and Solar Energetic Particles (SEP) by blocking the celestial horizon (`sky_view_factor_steradians`, ranging from $0.0$ to $2\pi = 6.283\text{ sr}$). Craters reduce annual GCR doses from $380\text{ mSv/yr}$ down to $280\text{ mSv/yr}$.
* **Albedo Secondary Neutrons**: Regolith with high titanium and iron content undergoes spallation under high-energy cosmic rays, increasing the albedo neutron backscatter flux (`albedo_neutron_flux`).
* **Subsurface Lava Tube Skylights**: Proximity to volcanic pits and skylights (`nearest_lava_tube_skylight_km`, e.g. Marius Hills, Mare Tranquillitatis pit, Alba Mons) provides immediate access to natural rock overburdens offering 100% GCR and micrometeorite shielding.

#### Domain 6: Mars Atmospheric Dynamics & Dust Corridors (`v_site_mars_atmospheric_dynamics`)
* **Mesoscale Katabatic Winds & Shear**: Parachute deceleration and terminal descent thrusters are vulnerable to intense katabatic slope winds and vertical wind shear (`vertical_wind_shear_s_inv` $> 0.04\text{ s}^{-1}$) funneling off crater rims (Gale, Jezero) and canyon walls (Valles Marineris).
* **Global Dust Storm Tracks**: Major dust storm genesis and transit tracks (Acidalia, Utopia, Hellas) experience 99th percentile wind gusts (`mcd_99pct_wind_gust_ms` $> 35 - 55\text{ m/s}$), high dust optical depths (`climatological_dust_optical_depth_tau` up to $1.85$), and heavy annual dust deposition (`annual_dust_deposition_rate_microns_sol` up to $0.42\ \mu\text{m/sol}$) that rapidly degrades solar power arrays. (Values are $0.0$ for lunar vacuum sites).

#### Domain 7: Legal, Heritage & Planetary Protection Keep-Out Zones (`v_site_planetary_protection_heritage`)
* **COSPAR Planetary Protection Categories**: Categorizes landing sites under COSPAR policies:
  * **Category II**: Chemical and biological inventory only (Moon).
  * **Category IVa**: Mars landers without life-detection experiments.
  * **Category IVb / IVc**: Mars landers with life-detection investigations.
  * **Special Regions**: Zones where Earth microbes could replicate ($a_w > 0.60$ and $T > -25^\circ\text{C}$), including shallow ice sheets (Arcadia, Deuteronilus, Korolev) and Recurring Slope Lineae (Melas Chasma RSL). Human missions and unsterilized probes are legally prohibited from landing inside these regions.
* **Historic Artifact Keep-Out Buffers**: NASA "Recommendations to Spacefaring Entities" mandates radial exclusion buffers (`heritage_exclusion_buffer_km` up to $2.0\text{ km}$) surrounding historic Apollo 11–17, Surveyor, and Soviet Luna landing sites.
* **Rocket Plume Sandblasting & Orbital Ejection**: High-thrust vehicle exhaust (e.g. SpaceX Starship HLS) exceeds lunar escape velocity ($2.38\text{ km/s}$), injecting high-velocity regolith shards into low lunar orbit and sandblasting nearby heritage hardware or orbital assets (`plume_orbital_contamination_risk`).

#### Domain 8: ISRU Feedstock & Chemical Toxicity (`v_site_isru_feedstock_toxicity`)
* **Lunar Oxygen & Solar Wind Feedstocks**: Ilmenite ($\text{FeTiO}_3$) enables carbothermal and hydrogen reduction for in-situ oxygen extraction. High-Ti basalts (Mare Tranquillitatis $10.4\text{ wt}\%$, Taurus-Littrow $9.8\text{ wt}\%$) also trap the highest concentrations of solar-wind volatiles, including Helium-3 (`helium3_ppb` up to $18.5\text{ ppb}$) for future fusion applications.
* **Martian Perchlorate Toxicity**: Martian regolith contains $0.5\% - 0.85\%$ toxic perchlorates ($\text{ClO}_4^-$) detected by Phoenix and Curiosity (`perchlorate_toxicity_wt_pct`), which disrupt human thyroid endocrine function and embrittle EVA seals.
* **Hydrated Mineral Water Yield**: In non-polar regions, water is bound inside phyllosilicate clays and hydrated sulfates (polyhydrated sulfates in Mawrth and Eos Chasma yield $8 - 14\text{ wt}\%\ \text{H}_2\text{O}$ upon heating to $300^\circ\text{C}$).

#### Domain 9: The Science-vs-Safety Paradox & Trafficability (`v_site_traverse_science_paradox`)
* **Traverse Stand-Off Distance**: Landing engineers require flat, unblemished terrain, whereas planetary geologists require steep crater walls, layered canyon strata, and deltaic scarps. The database calculates the required rover stand-off traverse distance (`distance_to_primary_science_km`).
* **Bekker-Wong Soil Trafficability & Energy**: Computes rover energy consumption (`rover_traverse_energy_wh_per_km`) derived from Bekker-Wong wheel-sinkage equations and terrain slope. Flat hardpack requires $\sim 85\text{ Wh/km}$, whereas loose canyon slopes require $> 195\text{ Wh/km}$.
* **Stratigraphic Contact Diversity**: Quantifies geological return by counting how many distinct chronostratigraphic epochs intersect within a $10\text{ km}$ rover radius (`contact_stratigraphic_diversity_count`), highlighting sites like Jezero (4 epochs) and Mawrth Vallis (4 epochs).

---

### 15. Expanded Site Engineering, Environmental & Operational Trade-Space (`site_candidate_matrix`)
A multi-domain aerospace decision matrix containing 43 parameters across geodesy, aerodynamics, geotechnics, thermal survival, telecommunications, ISRU feedstock availability, and planetary protection:
```sql
CREATE TABLE site_candidate_matrix (
    site_id INTEGER PRIMARY KEY,
    feature_id INTEGER,
    body TEXT NOT NULL,                        -- 'Moon' or 'Mars'
    program_catalog TEXT NOT NULL,             -- 'Artemis_III', 'CLPS', 'Mars_HLS2_EZ', 'M2020_Candidate'
    site_name TEXT NOT NULL,
    region_parent TEXT,                        -- e.g., 'Malapert Massif' or 'Syrtis Major'
    center_lat REAL NOT NULL,
    center_lon REAL NOT NULL,
    
    -- 1. Geodesy & EDL Aerodynamics / GNC
    elevation_datum_m REAL,                    -- LOLA / MOLA elevation (Mars needs <= -1500m)
    macro_slope_100m_deg REAL,                 -- 100m baseline slope
    micro_slope_5m_deg REAL,                   -- Lander leg span slope (NAC / HiRISE DTM)
    trn_optical_entropy_score REAL,            -- 0.0 (featureless/blind) to 1.0 (ideal LVS landmarks)
    bouguer_gravity_anomaly_mgal REAL,         -- GRAIL / MRO gravity perturbation on descent trajectory
    mcd_99pct_wind_shear_ms REAL,              -- Mars mesoscale wind gust hazard (NULL for Moon)
    
    -- 2. Surface Hazards & Geotechnics
    rock_abundance_pct REAL,                   -- Diviner / THEMIS (>7% high risk)
    golombek_sfd_q REAL,                       -- Exponential boulder distribution exponent
    prob_1m_boulder_in_footprint REAL,         -- Monte Carlo tip-over probability (0.0 to 1.0)
    bearing_capacity_kpa REAL,                 -- Terzaghi ultimate bearing capacity
    plume_scour_risk_index REAL,               -- Viscous erosion / sensor brownout risk (0.0 to 1.0)
    nearest_active_fault_km REAL,              -- Proximity to Lunar Lobate Scarps or Cerberus Fossae
    seismic_pga_hazard_g REAL,                 -- Estimated Peak Ground Acceleration
    
    -- 3. Illumination, Thermal & Radiation Environment
    annual_sunlight_fraction REAL,             -- 0.00 to 1.00
    max_continuous_eclipse_hrs REAL,           -- CRITICAL battery/survival sizing metric
    min_bolometric_temp_k REAL,                -- Diviner / TES minimum surface temperature
    max_bolometric_temp_k REAL,
    sky_view_factor_sr REAL,                   -- Horizon terrain shielding (Steradians of open sky)
    radiation_dose_msv_yr REAL,                -- CRaTER / RAD modeled surface dose
    crustal_mag_field_nt REAL,                 -- Local magnetic anomaly shielding / swirl
    terminator_charging_volts REAL,            -- Electrostatic dust levitation potential
    
    -- 4. Telecoms
    dte_visibility_fraction REAL,              -- Direct-to-Earth DSN line-of-sight
    relay_data_volume_mbit_sol REAL,           -- MRO/TGO/LRO daily relay throughput
    
    -- 5. ISRU Resources & Chemical Hazards
    ice_overburden_depth_m REAL,               -- Depth to stable water ice (SHARAD / Neutron)
    water_equiv_hydrogen_wt_pct REAL,          -- MONS / LP-NS / M3 wt% H2O
    ilmenite_ti_o2_wt_pct REAL,                -- Lunar O2 production feedstock
    hydrated_mineral_wt_pct REAL,              -- Martian clays/sulfates (CRISM)
    perchlorate_toxicity_wt_pct REAL,          -- Martian ClO4- chemical hazard
    subsurface_dielectric_permittivity REAL,   -- SHARAD/LRS radar real permittivity (density/ice proxy)
    
    -- 6. Science Value, Trafficability & Legal Compliance
    distance_to_science_target_km REAL,        -- Distance from safe flat pad to geologic contact
    traverse_slope_cost_wh_km REAL,            -- Rover energy expenditure to reach science target
    stratigraphic_epochs_accessible INT,       -- Number of geologic units within 10km radius
    nearest_skylight_cave_km REAL,             -- Distance to known lava tube pit
    cospar_protection_category TEXT,           -- 'Category_II', 'Category_IVa', 'Special_Region_Restricted'
    heritage_keepout_violation BOOLEAN,        -- True if within 2km of Apollo/historic lander
    
    FOREIGN KEY(feature_id) REFERENCES iau_planetary_features(feature_id)
);
```

### 16. Dynamic Sub-Orbital Plume & Lander Vehicle Compatibility (`v_lander_site_compatibility`)
Dynamic evaluation view joining candidate exploration zones and aerospace constraints:
```sql
CREATE VIEW v_lander_site_compatibility AS
SELECT 
    s.body,
    s.site_name,
    s.program_catalog,
    l.vehicle_name,
    l.agency_provider,
    CASE 
        WHEN s.micro_slope_5m_deg > l.max_touchdown_slope_deg THEN 'FAIL: Slope Exceeds Gear Limit'
        WHEN s.body = 'Mars' AND s.elevation_datum_m > l.max_mola_elevation_m THEN 'FAIL: Insufficient Atmospheric Density'
        WHEN s.max_continuous_eclipse_hrs > l.max_eclipse_survival_hrs THEN 'FAIL: Freezes During Night/Eclipse'
        WHEN s.rock_abundance_pct > l.max_rock_abundance_pct THEN 'FAIL: Boulder Clearance Exceeded'
        WHEN s.bearing_capacity_kpa < l.min_footpad_bearing_kpa THEN 'FAIL: Footpad Sinkage Risk'
        WHEN s.heritage_keepout_violation = 1 THEN 'FAIL: Historic Site Keep-Out Buffer'
        ELSE 'QUALIFIED'
    END AS qualification_status
FROM site_candidate_matrix s
JOIN lander_engineering_constraints l ON s.body = l.body;
```

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
# df_safety = pd.read_parquet("data/processed/parquet/site_engineering_safety.parquet")

# Example 5: Multi-Variable Landing Site Engineering Evaluation
df_safe_sites = pd.read_sql_query("""
    SELECT s.body, s.site_name, s.macro_slope_deg, s.elevation_mola_m,
           s.rock_abundance_percent, s.dte_visibility_fraction, s.ice_overburden_depth_m
    FROM site_engineering_safety s
    WHERE (s.body = 'Moon' AND s.macro_slope_deg <= 10.0 AND s.rock_abundance_percent <= 5.0 AND s.dte_visibility_fraction >= 0.70)
       OR (s.body = 'Mars' AND s.elevation_mola_m <= -1500.0 AND s.macro_slope_deg <= 5.0 AND s.rock_abundance_percent <= 7.0)
    ORDER BY s.body, s.macro_slope_deg ASC;
""", conn)
print(df_safe_sites.head(10))

# Example 6: Cross-Domain GNC, Seismic Safety & ISRU Optimization
df_optimal = pd.read_sql_query("""
    SELECT gnc.site_name, gnc.trn_visual_entropy_score, tec.peak_ground_acceleration_pga_g,
           isru.ti_o2_ilmenite_wt_pct, isru.helium3_ppb, prot.cospar_planetary_protection_cat
    FROM v_site_gnc_optical_gravity gnc
    JOIN v_site_active_tectonics_seismology tec ON gnc.feature_id = tec.feature_id
    JOIN v_site_isru_feedstock_toxicity isru ON gnc.feature_id = isru.feature_id
    JOIN v_site_planetary_protection_heritage prot ON gnc.feature_id = prot.feature_id
    WHERE gnc.trn_visual_entropy_score >= 0.65
      AND tec.peak_ground_acceleration_pga_g <= 0.25
    ORDER BY isru.ti_o2_ilmenite_wt_pct DESC;
""", conn)
print(df_optimal.head(10))
```

---

## 📜 Credible Sources & Primary References
1. **USGS Astrogeology Science Center**: *Gazetteer of Planetary Nomenclature*, Working Group for Planetary System Nomenclature (WGPSN), International Astronomical Union (IAU).
2. **NASA GSFC NSSDC**: Planetary Fact Sheets, Dr. David R. Williams (NASA Goddard Space Flight Center).
3. **NASA JPL Horizons System**: Solar System Dynamics Group, Ephemeris DE441 / SSD API.
4. **NASA JSC Astromaterials Curation**: *Apollo Lunar Sample Database* & *Mars Meteorite Compendium (MMC)*, Curatorial Facility, Johnson Space Center.
5. **NASA PDS Geosciences Node / CAB**: InSight Mars Weather Service (APSS), MSL REMS, Mars 2020 MEDA.
6. **LROC & MRO Teams**: Lunar Reconnaissance Orbiter Camera (ASU) and HiRISE/CTX (University of Arizona / JPL).
7. **NASA GRAIL & MRO Gravity Teams**: GRAIL JGL1500P Lunar Gravity Model & MRO GMM-3 Martian Gravity Field.
8. **LRO CRaTER & MSL RAD Teams**: Cosmic Ray Telescope for the Effects of Radiation (CRaTER) and Radiation Assessment Detector (RAD) in-situ dosimetry.
9. **InSight SEIS Team**: Mars Interior Structure and Marsquake Seismology Catalog.
10. **LMD / ESA / CNES**: Mars Climate Database (MCD v5.3) & NASA Mars Global Reference Atmospheric Model (MarsGRAM).
11. **COSPAR Planetary Protection Panel**: COSPAR Policy on Planetary Protection (Categories II, III, IVa, IVb, IVc & Special Regions).

