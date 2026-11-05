import urllib.request
import ssl
import certifi
import json
import csv
import os
import re
from bs4 import BeautifulSoup
import pyarrow as pa
import pyarrow.parquet as pq

ctx = ssl.create_default_context(cafile=certifi.where())

PAGES = {
    "Moon": "https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html",
    "Mars": "https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html"
}

os.makedirs("data/raw/nasa", exist_ok=True)
os.makedirs("data/processed/json", exist_ok=True)
os.makedirs("data/processed/csv", exist_ok=True)
os.makedirs("data/processed/parquet", exist_ok=True)

all_params = []
all_orbital = []

for body_name, url in PAGES.items():
    print(f"Scraping NSSDC Fact Sheet for {body_name} from {url}...")
    raw_path = f"data/raw/nasa/nssdc_{body_name.lower()}_factsheet.html"
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NASA Data Harvester)"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        html = resp.read().decode("utf-8", errors="replace")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(html)
            
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    print(f"Parsed {len(tables)} tables for {body_name}.")
    
    # Process Bulk / Physical Parameters (usually Table 0)
    if len(tables) > 0:
        rows = tables[0].find_all("tr")
        col_headers = [c.text.strip() for c in rows[0].find_all(["th", "td"])]
        
        # Find index for target body
        body_col_idx = 1
        for i, h in enumerate(col_headers):
            if body_name.lower() in h.lower():
                body_col_idx = i
                break
                
        for r in rows[1:]:
            cols = [c.text.strip().replace('\xa0', ' ') for c in r.find_all(["td", "th"])]
            if len(cols) > body_col_idx:
                raw_param = cols[0]
                raw_val = cols[body_col_idx]
                earth_val = cols[2] if len(cols) > 2 else ""
                ratio_val = cols[3] if len(cols) > 3 else ""
                
                # Split parameter name and unit
                param_clean = raw_param
                unit = ""
                m = re.search(r'\((.*?)\)', raw_param)
                if m:
                    unit = m.group(1).strip()
                    param_clean = raw_param[:m.start()].strip()
                    
                param_entry = {
                    "body": body_name,
                    "category": "Physical / Bulk Properties",
                    "parameter": param_clean,
                    "raw_parameter": raw_param,
                    "value_str": raw_val,
                    "unit": unit,
                    "earth_comparison_value": earth_val,
                    "ratio_to_earth": ratio_val,
                    "source": "NASA GSFC Planetary Fact Sheet (Dr. David R. Williams)"
                }
                all_params.append(param_entry)

    # Process Orbital Parameters (Table 1)
    if len(tables) > 1:
        rows = tables[1].find_all("tr")
        col_headers = [c.text.strip() for c in rows[0].find_all(["th", "td"])]
        body_col_idx = 1
        for i, h in enumerate(col_headers):
            if body_name.lower() in h.lower():
                body_col_idx = i
                break
                
        for r in rows[1:]:
            cols = [c.text.strip().replace('\xa0', ' ') for c in r.find_all(["td", "th"])]
            if len(cols) > body_col_idx:
                raw_param = cols[0]
                raw_val = cols[body_col_idx]
                earth_val = cols[2] if len(cols) > 2 else ""
                
                unit = ""
                m = re.search(r'\((.*?)\)', raw_param)
                if m:
                    unit = m.group(1).strip()
                    param_clean = raw_param[:m.start()].strip()
                else:
                    param_clean = raw_param.strip()
                    
                orbital_entry = {
                    "body": body_name,
                    "category": "Orbital Parameters",
                    "parameter": param_clean,
                    "raw_parameter": raw_param,
                    "value_str": raw_val,
                    "unit": unit,
                    "earth_comparison_value": earth_val,
                    "source": "NASA GSFC Planetary Fact Sheet"
                }
                all_orbital.append(orbital_entry)

    # For Mars, Table 2 contains Phobos and Deimos
    if body_name == "Mars" and len(tables) > 2:
        rows = tables[2].find_all("tr")
        for r in rows[1:]:
            cols = [c.text.strip().replace('\xa0', ' ') for c in r.find_all(["td", "th"])]
            if len(cols) >= 3:
                raw_param = cols[0]
                phobos_val = cols[1]
                deimos_val = cols[2]
                
                unit = ""
                m = re.search(r'\((.*?)\)', raw_param)
                if m:
                    unit = m.group(1).strip()
                    param_clean = raw_param[:m.start()].strip()
                else:
                    param_clean = raw_param.strip()
                    
                all_orbital.append({
                    "body": "Phobos",
                    "category": "Satellite Orbital Properties",
                    "parameter": param_clean,
                    "raw_parameter": raw_param,
                    "value_str": phobos_val,
                    "unit": unit,
                    "earth_comparison_value": "",
                    "source": "NASA GSFC Mars Moons Fact Sheet"
                })
                all_orbital.append({
                    "body": "Deimos",
                    "category": "Satellite Orbital Properties",
                    "parameter": param_clean,
                    "raw_parameter": raw_param,
                    "value_str": deimos_val,
                    "unit": unit,
                    "earth_comparison_value": "",
                    "source": "NASA GSFC Mars Moons Fact Sheet"
                })

# Save Physical Parameters
with open("data/processed/json/physical_parameters.json", "w", encoding="utf-8") as f:
    json.dump(all_params, f, indent=2)
with open("data/processed/csv/physical_parameters.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_params[0].keys()))
    writer.writeheader()
    writer.writerows(all_params)
pq.write_table(pa.Table.from_pylist(all_params), "data/processed/parquet/physical_parameters.parquet")

# Save Orbital Parameters
with open("data/processed/json/orbital_parameters.json", "w", encoding="utf-8") as f:
    json.dump(all_orbital, f, indent=2)
with open("data/processed/csv/orbital_parameters.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_orbital[0].keys()))
    writer.writeheader()
    writer.writerows(all_orbital)
pq.write_table(pa.Table.from_pylist(all_orbital), "data/processed/parquet/orbital_parameters.parquet")

print(f"Successfully processed {len(all_params)} physical parameters and {len(all_orbital)} orbital parameters.")

