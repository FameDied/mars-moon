import urllib.request
import ssl
import certifi
import json
import csv
import os
import xlrd
import pyarrow as pa
import pyarrow.parquet as pq

ctx = ssl.create_default_context(cafile=certifi.where())

FILES = {
    "Basaltic Shergottites": "https://curator.jsc.nasa.gov/antmet/mmc/MMC-chemical-basalt.xls",
    "Olivine-Phyric Shergottites": "https://curator.jsc.nasa.gov/antmet/mmc/MMC-chemical-oliv.xls",
    "Ancient, Nakhlites, Chassignites & Lherzolites": "https://curator.jsc.nasa.gov/antmet/mmc/MMC-chemical-Ancient-Nak-Chass-Lherz.xls"
}

raw_dir = "data/raw/jsc/mmc"
os.makedirs(raw_dir, exist_ok=True)
os.makedirs("data/processed/json", exist_ok=True)
os.makedirs("data/processed/csv", exist_ok=True)
os.makedirs("data/processed/parquet", exist_ok=True)

all_meteorites = []

for group_name, url in FILES.items():
    filename = url.split("/")[-1]
    local_path = os.path.join(raw_dir, filename)
    
    if not os.path.exists(local_path):
        print(f"Downloading {filename} from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NASA Harvester)"})
        with urllib.request.urlopen(req, context=ctx) as resp, open(local_path, "wb") as f:
            f.write(resp.read())
            
    print(f"Parsing {filename} ({group_name})...")
    book = xlrd.open_workbook(local_path)
    sheet_names = book.sheet_names()
    print(f"Found {len(sheet_names)} meteorite sheets in {filename}.")
    
    for s_name in sheet_names:
        sheet = book.sheet_by_name(s_name)
        if sheet.nrows < 5:
            continue
            
        # Parse chemistry
        major_elements = {}
        trace_elements = {}
        refs = []
        
        # Read column 0 for element names, column 1 or 3 for values
        for r in range(sheet.nrows):
            el_name = str(sheet.cell_value(r, 0)).strip()
            if not el_name:
                continue
                
            # Check row 0 for references
            if r == 0:
                for c in range(1, sheet.ncols):
                    val = str(sheet.cell_value(r, c)).strip()
                    if val and val not in refs:
                        refs.append(val)
                continue
                
            # Major oxides
            if any(ox in el_name for ox in ["SiO2", "TiO2", "Al2O3", "FeO", "MnO", "CaO", "MgO", "Na2O", "K2O", "P2O5", "Cr2O3"]):
                for c in range(1, sheet.ncols):
                    cell_val = sheet.cell_value(r, c)
                    if isinstance(cell_val, (int, float)) and cell_val > 0:
                        major_elements[el_name] = round(float(cell_val), 3)
                        break
            # Trace elements
            elif any(tr in el_name for tr in ["ppm", "La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu", "Hf", "Th", "U", "Ni", "Co", "V", "Sc", "Zr"]):
                for c in range(1, sheet.ncols):
                    cell_val = sheet.cell_value(r, c)
                    if isinstance(cell_val, (int, float)) and cell_val > 0:
                        trace_elements[el_name] = round(float(cell_val), 3)
                        break

        # Classify meteorite type
        clean_name = s_name.strip()
        m_type = "Martian Shergottite (Basaltic)"
        if "Ancient" in group_name or "Nak" in group_name:
            if "84001" in clean_name:
                m_type = "Martian Orthopyroxenite (Ancient 4.1 Ga Crust)"
            elif "7034" in clean_name or "Black Beauty" in clean_name or "7533" in clean_name:
                m_type = "Martian Polymict Regolith Breccia ('Black Beauty' Clan)"
            elif any(n in clean_name.lower() for n in ["nakhla", "lafayette", "governador", "milos"]):
                m_type = "Martian Nakhlite (Clinopyroxenite)"
            elif any(c in clean_name.lower() for c in ["chassigny", "2737"]):
                m_type = "Martian Chassignite (Dunite)"
            else:
                m_type = "Martian Lherzolitic Shergottite / Cumulate"
        elif "Olivine" in group_name:
            m_type = "Martian Shergottite (Olivine-Phyric)"

        # Determine fall vs find
        fall_find = "Find"
        if clean_name.lower() in ["shergotty", "zagami", "nakhla", "chassigny", "tissint"]:
            fall_find = "Fall (Observed)"

        # Provenance confirmation
        significance = (
            "Martian origin confirmed by noble gas isotopic ratios (36Ar/38Ar, 40Ar/36Ar, 129Xe/132Xe) "
            "and trapped volatile chemistry matching Viking and Curiosity atmospheric measurements."
        )

        all_meteorites.append({
            "meteorite_name": clean_name,
            "petrologic_classification": m_type,
            "sample_group": group_name,
            "fall_or_find": fall_find,
            "major_oxides_wt_pct": major_elements,
            "trace_elements_ppm": trace_elements,
            "literature_references": ", ".join(refs[:5]) if refs else "NASA JSC Astromaterials Curatorial Records",
            "scientific_significance": significance,
            "compendium_source": "NASA Johnson Space Center Mars Meteorite Compendium (MMC)"
        })

print(f"Total Martian meteorites parsed: {len(all_meteorites)}")

# Prepare flattened format for CSV & Parquet
flat_meteorites = []
for m in all_meteorites:
    item = dict(m)
    item["major_oxides_json"] = json.dumps(item.pop("major_oxides_wt_pct"))
    item["trace_elements_json"] = json.dumps(item.pop("trace_elements_ppm"))
    flat_meteorites.append(item)

# Save JSON
with open("data/processed/json/martian_meteorites.json", "w", encoding="utf-8") as f:
    json.dump(all_meteorites, f, indent=2)
print(f"Saved JSON ({os.path.getsize('data/processed/json/martian_meteorites.json'):,} bytes)")

# Save CSV
with open("data/processed/csv/martian_meteorites.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(flat_meteorites[0].keys()))
    writer.writeheader()
    writer.writerows(flat_meteorites)
print(f"Saved CSV ({os.path.getsize('data/processed/csv/martian_meteorites.csv'):,} bytes)")

# Save Parquet
pq.write_table(pa.Table.from_pylist(flat_meteorites), "data/processed/parquet/martian_meteorites.parquet")
print(f"Saved Parquet ({os.path.getsize('data/processed/parquet/martian_meteorites.parquet'):,} bytes)")

