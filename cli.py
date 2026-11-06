#!/usr/bin/env python3
"""
Master Planetary Database CLI for Moon and Mars
Unified access to physical parameters, IAU nomenclature, missions,
landing sites, Apollo lunar samples, Martian meteorites, weather logs,
geology, and full-text search.
"""

import sys
import os
import sqlite3
import argparse
import json
import csv

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planetary_moon_mars.db")

def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run 'python3 scripts/10_build_master_database.py' first.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cmd_stats(args):
    conn = get_connection()
    c = conn.cursor()
    print("\n" + "="*65)
    print("       MASTER MOON & MARS DATABASE SUMMARY & METRICS       ")
    print("="*65)
    tables = [
        ("celestial_bodies", "Planetary & Satellite Bodies"),
        ("physical_parameters", "Physical & Bulk Geodetic Constants"),
        ("orbital_parameters", "Orbital & Dynamic Characteristics"),
        ("ephemerides_2026", "JPL Horizons High-Precision Ephemerides"),
        ("iau_planetary_features", "Official IAU Gazetteer Named Features"),
        ("missions_catalog", "Historical & Current Space Missions"),
        ("surface_landing_sites", "Surface Landers, Rovers & Crash Sites"),
        ("lunar_samples_catalog", "Returned Lunar Samples (Apollo, Luna, CE)"),
        ("martian_meteorites_catalog", "Martian Meteorites (NASA JSC MMC)"),
        ("mars_surface_weather", "In-situ Surface Meteorological Logs"),
        ("atmospheric_profiles", "Atmospheric & Exospheric Profiles"),
        ("rover_science_targets", "Rover ChemCam/PIXL/SAM Drill Samples"),
        ("planetary_stratigraphy", "Geological Eras & Stratigraphy"),
        ("internal_structure", "Core/Mantle/Crust Geophysics"),
        ("ice_reservoirs", "Polar & Subsurface Ice Reservoirs"),
        ("planetary_basemaps", "Topographic DEMs & Global Basemaps"),
        ("curated_imagery", "Curated High-Res Scientific Photography"),
        ("remote_sensing_rasters", "Remote Sensing Science Rasters & DTMs"),
        ("site_candidate_matrix", "Site Candidate Trade-Space Matrix (43 Fields)"),
        ("site_engineering_safety", "Landing Site Engineering Safety & Constraints"),
        ("lander_engineering_constraints", "Lander Dynamics & EDL Envelopes"),
        ("regolith_geotechnics_psi", "Regolith Geotechnics & PSI Scour"),
        ("telecom_relay_visibility", "DSN Line-of-Sight & Orbiter Relays"),
        ("rock_hazard_sfd", "Rock Size-Frequency Distribution & Hazards"),
        ("fts_planetary_search", "Full-Text Search Index Entries"),
        ("v_site_gnc_optical_gravity", "  ↳ View: GNC & Optical Gravity"),
        ("v_site_active_tectonics_seismology", "  ↳ View: Active Tectonics & Seismology"),
        ("v_site_power_cryo_thermal", "  ↳ View: Power & Cryogenic Thermal"),
        ("v_site_dust_charging_magnetics", "  ↳ View: Dust Charging & Magnetics"),
        ("v_site_radiation_topographic_shielding", "  ↳ View: Radiation Shielding (SVF)"),
        ("v_site_mars_atmospheric_dynamics", "  ↳ View: Mars Atmospheric Dynamics"),
        ("v_site_planetary_protection_heritage", "  ↳ View: Planetary Protection & Heritage"),
        ("v_site_isru_feedstock_toxicity", "  ↳ View: ISRU Feedstock & Toxicity"),
        ("v_site_traverse_science_paradox", "  ↳ View: Science-vs-Safety Paradox")
    ]
    total = 0
    for t, label in tables:
        c.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = c.fetchone()[0]
        total += cnt
        print(f"• {label:<42} | {cnt:>7,} records")
    print("="*65)
    print(f"TOTAL INDEXED RECORDS: {total:,}")
    print(f"DATABASE FILE SIZE:    {os.path.getsize(DB_PATH):,} bytes ({os.path.getsize(DB_PATH)/(1024*1024):.2f} MB)")
    print("="*65 + "\n")
    conn.close()

def cmd_search(args):
    conn = get_connection()
    c = conn.cursor()
    query = args.query
    limit = args.limit
    print(f"\nSearching for '{query}' across all entities (limit {limit})...\n")
    c.execute("""
        SELECT entity_type, entity_id, body, title, category,
               snippet(fts_planetary_search, 5, '\033[1;32m', '\033[0m', '...', 16) as snip
        FROM fts_planetary_search
        WHERE fts_planetary_search MATCH ?
        LIMIT ?;
    """, (query, limit))
    rows = c.fetchall()
    if not rows:
        print("No matches found.")
    for i, r in enumerate(rows, 1):
        print(f"{i:2}. [{r['entity_type']:<16}] ({r['body']}) \033[1m{r['title']}\033[0m [{r['category']}]")
        print(f"    {r['snip']}")
    print(f"\nFound {len(rows)} matching records.\n")
    conn.close()

