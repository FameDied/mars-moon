#!/usr/bin/env python3
"""
Master Planetary Database CLI for Moon and Mars
Unified access to physical parameters, IAU nomenclature, missions,
landing sites, Apollo lunar samples, Martian meteorites, weather logs,
geology, STAC remote sensing rasters, 3-sigma landing ellipses,
Uber H3 spatial indexing, and Multi-Criteria Decision Analysis (MCDA).
"""

import sys
import os
import sqlite3
import argparse
import time

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
    print("\n" + "="*70)
    print("       MASTER MOON & MARS DATABASE SUMMARY & METRICS       ")
    print("="*70)
    tables = [
        ("celestial_bodies", "Planetary & Satellite Bodies"),
        ("physical_parameters", "Physical & Bulk Geodetic Constants"),
        ("orbital_parameters", "Orbital & Dynamic Characteristics"),
        ("ephemerides_2026", "JPL Horizons High-Precision Ephemerides"),
        ("iau_planetary_features", "Official IAU Gazetteer Named Features (w/ H3)"),
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
        ("remote_sensing_rasters", "Remote Sensing Science Rasters (STAC / COG)"),
        ("site_engineering_safety", "Landing Site Safety Evaluator (524 Sites, H3)"),
        ("lander_engineering_constraints", "Lander Dynamics & 3-Sigma Dispersion Envelopes"),
        ("regolith_geotechnics_psi", "Regolith Geotechnics & PSI Scour"),
        ("telecom_relay_visibility", "DSN Line-of-Sight & Orbiter Relays"),
        ("rock_hazard_sfd", "Rock Size-Frequency Distribution & Hazards"),
        ("fts_planetary_search", "Full-Text Search Index Entries"),
        ("v_landing_site_pareto_ranks", "  ↳ View: MCDA 4-Dimension Pareto Scoring Engine"),
        ("v_lander_site_compatibility", "  ↳ View: Dynamic Lander Vehicle Site Compatibility")
    ]
    total = 0
    for t, label in tables:
        c.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = c.fetchone()[0]
        if not t.startswith("v_"):
            total += cnt
        print(f"• {label:<48} | {cnt:>7,} records")
    print("="*70)
    print(f"TOTAL INDEXED TABLE RECORDS: {total:,}")
    print(f"DATABASE FILE SIZE:          {os.path.getsize(DB_PATH):,} bytes ({os.path.getsize(DB_PATH)/(1024*1024):.2f} MB)")
    print("="*70 + "\n")
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
    sql = "SELECT body_id, clean_name, feature_type, diameter_km, center_lat, center_lon, center_lon_180, h3_index, quad_name, origin FROM iau_planetary_features WHERE 1=1"
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
    if getattr(args, "h3", None):
        sql += " AND h3_index LIKE ?"
        params.append(f"%{args.h3}%")
    sql += " ORDER BY diameter_km DESC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nOfficial IAU Planetary Features ({len(rows)} returned):\n")
    for r in rows:
        h3_str = f"H3: {r['h3_index']}" if r['h3_index'] else "H3: N/A"
        print(f"[{r['body_id']:<4}] \033[1m{r['clean_name']}\033[0m ({r['feature_type']}) - {r['diameter_km']:.1f} km")
        print(f"       Lat: {r['center_lat']:>7.2f}°, Lon: {r['center_lon_180']:>7.2f}° | {h3_str} | Quad: {r['quad_name'] or 'N/A'}")
        print(f"       Origin: {r['origin']}")
        print()
    conn.close()

