import os
import zipfile
import shapefile
import json
import csv
import pyarrow as pa
import pyarrow.parquet as pq

DATASETS = {
    "Mars": "data/raw/usgs/Mars/MARS_nomenclature_center_pts.shp",
    "Moon": "data/raw/usgs/Moon/MOON_nomenclature_center_pts.shp"
}

all_features = []

for body, shp_path in DATASETS.items():
    print(f"Processing {body} nomenclature from {shp_path}...")
    sf = shapefile.Reader(shp_path)
    fields = [f[0] for f in sf.fields[1:]]
    
    count = 0
    for shape_rec in sf.iterShapeRecords():
        rec_dict = dict(zip(fields, shape_rec.record))
        pt = shape_rec.shape.points[0] if shape_rec.shape.points else (rec_dict.get('center_lon'), rec_dict.get('center_lat'))
        
        # Clean coordinates
        lon = float(pt[0]) if pt[0] is not None else float(rec_dict.get('center_lon', 0.0) or 0.0)
        lat = float(pt[1]) if pt[1] is not None else float(rec_dict.get('center_lat', 0.0) or 0.0)
        
        # Standardize longitude (-180 to 180 for standard GIS alongside 0 to 360 east longitude)
        lon_180 = lon if lon <= 180.0 else lon - 360.0
        
        feature_item = {
            "body": body,
            "feature_id": rec_dict.get("link", "").split("/")[-1] if rec_dict.get("link") else None,
            "name": str(rec_dict.get("name", "")).strip(),
            "clean_name": str(rec_dict.get("clean_name", "")).strip(),
            "feature_type": str(rec_dict.get("type", "")).strip(),
            "type_code": str(rec_dict.get("code", "")).strip(),
            "diameter_km": round(float(rec_dict.get("diameter", 0.0) or 0.0), 3),
            "center_lat": round(lat, 5),
            "center_lon": round(lon, 5),
            "center_lon_180": round(lon_180, 5),
            "min_lat": round(float(rec_dict.get("min_lat", 0.0) or 0.0), 5),
            "max_lat": round(float(rec_dict.get("max_lat", 0.0) or 0.0), 5),
            "min_lon": round(float(rec_dict.get("min_lon", 0.0) or 0.0), 5),
            "max_lon": round(float(rec_dict.get("max_lon", 0.0) or 0.0), 5),
            "origin": str(rec_dict.get("origin", "")).strip(),
            "approval_date": str(rec_dict.get("approvaldt", "")).strip(),
            "approval_status": str(rec_dict.get("approval", "")).strip(),
            "ethnicity": str(rec_dict.get("ethnicity", "")).strip(),
            "continent": str(rec_dict.get("continent", "")).strip(),
            "quad_name": str(rec_dict.get("quad_name", "")).strip(),
            "quad_code": str(rec_dict.get("quad_code", "")).strip(),
            "usgs_link": str(rec_dict.get("link", "")).strip(),
        }
        all_features.append(feature_item)
        count += 1
        
    print(f"Processed {count} features for {body}.")

print(f"Total features collected: {len(all_features)}")

# Save to JSON
json_path = "data/processed/json/iau_features.json"
os.makedirs(os.path.dirname(json_path), exist_ok=True)
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_features, f, indent=2, ensure_ascii=False)
print(f"Saved {json_path} ({os.path.getsize(json_path):,} bytes)")

# Save to CSV
csv_path = "data/processed/csv/iau_features.csv"
os.makedirs(os.path.dirname(csv_path), exist_ok=True)
if all_features:
    fieldnames = list(all_features[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_features)
print(f"Saved {csv_path} ({os.path.getsize(csv_path):,} bytes)")

# Save to Parquet
parquet_path = "data/processed/parquet/iau_features.parquet"
os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
table = pa.Table.from_pylist(all_features)
pq.write_table(table, parquet_path, compression="snappy")
print(f"Saved {parquet_path} ({os.path.getsize(parquet_path):,} bytes)")
