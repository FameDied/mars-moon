import sqlite3
import json
import csv
import os
import time

DB_PATH = "planetary_moon_mars.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print(f"Creating and initializing master database: {DB_PATH}...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Enable foreign keys and performance pragmas
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute("PRAGMA journal_mode = WAL;")
cursor.execute("PRAGMA synchronous = NORMAL;")

# --- SCHEMA DEFINITION ---

cursor.executescript("""
-- 1. Celestial Bodies
CREATE TABLE celestial_bodies (
    body_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    system TEXT NOT NULL,
    classification TEXT NOT NULL,
    discovery_history TEXT,
    summary_description TEXT NOT NULL
);

-- 2. Physical & Bulk Parameters
CREATE TABLE physical_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    category TEXT NOT NULL,
    parameter TEXT NOT NULL,
    raw_parameter TEXT,
    value_str TEXT NOT NULL,
    unit TEXT,
    earth_comparison_value TEXT,
    ratio_to_earth TEXT,
    source TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);
CREATE INDEX idx_phys_body ON physical_parameters(body_id);
CREATE INDEX idx_phys_param ON physical_parameters(parameter);

-- 3. Orbital Parameters
CREATE TABLE orbital_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    category TEXT NOT NULL,
    parameter TEXT NOT NULL,
    raw_parameter TEXT,
    value_str TEXT NOT NULL,
    unit TEXT,
    earth_comparison_value TEXT,
    source TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);
CREATE INDEX idx_orb_body ON orbital_parameters(body_id);

-- 4. High-Precision Ephemerides (NASA JPL Horizons)
CREATE TABLE ephemerides_2026 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    datetime_utc TEXT NOT NULL,
    ra_icrf TEXT NOT NULL,
    dec_icrf TEXT NOT NULL,
    apparent_visual_magnitude REAL,
    surface_brightness REAL,
    heliocentric_distance_au REAL NOT NULL,
    heliocentric_range_rate_kms REAL NOT NULL,
    geocentric_distance_au REAL NOT NULL,
    geocentric_range_rate_kms REAL NOT NULL,
    sun_observer_target_deg REAL NOT NULL,
    phase_angle_sto_deg REAL,
    source TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);
CREATE INDEX idx_eph_body_date ON ephemerides_2026(body_id, datetime_utc);

-- 5. IAU Planetary Nomenclature (USGS Astrogeology)
CREATE TABLE iau_planetary_features (
    feature_pk INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    feature_id TEXT,
    name TEXT NOT NULL,
    clean_name TEXT NOT NULL,
    feature_type TEXT NOT NULL,
    type_code TEXT,
    diameter_km REAL NOT NULL,
    center_lat REAL NOT NULL,
    center_lon REAL NOT NULL,
    center_lon_180 REAL NOT NULL,
    min_lat REAL,
    max_lat REAL,
    min_lon REAL,
    max_lon REAL,
    origin TEXT,
    approval_date TEXT,
    approval_status TEXT,
    ethnicity TEXT,
    continent TEXT,
    quad_name TEXT,
    quad_code TEXT,
    usgs_link TEXT,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);
CREATE INDEX idx_feat_body ON iau_planetary_features(body_id);
CREATE INDEX idx_feat_name ON iau_planetary_features(name);
CREATE INDEX idx_feat_type ON iau_planetary_features(feature_type);
CREATE INDEX idx_feat_diam ON iau_planetary_features(diameter_km DESC);
CREATE INDEX idx_feat_coords ON iau_planetary_features(center_lat, center_lon);

-- 6. Space Missions Catalog
CREATE TABLE missions_catalog (
    mission_id TEXT PRIMARY KEY,
    target_body TEXT NOT NULL,
    mission_name TEXT NOT NULL,
    space_agency TEXT NOT NULL,
    country TEXT NOT NULL,
    launch_date TEXT NOT NULL,
    arrival_date TEXT,
    end_date TEXT,
    mission_type TEXT NOT NULL,
    status TEXT NOT NULL,
    launch_vehicle TEXT,
    mass_kg REAL,
    objectives TEXT NOT NULL,
    key_discoveries TEXT NOT NULL,
    payload_json TEXT
);
CREATE INDEX idx_miss_target ON missions_catalog(target_body);
CREATE INDEX idx_miss_agency ON missions_catalog(space_agency);
CREATE INDEX idx_miss_status ON missions_catalog(status);

-- 7. Surface Landing and Impact Sites
CREATE TABLE surface_landing_sites (
    site_id TEXT PRIMARY KEY,
    body_id TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    site_name TEXT NOT NULL,
    target_feature TEXT NOT NULL,
    latitude_deg REAL NOT NULL,
    longitude_deg REAL NOT NULL,
    elevation_m REAL,
    landing_type TEXT NOT NULL,
    touchdown_date TEXT NOT NULL,
    operational_days REAL,
    current_status TEXT NOT NULL,
    hardware_inventory_json TEXT,
    coordinate_reference TEXT,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id),
    FOREIGN KEY (mission_id) REFERENCES missions_catalog(mission_id)
);
CREATE INDEX idx_site_body ON surface_landing_sites(body_id);
CREATE INDEX idx_site_coords ON surface_landing_sites(latitude_deg, longitude_deg);

-- 8. Lunar Samples Catalog (NASA JSC Apollo & International Returns)
CREATE TABLE lunar_samples_catalog (
    sample_id TEXT PRIMARY KEY,
    mission TEXT NOT NULL,
    return_year INTEGER NOT NULL,
    collection_site TEXT NOT NULL,
    rock_class TEXT NOT NULL,
    rock_subclass TEXT,
    weight_grams REAL NOT NULL,
    pristine_percent REAL NOT NULL,
    documentation_url TEXT,
    curating_institution TEXT NOT NULL
);
CREATE INDEX idx_lunar_rock_class ON lunar_samples_catalog(rock_class);
CREATE INDEX idx_lunar_mission ON lunar_samples_catalog(mission);
CREATE INDEX idx_lunar_weight ON lunar_samples_catalog(weight_grams DESC);

-- 9. Martian Meteorites Catalog (NASA JSC MMC)
CREATE TABLE martian_meteorites_catalog (
    meteorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
    meteorite_name TEXT NOT NULL,
    petrologic_classification TEXT NOT NULL,
    sample_group TEXT NOT NULL,
    fall_or_find TEXT NOT NULL,
    major_oxides_json TEXT,
    trace_elements_json TEXT,
    literature_references TEXT,
    scientific_significance TEXT,
    compendium_source TEXT NOT NULL
);
CREATE INDEX idx_mars_met_class ON martian_meteorites_catalog(petrologic_classification);

-- 10. Mars Surface Weather
CREATE TABLE mars_surface_weather (
    weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    mission TEXT NOT NULL,
    site TEXT NOT NULL,
    sol INTEGER NOT NULL,
    season_ls_deg REAL,
    first_utc TEXT,
    last_utc TEXT,
    temp_air_min_c REAL,
    temp_air_max_c REAL,
    temp_air_avg_c REAL,
    pressure_min_pa REAL,
    pressure_max_pa REAL,
    pressure_avg_pa REAL,
    wind_speed_min_mps REAL,
    wind_speed_max_mps REAL,
    wind_speed_avg_mps REAL,
    wind_direction_compass TEXT,
    wind_direction_deg REAL,
    source TEXT NOT NULL
);
CREATE INDEX idx_weather_mission ON mars_surface_weather(mission);
CREATE INDEX idx_weather_sol ON mars_surface_weather(sol);

-- 11. Atmospheric Profiles
CREATE TABLE atmospheric_profiles (
    body_id TEXT PRIMARY KEY,
    atmosphere_classification TEXT NOT NULL,
    surface_pressure_range TEXT NOT NULL,
    total_mass_kg REAL,
    scale_height_km REAL,
    diurnal_temperature_range_k TEXT NOT NULL,
    cold_trap_temperatures_k TEXT,
    primary_composition_json TEXT NOT NULL,
    trace_gases_or_species_json TEXT,
    dust_environment TEXT,
    radiation_environment TEXT,
    key_missions TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);

-- 12. Rover Science Targets & Sample Tubes
CREATE TABLE rover_science_targets (
    target_id TEXT PRIMARY KEY,
    rover TEXT NOT NULL,
    target_name TEXT NOT NULL,
    sol INTEGER NOT NULL,
    site_feature TEXT NOT NULL,
    formation_or_member TEXT NOT NULL,
    rock_type TEXT NOT NULL,
    tools_used TEXT NOT NULL,
    mineralogy TEXT NOT NULL,
    organic_molecules TEXT,
    scientific_significance TEXT NOT NULL,
    sample_cache_status TEXT NOT NULL
);
CREATE INDEX idx_rover_tgt_name ON rover_science_targets(target_name);
CREATE INDEX idx_rover_tgt_rover ON rover_science_targets(rover);

-- 13. Planetary Stratigraphy & Geological Eras
CREATE TABLE planetary_stratigraphy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    era_name TEXT NOT NULL,
    start_ga REAL NOT NULL,
    end_ga REAL NOT NULL,
    duration_ma REAL NOT NULL,
    defining_events TEXT NOT NULL,
    key_formations_and_rocks TEXT NOT NULL,
    seismic_and_thermal_state TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);
CREATE INDEX idx_strat_body ON planetary_stratigraphy(body_id);

-- 14. Internal Structure & Geophysics
CREATE TABLE internal_structure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    layer_name TEXT NOT NULL,
    depth_min_km REAL NOT NULL,
    depth_max_km REAL NOT NULL,
    composition TEXT NOT NULL,
    density_g_cm3 REAL NOT NULL,
    physical_state TEXT NOT NULL,
    seismic_p_velocity_kms REAL,
    discovery_notes TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);
CREATE INDEX idx_int_body ON internal_structure(body_id);

-- 15. Polar and Subsurface Ice Reservoirs
CREATE TABLE ice_reservoirs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_id TEXT NOT NULL,
    reservoir_name TEXT NOT NULL,
    latitude_deg REAL NOT NULL,
    longitude_deg REAL NOT NULL,
    area_km2 REAL,
    ice_purity_pct REAL,
    estimated_volume_km3 REAL,
    depth_m REAL,
    temperature_k REAL,
    detection_method TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);
CREATE INDEX idx_ice_body ON ice_reservoirs(body_id);

-- 16. Planetary Basemaps
CREATE TABLE planetary_basemaps (
    map_id TEXT PRIMARY KEY,
    body_id TEXT NOT NULL,
    map_title TEXT NOT NULL,
    instrument TEXT NOT NULL,
    local_file_path TEXT NOT NULL,
    remote_url TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    source_authority TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);

-- 17. Curated Planetary Imagery
CREATE TABLE curated_imagery (
    media_id TEXT PRIMARY KEY,
    body_id TEXT NOT NULL,
    title TEXT NOT NULL,
    curated_topic TEXT NOT NULL,
    date_created TEXT,
    description TEXT NOT NULL,
    high_res_image_url TEXT NOT NULL,
    thumbnail_url TEXT NOT NULL,
    keywords_json TEXT,
    source TEXT NOT NULL,
    FOREIGN KEY (body_id) REFERENCES celestial_bodies(body_id)
);

-- 18. Unified Full-Text Search (FTS5) Virtual Table
CREATE VIRTUAL TABLE fts_planetary_search USING fts5(
    entity_type,
    entity_id,
    body,
    title,
    category,
    content,
    tokenize = 'porter unicode61'
);
""")