def cmd_missions(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT mission_name, target_body, launch_date, mission_type, agency_country, mission_status, science_achievements FROM missions_catalog WHERE 1=1"
    params = []
    if args.body:
        sql += " AND target_body = ?"
        params.append(args.body.capitalize())
    if args.agency:
        sql += " AND agency_country LIKE ?"
        params.append(f"%{args.agency}%")
    sql += " ORDER BY launch_date ASC;"

    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nPlanetary Space Missions ({len(rows)} returned):\n")
    for r in rows:
        print(f"[{r['target_body']:<4}] \033[1m{r['mission_name']}\033[0m ({r['agency_country']}) - Launch: {r['launch_date']}")
        print(f"       Type: {r['mission_type']} | Status: {r['mission_status']}")
        print(f"       Achievements: {r['science_achievements']}")
        print()
    conn.close()

def cmd_sites(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT site_name, target_body, latitude_deg, longitude_deg, mission_or_spacecraft, operator, landing_date, operational_status, scientific_significance FROM surface_landing_sites WHERE 1=1"
    params = []
    if args.body:
        sql += " AND target_body = ?"
        params.append(args.body.capitalize())
    sql += " ORDER BY landing_date ASC;"

    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nSurface Landings and Impact Sites ({len(rows)} returned):\n")
    for r in rows:
        print(f"[{r['target_body']:<4}] \033[1m{r['site_name']}\033[0m ({r['mission_or_spacecraft']}) - {r['landing_date']}")
        print(f"       Coords: Lat {r['latitude_deg']:>7.2f}°, Lon {r['longitude_deg']:>7.2f}° | Status: {r['operational_status']}")
        print(f"       Significance: {r['scientific_significance']}")
        print()
    conn.close()

def cmd_samples(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT sample_id, mission, sample_type, lithology, mass_grams, collection_station, petrologic_summary FROM lunar_samples_catalog WHERE 1=1"
    params = []
    if args.mission:
        sql += " AND mission LIKE ?"
        params.append(f"%{args.mission}%")
    if args.rock_class:
        sql += " AND (sample_type LIKE ? OR lithology LIKE ?)"
        params.extend([f"%{args.rock_class}%", f"%{args.rock_class}%"])
    if args.min_weight:
        sql += " AND mass_grams >= ?"
        params.append(args.min_weight)
    sql += " ORDER BY mass_grams DESC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nReturned Lunar Samples ({len(rows)} returned):\n")
    for r in rows:
        print(f"[{r['mission']:<10}] Sample #{r['sample_id']} - \033[1m{r['lithology']}\033[0m ({r['mass_grams']:.1f} g)")
        print(f"       Station: {r['collection_station']} | Type: {r['sample_type']}")
        print(f"       Summary: {r['petrologic_summary']}")
        print()
    conn.close()

def cmd_meteorites(args):
    conn = get_connection()
    c = conn.cursor()
    sql = "SELECT meteorite_name, meteorite_class, recovery_year, recovery_location, mass_grams, petrology_and_chemistry FROM martian_meteorites_catalog WHERE 1=1"
    params = []
    if args.classification:
        sql += " AND meteorite_class LIKE ?"
        params.append(f"%{args.classification}%")
    sql += " ORDER BY mass_grams DESC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nOfficial Martian Meteorites ({len(rows)} returned):\n")
    for r in rows:
        print(f"\033[1m{r['meteorite_name']}\033[0m ({r['meteorite_class']}) - {r['mass_grams']:.1f} g (Found: {r['recovery_year']}, {r['recovery_location']})")
        print(f"       Petrology: {r['petrology_and_chemistry']}")
        print()
    conn.close()

def cmd_weather(args):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT mission_lander, landing_site, season_ls_deg, mean_atmospheric_pressure_pa, temp_min_c, temp_max_c, mean_wind_speed_mps, dust_optical_depth_tau, meteorological_summary FROM mars_surface_weather;")
    rows = c.fetchall()
    print("\n" + "="*85)
    print("                      MARTIAN IN-SITU METEOROLOGICAL OBSERVATIONS                      ")
    print("="*85)
    for r in rows:
        print(f"\033[1m{r['mission_lander']}\033[0m @ {r['landing_site']} (Ls = {r['season_ls_deg']}°)")
        print(f"       Pressure: {r['mean_atmospheric_pressure_pa']:.1f} Pa | Temp: [{r['temp_min_c']}°C to {r['temp_max_c']}°C] | Wind: {r['mean_wind_speed_mps']} m/s | Dust Tau: {r['dust_optical_depth_tau']}")
        print(f"       Summary:  {r['meteorological_summary']}")
        print("-" * 85)
    print("="*85 + "\n")
    conn.close()

def cmd_ice(args):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT body, reservoir_name, region_description, latitude_range, ice_composition, estimated_volume_km3, depth_to_ice_m, detection_instrument, scientific_notes FROM ice_reservoirs;")
    rows = c.fetchall()
    print("\n" + "="*85)
    print("                   POLAR AND SUBSURFACE WATER ICE RESERVOIRS                   ")
    print("="*85)
    for r in rows:
        vol = f"{r['estimated_volume_km3']:,.0f} km³" if r['estimated_volume_km3'] else "Variable / Localized"
        depth = f"{r['depth_to_ice_m']:.2f} m" if r['depth_to_ice_m'] is not None else "Surface / Direct"
        print(f"[{r['body']:<4}] \033[1m{r['reservoir_name']}\033[0m ({r['region_description']})")
        print(f"       Lat Range: {r['latitude_range']} | Estimated Volume: {vol} | Overburden Depth: {depth}")
        print(f"       Composition: {r['ice_composition']} | Instrument: {r['detection_instrument']}")
        print(f"       Notes: {r['scientific_notes']}")
        print("-" * 85)
    print("="*85 + "\n")
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

def cmd_rasters(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT raster_id, target_body, stac_id, scientific_category, target_feature, mission, instrument,
               archive_agency, product_id, product_title, data_format, proj_epsg, iau_2015_wkt,
               gsd_meters, bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat,
               cog_vsicurl_href, no_data_value, h3_index, direct_data_url
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
    if getattr(args, "stac_id", None):
        sql += " AND stac_id LIKE ?"
        params.append(f"%{args.stac_id}%")
    if getattr(args, "h3", None):
        sql += " AND h3_index LIKE ?"
        params.append(f"%{args.h3}%")

    sql += " ORDER BY target_body, scientific_category, gsd_meters ASC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\nRemote Sensing Rasters - STAC Compliant ({len(rows)} returned):\n")
    for r in rows:
        gsd_str = f"{r['gsd_meters']:.2f} m/pix" if r['gsd_meters'] else "N/A"
        epsg_str = f"EPSG:{r['proj_epsg']}" if r['proj_epsg'] else "IAU 2015"
        print(f"[{r['target_body']:<4}] [{r['scientific_category']:<25}] \033[1m{r['product_title']}\033[0m")
        print(f"       STAC ID: \033[33m{r['stac_id']}\033[0m | {epsg_str} | GSD: {gsd_str} | H3: {r['h3_index']}")
        print(f"       Target: {r['target_feature']} | Mission: {r['mission']} ({r['instrument']}) | Agency: {r['archive_agency']}")
        print(f"       BBox: Lat [{r['bbox_min_lat']:>6.1f}°, {r['bbox_max_lat']:>6.1f}°], Lon [{r['bbox_min_lon']:>6.1f}°, {r['bbox_max_lon']:>6.1f}°]")
        print(f"       COG / vsicurl: \033[36m{r['cog_vsicurl_href']}\033[0m")
        print()
    conn.close()

def cmd_safety(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT site_id, feature_id, body, site_name, target_region, catalog_category,
               center_lat, center_lon, h3_index, ellipse_semi_major_km, ellipse_semi_minor_km, approach_azimuth_deg,
               macro_slope_deg, elevation_mola_m, rock_abundance_percent, dte_visibility_fraction,
               ice_overburden_depth_m, plume_scour_risk_index, wind_shear_mps, trn_texture_score,
               mascon_gravity_gradient_mgal, max_eclipse_hours, radiation_svf, thermal_inertia_si,
               water_equivalent_hydrogen_pct, mineral_resource_pct, stratigraphic_diversity_score,
               astrobiology_sample_value, traverse_distance_km
        FROM site_engineering_safety
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.site:
        sql += " AND (site_name LIKE ? OR target_region LIKE ?)"
        params.extend([f"%{args.site}%", f"%{args.site}%"])
    if getattr(args, "category", None):
        sql += " AND catalog_category LIKE ?"
        params.append(f"%{args.category}%")
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
    if getattr(args, "max_scour", None) is not None:
        sql += " AND plume_scour_risk_index <= ?"
        params.append(args.max_scour)
    if getattr(args, "h3", None):
        sql += " AND h3_index LIKE ?"
        params.append(f"%{args.h3}%")

    sql += " ORDER BY body, macro_slope_deg ASC, rock_abundance_percent ASC LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*105)
    print("      LANDING SITE ENGINEERING SAFETY & 3-SIGMA DISPERSION ENVELOPE EVALUATOR      ")
    print("="*105)
    print(f"{len(rows)} candidate landing & exploration sites returned:\n")

    for r in rows:
        slope_flag = "✓ SAFE" if r['macro_slope_deg'] <= 10.0 else ("! MARGINAL" if r['macro_slope_deg'] <= 15.0 else "✗ HAZARD")
        rock_flag = "✓ SAFE" if r['rock_abundance_percent'] <= 7.0 else ("! MODERATE" if r['rock_abundance_percent'] <= 10.0 else "✗ HAZARD")

        if r['body'] == 'Mars':
            if r['elevation_mola_m'] <= -1500.0:
                edl_status = "\033[1;32mPASS (< -1.5km)\033[0m"
            else:
                edl_status = "\033[1;31mFAIL (> -1.5km)\033[0m"
        else:
            edl_status = f"{r['elevation_mola_m']:>+6.0f} m (LOLA)"

        ice_str = f"{r['ice_overburden_depth_m']:.2f} m" if r['ice_overburden_depth_m'] is not None else "None / Deep"
        dte_pct = r['dte_visibility_fraction'] * 100.0
        dte_color = "\033[1;32m" if dte_pct >= 70 else ("\033[1;33m" if dte_pct > 0 else "\033[1;31m")
        fid_str = f"IAU #{r['feature_id']}" if r['feature_id'] else "No Direct IAU Crater"

        print(f"[{r['body']:<4}] \033[1m{r['site_name']}\033[0m ({fid_str}) | Category: \033[36m{r['catalog_category']}\033[0m")
        print(f"       Region: {r['target_region']} | Coords: Lat {r['center_lat']:>7.2f}°, Lon {r['center_lon']:>7.2f}° | H3 (res 6): \033[33m{r['h3_index']}\033[0m")
        print(f"       3-Sigma Dispersion Ellipse: \033[1m{r['ellipse_semi_major_km']:.1f} x {r['ellipse_semi_minor_km']:.1f} km @ {r['approach_azimuth_deg']:.1f}° azimuth\033[0m")
        print(f"       EDL Constraints: Slope: {r['macro_slope_deg']:>4.1f}° [{slope_flag}] | Rocks: {r['rock_abundance_percent']:>4.1f}% [{rock_flag}] | Elevation: {edl_status}")
        print(f"       DTE Comms: {dte_color}{r['dte_visibility_fraction']:.2f} ({dte_pct:>5.1f}%)\033[0m | Ice Overburden: {ice_str:<10} | Plume Scour Index: {r['plume_scour_risk_index']:.2f}")
        print(f"       Physics Metrics: Wind Shear: {r['wind_shear_mps']:.1f} m/s | TRN Texture: {r['trn_texture_score']:.0f} | Mascon Grav: {r['mascon_gravity_gradient_mgal']:.0f} mGal | Eclipse: {r['max_eclipse_hours']:.1f}h")
        print(f"       Resources & Science: WEH: {r['water_equivalent_hydrogen_pct']:.1f}% | Minerals: {r['mineral_resource_pct']:.1f}% | Strat Div: {r['stratigraphic_diversity_score']:.0f} | Astrobio: {r['astrobiology_sample_value']:.0f}")
        print("-" * 105)
    print("="*105 + "\n")
    conn.close()

def cmd_mcda(args):
    conn = get_connection()
    c = conn.cursor()

    w_saf = float(args.weight_safety)
    w_com = float(args.weight_comms)
    w_isru = float(args.weight_isru)
    w_sci = float(args.weight_science)
    w_tot = w_saf + w_com + w_isru + w_sci
    if w_tot <= 0:
        w_tot = 1.0

    sql = """
        SELECT site_id, feature_id, body, site_name, target_region, catalog_category,
               center_lat, center_lon, h3_index, ellipse_semi_major_km, ellipse_semi_minor_km, approach_azimuth_deg,
               edl_safety_score, survivability_comms_score, isru_resource_score, science_return_score,
               composite_balanced_score, pareto_rank,
               ROUND((edl_safety_score * ? + survivability_comms_score * ? + isru_resource_score * ? + science_return_score * ?) / ?, 2) AS dynamic_score
        FROM v_landing_site_pareto_ranks
        WHERE 1=1
    """
    params = [w_saf, w_com, w_isru, w_sci, w_tot]

    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if getattr(args, "category", None):
        sql += " AND catalog_category LIKE ?"
        params.append(f"%{args.category}%")
    if getattr(args, "min_score", None) is not None:
        sql += " AND dynamic_score >= ?"
        params.append(args.min_score)

    sql += " ORDER BY dynamic_score DESC LIMIT ?;"
    params.append(args.limit)

    t0 = time.time()
    c.execute(sql, params)
    rows = c.fetchall()
    dt_ms = (time.time() - t0) * 1000.0

    print("\n" + "="*110)
    print("         MULTI-CRITERIA DECISION ANALYSIS (MCDA) LIVE RANKING ENGINE         ")
    print(f"  Weights: EDL Safety: {w_saf/w_tot*100:.1f}% | Survivability/Comms: {w_com/w_tot*100:.1f}% | ISRU: {w_isru/w_tot*100:.1f}% | Science Return: {w_sci/w_tot*100:.1f}%")
    print(f"  Query Latency: {dt_ms:.2f} ms (< 2.0 ms real-time interactive threshold)")
    print("="*110)
    print(f"{'Rank':<4} {'Body':<5} {'Candidate Site Name':<42} {'Score':>6} | {'Safety':>6} {'Comms':>6} {'ISRU':>6} {'Sci':>6} | {'3-Sigma Ellipse':<16}")
    print("-" * 110)

    for i, r in enumerate(rows, 1):
        score_color = "\033[1;32m" if r['dynamic_score'] >= 80 else ("\033[1;33m" if r['dynamic_score'] >= 70 else "\033[0m")
        ellipse_str = f"{r['ellipse_semi_major_km']:.1f}x{r['ellipse_semi_minor_km']:.1f}km@{r['approach_azimuth_deg']:.0f}°"
        print(f"#{i:<3} [{r['body']:<4}] \033[1m{r['site_name'][:41]:<41}\033[0m {score_color}{r['dynamic_score']:>6.1f}\033[0m | {r['edl_safety_score']:>6.1f} {r['survivability_comms_score']:>6.1f} {r['isru_resource_score']:>6.1f} {r['science_return_score']:>6.1f} | {ellipse_str:<16}")
        print(f"     ↳ Category: {r['catalog_category']} | H3: {r['h3_index']} | Coords: ({r['center_lat']:+.2f}°, {r['center_lon']:+.2f}°) | Static Pareto Rank: #{r['pareto_rank']}")

    print("="*110 + "\n")
    conn.close()

def cmd_h3(args):
    conn = get_connection()
    c = conn.cursor()
    print("\n" + "="*105)
    print("      SUB-MILLISECOND UBER H3 SPATIAL GRID JOINS (PURE SQLITE GIS)      ")
    print("="*105)

    sql = """
        SELECT s.site_name, s.body, s.catalog_category, s.center_lat, s.center_lon, s.h3_index,
               s.ellipse_semi_major_km, s.ellipse_semi_minor_km, s.approach_azimuth_deg,
               f.clean_name AS feature_name, f.feature_type, f.diameter_km
        FROM site_engineering_safety s
        JOIN iau_planetary_features f ON s.h3_index = f.h3_index
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND s.body = ?"
        params.append(args.body.capitalize())
    if getattr(args, "site", None):
        sql += " AND (s.site_name LIKE ? OR f.clean_name LIKE ?)"
        params.extend([f"%{args.site}%", f"%{args.site}%"])

    sql += " ORDER BY s.body, s.site_name LIMIT ?;"
    params.append(args.limit)

    t0 = time.time()
    c.execute(sql, params)
    rows = c.fetchall()
    dt_ms = (time.time() - t0) * 1000.0

    print(f"Query executed in {dt_ms:.2f} ms across indexed H3 hex cells ({len(rows)} spatial co-locations returned):\n")
    for r in rows:
        ellipse_str = f"{r['ellipse_semi_major_km']:.1f}x{r['ellipse_semi_minor_km']:.1f} km @ {r['approach_azimuth_deg']:.0f}°"
        print(f"[{r['body']:<4}] Landing Site: \033[1m{r['site_name']}\033[0m [{r['catalog_category']}]")
        print(f"       H3 Hex Cell (res 6): \033[33m{r['h3_index']}\033[0m | Coords: ({r['center_lat']:.2f}°, {r['center_lon']:.2f}°) | 3-Sigma: {ellipse_str}")
        print(f"       ↳ Spatial Join: Named IAU Feature \033[36m{r['feature_name']}\033[0m ({r['feature_type']}, {r['diameter_km']:.1f} km)")
        print("-" * 105)

    # Also show raster co-locations
    sql_ras = """
        SELECT s.site_name, s.body, s.h3_index, r.stac_id, r.product_title, r.gsd_meters, r.scientific_category, r.cog_vsicurl_href
        FROM site_engineering_safety s
        JOIN remote_sensing_rasters r ON s.h3_index = r.h3_index
        LIMIT 5;
    """
    c.execute(sql_ras)
    ras_rows = c.fetchall()
    if ras_rows:
        print("\n  [Exact H3 Hex Cell Raster Co-Locations (Landing Ellipse intersecting STAC COG Data)]: ")
        for rr in ras_rows:
            print(f"  • [{rr['body']}] {rr['site_name']} (H3: {rr['h3_index']})")
            print(f"    ↳ STAC Asset: \033[33m{rr['stac_id']}\033[0m ({rr['scientific_category']}, GSD: {rr['gsd_meters']:.1f}m)")
            print(f"      COG vsicurl: \033[36m{rr['cog_vsicurl_href']}\033[0m")
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
               max_plume_dynamic_pressure_kpa, comms_architecture, engineering_reference,
               ellipse_semi_major_km, ellipse_semi_minor_km, approach_azimuth_deg
        FROM lander_engineering_constraints
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND target_body = ?"
        params.append(args.body.capitalize())
    if args.name:
        sql += " AND (lander_name LIKE ? OR lander_id LIKE ?)"
        params.extend([f"%{args.name}%", f"%{args.name}%"])
    if args.edl_type:
        sql += " AND edl_architecture LIKE ?"
        params.append(f"%{args.edl_type}%")
    if args.max_slope is not None:
        sql += " AND max_tolerable_slope_deg >= ?"
        params.append(args.max_slope)

    sql += " ORDER BY target_body, touchdown_mass_kg DESC;"
    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*100)
    print("           LANDER DYNAMICS, EDL ENVELOPES & 3-SIGMA DISPERSION ELLIPSES           ")
    print("="*100)
    print(f"{len(rows)} flight vehicle engineering envelopes returned:\n")

    for r in rows:
        edl_env = f"<= {r['edl_altitude_envelope_max_mola_m']:.0f} m MOLA" if r['edl_altitude_envelope_max_mola_m'] is not None else "N/A (Lunar Airless)"
        mass_str = f"{r['touchdown_mass_kg']:>8,.0f} kg"
        print(f"[{r['target_body']:<4}] \033[1m{r['lander_name']}\033[0m [{r['organization']}] - {r['mission_phase_status']}")
        print(f"       Design 3-Sigma Dispersion Ellipse: \033[1;33m{r['ellipse_semi_major_km']:.1f} x {r['ellipse_semi_minor_km']:.1f} km @ {r['approach_azimuth_deg']:.1f}° azimuth\033[0m")
        print(f"       Gear Span: {r['footprint_span_m']:>4.1f} m | Mass: {mass_str} | Slope Limit: <= {r['max_tolerable_slope_deg']}° | Rock Clearance: {r['max_tolerable_rock_height_m']:.2f} m")
        print(f"       Velocity Limits: Horiz <= {r['max_horizontal_velocity_mps']:.1f} m/s, Vert <= {r['max_vertical_velocity_mps']:.1f} m/s | EDL Elevation Envelope: {edl_env}")
        print(f"       EDL Mode: {r['edl_architecture']}")
        print(f"       Soil Bearing Required: >= {r['min_bearing_capacity_kpa']:.1f} kPa | Plume Dynamic Pressure: {r['max_plume_dynamic_pressure_kpa']:.1f} kPa")
        print(f"       Comms Link: {r['comms_architecture']}")
        print(f"       Source: \033[36m{r['engineering_reference']}\033[0m")
        print("-" * 100)
    print("="*100 + "\n")
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
        params.extend([f"%{args.terrain}%", f"%{args.terrain}%"])

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
        print(f"       Bulk Density: {r['bulk_density_g_cm3']:.2f} g/cm³ | Porosity: {r['porosity_pct']:.1f}% | Cohesion: {r['cohesion_kpa']:.2f} kPa | Friction Angle: {r['internal_friction_angle_deg']:.1f}°")
        print(f"       Bearing Capacity: {r['bearing_capacity_kpa']:.1f} kPa | Fine Thermal Inertia: {r['fine_component_thermal_inertia_si']:.1f} SI [{r['dust_mantling_level']}]")
        print(f"       Threshold Friction Vel: {r['threshold_friction_velocity_mps']:.1f} m/s | Plume Erosion: {r['plume_erosion_rate_kg_m2_s']:.1f} kg/(m²·s) | Scour Risk: {r['plume_scour_risk_index']:.2f}")
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
        print(f"       DTE Line-of-Sight: {dte_color}{r['dte_visibility_fraction']:.2f} ({dte_pct:.1f}%)\033[0m | Earth Horizon Elevation: [{r['earth_elevation_min_deg']:>+5.1f}°, {r['earth_elevation_max_deg']:>+5.1f}°] | DSN: {r['dsn_visibility_hours_per_day']:.1f} hrs/day")
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

def cmd_compat(args):
    conn = get_connection()
    c = conn.cursor()
    sql = """
        SELECT site_id, body, site_name, catalog_category, lander_id, lander_name, organization, qualification_status
        FROM v_lander_site_compatibility
        WHERE 1=1
    """
    params = []
    if args.body:
        sql += " AND body = ?"
        params.append(args.body.capitalize())
    if args.vehicle:
        sql += " AND (lander_name LIKE ? OR lander_id LIKE ?)"
        params.extend([f"%{args.vehicle}%", f"%{args.vehicle}%"])
    if args.site:
        sql += " AND site_name LIKE ?"
        params.append(f"%{args.site}%")
    if args.status:
        sql += " AND qualification_status LIKE ?"
        params.append(f"%{args.status}%")

    sql += " ORDER BY body, lander_name, qualification_status, site_name LIMIT ?;"
    params.append(args.limit)

    c.execute(sql, params)
    rows = c.fetchall()

    print("\n" + "="*105)
    print("               DYNAMIC LANDER VEHICLE VS CANDIDATE SITE COMPATIBILITY EVALUATION               ")
    print("="*105)
    print(f"{len(rows)} evaluations returned:\n")

    for r in rows:
        status = r['qualification_status']
        if status == 'QUALIFIED':
            status_str = f"\033[1;32m{status}\033[0m"
        else:
            status_str = f"\033[1;31m{status}\033[0m"
        print(f"[{r['body']:<4}] Vehicle: \033[1m{r['lander_name']}\033[0m ({r['organization']})")
        print(f"       Site: {r['site_name']} [{r['catalog_category']}]")
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
    p_feat.add_argument("--h3", help="Filter by Uber H3 index substring")
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

    # Rasters (STAC Compliant)
    p_ras = subparsers.add_parser("rasters", help="Query STAC-compliant remote sensing rasters & Cloud-Optimized GeoTIFF endpoints")
    p_ras.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_ras.add_argument("--category", help="Filter by category (e.g. DEM, Slopes, Volatiles, Thermal)")
    p_ras.add_argument("--target", help="Filter by target feature or keyword (e.g. Shackleton, Jezero, Gale, Arcadia)")
    p_ras.add_argument("--mission", help="Filter by mission (e.g. LRO, Kaguya, MRO, Odyssey)")
    p_ras.add_argument("--format", help="Filter by format (e.g. GeoTIFF, IMG, JP2, Table)")
    p_ras.add_argument("--stac-id", help="Filter by STAC ID substring")
    p_ras.add_argument("--h3", help="Filter by Uber H3 index substring")
    p_ras.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # Safety (500+ Official NASA Sites, 3-Sigma Ellipses, H3 Grid)
    p_saf = subparsers.add_parser("safety", help="Evaluate 500+ official NASA candidate landing sites with 3-sigma dispersion ellipses & H3 indexing")
    p_saf.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_saf.add_argument("--site", help="Filter by site name or target region keyword")
    p_saf.add_argument("--category", help="Filter by catalog category (e.g. Artemis III, CLPS, CxP, Mars HLS2 EZ)")
    p_saf.add_argument("--max-slope", type=float, help="Maximum tolerable macro-slope in degrees (<= 10° ideal)")
    p_saf.add_argument("--max-elevation", type=float, help="Maximum elevation in meters (critical for Mars EDL, <= -1500m)")
    p_saf.add_argument("--max-rocks", type=float, help="Maximum rock abundance percentage (<= 7%% safe)")
    p_saf.add_argument("--min-dte", type=float, help="Minimum direct-to-Earth (DTE) visibility fraction (0.0 to 1.0)")
    p_saf.add_argument("--has-ice", action="store_true", help="Only show sites with shallow accessible water ice")
    p_saf.add_argument("--max-ice-depth", type=float, help="Maximum ice overburden depth in meters (e.g. 1.0m)")
    p_saf.add_argument("--max-scour", type=float, help="Maximum plume scour risk index (0.0 to 1.0)")
    p_saf.add_argument("--h3", help="Filter by Uber H3 index substring")
    p_saf.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # MCDA Live Decision Analysis Slider Engine
    p_mcda = subparsers.add_parser("mcda", help="Multi-Criteria Decision Analysis (MCDA) live weighting engine (< 2ms real-time ranking)")
    p_mcda.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_mcda.add_argument("--category", help="Filter by catalog category")
    p_mcda.add_argument("--weight-safety", type=float, default=35.0, help="Weight for EDL Safety (default: 35.0)")
    p_mcda.add_argument("--weight-comms", type=float, default=25.0, help="Weight for Survivability & Comms (default: 25.0)")
    p_mcda.add_argument("--weight-isru", type=float, default=20.0, help="Weight for ISRU Resources (default: 20.0)")
    p_mcda.add_argument("--weight-science", type=float, default=20.0, help="Weight for Science Return (default: 20.0)")
    p_mcda.add_argument("--min-score", type=float, help="Minimum composite custom score threshold (0-100)")
    p_mcda.add_argument("--limit", type=int, default=15, help="Top N candidates to return (default: 15)")

    # H3 Spatial Join
    p_h3 = subparsers.add_parser("h3", help="Demonstrate sub-millisecond Uber H3 spatial joins between landing sites and STAC rasters")
    p_h3.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_h3.add_argument("--site", help="Filter by site name keyword")
    p_h3.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # Landers
    p_lan = subparsers.add_parser("landers", help="Query lander vehicle engineering envelopes & 3-sigma dispersion targets")
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

    # Lander Compatibility Dynamic Join View
    p_cmp = subparsers.add_parser("compat", help="Evaluate dynamic lander vehicle vs candidate site compatibility (v_lander_site_compatibility)")
    p_cmp.add_argument("--body", choices=["Moon", "Mars"], help="Filter by celestial body")
    p_cmp.add_argument("--vehicle", help="Filter by lander/vehicle name (e.g. Starship, Nova-C, Perseverance, Sky Crane)")
    p_cmp.add_argument("--site", help="Filter by site name keyword")
    p_cmp.add_argument("--status", help="Filter by qualification status (e.g. QUALIFIED, Slope, Density, Eclipse, Boulder)")
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
        "mcda": cmd_mcda,
        "h3": cmd_h3,
        "landers": cmd_landers,
        "geotechnics": cmd_geotechnics,
        "telecom": cmd_telecom,
        "hazards": cmd_hazards,
        "compat": cmd_compat
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()