def cmd_features(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT body_id, clean_name, feature_type, diameter_km, center_lat, center_lon, quad_name, origin FROM iau_planetary_features WHERE 1=1"
    params = []
    if args.body:
        sql += " AND body_id = ?"
        params.append(args.body.capitalize())
    if args.type:
        sql += " AND feature_type LIKE ?"
        params.append(f"%{args.type}%")
    if args.min_diam:
        sql += " AND diameter_km >= ?"
        params.append(args.min_diam)
    sql += " ORDER BY diameter_km DESC LIMIT ?"
    params.append(args.limit)
    
    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nIAU Nomenclature Features (Showing top {len(rows)}):\n")
    for r in rows:
        print(f"[{r['body_id']:<5}] {r['clean_name']:<25} | {r['feature_type']:<18} | Diam: {r['diameter_km']:>7.1f} km | Lat: {r['center_lat']:>7.2f}°, Lon: {r['center_lon']:>7.2f}° | Quad: {r['quad_name'] or 'N/A'}")
    print()
    conn.close()

def cmd_missions(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT mission_id, target_body, mission_name, space_agency, country, launch_date, mission_type, status, key_discoveries FROM missions_catalog WHERE 1=1"
    params = []
    if args.body:
        sql += " AND target_body = ?"
        params.append(args.body.capitalize())
    if args.agency:
        sql += " AND (space_agency LIKE ? OR country LIKE ?)"
        params.extend([f"%{args.agency}%", f"%{args.agency}%"])
    sql += " ORDER BY launch_date ASC;"
    
    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nSpace Missions ({len(rows)} returned):\n")
    for r in rows:
        print(f"[{r['target_body']:<5}] {r['launch_date']} | {r['mission_name']:<28} | {r['space_agency']} ({r['country']}) | Status: {r['status']}")
        print(f"       Type: {r['mission_type']}")
        print(f"       Key Discovery: {r['key_discoveries'][:110]}...")
    print()
    conn.close()

def cmd_sites(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT body_id, site_name, target_feature, latitude_deg, longitude_deg, touchdown_date, landing_type, current_status FROM surface_landing_sites WHERE 1=1"
    params = []
    if args.body:
        sql += " AND body_id = ?"
        params.append(args.body.capitalize())
    sql += " ORDER BY touchdown_date ASC;"
    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nSurface Landing & Impact Sites ({len(rows)} returned):\n")
    for r in rows:
        print(f"[{r['body_id']:<5}] {r['touchdown_date']} | {r['site_name']:<32} | Lat: {r['latitude_deg']:>6.2f}°, Lon: {r['longitude_deg']:>6.2f}° | {r['landing_type']}")
        print(f"       Status: {r['current_status']}")
    print()
    conn.close()

def cmd_samples(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT sample_id, mission, return_year, collection_site, rock_class, rock_subclass, weight_grams, pristine_percent FROM lunar_samples_catalog WHERE 1=1"
    params = []
    if args.mission:
        sql += " AND mission LIKE ?"
        params.append(f"%{args.mission}%")
    if args.rock_class:
        sql += " AND rock_class LIKE ?"
        params.append(f"%{args.rock_class}%")
    if args.min_weight:
        sql += " AND weight_grams >= ?"
        params.append(args.min_weight)
    sql += " ORDER BY weight_grams DESC LIMIT ?"
    params.append(args.limit)
    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nLunar Samples Catalog ({len(rows)} returned):\n")
    for r in rows:
        print(f"Sample #{r['sample_id']:<10} | {r['mission']:<10} ({r['return_year']}) | Weight: {r['weight_grams']:>8.1f} g | Pristine: {r['pristine_percent']:>5.1f}% | {r['rock_class']} ({r['rock_subclass']}) | Site: {r['collection_site']}")
    print()
    conn.close()

def cmd_meteorites(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT meteorite_name, petrologic_classification, sample_group, fall_or_find, major_oxides_json FROM martian_meteorites_catalog WHERE 1=1"
    params = []
    if args.classification:
        sql += " AND petrologic_classification LIKE ?"
        params.append(f"%{args.classification}%")
    sql += " ORDER BY meteorite_name ASC LIMIT ?"
    params.append(args.limit)
    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nMartian Meteorites ({len(rows)} returned):\n")
    for r in rows:
        print(f"• {r['meteorite_name']:<25} | {r['petrologic_classification']:<40} | Type: {r['fall_or_find']}")
        try:
            ox = json.loads(r['major_oxides_json'])
            ox_str = ", ".join([f"{k}: {v}%" for k, v in list(ox.items())[:4]])
            print(f"    Major Oxides: {ox_str}")
        except Exception:
            pass
    print()
    conn.close()

def cmd_weather(args):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT mission, site, sol, first_utc, temp_air_min_c, temp_air_max_c, pressure_avg_pa, wind_speed_avg_mps, wind_direction_compass FROM mars_surface_weather ORDER BY mission, sol;")
    rows = c.fetchall()
    print(f"\nMars Surface Meteorological Observations ({len(rows)} records):\n")
    for r in rows:
        print(f"[{r['mission']:<25}] Sol {r['sol']:>4} ({r['first_utc'][:10]}) | Temp: {r['temp_air_min_c']:>5.1f}°C to {r['temp_air_max_c']:>5.1f}°C | Press: {r['pressure_avg_pa']:>6.1f} Pa | Wind: {r['wind_speed_avg_mps']:>4.1f} m/s {r['wind_direction_compass']}")
    print()
    conn.close()

def cmd_ice(args):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT body_id, reservoir_name, latitude_deg, longitude_deg, ice_purity_pct, estimated_volume_km3, depth_m, detection_method, description FROM ice_reservoirs ORDER BY body_id, estimated_volume_km3 DESC;")
    rows = c.fetchall()
    print(f"\nPolar and Subsurface Ice Reservoirs ({len(rows)} returned):\n")
    for r in rows:
        vol = f"{r['estimated_volume_km3']:,.1f} km3" if r['estimated_volume_km3'] else "N/A"
        purity = f"{r['ice_purity_pct']}%" if r['ice_purity_pct'] else "N/A"
        print(f"[{r['body_id']:<5}] {r['reservoir_name']:<40} | Lat: {r['latitude_deg']:>6.1f}°, Lon: {r['longitude_deg']:>6.1f}°")
        print(f"       Vol: {vol:<12} | Purity: {purity:<6} | Depth: {r['depth_m']} m | Method: {r['detection_method']}")
        print(f"       Notes: {r['description'][:100]}...")
    print()
    conn.close()

def cmd_rasters(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT raster_id, target_body, scientific_category, target_feature, mission, instrument,
               archive_agency, product_id, product_title, data_format, min_lat, max_lat,
               min_lon, max_lon, spatial_resolution_m, projection, direct_data_url, direct_label_url
        FROM remote_sensing_rasters WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND target_body = ?"
        params.append(args.body.capitalize())
    if args.category:
        sql += " AND scientific_category LIKE ?"
        params.append(f"%{args.category}%")
    if args.target:
        sql += " AND (target_feature LIKE ? OR product_title LIKE ?)"
        params.extend([f"%{args.target}%", f"%{args.target}%"])
    if args.mission:
        sql += " AND mission LIKE ?"
        params.append(f"%{args.mission}%")
    if args.format:
        sql += " AND data_format LIKE ?"
        params.append(f"%{args.format}%")
    
    sql += " ORDER BY target_body, scientific_category, spatial_resolution_m ASC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nRemote Sensing Scientific Rasters & Endpoints ({len(rows)} returned):\n")
    for r in rows:
        res = f"{r['spatial_resolution_m']:.1f} m/pix" if r['spatial_resolution_m'] else "Variable"
        print(f"[{r['target_body']:<4}] [{r['scientific_category']:<30}] \033[1m{r['product_title']}\033[0m")
        print(f"       Target: {r['target_feature']} | Mission: {r['mission']} ({r['instrument']}) | Agency: {r['archive_agency']}")
        print(f"       Res: {res:<14} | Format: {r['data_format']:<16} | BBox: Lat [{r['min_lat']:>6.1f}°, {r['max_lat']:>6.1f}°], Lon [{r['min_lon']:>6.1f}°, {r['max_lon']:>6.1f}°]")
        print(f"       Data URL:  \033[36m{r['direct_data_url']}\033[0m")
        if r['direct_label_url']:
            print(f"       Label URL: {r['direct_label_url']}")
        print()
    conn.close()

def cmd_compare(args):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT parameter, 
               MAX(CASE WHEN body_id = 'Moon' THEN value_str END) as moon_val,
               MAX(CASE WHEN body_id = 'Mars' THEN value_str END) as mars_val,
               MAX(unit) as unit,
               MAX(earth_comparison_value) as earth_val
        FROM physical_parameters
        GROUP BY parameter
        HAVING moon_val IS NOT NULL OR mars_val IS NOT NULL;
    """)
    rows = c.fetchall()
    print("\n" + "="*80)
    print("                 PLANETARY PHYSICAL CONSTANTS COMPARISON                 ")
    print("="*80)
    print(f"{'Parameter':<28} {'Unit':<15} {'Moon':<15} {'Mars':<15} {'Earth'}")
    print("-" * 80)
    for r in rows:
        unit = f"[{r['unit']}]" if r['unit'] else ""
        moon = r['moon_val'] or "-"
        mars = r['mars_val'] or "-"
        earth = r['earth_val'] or "-"
        print(f"{r['parameter']:<28} {unit:<15} {moon:<15} {mars:<15} {earth}")
    print("="*80 + "\n")
    conn.close()

def cmd_safety(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT feature_id, body, site_name, center_lat, center_lon,
               macro_slope_deg, elevation_mola_m, rock_abundance_percent,
               dte_visibility_fraction, ice_overburden_depth_m, plume_scour_risk_index,
               trn_visual_entropy_score, solar_incidence_glare_risk, free_air_gravity_anomaly_mgal,
               bouguer_gravity_anomaly_mgal, local_vertical_deflection_arcsec,
               nearest_fault_scarp_dist_km, peak_ground_acceleration_pga_g, landslide_runout_susceptibility,
               max_continuous_night_hours, min_winter_bolometric_temp_k, diurnal_thermal_shock_k_per_hr,
               crustal_magnetic_field_nt, terminator_surface_potential_v, electrostatic_dust_levitation_risk,
               sky_view_factor_steradians, gcr_dose_equivalent_msv_yr, albedo_neutron_flux,
               nearest_lava_tube_skylight_km, mcd_99pct_wind_gust_ms, vertical_wind_shear_s_inv,
               climatological_dust_optical_depth_tau, annual_dust_deposition_rate_microns_sol,
               cospar_planetary_protection_cat, heritage_exclusion_buffer_km, plume_orbital_contamination_risk,
               fe_o_wt_pct, ti_o2_ilmenite_wt_pct, helium3_ppb,
               perchlorate_toxicity_wt_pct, hydrated_mineral_bound_h2o_wt_pct,
               distance_to_primary_science_km, rover_traverse_energy_wh_per_km, contact_stratigraphic_diversity_count
        FROM site_engineering_safety
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.site:
        sql += " AND site_name LIKE ?"
        params.append(f"%{args.site}%")
    if args.max_slope is not None:
        sql += " AND macro_slope_deg <= ?"
        params.append(args.max_slope)
    if args.max_elevation is not None:
        sql += " AND elevation_mola_m <= ?"
        params.append(args.max_elevation)
    if args.max_rocks is not None:
        sql += " AND rock_abundance_percent <= ?"
        params.append(args.max_rocks)
    if args.min_dte is not None:
        sql += " AND dte_visibility_fraction >= ?"
        params.append(args.min_dte)
    if args.has_ice:
        sql += " AND ice_overburden_depth_m IS NOT NULL"
    if args.max_ice_depth is not None:
        sql += " AND ice_overburden_depth_m IS NOT NULL AND ice_overburden_depth_m <= ?"
        params.append(args.max_ice_depth)
    if args.max_scour is not None:
        sql += " AND plume_scour_risk_index <= ?"
        params.append(args.max_scour)

    # Domain-specific filters
    if hasattr(args, "min_trn") and args.min_trn is not None:
        sql += " AND trn_visual_entropy_score >= ?"
        params.append(args.min_trn)
    if hasattr(args, "max_pga") and args.max_pga is not None:
        sql += " AND peak_ground_acceleration_pga_g <= ?"
        params.append(args.max_pga)
    if hasattr(args, "max_night_hours") and args.max_night_hours is not None:
        sql += " AND max_continuous_night_hours <= ?"
        params.append(args.max_night_hours)
    if hasattr(args, "min_temp") and args.min_temp is not None:
        sql += " AND min_winter_bolometric_temp_k >= ?"
        params.append(args.min_temp)
    if hasattr(args, "max_radiation") and args.max_radiation is not None:
        sql += " AND gcr_dose_equivalent_msv_yr <= ?"
        params.append(args.max_radiation)
    if hasattr(args, "cospar") and args.cospar:
        sql += " AND cospar_planetary_protection_cat LIKE ?"
        params.append(f"%{args.cospar}%")
    if hasattr(args, "min_tio2") and args.min_tio2 is not None:
        sql += " AND ti_o2_ilmenite_wt_pct >= ?"
        params.append(args.min_tio2)
    if hasattr(args, "min_he3") and args.min_he3 is not None:
        sql += " AND helium3_ppb >= ?"
        params.append(args.min_he3)
    if hasattr(args, "max_perchlorate") and args.max_perchlorate is not None:
        sql += " AND perchlorate_toxicity_wt_pct <= ?"
        params.append(args.max_perchlorate)
    if hasattr(args, "max_dist_science") and args.max_dist_science is not None:
        sql += " AND distance_to_primary_science_km <= ?"
        params.append(args.max_dist_science)
    if hasattr(args, "min_diversity") and args.min_diversity is not None:
        sql += " AND contact_stratigraphic_diversity_count >= ?"
        params.append(args.min_diversity)

    sql += " ORDER BY body, macro_slope_deg ASC, rock_abundance_percent ASC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()

    view_mode = getattr(args, "view", "summary")

    titles = {
        "summary": "LANDING SITE ENGINEERING SAFETY & MULTI-DOMAIN OVERVIEW",
        "gnc": "DOMAIN 1: GNC OPTICAL NAVIGATION (TRN ENTROPY & GRAVITY ANOMALIES)",
        "tectonics": "DOMAIN 2: ACTIVE TECTONICS, SEISMIC PGA HAZARD & RUNOUT",
        "thermal": "DOMAIN 3: POWER & CRYOGENIC SURVIVAL (WORST-CASE NIGHT & SHOCK)",
        "dust": "DOMAIN 4: ELECTROSTATIC DUST LEVITATION & SURFACE CHARGING",
        "radiation": "DOMAIN 5: TOPOGRAPHIC RADIATION SHIELDING & SKY-VIEW FACTOR (SVF)",
        "atmosphere": "DOMAIN 6: MARS ATMOSPHERIC DYNAMICS, WIND SHEAR & DUST STORMS",
        "protection": "DOMAIN 7: LEGAL, HERITAGE & PLANETARY PROTECTION KEEP-OUT ZONES",
        "isru": "DOMAIN 8: ISRU FEEDSTOCK (ILMENITE, HE-3) & PERCHLORATE TOXICITY",
        "science": "DOMAIN 9: THE SCIENCE-VS-SAFETY PARADOX (STAND-OFF & DIVERSITY)",
        "all": "COMPREHENSIVE 9-DOMAIN FULL FLIGHT SPECIFICATION REPORT"
    }

    print("\n" + "="*105)
    print(f"             {titles.get(view_mode, 'LANDING SITE SAFETY EVALUATOR')}             ")
    print("="*105)
    print(f"{len(rows)} candidate landing & exploration sites returned [View Mode: {view_mode.upper()}]:\n")

    for r in rows:
        slope_flag = "✓ SAFE" if r['macro_slope_deg'] <= 10.0 else ("! MARGINAL" if r['macro_slope_deg'] <= 15.0 else "✗ HAZARD")
        rock_flag = "✓ SAFE" if r['rock_abundance_percent'] <= 7.0 else ("! MODERATE" if r['rock_abundance_percent'] <= 10.0 else "✗ HAZARD")
        
        if r['body'] == 'Mars':
            if r['elevation_mola_m'] <= -1500.0:
                edl_status = "[1;32mPASS (< -1.5km)[0m"
            else:
                edl_status = "[1;31mFAIL (> -1.5km)[0m"
        else:
            edl_status = f"{r['elevation_mola_m']:>+6.0f} m (LOLA)"

        ice_str = f"{r['ice_overburden_depth_m']:.2f} m" if r['ice_overburden_depth_m'] is not None else "None / Deep"
        dte_pct = r['dte_visibility_fraction'] * 100.0
        dte_color = "[1;32m" if dte_pct >= 70 else ("[1;33m" if dte_pct > 0 else "[1;31m")

        print(f"[{r['body']:<4}] [1m{r['site_name']}[0m (IAU #{r['feature_id']})")
        print(f"       Coords: Lat {r['center_lat']:>7.2f}°, Lon {r['center_lon']:>7.2f}° | Elevation: {edl_status}")
        print(f"       Slope:  {r['macro_slope_deg']:>4.1f}° [{slope_flag:<10}] | Rocks: {r['rock_abundance_percent']:>4.1f}% [{rock_flag:<10}]")
        print(f"       DTE LoS Comms: {dte_color}{r['dte_visibility_fraction']:.2f} ({dte_pct:>5.1f}%)[0m | Ice Overburden: {ice_str:<12} | Plume Scour Index: {r['plume_scour_risk_index']:.2f}")

        if view_mode in ("summary", "all"):
            print(f"       --- 9-Domain Highlights ---")
            print(f"       • GNC & Gravity:    TRN Entropy: {r['trn_visual_entropy_score']:.2f} | Glare: {r['solar_incidence_glare_risk']} | FA Grav: {r['free_air_gravity_anomaly_mgal']:>+6.1f} mGal")
            print(f"       • Active Tectonics: Scarp Dist: {r['nearest_fault_scarp_dist_km']:>5.1f} km | PGA Shaking: {r['peak_ground_acceleration_pga_g']:>4.2f}g | Runout: {r['landslide_runout_susceptibility']}")
            print(f"       • Cryo & Thermal:   Max Night: {r['max_continuous_night_hours']:>6.1f} hrs | Min Temp: {r['min_winter_bolometric_temp_k']:>5.1f} K | Sunset Drop: {r['diurnal_thermal_shock_k_per_hr']:>4.1f} K/hr")
            print(f"       • Dust & Potential: Crustal B: {r['crustal_magnetic_field_nt']:>5.1f} nT | Terminator V: {r['terminator_surface_potential_v']:>+6.0f} V | Levitation: {r['electrostatic_dust_levitation_risk']}")
            print(f"       • Radiation & SVF:  Sky-View: {r['sky_view_factor_steradians']:>4.2f} sr | GCR Dose: {r['gcr_dose_equivalent_msv_yr']:>5.1f} mSv/yr | Lava Tube: {r['nearest_lava_tube_skylight_km']:>6.1f} km")
            if r['body'] == 'Mars':
                print(f"       • Mars Atmosphere:  Peak Gust: {r['mcd_99pct_wind_gust_ms']:>4.1f} m/s | Shear: {r['vertical_wind_shear_s_inv']:>5.3f} s^-1 | Dust Tau: {r['climatological_dust_optical_depth_tau']:>4.2f} | Deposition: {r['annual_dust_deposition_rate_microns_sol']:>4.2f} µm/sol")
            print(f"       • Legal & Heritage: COSPAR: {r['cospar_planetary_protection_cat']} | Buffer: {r['heritage_exclusion_buffer_km']:.1f} km | Plume Hazard: {r['plume_orbital_contamination_risk']}")
            if r['body'] == 'Moon':
                print(f"       • ISRU Feedstock:   Ilmenite TiO2: {r['ti_o2_ilmenite_wt_pct']:>4.1f} wt% | FeO: {r['fe_o_wt_pct']:>4.1f} wt% | He-3: {r['helium3_ppb']:>4.1f} ppb | Bound H2O: {r['hydrated_mineral_bound_h2o_wt_pct']:>4.1f} wt%")
            else:
                print(f"       • ISRU & Toxicity:  Perchlorate Tox: {r['perchlorate_toxicity_wt_pct']:>4.2f} wt% | FeO: {r['fe_o_wt_pct']:>4.1f} wt% | Extractable H2O: {r['hydrated_mineral_bound_h2o_wt_pct']:>4.1f} wt%")
            print(f"       • Science Paradox:  Stand-off to Science: {r['distance_to_primary_science_km']:>4.1f} km | Traverse Energy: {r['rover_traverse_energy_wh_per_km']:>5.1f} Wh/km | Epoch Diversity: {r['contact_stratigraphic_diversity_count']}")

        elif view_mode == "gnc":
            ent_rating = "[1;32mEXCELLENT[0m" if r['trn_visual_entropy_score'] >= 0.70 else ("[1;33mMODERATE[0m" if r['trn_visual_entropy_score'] >= 0.40 else "[1;31mPOOR/CORRELATION DROPOUT[0m")
            print(f"       GNC Optical TRN Entropy: {r['trn_visual_entropy_score']:.2f} [{ent_rating}] | Glare/Surge: {r['solar_incidence_glare_risk']}")
            print(f"       Free-Air Gravity: {r['free_air_gravity_anomaly_mgal']:>+7.1f} mGal | Bouguer Anomaly: {r['bouguer_gravity_anomaly_mgal']:>+7.1f} mGal | Deflection: {r['local_vertical_deflection_arcsec']:>5.1f}\"")

        elif view_mode == "tectonics":
            scarp_flag = "[1;31mIMMEDIATE SCARP HAZARD (<5km)[0m" if r['nearest_fault_scarp_dist_km'] <= 5.0 else ("[1;33mMODERATE PROXIMITY[0m" if r['nearest_fault_scarp_dist_km'] <= 20.0 else "[1;32mSTABLE FAR FIELD[0m")
            print(f"       Nearest Lobate Fault Scarp: {r['nearest_fault_scarp_dist_km']:>6.1f} km [{scarp_flag}]")
            print(f"       PGA Seismic Shaking Hazard: {r['peak_ground_acceleration_pga_g']:>5.2f}g | Landslide Runout: {r['landslide_runout_susceptibility']}")

        elif view_mode == "thermal":
            night_flag = "[1;32mSHORT ECLIPSE (<100h)[0m" if r['max_continuous_night_hours'] <= 100.0 else ("[1;33mEQUATORIAL NIGHT (~354h)[0m" if r['max_continuous_night_hours'] <= 400.0 else "[1;31mCRYOGENIC PSR PERPETUAL FREEZE[0m")
            print(f"       Max Continuous Night / Eclipse: {r['max_continuous_night_hours']:>8.1f} hrs [{night_flag}]")
            print(f"       Min Winter Surface Temp: {r['min_winter_bolometric_temp_k']:>5.1f} K | Diurnal Thermal Shock Rate: {r['diurnal_thermal_shock_k_per_hr']:>4.1f} K/hr")

        elif view_mode == "dust":
            b_flag = "[1;32mMINI-MAGNETOSPHERE (>100 nT)[0m" if r['crustal_magnetic_field_nt'] >= 100.0 else "NOMINAL AMBIENT"
            print(f"       Crustal Magnetic Field: {r['crustal_magnetic_field_nt']:>6.1f} nT [{b_flag}]")
            print(f"       Terminator Electrostatic Potential: {r['terminator_surface_potential_v']:>+6.0f} V | Dust Levitation Hazard: {r['electrostatic_dust_levitation_risk']}")

        elif view_mode == "radiation":
            svf_pct = (r['sky_view_factor_steradians'] / 6.283185) * 100.0
            print(f"       Topographic Sky-View Factor (SVF): {r['sky_view_factor_steradians']:>4.2f} sr ({svf_pct:>5.1f}% 2π) | GCR Dose: {r['gcr_dose_equivalent_msv_yr']:>5.1f} mSv/yr")
            print(f"       Albedo Secondary Neutron Flux: {r['albedo_neutron_flux']:>4.2f} | Nearest Subsurface Lava Tube Pit: {r['nearest_lava_tube_skylight_km']:>6.1f} km")

        elif view_mode == "atmosphere":
            if r['body'] == 'Mars':
                print(f"       MCD 99% Peak Wind Gust: {r['mcd_99pct_wind_gust_ms']:>4.1f} m/s | Vertical Wind Shear (dU/dz): {r['vertical_wind_shear_s_inv']:>5.3f} s^-1")
                print(f"       Climatological Dust Optical Depth: {r['climatological_dust_optical_depth_tau']:>4.2f} tau | Annual Dust Deposition: {r['annual_dust_deposition_rate_microns_sol']:>4.2f} µm/sol")
            else:
                print(f"       Atmospheric Dynamics: Vacuum Exosphere (0.0 m/s wind, 0.0 tau dust extinction)")

        elif view_mode == "protection":
            print(f"       COSPAR Planetary Protection: {r['cospar_planetary_protection_cat']}")
            print(f"       Historic Heritage Buffer: {r['heritage_exclusion_buffer_km']:>4.1f} km exclusion perimeter | Rocket Plume Contamination: {r['plume_orbital_contamination_risk']}")

        elif view_mode == "isru":
            print(f"       Regolith FeO: {r['fe_o_wt_pct']:>4.1f} wt% | Ilmenite TiO2: {r['ti_o2_ilmenite_wt_pct']:>4.1f} wt% | Solar Wind He-3: {r['helium3_ppb']:>4.1f} ppb")
            print(f"       Soil Perchlorate Toxicity: {r['perchlorate_toxicity_wt_pct']:>4.2f} wt% | Hydrated / Glacial Water H2O: {r['hydrated_mineral_bound_h2o_wt_pct']:>4.1f} wt%")

        elif view_mode == "science":
            print(f"       Stand-off Distance to Primary Science: {r['distance_to_primary_science_km']:>4.1f} km")
            print(f"       Rover Traverse Mobility Energy: {r['rover_traverse_energy_wh_per_km']:>5.1f} Wh/km | Contact Stratigraphic Diversity: {r['contact_stratigraphic_diversity_count']} epochs")

        print("-" * 105)
    print("="*105 + "\n")
    conn.close()

def cmd_landers(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT lander_id, target_body, lander_name, organization, mission_phase_status,
               footprint_span_m, touchdown_mass_kg, max_tolerable_slope_deg,
               max_tolerable_rock_height_m, max_horizontal_velocity_mps, max_vertical_velocity_mps,
               edl_architecture, edl_altitude_envelope_max_mola_m, min_bearing_capacity_kpa,
               max_plume_dynamic_pressure_kpa, comms_architecture, engineering_reference
        FROM lander_engineering_constraints
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND target_body = ?"
        params.append(args.body.capitalize())
    if args.name:
        sql += " AND (lander_name LIKE ? OR lander_id LIKE ?)"
        params.append(f"%{args.name}%")
        params.append(f"%{args.name}%")
    if args.edl_type:
        sql += " AND edl_architecture LIKE ?"
        params.append(f"%{args.edl_type}%")
    if args.max_slope is not None:
        sql += " AND max_tolerable_slope_deg >= ?"
        params.append(args.max_slope)

    sql += " ORDER BY target_body, touchdown_mass_kg DESC;"
    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*95)
    print("                  LANDER DYNAMICS & EDL ENGINEERING CONSTRAINTS                  ")
    print("="*95)
    print(f"{len(rows)} flight vehicle engineering envelopes returned:\n")

    for r in rows:
        edl_env = f"<= {r['edl_altitude_envelope_max_mola_m']:.0f} m MOLA" if r['edl_altitude_envelope_max_mola_m'] is not None else "N/A (Lunar Airless)"
        mass_str = f"{r['touchdown_mass_kg']:>8,.0f} kg"
        print(f"[{r['target_body']:<4}] \033[1m{r['lander_name']}\033[0m [{r['organization']}] - {r['mission_phase_status']}")
        print(f"       Gear Span: {r['footprint_span_m']:>4.1f} m | Mass: {mass_str} | Slope Limit: <= {r['max_tolerable_slope_deg']}° | Rock Clearance: {r['max_tolerable_rock_height_m']:.2f} m")
        print(f"       Velocity Envelopes: Horiz <= {r['max_horizontal_velocity_mps']:.1f} m/s, Vert <= {r['max_vertical_velocity_mps']:.1f} m/s | EDL Elevation Envelope: {edl_env}")
        print(f"       EDL Mode: {r['edl_architecture']}")
        print(f"       Soil Bearing Required: >= {r['min_bearing_capacity_kpa']:.1f} kPa | Plume Stagnation Pressure: {r['max_plume_dynamic_pressure_kpa']:.1f} kPa")
        print(f"       Comms Link: {r['comms_architecture']}")
        print(f"       Source: \033[36m{r['engineering_reference']}\033[0m")
        print("-" * 95)
    print("="*95 + "\n")
    conn.close()

def cmd_geotechnics(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT terrain_id, body, terrain_name, representative_feature,
               bulk_density_g_cm3, porosity_pct, cohesion_kpa, internal_friction_angle_deg,
               bearing_capacity_kpa, fine_component_thermal_inertia_si, dust_mantling_level,
               threshold_friction_velocity_mps, plume_erosion_rate_kg_m2_s, plume_scour_risk_index,
               blast_ejecta_hazard, data_sources
        FROM regolith_geotechnics_psi
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.terrain:
        sql += " AND (terrain_name LIKE ? OR representative_feature LIKE ?)"
        params.append(f"%{args.terrain}%")
        params.append(f"%{args.terrain}%")

    sql += " ORDER BY body, plume_scour_risk_index ASC;"
    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*95)
    print("             REGOLITH GEOTECHNICS & PLUME-SURFACE INTERACTION (PSI)             ")
    print("="*95)
    print(f"{len(rows)} geotechnical regolith units returned:\n")

    for r in rows:
        print(f"[{r['body']:<4}] \033[1m{r['terrain_name']}\033[0m")
        print(f"       Features: {r['representative_feature']}")
        print(f"       Bulk Density: {r['bulk_density_g_cm3']:.2f} g/cm³ | Porosity: {r['porosity_pct']:.1f}% | Cohesion: {r['cohesion_kpa']:.2f} kPa | Friction Angle (φ): {r['internal_friction_angle_deg']:.1f}°")
        print(f"       Ultimate Bearing Capacity: {r['bearing_capacity_kpa']:.1f} kPa | Fine Thermal Inertia: {r['fine_component_thermal_inertia_si']:.1f} SI [{r['dust_mantling_level']}]")
        print(f"       Threshold Friction Vel: {r['threshold_friction_velocity_mps']:.1f} m/s | Plume Erosion: {r['plume_erosion_rate_kg_m2_s']:.1f} kg/(m²·s) | Scour Risk Index: {r['plume_scour_risk_index']:.2f}")
        print(f"       Blast Hazard: \033[1;31m{r['blast_ejecta_hazard']}\033[0m")
        print(f"       Data: {r['data_sources']}")
        print("-" * 95)
    print("="*95 + "\n")
    conn.close()

def cmd_telecom(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT site_id, body, site_name, latitude_deg, longitude_deg,
               dte_visibility_fraction, earth_elevation_min_deg, earth_elevation_max_deg,
               dsn_visibility_hours_per_day, relay_orbiter_support, relay_passes_per_sol,
               mean_pass_duration_min, daily_data_volume_mb, comms_blackout_hazard, horizon_mask_source
        FROM telecom_relay_visibility
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.site:
        sql += " AND site_name LIKE ?"
        params.append(f"%{args.site}%")
    if args.min_dte is not None:
        sql += " AND dte_visibility_fraction >= ?"
        params.append(args.min_dte)

    sql += " ORDER BY body, dte_visibility_fraction DESC;"
    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*95)
    print("         DIRECT-TO-EARTH (DTE) LINE-OF-SIGHT & ORBITER RELAY TELECOMMUNICATIONS         ")
    print("="*95)
    print(f"{len(rows)} telecommunications profiles returned:\n")

    for r in rows:
        dte_pct = r['dte_visibility_fraction'] * 100.0
        dte_color = "\033[1;32m" if dte_pct >= 70 else ("\033[1;33m" if dte_pct > 0 else "\033[1;31m")
        print(f"[{r['body']:<4}] \033[1m{r['site_name']}\033[0m (Lat {r['latitude_deg']:.2f}°, Lon {r['longitude_deg']:.2f}°)")
        print(f"       DTE Line-of-Sight: {dte_color}{r['dte_visibility_fraction']:.2f} ({dte_pct:.1f}%)\033[0m | Earth Horizon Elevation: [{r['earth_elevation_min_deg']:>+5.1f}°, {r['earth_elevation_max_deg']:>+5.1f}°] | DSN Visibility: {r['dsn_visibility_hours_per_day']:.1f} hrs/day")
        print(f"       Relay Infrastructure: {r['relay_orbiter_support']}")
        print(f"       Relay Overflights: {r['relay_passes_per_sol']:.1f} passes/sol (avg {r['mean_pass_duration_min']:.1f} min/pass) | Data Return: {r['daily_data_volume_mb']:,.0f} Mbit/sol")
        print(f"       Comms Risk / Blackout: \033[33m{r['comms_blackout_hazard']}\033[0m")
        print(f"       Horizon Mask Model: {r['horizon_mask_source']}")
        print("-" * 95)
    print("="*95 + "\n")
    conn.close()

def cmd_hazards(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT hazard_id, body, site_name, feature_id, rock_abundance_percent,
               mean_rock_height_m, sfd_slope_q, density_rocks_gt_0_5m_per_m2,
               density_rocks_gt_1_0m_per_m2, tip_over_probability_percent,
               cpr_roughness_ratio, hazard_classification, data_instrument
        FROM rock_hazard_sfd
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.max_rocks is not None:
        sql += " AND rock_abundance_percent <= ?"
        params.append(args.max_rocks)
    if args.classification:
        sql += " AND hazard_classification LIKE ?"
        params.append(f"%{args.classification}%")

    sql += " ORDER BY body, rock_abundance_percent ASC;"
    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*95)
    print("          ROCK SIZE-FREQUENCY DISTRIBUTION (SFD) & BOULDER HAZARD DENSITY          ")
    print("="*95)
    print(f"{len(rows)} rock SFD profiles returned:\n")

    for r in rows:
        tip_color = "\033[1;32m" if r['tip_over_probability_percent'] < 2.0 else ("\033[1;33m" if r['tip_over_probability_percent'] < 5.0 else "\033[1;31m")
        print(f"[{r['body']:<4}] \033[1m{r['site_name']}\033[0m [{r['hazard_classification']}]")
        print(f"       Rock Abundance: {r['rock_abundance_percent']:.1f}% | Mean Rock Height: {r['mean_rock_height_m']:.2f} m | SFD Slope (q): {r['sfd_slope_q']:.2f}")
        print(f"       Boulders > 0.5m: {r['density_rocks_gt_0_5m_per_m2']:.5f} /m² | Boulders > 1.0m: {r['density_rocks_gt_1_0m_per_m2']:.5f} /m²")
        print(f"       Lander Tip-Over Probability: {tip_color}{r['tip_over_probability_percent']:.1f}%\033[0m | CPR Roughness Ratio: {r['cpr_roughness_ratio']:.2f}")
        print(f"       Instrument: \033[36m{r['data_instrument']}\033[0m")
        print("-" * 95)
    print("="*95 + "\n")
    conn.close()

def cmd_matrix(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT site_id, feature_id, body, program_catalog, site_name, region_parent,
               center_lat, center_lon, elevation_datum_m, macro_slope_100m_deg, micro_slope_5m_deg,
               trn_optical_entropy_score, bouguer_gravity_anomaly_mgal, mcd_99pct_wind_shear_ms,
               rock_abundance_pct, golombek_sfd_q, prob_1m_boulder_in_footprint, bearing_capacity_kpa,
               plume_scour_risk_index, nearest_active_fault_km, seismic_pga_hazard_g,
               annual_sunlight_fraction, max_continuous_eclipse_hrs, min_bolometric_temp_k, max_bolometric_temp_k,
               sky_view_factor_sr, radiation_dose_msv_yr, crustal_mag_field_nt, terminator_charging_volts,
               dte_visibility_fraction, relay_data_volume_mbit_sol, ice_overburden_depth_m,
               water_equiv_hydrogen_wt_pct, ilmenite_ti_o2_wt_pct, hydrated_mineral_wt_pct,
               perchlorate_toxicity_wt_pct, subsurface_dielectric_permittivity, distance_to_science_target_km,
               traverse_slope_cost_wh_km, stratigraphic_epochs_accessible, nearest_skylight_cave_km,
               cospar_protection_category, heritage_keepout_violation
        FROM site_candidate_matrix
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.catalog:
        sql += " AND program_catalog LIKE ?"
        params.append(f"%{args.catalog}%")
    if args.site:
        sql += " AND site_name LIKE ?"
        params.append(f"%{args.site}%")
    if args.max_slope is not None:
        sql += " AND micro_slope_5m_deg <= ?"
        params.append(args.max_slope)
    if args.max_rocks is not None:
        sql += " AND rock_abundance_pct <= ?"
        params.append(args.max_rocks)
    if args.min_bearing is not None:
        sql += " AND bearing_capacity_kpa >= ?"
        params.append(args.min_bearing)

    sql += " ORDER BY body, micro_slope_5m_deg ASC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*100)
    print("       EXPANDED SITE ENGINEERING, ENVIRONMENTAL & OPERATIONAL TRADE-SPACE MATRIX       ")
    print("="*100)
    print(f"{len(rows)} site candidates returned:\n")

    for r in rows:
        ice_info = f"{r['ice_overburden_depth_m']:.2f} m" if r['ice_overburden_depth_m'] is not None else "None"
        keepout_str = "\033[1;31mYES (Historic Keep-out)\033[0m" if r['heritage_keepout_violation'] else "\033[1;32mNO\033[0m"
        print(f"[{r['body']:<4}] \033[1m{r['site_name']}\033[0m | Catalog: \033[36m{r['program_catalog']}\033[0m (IAU #{r['feature_id']})")
        print(f"       Region: {r['region_parent']} | Coords: ({r['center_lat']:+.2f}°, {r['center_lon']:+.2f}°) | Datum: {r['elevation_datum_m']:+,.0f} m")
        print(f"       Slopes: 100m: {r['macro_slope_100m_deg']:.1f}°, 5m leg: {r['micro_slope_5m_deg']:.1f}° | Rocks: {r['rock_abundance_pct']:.1f}% | Bearing: {r['bearing_capacity_kpa']:.0f} kPa")
        print(f"       Thermal/Sun: Sun {r['annual_sunlight_fraction']*100:.0f}%, Max Eclipse {r['max_continuous_eclipse_hrs']:.1f}h | Temp: [{r['min_bolometric_temp_k']:.0f}K, {r['max_bolometric_temp_k']:.0f}K]")
        print(f"       ISRU / Hazards: Ice: {ice_info} (WEH: {r['water_equiv_hydrogen_wt_pct']:.1f} wt%) | COSPAR: {r['cospar_protection_category']} | Keep-out: {keepout_str}")
        print("-" * 100)
    print("="*100 + "\n")
    conn.close()

def cmd_compat(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT body, site_name, program_catalog, vehicle_name, agency_provider, qualification_status
        FROM v_lander_site_compatibility
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.vehicle:
        sql += " AND vehicle_name LIKE ?"
        params.append(f"%{args.vehicle}%")
    if args.site:
        sql += " AND site_name LIKE ?"
        params.append(f"%{args.site}%")
    if args.status:
        sql += " AND qualification_status LIKE ?"
        params.append(f"%{args.status}%")

    sql += " ORDER BY body, vehicle_name, qualification_status, site_name LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*105)
    print("               DYNAMIC SUB-ORBITAL PLUME & LANDER VEHICLE COMPATIBILITY EVALUATION               ")
    print("="*105)
    print(f"{len(rows)} evaluations returned:\n")

    for r in rows:
        status = r['qualification_status']
        if status == 'QUALIFIED':
            status_str = f"\033[1;32m{status}\033[0m"
        else:
            status_str = f"\033[1;31m{status}\033[0m"
        print(f"[{r['body']:<4}] Vehicle: \033[1m{r['vehicle_name']}\033[0m ({r['agency_provider']})")
        print(f"       Site: {r['site_name']} [{r['program_catalog']}]")
        print(f"       Qualification: {status_str}")
        print("-" * 105)
    print("="*105 + "\n")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Master Database CLI for Moon and Mars")
    subparsers = parser.add_subparsers(dest="command")

    # Stats
    subparsers.add_parser("stats", help="Show database overview and total record counts")

    # Search
    p_search = subparsers.add_parser("search", help="Perform full-text search across all database records")
    p_search.add_argument("query", help="Keywords to search (e.g., 'water ice', 'Apollo 11', 'Jezero')")
    p_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # Features
    p_feat = subparsers.add_parser("features", help="Query official IAU planetary features")
    p_feat.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_feat.add_argument("--type", help="Filter by feature type (e.g. Crater, Mare, Mons, Vallis)")
    p_feat.add_argument("--min-diam", type=float, help="Minimum diameter in km")
    p_feat.add_argument("--limit", type=int, default=15, help="Max results (default: 15)")

    # Missions
    p_miss = subparsers.add_parser("missions", help="Query space missions catalog")
    p_miss.add_argument("--body", choices=["Moon", "Mars"], help="Filter by target body")
    p_miss.add_argument("--agency", help="Filter by agency or country (e.g. NASA, ESA, ISRO, USSR)")

    # Landing Sites
    p_sites = subparsers.add_parser("sites", help="Query landing and surface hardware sites")
    p_sites.add_argument("--body", choices=["Moon", "Mars"], help="Filter by body")

    # Samples
    p_samp = subparsers.add_parser("samples", help="Query returned lunar samples")
    p_samp.add_argument("--mission", help="Filter by mission (e.g. Apollo 11, Apollo 17, Chang'e 5)")
    p_samp.add_argument("--rock-class", help="Filter by rock class (e.g. Basalt, Breccia, Soil)")
    p_samp.add_argument("--min-weight", type=float, help="Minimum weight in grams")
    p_samp.add_argument("--limit", type=int, default=15, help="Max results (default: 15)")

    # Meteorites
    p_met = subparsers.add_parser("meteorites", help="Query Martian meteorites catalog")
    p_met.add_argument("--classification", help="Filter by petrologic classification")
    p_met.add_argument("--limit", type=int, default=15, help="Max results (default: 15)")

    # Weather
    subparsers.add_parser("weather", help="Inspect surface weather and meteorological logs")

    # Ice
    subparsers.add_parser("ice", help="Inspect polar and subsurface water ice reservoirs")

    # Compare
    subparsers.add_parser("compare", help="Compare physical constants between Moon, Mars, and Earth")

    # Rasters
    p_ras = subparsers.add_parser("rasters", help="Query PDS/USGS/JAXA/ESA remote sensing rasters and direct endpoints")
    p_ras.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_ras.add_argument("--category", help="Filter by category (e.g. DEM, Slopes, Volatiles, Thermal)")
    p_ras.add_argument("--target", help="Filter by target feature or keyword (e.g. Shackleton, Jezero, Gale, Arcadia)")
    p_ras.add_argument("--mission", help="Filter by mission (e.g. LRO, Kaguya, MRO, Odyssey)")
    p_ras.add_argument("--format", help="Filter by format (e.g. GeoTIFF, IMG, JP2, Table)")
    p_ras.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # Safety
    p_saf = subparsers.add_parser("safety", help="Evaluate landing site engineering safety across 9 planetary science & physics domains")
    p_saf.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_saf.add_argument("--site", help="Filter by site name keyword")
    p_saf.add_argument("--view", choices=["summary", "all", "gnc", "tectonics", "thermal", "dust", "radiation", "atmosphere", "protection", "isru", "science"], default="summary", help="Domain view mode (default: summary)")
    p_saf.add_argument("--max-slope", type=float, help="Maximum tolerable macro-slope in degrees (<= 10° ideal)")
    p_saf.add_argument("--max-elevation", type=float, help="Maximum elevation in meters (critical for Mars EDL, <= -1500m)")
    p_saf.add_argument("--max-rocks", type=float, help="Maximum rock abundance percentage (<= 7%% safe)")
    p_saf.add_argument("--min-dte", type=float, help="Minimum direct-to-Earth (DTE) visibility fraction (0.0 to 1.0)")
    p_saf.add_argument("--has-ice", action="store_true", help="Only show sites with shallow accessible water ice")
    p_saf.add_argument("--max-ice-depth", type=float, help="Maximum ice overburden depth in meters (e.g. 1.0m)")
    p_saf.add_argument("--max-scour", type=float, help="Maximum plume scour risk index (0.0 to 1.0)")
    p_saf.add_argument("--min-trn", type=float, help="Minimum TRN visual entropy score (0.0 to 1.0)")
    p_saf.add_argument("--max-pga", type=float, help="Maximum tolerable PGA seismic shaking in g")
    p_saf.add_argument("--max-night-hours", type=float, help="Maximum continuous shadow/eclipse duration in hours")
    p_saf.add_argument("--min-temp", type=float, help="Minimum allowable surface bolometric temperature in K")
    p_saf.add_argument("--max-radiation", type=float, help="Maximum annual GCR dose in mSv/yr")
    p_saf.add_argument("--cospar", help="Filter by COSPAR planetary protection category keyword")
    p_saf.add_argument("--min-tio2", type=float, help="Minimum ilmenite TiO2 abundance (wt%%)")
    p_saf.add_argument("--min-he3", type=float, help="Minimum Helium-3 concentration (ppb)")
    p_saf.add_argument("--max-perchlorate", type=float, help="Maximum soil perchlorate toxicity (wt%%)")
    p_saf.add_argument("--max-dist-science", type=float, help="Maximum stand-off distance to primary science (km)")
    p_saf.add_argument("--min-diversity", type=int, help="Minimum stratigraphic diversity count")
    p_saf.add_argument("--limit", type=int, default=25, help="Max results (default: 25)")

    # Landers
    p_lan = subparsers.add_parser("landers", help="Query lander vehicle engineering envelopes (Starship, Nova-C, Sky Crane, etc.)")
    p_lan.add_argument("--body", choices=["Moon", "Mars"], help="Filter by target body")
    p_lan.add_argument("--name", help="Filter by lander name or id")
    p_lan.add_argument("--edl-type", help="Filter by EDL architecture (e.g. propulsive, sky crane, parachute, airbag)")
    p_lan.add_argument("--max-slope", type=float, help="Minimum slope tolerance required in degrees")

    # Geotechnics & PSI
    p_geo = subparsers.add_parser("geotechnics", help="Query regolith geotechnics, soil mechanics, bearing capacity, and plume scour")
    p_geo.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_geo.add_argument("--terrain", help="Filter by terrain name or representative feature keyword")

    # Telecom & DSN Visibility
    p_tel = subparsers.add_parser("telecom", help="Query Earth DSN line-of-sight visibility and Mars orbiter relay windows")
    p_tel.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_tel.add_argument("--site", help="Filter by site name")
    p_tel.add_argument("--min-dte", type=float, help="Minimum DTE visibility fraction (0.0 to 1.0)")

    # Boulder Hazards & SFD
    p_haz = subparsers.add_parser("hazards", help="Query rock size-frequency distributions (SFD), boulder density, and tip-over risks")
    p_haz.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_haz.add_argument("--max-rocks", type=float, help="Maximum rock abundance percentage")
    p_haz.add_argument("--classification", help="Filter by hazard classification (e.g. Low, Moderate, Extreme)")

    # Site Candidate Matrix (43 Fields Trade-Space)
    p_mat = subparsers.add_parser("matrix", help="Query expanded site candidate trade-space matrix (43 geodesy, thermal, ISRU fields)")
    p_mat.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_mat.add_argument("--catalog", help="Filter by program catalog (e.g. Artemis_III, CLPS, Mars_HLS2_EZ, M2020_Perseverance)")
    p_mat.add_argument("--site", help="Filter by site name keyword")
    p_mat.add_argument("--max-slope", type=float, help="Maximum micro-slope (5m gear baseline) in degrees")
    p_mat.add_argument("--max-rocks", type=float, help="Maximum rock abundance percentage")
    p_mat.add_argument("--min-bearing", type=float, help="Minimum Terzaghi bearing capacity in kPa")
    p_mat.add_argument("--limit", type=int, default=15, help="Max results (default: 15)")

    # Lander Compatibility Dynamic Join View
    p_cmp = subparsers.add_parser("compat", help="Evaluate dynamic lander vehicle vs candidate site compatibility (v_lander_site_compatibility)")
    p_cmp.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_cmp.add_argument("--vehicle", help="Filter by lander/vehicle name (e.g. Starship, Nova-C, Perseverance, Sky Crane)")
    p_cmp.add_argument("--site", help="Filter by site name keyword")
    p_cmp.add_argument("--status", help="Filter by qualification status (e.g. QUALIFIED, Slope, Density, Eclipse, Boulder, Footpad, Keep-Out)")
    p_cmp.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "stats": cmd_stats,
        "search": cmd_search,
        "features": cmd_features,
        "missions": cmd_missions,
        "sites": cmd_sites,
        "samples": cmd_samples,
        "meteorites": cmd_meteorites,
        "weather": cmd_weather,
        "ice": cmd_ice,
        "compare": cmd_compare,
        "rasters": cmd_rasters,
        "safety": cmd_safety,
        "landers": cmd_landers,
        "geotechnics": cmd_geotechnics,
        "telecom": cmd_telecom,
        "hazards": cmd_hazards,
        "matrix": cmd_matrix,
        "compat": cmd_compat
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()