print("Database schema successfully generated.")

# --- POPULATE CELESTIAL BODIES ---
bodies_data = [
    (
        "Moon",
        "The Moon (Luna / Earth I)",
        "Earth-Moon Barycentric System",
        "Planetary-mass Natural Satellite",
        "Known since antiquity; first orbited by Luna 10 (1966); first human landing by Apollo 11 (1969).",
        "Earth's sole natural satellite, the fifth largest satellite in the Solar System, and the largest planetary satellite relative to the size of the planet it orbits. Formed ~4.51 Ga from collision debris (Theia hypothesis). Possesses a differentiated structure, an anorthositic crust, basaltic flood maria, and a surface boundary exosphere."
    ),
    (
        "Mars",
        "Mars (Ares / Sol IV)",
        "Solar System (Outer Terrestrial Planet)",
        "Terrestrial Planet",
        "Known since antiquity; first flyby by Mariner 4 (1965); first orbiter Mariner 9 (1971); first soft lander Mars 3 (1971) / Viking 1 (1976).",
        "The fourth planet from the Sun and the second smallest planet in the Solar System. Known as the Red Planet due to ubiquitous iron(III) oxide (rust) dust. Features the tallest volcano in the Solar System (Olympus Mons, 21.9 km) and one of the largest canyon systems (Valles Marineris, 4,000 km). Proved to have hosted warm, wet, habitable paleolakes and river networks during the Noachian era (~4.1-3.7 Ga)."
    ),
    (
        "Phobos",
        "Phobos (Mars I)",
        "Martian System",
        "Innermost and Larger Moon of Mars",
        "Discovered on August 18, 1877, by American astronomer Asaph Hall at USNO.",
        "Irregularly shaped moon measuring 26.8 x 22.4 x 18.4 km orbiting only 6,000 km above the Martian surface (closer to its primary than any other known planetary moon). Dominated by the giant Stickney impact crater (9 km diameter) and prominent parallel grooves. Undergoes orbital decay (-1.8 m per century) and will break up into a ring system or impact Mars in ~30-50 million years."
    ),
    (
        "Deimos",
        "Deimos (Mars II)",
        "Martian System",
        "Outermost and Smaller Moon of Mars",
        "Discovered on August 12, 1877, by Asaph Hall at USNO.",
        "Smooth, triaxial ellipsoid moon measuring 15 x 12.2 x 11 km orbiting at 23,460 km from Mars. C-type or D-type carbonaceous chondrite-like surface blanketed in a thick 100-meter regolith mantle that softens crater contours (Swift and Voltaire craters)."
    )
]

