from pathlib import Path
import urllib.request
import urllib.parse
import ssl
import certifi
import json
import csv
import os
import re
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ctx = ssl.create_default_context(cafile=certifi.where())

BODIES = {
    "Moon": "301",
    "Mars": "499",
    "Phobos": "401",
    "Deimos": "402"
}

os.makedirs(PROJECT_ROOT / "data/raw/nasa/horizons", exist_ok=True)
os.makedirs(PROJECT_ROOT / "data/processed/json", exist_ok=True)
os.makedirs(PROJECT_ROOT / "data/processed/csv", exist_ok=True)
os.makedirs(PROJECT_ROOT / "data/processed/parquet", exist_ok=True)

# 1. Fetch raw geophysical texts
geophysical_cards = {}
for name, cmd in BODIES.items():
    print(f"Fetching JPL Horizons data for {name} ({cmd})...")
    card_path = PROJECT_ROOT / "data/raw/nasa/horizons" / f"{name}_horizons_card.txt"
    raw_text = None
    if card_path.exists():
        with open(card_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    if not raw_text:
        try:
            url = f"https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND=%27{cmd}%27&OBJ_DATA=%27YES%27&MAKE_EPHEM=%27NO%27"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NASA Harvester)"})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data.get("result", "")
                with open(card_path, "w", encoding="utf-8") as f:
                    f.write(raw_text)
        except Exception as e:
            print(f"Offline fallback warning for {name}: {e}")
            raw_text = ""
    geophysical_cards[name] = raw_text

# 2. Fetch Ephemeris Observer Tables for Moon and Mars (2026 full year sample)
ephemerides_records = []
for name, cmd in [("Moon", "301"), ("Mars", "499")]:
    print(f"Fetching 2026 Ephemeris for {name} ({cmd})...")
    ephem_path = PROJECT_ROOT / "data/raw/nasa/horizons" / f"{name}_ephemeris_2026.txt"
    raw_text = None
    if ephem_path.exists():
        with open(ephem_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    if not raw_text:
        try:
            url = (
                f"https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND=%27{cmd}%27"
                f"&MAKE_EPHEM=%27YES%27&EPHEM_TYPE=%27OBSERVER%27&CENTER=%27500@399%27"
                f"&START_TIME=%272026-01-01%27&STOP_TIME=%272026-12-31%27&STEP_SIZE=%275d%27"
                f"&QUANTITIES=%271,9,19,20,23,24%27"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NASA Harvester)"})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data.get("result", "")
                with open(ephem_path, "w", encoding="utf-8") as f:
                    f.write(raw_text)
        except Exception as e:
            print(f"Offline fallback warning for {name} ephemeris: {e}")
            raw_text = ""
            
    # Parse between $$SOE and $$EOE
    if raw_text:
        soe_idx = raw_text.find("$$SOE")
        eoe_idx = raw_text.find("$$EOE")
        if soe_idx != -1 and eoe_idx != -1:
            data_block = raw_text[soe_idx + 5:eoe_idx].strip()
            for line in data_block.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Line format: Date__(UT)__HR:MN     R.A._____(ICRF)_____DEC    APmag   S-brt                r        rdot             delta      deldot     S-O-T /r     S-T-O
                parts = line.split()
                if len(parts) >= 11:
                    date_str = f"{parts[0]} {parts[1]}"
                    ra = f"{parts[2]} {parts[3]} {parts[4]}"
                    dec = f"{parts[5]} {parts[6]} {parts[7]}"
                    ap_mag = float(parts[8]) if parts[8] != "n.a." else None
                    s_brt = float(parts[9]) if parts[9] != "n.a." else None
                    r_au = float(parts[10])
                    rdot_kms = float(parts[11])
                    delta_au = float(parts[12])
                    deldot_kms = float(parts[13])
                    sot = float(parts[14])
                    sto = float(parts[16]) if len(parts) > 16 else (float(parts[15]) if len(parts) > 15 else None)
                    
                    ephemerides_records.append({
                        "body": name,
                        "datetime_utc": date_str,
                        "ra_icrf": ra,
                        "dec_icrf": dec,
                        "apparent_visual_magnitude": ap_mag,
                        "surface_brightness": s_brt,
                        "heliocentric_distance_au": r_au,
                        "heliocentric_range_rate_kms": rdot_kms,
                        "geocentric_distance_au": delta_au,
                        "geocentric_range_rate_kms": deldot_kms,
                        "sun_observer_target_deg": sot,
                        "phase_angle_sto_deg": sto,
                        "source": "NASA JPL Horizons DE441 Ephemeris"
                    })

print(f"Total ephemeris points parsed: {len(ephemerides_records)}")

# Save Ephemerides
json_ephem = PROJECT_ROOT / "data/processed/json/jpl_ephemerides_2026.json"
csv_ephem = PROJECT_ROOT / "data/processed/csv/jpl_ephemerides_2026.csv"
parquet_ephem = PROJECT_ROOT / "data/processed/parquet/jpl_ephemerides_2026.parquet"

with open(json_ephem, "w", encoding="utf-8") as f:
    json.dump(ephemerides_records, f, indent=2)
if ephemerides_records:
    with open(csv_ephem, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ephemerides_records[0].keys()))
        writer.writeheader()
        writer.writerows(ephemerides_records)
    pq.write_table(pa.Table.from_pylist(ephemerides_records), str(parquet_ephem))

# Save horizons geophysical metadata overview
horizons_summary = []
for name, raw in geophysical_cards.items():
    horizons_summary.append({
        "body": name,
        "raw_header": raw[:300].strip(),
        "source": "NASA JPL Solar System Dynamics (SSD) Group Horizons System"
    })
json_horizons = PROJECT_ROOT / "data/processed/json/horizons_summary.json"
with open(json_horizons, "w", encoding="utf-8") as f:
    json.dump(horizons_summary, f, indent=2)

print("JPL Horizons data harvesting and ephemerides successfully compiled.")

