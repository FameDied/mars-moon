from pathlib import Path
import urllib.request
import ssl
import certifi
import json
import csv
import os
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ctx = ssl.create_default_context(cafile=certifi.where())

os.makedirs(PROJECT_ROOT / "data/maps", exist_ok=True)
os.makedirs(PROJECT_ROOT / "data/processed/json", exist_ok=True)
os.makedirs(PROJECT_ROOT / "data/processed/csv", exist_ok=True)
os.makedirs(PROJECT_ROOT / "data/processed/parquet", exist_ok=True)

# 1. Download official maps directly
MAPS_TO_DOWNLOAD = [
    {
        "filename": "luna_lola_global_topography.jpg",
        "url": "http://images-assets.nasa.gov/image/GSFC_20171208_Archive_e000954/GSFC_20171208_Archive_e000954~medium.jpg",
        "body": "Moon",
        "title": "LRO LOLA Global Lunar Topographic Relief Map",
        "instrument": "Lunar Orbiter Laser Altimeter (LOLA / LRO)",
        "source": "NASA Goddard Space Flight Center"
    },
    {
        "filename": "mars_mola_global_topography.jpg",
        "url": "http://images-assets.nasa.gov/image/PIA02031/PIA02031~medium.jpg",
        "body": "Mars",
        "title": "MGS MOLA Global Martian Topographic Shaded Relief Map",
        "instrument": "Mars Orbiter Laser Altimeter (MOLA / MGS)",
        "source": "NASA Jet Propulsion Laboratory / GSFC"
    },
    {
        "filename": "mars_mola_surface_relief.jpg",
        "url": "http://images-assets.nasa.gov/image/PIA00957/PIA00957~medium.jpg",
        "body": "Mars",
        "title": "MGS MOLA Surface Topography Color Elevation Grid",
        "instrument": "MOLA / MGS",
        "source": "NASA Jet Propulsion Laboratory"
    },
    {
        "filename": "mars_usgs_mola_colorhillshade.jpg",
        "url": "https://astrogeology.usgs.gov/ckan/dataset/0c30e797-b7d7-4d06-87c2-d3b01abcd797/resource/c384f456-8182-4e40-94de-727b74dab4ec/download/mars_mgs_colorhillshade_mola_1024.jpg",
        "body": "Mars",
        "title": "USGS Astrogeology Mars MGS MOLA Global Color Shaded Relief (1024px)",
        "instrument": "MOLA / USGS Planetary GIS",
        "source": "USGS Astrogeology Science Center"
    }
]