cursor.executemany("INSERT INTO celestial_bodies VALUES (?, ?, ?, ?, ?, ?);", bodies_data)
conn.commit()
print("Populated celestial_bodies.")

# --- INGEST TABLE DATA ---

# Ingest physical parameters
with open("data/processed/json/physical_parameters.json", "r", encoding="utf-8") as f:
    phys_data = json.load(f)
phys_rows = [
    (item["body"], item["category"], item["parameter"], item.get("raw_parameter"), item["value_str"], item.get("unit"), item.get("earth_comparison_value"), item.get("ratio_to_earth"), item["source"])
    for item in phys_data
]
cursor.executemany("INSERT INTO physical_parameters (body_id, category, parameter, raw_parameter, value_str, unit, earth_comparison_value, ratio_to_earth, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", phys_rows)

# Ingest orbital parameters
with open("data/processed/json/orbital_parameters.json", "r", encoding="utf-8") as f:
    orb_data = json.load(f)
orb_rows = [
    (item["body"], item["category"], item["parameter"], item.get("raw_parameter"), item["value_str"], item.get("unit"), item.get("earth_comparison_value"), item["source"])
    for item in orb_data
]
cursor.executemany("INSERT INTO orbital_parameters (body_id, category, parameter, raw_parameter, value_str, unit, earth_comparison_value, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", orb_rows)

