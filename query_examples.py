import sqlite3
import json

DB_PATH = "planetary_moon_mars.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

# 1. Top 5 Largest Craters on the Moon & Mars
print_section("TOP 5 LARGEST IMPACT CRATERS & BASINS")
cursor.execute("""
SELECT body_id, clean_name, feature_type, diameter_km, center_lat, center_lon, origin
FROM iau_planetary_features
WHERE feature_type LIKE '%Crater%' OR feature_type LIKE '%Planitia%'
ORDER BY diameter_km DESC
LIMIT 10;
""")
for r in cursor.fetchall():
    print(f"[{r['body_id']:<5}] {r['clean_name']:<22} | Diam: {r['diameter_km']:>7.1f} km | Lat: {r['center_lat']:>7.2f}°, Lon: {r['center_lon']:>7.2f}° | Origin: {r['origin'][:40] if r['origin'] else 'N/A'}")

# 2. Heaviest Apollo Lunar Samples
print_section("TOP 5 HEAVIEST RETURNED APOLLO LUNAR SAMPLES")
cursor.execute("""
SELECT sample_id, mission, collection_site, rock_class, rock_subclass, weight_grams, pristine_percent
FROM lunar_samples_catalog
ORDER BY weight_grams DESC
LIMIT 5;
""")
for r in cursor.fetchall():
    print(f"Sample #{r['sample_id']:<6} | {r['mission']:<10} | Weight: {r['weight_grams']:>8.1f} g ({r['weight_grams']/1000:>5.2f} kg) | Pristine: {r['pristine_percent']:>5.1f}% | Class: {r['rock_class']} ({r['rock_subclass']})")

# 3. All Surface Landings and Current Hardware Status
print_section("ALL SURFACE LANDING & CRASH SITES")
cursor.execute("""
SELECT body_id, site_name, landing_type, touchdown_date, latitude_deg, longitude_deg, current_status
FROM surface_landing_sites
ORDER BY touchdown_date ASC;
""")
for r in cursor.fetchall():
    print(f"[{r['body_id']:<5}] {r['touchdown_date']} | {r['site_name']:<30} | {r['latitude_deg']:>6.2f}°, {r['longitude_deg']:>6.2f}° | {r['landing_type']}")

# 4. FTS5 Sub-Millisecond Search Test
print_section("FULL-TEXT SEARCH QUERY: 'water ice'")
cursor.execute("""
SELECT entity_type, entity_id, body, title, snippet(fts_planetary_search, 5, '«', '»', '...', 15) as match_snip
FROM fts_planetary_search
WHERE fts_planetary_search MATCH 'water ice'
LIMIT 8;
""")
for r in cursor.fetchall():
    print(f"[{r['entity_type']:<15}] ({r['body']}) {r['title']:<30} | Match: {r['match_snip']}")

# 5. Martian Meteorites Petrographic Types
print_section("MARTIAN METEORITES CATALOG SUMMARY")
cursor.execute("""
SELECT petrologic_classification, COUNT(*) as count, GROUP_CONCAT(meteorite_name, ', ') as names
FROM martian_meteorites_catalog
GROUP BY petrologic_classification;
""")
for r in cursor.fetchall():
    short_names = r['names'][:60] + "..." if len(r['names']) > 60 else r['names']
    print(f"• {r['petrologic_classification']:<45} (n={r['count']}): {short_names}")

# 6. Physical Comparison: Moon vs Mars vs Earth
print_section("PHYSICAL PARAMETERS: MOON vs MARS vs EARTH")
cursor.execute("""
SELECT parameter, 
       MAX(CASE WHEN body_id = 'Moon' THEN value_str END) as Moon_Val,
       MAX(CASE WHEN body_id = 'Mars' THEN value_str END) as Mars_Val,
       MAX(unit) as Unit,
       MAX(earth_comparison_value) as Earth_Val
FROM physical_parameters
WHERE parameter IN ('Mass', 'Volume', 'Equatorial radius', 'Surface gravity', 'Escape velocity', 'Mean density')
GROUP BY parameter;
""")
for r in cursor.fetchall():
    unit_str = f"({r['Unit']})" if r['Unit'] else ""
    print(f"{r['parameter']:<20} {unit_str:<12} | Moon: {r['Moon_Val']:<10} | Mars: {r['Mars_Val']:<10} | Earth: {r['Earth_Val']}")

conn.close()