print("Checking authentic global planetary maps...")
downloaded_maps = []
for m in MAPS_TO_DOWNLOAD:
    dest = str(PROJECT_ROOT / "data/maps" / m["filename"])
    if not (os.path.exists(dest) and os.path.getsize(dest) > 1000):
        try:
            req = urllib.request.Request(m["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            print(f"Downloaded {m['filename']} ({os.path.getsize(dest):,} bytes)")
        except Exception as e:
            print(f"Offline fallback note for map {m['filename']}: {e}")
    if os.path.exists(dest):
        downloaded_maps.append({
            "map_id": m["filename"].split(".")[0],
            "body": m["body"],
            "map_title": m["title"],
            "instrument": m["instrument"],
            "local_file_path": dest,
            "remote_url": m["url"],
            "file_size_bytes": os.path.getsize(dest),
            "source_authority": m["source"]
        })

# 2. Curate Iconic Scientific Planetary Imagery from NASA Image Library
curated_searches = [
    ("Moon", "Apollo 11 Buzz Aldrin", "Neil Armstrong's photograph of Buzz Aldrin on lunar surface at Tranquillity Base"),
    ("Moon", "Earthrise Apollo 8", "Iconic Earthrise photograph taken by William Anders from lunar orbit"),
    ("Moon", "Apollo 17 Harrison Schmitt Taurus-Littrow", "Geologist Harrison Schmitt working next to giant split boulder"),
    ("Moon", "LROC Apollo 11 Tranquility Base", "High-resolution orbital image of Lunar Module descent stage and astronaut footpaths"),
    ("Moon", "LCROSS Cabeus impact plume", "Discovery of water ice and hydroxyl in permanently shadowed lunar crater Cabeus"),
    ("Mars", "Curiosity rover self-portrait Gale Crater", "Curiosity rover MAHLI self-portrait on the slopes of Mount Sharp"),
    ("Mars", "Perseverance rover Jezero delta", "Perseverance rover exploring ancient river delta deposits in Jezero Crater"),
    ("Mars", "Ingenuity helicopter Mars flight", "First powered flight on another planet by Ingenuity helicopter"),
    ("Mars", "Olympus Mons Mars Express MRO", "Orbital perspective of the tallest volcano in the Solar System (Olympus Mons, 21.9 km)"),
    ("Mars", "Valles Marineris global mosaic", "Giant canyon system Valles Marineris spanning 4,000 km across Mars"),
    ("Mars", "InSight lander seismometer Elysium Planitia", "InSight geophysical station and SEIS wind-and-thermal shield on surface")
]

curated_media = []
print("Harvesting curated scientific image metadata from NASA Image & Video Library API...")

for body, query, description_note in curated_searches:
    url = f"https://images-api.nasa.gov/search?q={urllib.request.quote(query)}&media_type=image"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("collection", {}).get("items", [])
            if items:
                top_item = items[0]
                d = top_item["data"][0]
                nasa_id = d.get("nasa_id", "")
                title = d.get("title", "")
                desc = d.get("description", description_note)
                date_created = d.get("date_created", "")
                keywords = d.get("keywords", [])
                
                # Retrieve direct asset link
                asset_url = f"https://images-api.nasa.gov/asset/{nasa_id}"
                req_asset = urllib.request.Request(asset_url, headers={"User-Agent": "Mozilla/5.0"})
                img_url = ""
                thumb_url = ""
                try:
                    with urllib.request.urlopen(req_asset, context=ctx, timeout=10) as a_resp:
                        a_data = json.loads(a_resp.read().decode("utf-8"))
                        for a_item in a_data.get("collection", {}).get("items", []):
                            href = a_item.get("href", "")
                            if "~orig.jpg" in href or "~large.jpg" in href:
                                img_url = href
                            elif "~thumb.jpg" in href:
                                thumb_url = href
                except Exception:
                    pass
                
                curated_media.append({
                    "media_id": nasa_id,
                    "body": body,
                    "title": title,
                    "curated_topic": query,
                    "date_created": date_created,
                    "description": desc[:500] if desc else description_note,
                    "high_res_image_url": img_url if img_url else f"http://images-assets.nasa.gov/image/{nasa_id}/{nasa_id}~orig.jpg",
                    "thumbnail_url": thumb_url if thumb_url else f"http://images-assets.nasa.gov/image/{nasa_id}/{nasa_id}~thumb.jpg",
                    "keywords_json": json.dumps(keywords[:10]),
                    "source": "NASA Image and Video Library"
                })
                print(f"Added: {nasa_id} - {title[:40]}")
    except Exception as e:
        print(f"Error harvesting media for {query}: {e}")

print(f"Compiled {len(downloaded_maps)} downloaded basemaps and {len(curated_media)} curated media items.")

# Save maps metadata
json_maps = PROJECT_ROOT / "data/processed/json/planetary_basemaps.json"
csv_maps = PROJECT_ROOT / "data/processed/csv/planetary_basemaps.csv"
parquet_maps = PROJECT_ROOT / "data/processed/parquet/planetary_basemaps.parquet"

with open(json_maps, "w", encoding="utf-8") as f:
    json.dump(downloaded_maps, f, indent=2)
if downloaded_maps:
    with open(csv_maps, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(downloaded_maps[0].keys()))
        writer.writeheader()
        writer.writerows(downloaded_maps)
    pq.write_table(pa.Table.from_pylist(downloaded_maps), str(parquet_maps))

# Save curated media metadata
json_media = PROJECT_ROOT / "data/processed/json/curated_imagery.json"
csv_media = PROJECT_ROOT / "data/processed/csv/curated_imagery.csv"
parquet_media = PROJECT_ROOT / "data/processed/parquet/curated_imagery.parquet"

if not curated_media and json_media.exists():
    with open(json_media, "r", encoding="utf-8") as f:
        curated_media = json.load(f)

with open(json_media, "w", encoding="utf-8") as f:
    json.dump(curated_media, f, indent=2)
if curated_media:
    with open(csv_media, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(curated_media[0].keys()))
        writer.writeheader()
        writer.writerows(curated_media)
    pq.write_table(pa.Table.from_pylist(curated_media), str(parquet_media))

print("Maps and curated media successfully compiled and saved.")

