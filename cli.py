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
        ("fts_planetary_search", "Full-Text Search Index Entries")
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
        "rasters": cmd_rasters
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()