# Ingest ephemerides
with open("data/processed/json/jpl_ephemerides_2026.json", "r", encoding="utf-8") as f:
    eph_data = json.load(f)
eph_rows = [
    (item["body"], item["datetime_utc"], item["ra_icrf"], item["dec_icrf"], item.get("apparent_visual_magnitude"), item.get("surface_brightness"), item["heliocentric_distance_au"], item["heliocentric_range_rate_kms"], item["geocentric_distance_au"], item["geocentric_range_rate_kms"], item["sun_observer_target_deg"], item.get("phase_angle_sto_deg"), item["source"])
    for item in eph_data
]
cursor.executemany("INSERT INTO ephemerides_2026 (body_id, datetime_utc, ra_icrf, dec_icrf, apparent_visual_magnitude, surface_brightness, heliocentric_distance_au, heliocentric_range_rate_kms, geocentric_distance_au, geocentric_range_rate_kms, sun_observer_target_deg, phase_angle_sto_deg, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", eph_rows)

# Ingest IAU features (11,139 records)
print("Ingesting 11,139 IAU Planetary Features...")
with open("data/processed/json/iau_features.json", "r", encoding="utf-8") as f:
    feat_data = json.load(f)
feat_rows = [
    (item["body"], item.get("feature_id"), item["name"], item["clean_name"], item["feature_type"], item.get("type_code"), item["diameter_km"], item["center_lat"], item["center_lon"], item["center_lon_180"], item.get("min_lat"), item.get("max_lat"), item.get("min_lon"), item.get("max_lon"), item.get("origin"), item.get("approval_date"), item.get("approval_status"), item.get("ethnicity"), item.get("continent"), item.get("quad_name"), item.get("quad_code"), item.get("usgs_link"))
    for item in feat_data
]
cursor.executemany("""
INSERT INTO iau_planetary_features (body_id, feature_id, name, clean_name, feature_type, type_code, diameter_km, center_lat, center_lon, center_lon_180, min_lat, max_lat, min_lon, max_lon, origin, approval_date, approval_status, ethnicity, continent, quad_name, quad_code, usgs_link)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", feat_rows)

# Ingest Missions
with open("data/processed/json/missions_catalog.json", "r", encoding="utf-8") as f:
    miss_data = json.load(f)
miss_rows = [
    (m["mission_id"], m["target_body"], m["mission_name"], m["space_agency"], m["country"], m["launch_date"], m.get("arrival_date"), m.get("end_date"), m["mission_type"], m["status"], m.get("launch_vehicle"), m.get("mass_kg"), m["objectives"], m["key_discoveries"], json.dumps(m.get("payload", [])))
    for m in miss_data
]
cursor.executemany("""
INSERT INTO missions_catalog (mission_id, target_body, mission_name, space_agency, country, launch_date, arrival_date, end_date, mission_type, status, launch_vehicle, mass_kg, objectives, key_discoveries, payload_json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", miss_rows)

# Ingest Surface Landing Sites
with open("data/processed/json/surface_landing_sites.json", "r", encoding="utf-8") as f:
    site_data = json.load(f)
site_rows = [
    (s["site_id"], s["body"], s["mission_id"], s["site_name"], s["target_feature"], s["latitude_deg"], s["longitude_deg"], s.get("elevation_m"), s["landing_type"], s["touchdown_date"], s.get("operational_days"), s["current_status"], json.dumps(s.get("hardware_inventory", [])), s.get("coordinate_reference"))
    for s in site_data
]
cursor.executemany("""
INSERT INTO surface_landing_sites (site_id, body_id, mission_id, site_name, target_feature, latitude_deg, longitude_deg, elevation_m, landing_type, touchdown_date, operational_days, current_status, hardware_inventory_json, coordinate_reference)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", site_rows)

# Ingest Lunar Samples
print("Ingesting Lunar Samples Catalog...")
with open("data/processed/json/lunar_samples.json", "r", encoding="utf-8") as f:
    lunar_data = json.load(f)
lunar_rows = [
    (s["sample_id"], s["mission"], s["return_year"], s["collection_site"], s["rock_class"], s.get("rock_subclass"), s["weight_grams"], s["pristine_percent"], s.get("documentation_url"), s["curating_institution"])
    for s in lunar_data
]
cursor.executemany("""
INSERT INTO lunar_samples_catalog (sample_id, mission, return_year, collection_site, rock_class, rock_subclass, weight_grams, pristine_percent, documentation_url, curating_institution)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", lunar_rows)

# Ingest Martian Meteorites
with open("data/processed/json/martian_meteorites.json", "r", encoding="utf-8") as f:
    met_data = json.load(f)
met_rows = [
    (m["meteorite_name"], m["petrologic_classification"], m["sample_group"], m["fall_or_find"], json.dumps(m.get("major_oxides_wt_pct", {})), json.dumps(m.get("trace_elements_ppm", {})), m.get("literature_references"), m.get("scientific_significance"), m["compendium_source"])
    for m in met_data
]
cursor.executemany("""
INSERT INTO martian_meteorites_catalog (meteorite_name, petrologic_classification, sample_group, fall_or_find, major_oxides_json, trace_elements_json, literature_references, scientific_significance, compendium_source)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
""", met_rows)

# Ingest Weather
with open("data/processed/json/mars_surface_weather.json", "r", encoding="utf-8") as f:
    weather_data = json.load(f)
weather_rows = [
    (w["body"], w["mission"], w["site"], w["sol"], w.get("season_ls_deg"), w.get("first_utc"), w.get("last_utc"), w.get("temp_air_min_c"), w.get("temp_air_max_c"), w.get("temp_air_avg_c"), w.get("pressure_min_pa"), w.get("pressure_max_pa"), w.get("pressure_avg_pa"), w.get("wind_speed_min_mps"), w.get("wind_speed_max_mps"), w.get("wind_speed_avg_mps"), w.get("wind_direction_compass"), w.get("wind_direction_deg"), w["source"])
    for w in weather_data
]
cursor.executemany("""
INSERT INTO mars_surface_weather (body_id, mission, site, sol, season_ls_deg, first_utc, last_utc, temp_air_min_c, temp_air_max_c, temp_air_avg_c, pressure_min_pa, pressure_max_pa, pressure_avg_pa, wind_speed_min_mps, wind_speed_max_mps, wind_speed_avg_mps, wind_direction_compass, wind_direction_deg, source)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", weather_rows)

# Ingest Atmospheric Profiles
with open("data/processed/json/atmospheric_profiles.json", "r", encoding="utf-8") as f:
    atm_data = json.load(f)
atm_rows = [
    (a["body"], a["atmosphere_classification"], a["surface_pressure_range"], a.get("total_mass_kg"), a.get("scale_height_km"), a["diurnal_temperature_range_k"], a.get("cold_trap_temperatures_k"), json.dumps(a.get("primary_composition", {})), json.dumps(a.get("trace_gases_and_isotopes", {}) or a.get("optical_trace_species", {})), a.get("dust_and_meteorology") or a.get("dust_environment"), a.get("radiation_environment"), a["key_missions"])
    for a in atm_data
]
cursor.executemany("""
INSERT INTO atmospheric_profiles (body_id, atmosphere_classification, surface_pressure_range, total_mass_kg, scale_height_km, diurnal_temperature_range_k, cold_trap_temperatures_k, primary_composition_json, trace_gases_or_species_json, dust_environment, radiation_environment, key_missions)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", atm_rows)

# Ingest Rover Science Targets
with open("data/processed/json/rover_targets.json", "r", encoding="utf-8") as f:
    tgt_data = json.load(f)
tgt_rows = [
    (t["target_id"], t["rover"], t["target_name"], t["sol"], t["site_feature"], t["formation_or_member"], t["rock_type"], t["tools_used"], t["mineralogy"], t.get("organic_molecules"), t["scientific_significance"], t["sample_cache_status"])
    for t in tgt_data
]
cursor.executemany("""
INSERT INTO rover_science_targets (target_id, rover, target_name, sol, site_feature, formation_or_member, rock_type, tools_used, mineralogy, organic_molecules, scientific_significance, sample_cache_status)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", tgt_rows)

# Ingest Stratigraphy
with open("data/processed/json/planetary_stratigraphy.json", "r", encoding="utf-8") as f:
    strat_data = json.load(f)
strat_rows = [
    (s["body"], s["era_name"], s["start_ga"], s["end_ga"], s["duration_ma"], s["defining_events"], s["key_formations_and_rocks"], s["seismic_and_thermal_state"])
    for s in strat_data
]
cursor.executemany("""
INSERT INTO planetary_stratigraphy (body_id, era_name, start_ga, end_ga, duration_ma, defining_events, key_formations_and_rocks, seismic_and_thermal_state)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
""", strat_rows)

# Ingest Internal Structure
with open("data/processed/json/internal_structure.json", "r", encoding="utf-8") as f:
    int_data = json.load(f)
int_rows = [
    (i["body"], i["layer_name"], i["depth_min_km"], i["depth_max_km"], i["composition"], i["density_g_cm3"], i["physical_state"], i.get("seismic_p_velocity_kms"), i["discovery_notes"])
    for i in int_data
]
cursor.executemany("""
INSERT INTO internal_structure (body_id, layer_name, depth_min_km, depth_max_km, composition, density_g_cm3, physical_state, seismic_p_velocity_kms, discovery_notes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
""", int_rows)

# Ingest Ice Reservoirs
with open("data/processed/json/ice_reservoirs.json", "r", encoding="utf-8") as f:
    ice_data = json.load(f)
ice_rows = [
    (r["body"], r["reservoir_name"], r["latitude_deg"], r["longitude_deg"], r.get("area_km2"), r.get("ice_purity_pct"), r.get("estimated_volume_km3"), r.get("depth_m"), r.get("temperature_k"), r["detection_method"], r["description"])
    for r in ice_data
]
cursor.executemany("""
INSERT INTO ice_reservoirs (body_id, reservoir_name, latitude_deg, longitude_deg, area_km2, ice_purity_pct, estimated_volume_km3, depth_m, temperature_k, detection_method, description)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", ice_rows)

# Ingest Basemaps
with open("data/processed/json/planetary_basemaps.json", "r", encoding="utf-8") as f:
    map_data = json.load(f)
map_rows = [
    (m["map_id"], m["body"], m["map_title"], m["instrument"], m["local_file_path"], m["remote_url"], m["file_size_bytes"], m["source_authority"])
    for m in map_data
]
cursor.executemany("""
INSERT INTO planetary_basemaps (map_id, body_id, map_title, instrument, local_file_path, remote_url, file_size_bytes, source_authority)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
""", map_rows)

# Ingest Curated Imagery
with open("data/processed/json/curated_imagery.json", "r", encoding="utf-8") as f:
    media_data = json.load(f)
media_rows = [
    (img["media_id"], img["body"], img["title"], img["curated_topic"], img.get("date_created"), img["description"], img["high_res_image_url"], img["thumbnail_url"], img.get("keywords_json"), img["source"])
    for img in media_data
]
cursor.executemany("""
INSERT INTO curated_imagery (media_id, body_id, title, curated_topic, date_created, description, high_res_image_url, thumbnail_url, keywords_json, source)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", media_rows)

conn.commit()
print("All core relational tables populated.")

# --- BUILD UNIFIED FULL-TEXT SEARCH (FTS5) ---
print("Building Full-Text Search (FTS5) index...")

# 1. Index IAU Features
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'FEATURE', COALESCE(feature_id, CAST(feature_pk AS TEXT)), body_id, name, feature_type,
       clean_name || ' ' || feature_type || ' Diameter ' || diameter_km || ' km. Quad: ' || COALESCE(quad_name, '') || '. ' || COALESCE(origin, '') || '. Approval: ' || COALESCE(approval_status, '')
FROM iau_planetary_features;
""")

# 2. Index Missions
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'MISSION', mission_id, target_body, mission_name, mission_type,
       mission_name || ' Agency: ' || space_agency || ' (' || country || '). Status: ' || status || '. Objectives: ' || objectives || ' Key Discoveries: ' || key_discoveries
FROM missions_catalog;
""")

# 3. Index Landing Sites
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'LANDING_SITE', site_id, body_id, site_name, landing_type,
       site_name || ' Feature: ' || target_feature || ' Coordinates: ' || latitude_deg || '° N/S, ' || longitude_deg || '° E. Status: ' || current_status || ' Hardware: ' || hardware_inventory_json
FROM surface_landing_sites;
""")

# 4. Index Lunar Samples
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'LUNAR_SAMPLE', sample_id, 'Moon', 'Lunar Sample ' || sample_id, rock_class,
       'Mission: ' || mission || ' Class: ' || rock_class || ' Subclass: ' || COALESCE(rock_subclass, '') || ' Site: ' || collection_site || ' Weight: ' || weight_grams || 'g. Pristine: ' || pristine_percent || '%. Curated by: ' || curating_institution
FROM lunar_samples_catalog;
""")

# 5. Index Martian Meteorites
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'MARTIAN_METEORITE', CAST(meteorite_id AS TEXT), 'Mars', meteorite_name, petrologic_classification,
       meteorite_name || ' Classification: ' || petrologic_classification || ' Group: ' || sample_group || ' Type: ' || fall_or_find || '. Significance: ' || COALESCE(scientific_significance, '') || ' Oxides: ' || COALESCE(major_oxides_json, '')
FROM martian_meteorites_catalog;
""")

# 6. Index Rover Science Targets
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'ROVER_TARGET', target_id, 'Mars', target_name, rock_type,
       target_name || ' Rover: ' || rover || ' Sol ' || sol || ' Feature: ' || site_feature || ' Formation: ' || formation_or_member || ' Mineralogy: ' || mineralogy || ' Organics: ' || COALESCE(organic_molecules, '') || ' Significance: ' || scientific_significance
FROM rover_science_targets;
""")

# 7. Index Stratigraphy Eras
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'STRATIGRAPHY', CAST(id AS TEXT), body_id, era_name, 'Geological Era',
       era_name || ' (' || start_ga || ' - ' || end_ga || ' Ga). Defining events: ' || defining_events || ' Formations: ' || key_formations_and_rocks || ' State: ' || seismic_and_thermal_state
FROM planetary_stratigraphy;
""")

# 8. Index Ice Reservoirs
cursor.execute("""
INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
SELECT 'ICE_RESERVOIR', CAST(id AS TEXT), body_id, reservoir_name, 'Water Ice Reservoir',
       reservoir_name || ' Method: ' || detection_method || ' Ice Purity: ' || COALESCE(ice_purity_pct, 0) || '%. Volume: ' || COALESCE(estimated_volume_km3, 0) || ' km3. ' || description
FROM ice_reservoirs;
""")

conn.commit()
print("FTS5 index successfully built and committed.")

# --- DATABASE AUDIT & ROW COUNTS ---
print("\n" + "="*60)
print("       MASTER PLANETARY DATABASE AUDIT & VERIFICATION       ")
print("="*60)

tables = [
    "celestial_bodies",
    "physical_parameters",
    "orbital_parameters",
    "ephemerides_2026",
    "iau_planetary_features",
    "missions_catalog",
    "surface_landing_sites",
    "lunar_samples_catalog",
    "martian_meteorites_catalog",
    "mars_surface_weather",
    "atmospheric_profiles",
    "rover_science_targets",
    "planetary_stratigraphy",
    "internal_structure",
    "ice_reservoirs",
    "planetary_basemaps",
    "curated_imagery",
    "fts_planetary_search"
]

total_rows = 0
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {t};")
    cnt = cursor.fetchone()[0]
    total_rows += cnt
    print(f"Table: {t:<30} | Records: {cnt:>8,}")

db_size = os.path.getsize(DB_PATH)
print("="*60)
print(f"TOTAL ROWS ACROSS ALL TABLES: {total_rows:,}")
print(f"DATABASE FILE SIZE:           {db_size:,} bytes ({db_size / (1024*1024):.2f} MB)")
print("="*60 + "\n")

conn.close()

