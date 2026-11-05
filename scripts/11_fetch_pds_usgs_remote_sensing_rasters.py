#!/usr/bin/env python3
"""
PDS, USGS Astrogeology, JAXA DARTS, and ESA PSA Remote Sensing Raster Catalog ETL
Extracts, verifies, and registers direct endpoints for Moon & Mars:
1. Digital Elevation Models (LOLA GDR/EDR, Kaguya TC DEM, MOLA MEGDR, HRSC DTM)
2. High-Resolution Imagery & Slope Maps (LROC NAC Shackleton/Malapert/Faustini, HiRISE/CTX Jezero/Arcadia/Gale)
3. Resource & Volatiles Distribution (Lunar Prospector NS, Chandrayaan-1 M3, Odyssey GRS/MONS, CRISM MTRDR)
4. Thermal & Illumination Regimes (LRO Diviner, LOLA Illumination / Peak-of-Eternal-Light, THEMIS Night/Day IR)
"""

import os
import sys
import json
import csv
import sqlite3
import requests
import pyarrow as pa
import pyarrow.parquet as pq

DB_PATH = "planetary_moon_mars.db"

RASTERS = [
    # =========================================================================
    # SECTION 1: DIGITAL ELEVATION MODELS (DEM / DHM)
    # =========================================================================
    # Moon: LRO LOLA & Kaguya TC
    {
        "raster_id": "MOON_LOLA_GDR_CYL_128",
        "target_body": "Moon",
        "scientific_category": "DEM/DHM",
        "sub_category": "Global Digital Elevation Model",
        "target_feature": "Global Lunar Surface",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Orbiter Laser Altimeter (LOLA)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "ldem_128.img",
        "product_title": "LRO LOLA Global Cylindrical Elevation Model (128 ppd, ~237 m/pix)",
        "data_format": "PDS3/IMG (16-bit signed integer)",
        "min_lat": -90.0,
        "max_lat": 90.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 237.0,
        "map_scale_desc": "128 pixels/degree (~237 m/pix at equator)",
        "projection": "Equirectangular / Simple Cylindrical (Sphere R=1737.4 km)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_128.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_128.lbl",
        "ancillary_urls_json": json.dumps({
            "ode_product_page": "https://oderest.rsl.wustl.edu/live2/?target=moon&query=product&pt=GDRIMG&iid=LOLA&ihid=LRO&proj=cyl&f=json"
        }),
        "description": "Global digital elevation model gridded from over 6.5 billion LOLA altimetric pulse measurements. Elevations relative to lunar reference radius of 1737.4 km.",
        "scientific_significance": "Definitive geodetic global vertical reference frame for lunar topography, basin structure analysis, and landing site targeting."
    },
    {
        "raster_id": "MOON_LOLA_GDR_SOUTH_POLAR_20M",
        "target_body": "Moon",
        "scientific_category": "DEM/DHM",
        "sub_category": "Polar Digital Elevation Model",
        "target_feature": "Lunar South Pole (80°S - 90°S)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Orbiter Laser Altimeter (LOLA)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "ldem_80s_20m.img",
        "product_title": "LRO LOLA South Pole High-Resolution Elevation Model (20 m/pixel)",
        "data_format": "PDS3/IMG (16-bit signed integer)",
        "min_lat": -90.0,
        "max_lat": -80.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 20.0,
        "map_scale_desc": "20 meters/pixel (Polar Stereographic)",
        "projection": "Polar Stereographic (South Pole centered, standard parallel -90°)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_20m.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_20m.lbl",
        "ancillary_urls_json": json.dumps({
            "north_pole_counterpart": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80n_20m.img"
        }),
        "description": "Ultra-high-density polar altimetry grid covering Shackleton, Malapert, Faustini, and Amundsen craters. Derived from densely overlapping polar passes.",
        "scientific_significance": "Critical baseline topography for Artemis landing site slope hazards, illumination simulations, and direct line-of-sight communication modeling."
    },
    {
        "raster_id": "MOON_LOLA_EDR_ALTIMETER_TRACKS",
        "target_body": "Moon",
        "scientific_category": "DEM/DHM",
        "sub_category": "Raw Altimeter Profiles (EDR)",
        "target_feature": "Lunar Polar & Equatorial Tracks",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Orbiter Laser Altimeter (LOLA)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "lolaedr122590153.dat",
        "product_title": "LRO LOLA Experiment Data Record (EDR) Raw Calibrated Laser Ranges",
        "data_format": "PDS3 Binary Table / DAT",
        "min_lat": -90.0,
        "max_lat": 90.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 1.0,
        "map_scale_desc": "Along-track spot spacing ~10 m across 5-laser spot cross-pattern",
        "projection": "Along-track Orbit Ground-Track (Spacecraft Coordinates)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-2-edr-v1/lrolol_0xxx/data/lola_edr/lro_es_01/lolaedr122590153.dat",
        "direct_label_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-2-edr-v1/lrolol_0xxx/data/lola_edr/lro_es_01/lolaedr122590153.lbl",
        "ancillary_urls_json": json.dumps({
            "edr_series": "lro-l-lola-2-edr-v1"
        }),
        "description": "Level 1/2 raw instrument telemetry containing time-of-flight, detector pulse energies, pulse widths, and instrument status for 5 simultaneous laser detectors.",
        "scientific_significance": "Essential for surface roughness (RMS slope) derivation, laser return pulse reflectance, and custom re-orbit geodetic trajectory processing."
    },
    {
        "raster_id": "MOON_KAGUYA_TC_DTM_SEAMLESS",
        "target_body": "Moon",
        "scientific_category": "DEM/DHM",
        "sub_category": "Stereo Photogrammetric DTM",
        "target_feature": "Lunar Equatorial & Mid-Latitudes (0°N-3°S, 0°E-3°E)",
        "mission": "SELENE / Kaguya",
        "instrument": "Terrain Camera (TC)",
        "archive_agency": "JAXA DARTS",
        "product_id": "DTM_MAPs02_N00E000S03E003SC.img",
        "product_title": "Kaguya Terrain Camera Seamless Digital Elevation Model v2.0 (8.42 m/pix)",
        "data_format": "PDS3/IMG (16-bit signed integer)",
        "min_lat": -3.0,
        "max_lat": 0.0,
        "min_lon": 0.0,
        "max_lon": 3.0,
        "spatial_resolution_m": 8.42,
        "map_scale_desc": "3600 pixels/degree (~8.42 m/pixel)",
        "projection": "Simple Cylindrical (Spherical radius 1737.4 km)",
        "direct_data_url": "https://data.darts.isas.jaxa.jp/pub/pds3/sln-l-tc-5-dtm-map-seamless-v2.0/lon000/data/DTM_MAPs02_N00E000S03E003SC.img",
        "direct_label_url": "https://data.darts.isas.jaxa.jp/pub/pds3/sln-l-tc-5-dtm-map-seamless-v2.0/lon000/data/DTM_MAPs02_N00E000S03E003SC.lbl",
        "ancillary_urls_json": json.dumps({
            "darts_dataset_urn": "urn:jaxa:darts:sln-l-tc-5-dtm-map-seamless-v2.0"
        }),
        "description": "Seamless high-precision stereogrammetric DTM produced by JAXA SELENE TC stereo forward/backward slant optics, tied to laser altimeter (LALT) points.",
        "scientific_significance": "Highest resolution seamless global stereo topography dataset outside extreme polar shadow zones."
    },
    {
        "raster_id": "MOON_KAGUYA_TC_USGS_POLAR_COG",
        "target_body": "Moon",
        "scientific_category": "DEM/DHM",
        "sub_category": "Stereo DTM Cloud-Optimized GeoTIFF",
        "target_feature": "Lunar South Polar Region (73.6°S, 260.6°E)",
        "mission": "SELENE / Kaguya",
        "instrument": "Terrain Camera (TC) / USGS Astrogeology Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "TC2W2B0_01_07536S736E2606__TC1W2B0_01_07536S733E2605-DEM.tif",
        "product_title": "USGS Controlled Kaguya TC Polar DTM Cloud-Optimized GeoTIFF (10.3 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 32-bit float)",
        "min_lat": -75.36,
        "max_lat": -73.30,
        "min_lon": 258.5,
        "max_lon": 262.0,
        "spatial_resolution_m": 10.3,
        "map_scale_desc": "10.3 meters/pixel",
        "projection": "Polar Stereographic (Moon 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/moon/kaguya/terrain_camera/usgs_dtms_v2/TC2W2B0_01_07536S736E2606__TC1W2B0_01_07536S733E2605/TC2W2B0_01_07536S736E2606__TC1W2B0_01_07536S733E2605-DEM.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "stac_item_url": "https://stac.astrogeology.usgs.gov/api/collections/kaguya_tc_dtms_v2/items/TC2W2B0_01_07536S736E2606__TC1W2B0_01_07536S733E2605"
        }),
        "description": "USGS Analysis-Ready Dataset (ARD) derived from ISIS3 stereo bundle-adjustment of Kaguya TC stereo pairs, cloud-optimized for direct streaming.",
        "scientific_significance": "Direct GDAL / Rasterio streaming capability for polar slope mapping and optical-laser co-registration."
    },
    {
        "raster_id": "MOON_KAGUYA_LALT_SOUTH_POLAR_GRID",
        "target_body": "Moon",
        "scientific_category": "DEM/DHM",
        "sub_category": "Laser Altimetry Polar Grid",
        "target_feature": "Lunar South Pole (70°S - 90°S)",
        "mission": "SELENE / Kaguya",
        "instrument": "Laser Altimeter (LALT)",
        "archive_agency": "JAXA DARTS",
        "product_id": "LALT_GT_SP_IMG.IMG",
        "product_title": "Kaguya LALT South Polar Topographic Grid v2.0",
        "data_format": "PDS3/IMG (16-bit signed integer)",
        "min_lat": -90.0,
        "max_lat": -70.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 7500.0,
        "map_scale_desc": "0.25 degrees grid (~7.5 km/pixel)",
        "projection": "Polar Stereographic (South Pole)",
        "direct_data_url": "https://data.darts.isas.jaxa.jp/pub/pds3/sln-l-lalt-5-topo-gt-sp-img-v2.0/data/LALT_GT_SP_IMG.IMG",
        "direct_label_url": "https://data.darts.isas.jaxa.jp/pub/pds3/sln-l-lalt-5-topo-gt-sp-img-v2.0/data/LALT_GT_SP_IMG.LBL",
        "ancillary_urls_json": json.dumps({
            "jaxa_pds_node": "https://data.darts.isas.jaxa.jp/pub/pds3/sln-l-lalt-5-topo-gt-sp-img-v2.0/"
        }),
        "description": "South polar laser altimetry map compiled by the SELENE science project, anchoring lunar center-of-mass to center-of-figure offsets.",
        "scientific_significance": "Historical baseline cross-calibrator for LOLA and Chang'e laser altimeters."
    },

    # Mars: MGS MOLA MEGDR & Mars Express HRSC
    {
        "raster_id": "MARS_MGS_MOLA_MEGDR_GLOBAL_128",
        "target_body": "Mars",
        "scientific_category": "DEM/DHM",
        "sub_category": "Global Topographic Grid",
        "target_feature": "Global Mars Topography (Quadrant 0°-90°E, 0°-44°N)",
        "mission": "Mars Global Surveyor (MGS)",
        "instrument": "Mars Orbiter Laser Altimeter (MOLA)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "megt44n000hb.img",
        "product_title": "MGS MOLA Mission Experiment Gridded Data Record (MEGDR) 128 ppd (463 m/pix)",
        "data_format": "PDS3/IMG (16-bit signed integer)",
        "min_lat": 0.0,
        "max_lat": 44.0,
        "min_lon": 0.0,
        "max_lon": 90.0,
        "spatial_resolution_m": 463.0,
        "map_scale_desc": "128 pixels/degree (~463 m/pixel at equator)",
        "projection": "Equirectangular / Simple Cylindrical (Mars IAU 2000 ellipsoid)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/megt44n000hb.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/megt44n000hb.lbl",
        "ancillary_urls_json": json.dumps({
            "areoid_geoid_grid": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/megr44n000hb.img"
        }),
        "description": "Authoritative standard MOLA topography gridded dataset (MEGDR 128). Elevation relative to the MOLA Martian Areoid (geoid defined by gravity model GMM-2B).",
        "scientific_significance": "Foundational global Martian topographic datum, used to calibrate all subsequent camera stereo DTMs (HRSC, CTX, HiRISE)."
    },
    {
        "raster_id": "MARS_MGS_MOLA_POLAR_SOUTH_512",
        "target_body": "Mars",
        "scientific_category": "DEM/DHM",
        "sub_category": "Polar Digital Elevation Model",
        "target_feature": "Planum Australe / South Polar Ice Cap (-90° to -73.15°)",
        "mission": "Mars Global Surveyor (MGS)",
        "instrument": "Mars Orbiter Laser Altimeter (MOLA)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "megt_s_512_1.img",
        "product_title": "MGS MOLA South Polar Stereographic Elevation Model (512 ppd, 115 m/pix)",
        "data_format": "PDS3/IMG (16-bit signed integer)",
        "min_lat": -90.0,
        "max_lat": -73.15,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 115.0,
        "map_scale_desc": "512 pixels/degree (~115 m/pixel)",
        "projection": "Polar Stereographic (South Pole centered)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/polar/megt_s_512_1.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/polar/megt_s_512_1.lbl",
        "ancillary_urls_json": json.dumps({
            "north_pole_mola_dem": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/polar/megt_n_512_1.img"
        }),
        "description": "High-density polar stereographic grid of Mars South Polar Layered Deposits (SPLD), revealing spiral troughs and ice cap thickness up to 3.7 km.",
        "scientific_significance": "Essential for calculating polar ice volume, seasonal CO2 sublimation budgets, and basal topography."
    },
    {
        "raster_id": "MARS_MEX_HRSC_DTM_ORBIT_0010",
        "target_body": "Mars",
        "scientific_category": "DEM/DHM",
        "sub_category": "Multi-Line Stereo DTM",
        "target_feature": "Mars Equatorial Highlands / Orbit 0010 Swath",
        "mission": "Mars Express (MEX)",
        "instrument": "High Resolution Stereo Camera (HRSC)",
        "archive_agency": "NASA PDS / ESA Planetary Science Archive (PSA)",
        "product_id": "h0010_0009_dt4.img",
        "product_title": "Mars Express HRSC Level 4 Digital Terrain Model (50 m/pixel)",
        "data_format": "PDS3/VICAR IMG (32-bit floating point)",
        "min_lat": -12.4,
        "max_lat": 8.6,
        "min_lon": 338.2,
        "max_lon": 344.8,
        "spatial_resolution_m": 50.0,
        "map_scale_desc": "50 meters/pixel (Level 4 DTM)",
        "projection": "Sinusoidal / Equirectangular (tied to MOLA Areoid)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/mex/mex-m-hrsc-5-refdr-dtm-v1/mexhrs_2001/data/0010/h0010_0009_dt4.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/mex/mex-m-hrsc-5-refdr-dtm-v1/mexhrs_2001/data/0010/h0010_0009_dt4.lbl",
        "ancillary_urls_json": json.dumps({
            "esa_psa_level5_ortho": "https://archives.esac.esa.int/psa/ftp/MARS-EXPRESS/HRSC/MEX-M-HRSC-5-REFDR-MAPPROJECTED-V3.0/DATA/0010/H0010_0009_ND3.JP2",
            "esa_psa_level5_label": "https://archives.esac.esa.int/psa/ftp/MARS-EXPRESS/HRSC/MEX-M-HRSC-5-REFDR-MAPPROJECTED-V3.0/DATA/0010/H0010_0009_ND3.LBL"
        }),
        "description": "ESA Mars Express HRSC stereo terrain model generated from 9 CCD line detectors observing Mars under 5 distinct stereo tilt angles simultaneously.",
        "scientific_significance": "Bridging regional scale (50 m) between MOLA global altimetry (463 m) and local CTX/HiRISE stereo models."
    },

    # =========================================================================
    # SECTION 2: HIGH-RESOLUTION IMAGERY & SLOPE MAPS
    # =========================================================================
    # Moon: LROC NAC Polar Tiles (Shackleton, Malapert, Faustini)
    {
        "raster_id": "MOON_LROC_NAC_SHACKLETON_DTM",
        "target_body": "Moon",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Photogrammetric Polar DTM",
        "target_feature": "Shackleton Crater Connecting Ridge (89.5°S - 90.0°S)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Reconnaissance Orbiter Camera (LROC NAC)",
        "archive_agency": "NASA PDS Imaging Node / LROC SOC",
        "product_id": "NAC_DTM_SHACKRDGE02.TIF",
        "product_title": "LROC NAC Shackleton Connecting Ridge Digital Terrain Model GeoTIFF (3.5 m/pix)",
        "data_format": "GeoTIFF (32-bit floating point)",
        "min_lat": -90.0,
        "max_lat": -89.45,
        "min_lon": 85.0,
        "max_lon": 140.0,
        "spatial_resolution_m": 3.5,
        "map_scale_desc": "3.5 meters/pixel",
        "projection": "Polar Stereographic (Center -90.0° Lat, 0.0° Lon)",
        "direct_data_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/SHACKRDGE02/NAC_DTM_SHACKRDGE02.TIF",
        "direct_label_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/SHACKRDGE02/NAC_DTM_SHACKRDGE02.LBL",
        "ancillary_urls_json": json.dumps({
            "xml_pds4_label": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/SHACKRDGE02/NAC_DTM_SHACKRDGE02.xml"
        }),
        "description": "High-resolution stereo elevation model constructed from paired LROC Narrow Angle Camera sub-meter orbit frames, tied to LOLA polar control points.",
        "scientific_significance": "Primary candidate site for Artemis III human landing and permanent lunar habitat due to elevated solar illumination."
    },
    {
        "raster_id": "MOON_LROC_NAC_SHACKLETON_SLOPE",
        "target_body": "Moon",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Slope Hazard Map",
        "target_feature": "Shackleton Crater Connecting Ridge (89.5°S - 90.0°S)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Reconnaissance Orbiter Camera (LROC NAC)",
        "archive_agency": "NASA PDS Imaging Node / LROC SOC",
        "product_id": "NAC_DTM_SHACKRDGE02_SLOPE.TIF",
        "product_title": "LROC NAC Shackleton Connecting Ridge Slope Map GeoTIFF (Degrees)",
        "data_format": "GeoTIFF (32-bit floating point, units in degrees 0-90°)",
        "min_lat": -90.0,
        "max_lat": -89.45,
        "min_lon": 85.0,
        "max_lon": 140.0,
        "spatial_resolution_m": 3.5,
        "map_scale_desc": "3.5 meters/pixel",
        "projection": "Polar Stereographic (Center -90.0° Lat, 0.0° Lon)",
        "direct_data_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/SHACKRDGE02/NAC_DTM_SHACKRDGE02_SLOPE.TIF",
        "direct_label_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/SHACKRDGE02/NAC_DTM_SHACKRDGE02_SLOPE.LBL",
        "ancillary_urls_json": json.dumps({
            "xml_pds4_label": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/SHACKRDGE02/NAC_DTM_SHACKRDGE02_SLOPE.xml"
        }),
        "description": "Quantitative slope magnitude map calculated from the 3.5 m Shackleton DTM using a 3x3 pixel kernel gradient. Slopes expressed in degrees (0° to 90°).",
        "scientific_significance": "Direct lander stability validation (threshold < 15°) and rover trafficability corridor pathfinding."
    },
    {
        "raster_id": "MOON_LROC_NAC_MALAPERT_DTM",
        "target_body": "Moon",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Photogrammetric Polar DTM",
        "target_feature": "Malapert Massif Peak (85.8°S, 357.0°E)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Reconnaissance Orbiter Camera (LROC NAC)",
        "archive_agency": "NASA PDS Imaging Node / LROC SOC",
        "product_id": "NAC_DTM_MALAPERT01.TIF",
        "product_title": "LROC NAC Malapert Massif Elevation Model GeoTIFF (4.0 m/pix)",
        "data_format": "GeoTIFF (32-bit floating point)",
        "min_lat": -86.1,
        "max_lat": -85.6,
        "min_lon": 355.0,
        "max_lon": 359.5,
        "spatial_resolution_m": 4.0,
        "map_scale_desc": "4.0 meters/pixel",
        "projection": "Polar Stereographic (Center -90.0° Lat, 0.0° Lon)",
        "direct_data_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/MALAPERT01/NAC_DTM_MALAPERT01.TIF",
        "direct_label_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/MALAPERT01/NAC_DTM_MALAPERT01.LBL",
        "ancillary_urls_json": json.dumps({
            "xml_pds4_label": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/MALAPERT01/NAC_DTM_MALAPERT01.xml"
        }),
        "description": "Stereo digital terrain model covering the summit of Malapert Massif, an elevated lunar mountain standing ~5,000 meters above surrounding lowlands.",
        "scientific_significance": "Touchdown site for Intuitive Machines IM-1 Odysseus and key candidate for continuous Earth line-of-sight telecommunications relays."
    },
    {
        "raster_id": "MOON_LROC_NAC_MALAPERT_SLOPE",
        "target_body": "Moon",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Slope Hazard Map",
        "target_feature": "Malapert Massif Peak (85.8°S, 357.0°E)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Reconnaissance Orbiter Camera (LROC NAC)",
        "archive_agency": "NASA PDS Imaging Node / LROC SOC",
        "product_id": "NAC_DTM_MALAPERT01_SLOPE.TIF",
        "product_title": "LROC NAC Malapert Massif Slope Map GeoTIFF (Degrees)",
        "data_format": "GeoTIFF (32-bit floating point, units in degrees)",
        "min_lat": -86.1,
        "max_lat": -85.6,
        "min_lon": 355.0,
        "max_lon": 359.5,
        "spatial_resolution_m": 4.0,
        "map_scale_desc": "4.0 meters/pixel",
        "projection": "Polar Stereographic (Center -90.0° Lat, 0.0° Lon)",
        "direct_data_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/MALAPERT01/NAC_DTM_MALAPERT01_SLOPE.TIF",
        "direct_label_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/MALAPERT01/NAC_DTM_MALAPERT01_SLOPE.LBL",
        "ancillary_urls_json": json.dumps({
            "xml_pds4_label": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/SDP/NAC_DTM/MALAPERT01/NAC_DTM_MALAPERT01_SLOPE.xml"
        }),
        "description": "Slope angle raster derived from Malapert Massif 4m DTM showing gentle summit plateaus (< 8°) bordered by steep 25°-32° escarpments.",
        "scientific_significance": "Defining safe landing envelopes and evaluating tip-over risks during lunar descent."
    },
    {
        "raster_id": "MOON_LROC_NAC_FAUSTINI_POLAR_TILE",
        "target_body": "Moon",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Sub-Meter Polar Orthomosaic",
        "target_feature": "Faustini Crater Rim & Floor (87.8°S, 90.0°E)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Reconnaissance Orbiter Camera (LROC NAC)",
        "archive_agency": "NASA PDS Imaging Node / LROC SOC",
        "product_id": "NAC_ROI_FAUSTINILO1_P878S0900.TIF",
        "product_title": "LROC NAC Faustini Crater Sub-Meter Polar Orthoimage GeoTIFF (1.0 m/pix)",
        "data_format": "GeoTIFF (8-bit grayscale)",
        "min_lat": -88.5,
        "max_lat": -87.1,
        "min_lon": 75.0,
        "max_lon": 105.0,
        "spatial_resolution_m": 1.0,
        "map_scale_desc": "1.0 meter/pixel (Polar Stereographic)",
        "projection": "Polar Stereographic (Center -90.0° Lat, 0.0° Lon)",
        "direct_data_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/EXTRAS/BROWSE/NAC_ROI/FAUSTINILO1/NAC_ROI_FAUSTINILO1_P878S0900.TIF",
        "direct_label_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/BDR/NAC_ROI/FAUSTINILO1/NAC_ROI_FAUSTINILO1_P878S0900.xml",
        "ancillary_urls_json": json.dumps({
            "raw_img_url": "https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/DATA/BDR/NAC_ROI/FAUSTINILO1/NAC_ROI_FAUSTINILO1_P878S0900.IMG"
        }),
        "description": "Controlled sub-meter orthorectified mosaic of Faustini crater, resolving boulders down to 2-3 meters and crater rims harboring permanent shadow.",
        "scientific_significance": "Target candidate for volatile prospecting into nearby permanently shadowed regions (PSRs)."
    },

    # Mars: HiRISE / CTX DTMs for Candidate Landing Zones (Jezero, Arcadia Planitia, Gale)
    {
        "raster_id": "MARS_MRO_HIRISE_JEZERO_DTM",
        "target_body": "Mars",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Sub-Meter Rover Landing DTM",
        "target_feature": "Jezero Crater Western Fan & Delta (18.4°N, 77.5°E)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "instrument": "High Resolution Imaging Science Experiment (HiRISE)",
        "archive_agency": "NASA PDS / Univ of Arizona HiRISE Operations Center",
        "product_id": "DTEEC_045994_1985_046060_1985_U01.IMG",
        "product_title": "HiRISE Jezero Crater Delta High-Precision DTM (1.01 m/pixel)",
        "data_format": "PDS3/VICAR IMG (32-bit floating point, meters elevation)",
        "min_lat": 18.25,
        "max_lat": 18.65,
        "min_lon": 77.25,
        "max_lon": 77.65,
        "spatial_resolution_m": 1.01,
        "map_scale_desc": "1.01 meters/pixel",
        "projection": "Equirectangular (Center lat 0.0°, standard parallel 18.0°)",
        "direct_data_url": "https://hirise-pds.lpl.arizona.edu/PDS/DTM/ESP/ORB_045900_045999/ESP_045994_1985_ESP_046060_1985/DTEEC_045994_1985_046060_1985_U01.IMG",
        "direct_label_url": "https://hirise-pds.lpl.arizona.edu/PDS/DTM/ESP/ORB_045900_045999/ESP_045994_1985_ESP_046060_1985/DTEEC_045994_1985_046060_1985_U01.LBL",
        "ancillary_urls_json": json.dumps({
            "color_relief_jp2": "https://hirise-pds.lpl.arizona.edu/PDS/EXTRAS/DTM/ESP/ORB_045900_045999/ESP_045994_1985_ESP_046060_1985/DTFEC_045994_1985_046060_1985_U01.JP2"
        }),
        "description": "Stereo digital terrain model covering the Perseverance rover landing ellipse (Octavia E. Butler Landing) and the ancient river delta scarps.",
        "scientific_significance": "Enabled NASA Mars 2020 Terrain-Relative Navigation (TRN) landing and ongoing Perseverance traverse route elevation profiling."
    },
    {
        "raster_id": "MARS_MRO_CTX_JEZERO_CONTROLLED_MOSAIC",
        "target_body": "Mars",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Controlled Context Orthomosaic",
        "target_feature": "Jezero Crater & Surrounding Nili Fossae",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "instrument": "Context Camera (CTX) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W_orthoimage.tif",
        "product_title": "USGS Controlled CTX Jezero Crater Orthomosaic GeoTIFF (6.0 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 8-bit grayscale)",
        "min_lat": 17.5,
        "max_lat": 19.5,
        "min_lon": 76.5,
        "max_lon": 78.5,
        "spatial_resolution_m": 6.0,
        "map_scale_desc": "6.0 meters/pixel",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/mro/ctx/controlled/usgs/P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W/P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W_orthoimage.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "stac_item_url": "https://stac.astrogeology.usgs.gov/api/collections/mro_ctx_controlled/items/P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W"
        }),
        "description": "USGS Astrogeology bundle-adjusted CTX controlled mosaic tied directly to MOLA elevation, providing regional context for Jezero Crater.",
        "scientific_significance": "Wide-area regional baseline connecting HiRISE local tiles to regional watershed channels and crater rim geometry."
    },
    {
        "raster_id": "MARS_MRO_HIRISE_GALE_CRATER_DTM",
        "target_body": "Mars",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Sub-Meter Rover Landing DTM",
        "target_feature": "Gale Crater & Mount Sharp (Aeolis Mons) Slopes (-4.6°S, 137.4°E)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "instrument": "High Resolution Imaging Science Experiment (HiRISE)",
        "archive_agency": "NASA PDS / Univ of Arizona HiRISE Operations Center",
        "product_id": "DTEEC_009149_1750_009294_1750_U01.IMG",
        "product_title": "HiRISE Gale Crater Curiosity Rover Traverse DTM (1.01 m/pixel)",
        "data_format": "PDS3/VICAR IMG (32-bit floating point)",
        "min_lat": -4.85,
        "max_lat": -4.45,
        "min_lon": 137.2,
        "max_lon": 137.6,
        "spatial_resolution_m": 1.01,
        "map_scale_desc": "1.01 meters/pixel",
        "projection": "Equirectangular (Center lat 0.0°, standard parallel -4.0°)",
        "direct_data_url": "https://hirise-pds.lpl.arizona.edu/PDS/DTM/PSP/ORB_009100_009199/PSP_009149_1750_PSP_009294_1750/DTEEC_009149_1750_009294_1750_U01.IMG",
        "direct_label_url": "https://hirise-pds.lpl.arizona.edu/PDS/DTM/PSP/ORB_009100_009199/PSP_009149_1750_PSP_009294_1750/DTEEC_009149_1750_009294_1750_U01.LBL",
        "ancillary_urls_json": json.dumps({
            "color_relief_jp2": "https://hirise-pds.lpl.arizona.edu/PDS/EXTRAS/DTM/PSP/ORB_009100_009199/PSP_009149_1750_PSP_009294_1750/DTFEC_009149_1750_009294_1750_U01.JP2"
        }),
        "description": "Stereo terrain model covering Bradbury Landing and the sulfate-bearing stratigraphy along Mount Sharp traversed by Curiosity.",
        "scientific_significance": "Crucial for navigating Curiosity through the Bagnold Dune fields and Vera Rubin Ridge."
    },
    {
        "raster_id": "MARS_MRO_CTX_GALE_GEOID_DTM",
        "target_body": "Mars",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Controlled Regional DTM",
        "target_feature": "Gale Crater Rim to Peak (-4.5°S, 137.4°E)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "instrument": "Context Camera (CTX) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "T01_000881_1752_XI_04S223W__P22_009716_1773_XI_02S223W-DEM-geoid-adj.tif",
        "product_title": "USGS Controlled CTX Gale Crater Geoid-Adjusted DTM GeoTIFF (20 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 32-bit float)",
        "min_lat": -5.5,
        "max_lat": -3.5,
        "min_lon": 136.0,
        "max_lon": 138.5,
        "spatial_resolution_m": 20.0,
        "map_scale_desc": "20 meters/pixel (Geoid-adjusted)",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/mro/ctx/controlled/usgs/T01_000881_1752_XI_04S223W__P22_009716_1773_XI_02S223W/T01_000881_1752_XI_04S223W__P22_009716_1773_XI_02S223W-DEM-geoid-adj.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "stac_item_url": "https://stac.astrogeology.usgs.gov/api/collections/mro_ctx_controlled/items/T01_000881_1752_XI_04S223W__P22_009716_1773_XI_02S223W"
        }),
        "description": "Controlled 20m/pixel DTM adjusted to the MOLA geoid spanning the entirety of Gale Crater's central mound and northern floor.",
        "scientific_significance": "Hydrological modeling of ancient paleolake levels and sedimentary mound compaction."
    },
    {
        "raster_id": "MARS_MRO_HIRISE_ARCADIA_ICE_DTM",
        "target_body": "Mars",
        "scientific_category": "High-Res Imagery & Slopes",
        "sub_category": "Subsurface Ice Landing Zone DTM",
        "target_feature": "Arcadia Planitia Shallow Ice Sheets (38.8°N, 189.6°E)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "instrument": "High Resolution Imaging Science Experiment (HiRISE)",
        "archive_agency": "NASA PDS / Univ of Arizona HiRISE Operations Center",
        "product_id": "DTEED_055378_2190_055444_2190_A01.IMG",
        "product_title": "HiRISE Arcadia Planitia Subsurface Ice Site DTM (1.0 m/pixel)",
        "data_format": "PDS3/VICAR IMG (32-bit floating point)",
        "min_lat": 38.6,
        "max_lat": 39.1,
        "min_lon": 189.4,
        "max_lon": 189.8,
        "spatial_resolution_m": 1.0,
        "map_scale_desc": "1.0 meter/pixel",
        "projection": "Equirectangular (Center lat 0.0°, standard parallel 39.0°)",
        "direct_data_url": "https://hirise-pds.lpl.arizona.edu/PDS/DTM/ESP/ORB_055300_055399/ESP_055378_2190_ESP_055444_2190/DTEED_055378_2190_055444_2190_A01.IMG",
        "direct_label_url": "https://hirise-pds.lpl.arizona.edu/PDS/DTM/ESP/ORB_055300_055399/ESP_055378_2190_ESP_055444_2190/DTEED_055378_2190_055444_2190_A01.LBL",
        "ancillary_urls_json": json.dumps({
            "color_relief_jp2": "https://hirise-pds.lpl.arizona.edu/PDS/EXTRAS/DTM/ESP/ORB_055300_055399/ESP_055378_2190_ESP_055444_2190/DTFED_055378_2190_055444_2190_A01.JP2"
        }),
        "description": "High-resolution elevation model across Arcadia Planitia expanded thermal contraction polygons indicating sheet ice within 1-2 meters of surface.",
        "scientific_significance": "Prime candidate human landing site and In-Situ Resource Utilization (ISRU) water extraction zone."
    },

    # =========================================================================
    # SECTION 3: RESOURCE & VOLATILES DISTRIBUTION
    # =========================================================================
    # Moon: Lunar Prospector NS & Chandrayaan-1 M3
    {
        "raster_id": "MOON_LP_NS_EPITHERMAL_HYDROGEN",
        "target_body": "Moon",
        "scientific_category": "Resource & Volatiles Distribution",
        "sub_category": "Neutron Spectrometer Volatiles Map",
        "target_feature": "Global Lunar Hydrogen & Polar Volatiles",
        "mission": "Lunar Prospector",
        "instrument": "Neutron Spectrometer (NS)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "epitherm_neutron_high32sec.dat",
        "product_title": "Lunar Prospector High-Altitude 32-Second Epithermal Neutron Flux (0.5°/pix)",
        "data_format": "PDS3 Binary Table / DAT",
        "min_lat": -90.0,
        "max_lat": 90.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 15000.0,
        "map_scale_desc": "0.5 degrees/pixel (~15 km/pixel)",
        "projection": "Simple Cylindrical (Center 0° Lon)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/lunar/lp-l-grs-3-rdr-v1/lp_2xxx/ns/epitherm_neutron_high32sec.dat",
        "direct_label_url": "https://pds-geosciences.wustl.edu/lunar/lp-l-grs-3-rdr-v1/lp_2xxx/ns/epitherm_neutron_high32sec.lbl",
        "ancillary_urls_json": json.dumps({
            "thermal_neutrons": "https://pds-geosciences.wustl.edu/lunar/lp-l-grs-3-rdr-v1/lp_2xxx/ns/thermal_neutron_high32sec.dat"
        }),
        "description": "Calibrated epithermal neutron counting rates from Lunar Prospector. Dips in epithermal flux directly correlate with elevated hydrogen/water concentrations.",
        "scientific_significance": "Historical dataset providing the first direct orbital evidence of hydrogen enrichment (up to 1.5 wt% WEH) in lunar polar cold traps."
    },
    {
        "raster_id": "MOON_CH1_M3_REFLECTANCE_CUBE_EQUATOR",
        "target_body": "Moon",
        "scientific_category": "Resource & Volatiles Distribution",
        "sub_category": "Hyperspectral Reflectance Cube (Water/OH Absorption)",
        "target_feature": "Lunar Equatorial Highland / Mare Boundary",
        "mission": "Chandrayaan-1",
        "instrument": "Moon Mineralogy Mapper (M3)",
        "archive_agency": "NASA PDS Imaging Node / JPL",
        "product_id": "M3G20090201T064933_V01_RFL.IMG",
        "product_title": "Chandrayaan-1 M3 Level 2 Surface Reflectance Hypercube (85 bands, 430-3000 nm)",
        "data_format": "PDS3/VICAR Spectral Cube / IMG (16-bit signed integer)",
        "min_lat": -10.0,
        "max_lat": 15.0,
        "min_lon": 45.0,
        "max_lon": 52.0,
        "spatial_resolution_m": 140.0,
        "map_scale_desc": "140 meters/pixel (Global Mode)",
        "projection": "Equirectangular / Spacecraft Coordinate Pushbroom",
        "direct_data_url": "https://planetarydata.jpl.nasa.gov/img/data/m3/CH1M3_0004/DATA/20081118_20090214/200902/L2/M3G20090201T064933_V01_RFL.IMG",
        "direct_label_url": "https://planetarydata.jpl.nasa.gov/img/data/m3/CH1M3_0004/DATA/20081118_20090214/200902/L2/M3G20090201T064933_V01_RFL.LBL",
        "ancillary_urls_json": json.dumps({
            "gdal_vrt_header": "https://planetarydata.jpl.nasa.gov/img/data/m3/CH1M3_0004/DATA/20081118_20090214/200902/L2/M3G20090201T064933_V01_RFL.vrt"
        }),
        "description": "Level 2 photometrically- and atmospherically-corrected surface reflectance cube spanning 85 continuous spectral bands from 430 nm to 3000 nm.",
        "scientific_significance": "Detection of diagnostic 2.8-3.0 µm OH/H2O absorption features across illuminated sunlit lunar regolith."
    },
    {
        "raster_id": "MOON_CH1_M3_REFLECTANCE_CUBE_SOUTH_POLE",
        "target_body": "Moon",
        "scientific_category": "Resource & Volatiles Distribution",
        "sub_category": "Polar Hyperspectral Cube (Water Ice Detection)",
        "target_feature": "Lunar South Polar Region (Cabeus / Faustini / Shackleton)",
        "mission": "Chandrayaan-1",
        "instrument": "Moon Mineralogy Mapper (M3)",
        "archive_agency": "NASA PDS Imaging Node / JPL",
        "product_id": "M3G20090131T112714_V01_RFL.IMG",
        "product_title": "Chandrayaan-1 M3 South Polar Target Reflectance Hypercube (140 m/pix)",
        "data_format": "PDS3/VICAR Spectral Cube / IMG",
        "min_lat": -90.0,
        "max_lat": -75.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 140.0,
        "map_scale_desc": "140 meters/pixel (Orbit 1015, Global Mode)",
        "projection": "Polar Stereographic / Spacecraft Pushbroom",
        "direct_data_url": "https://planetarydata.jpl.nasa.gov/img/data/m3/CH1M3_0004/DATA/20081118_20090214/200901/L2/M3G20090131T112714_V01_RFL.IMG",
        "direct_label_url": "https://planetarydata.jpl.nasa.gov/img/data/m3/CH1M3_0004/DATA/20081118_20090214/200901/L2/M3G20090131T112714_V01_L2.LBL",
        "ancillary_urls_json": json.dumps({
            "envi_header": "https://planetarydata.jpl.nasa.gov/img/data/m3/CH1M3_0004/DATA/20081118_20090214/200901/L2/M3G20090131T112714_V01_RFL.HDR"
        }),
        "description": "High-latitude M3 hypercube capturing scattered sunlight inside polar crater walls, measuring 1.3, 1.5, and 2.0 µm diagnostic water ice absorption bands.",
        "scientific_significance": "Confirmed direct spectroscopic surface exposure of water ice deposits inside permanently shadowed lunar craters."
    },

    # Mars: Mars Odyssey GRS/MONS & CRISM MTRDR
    {
        "raster_id": "MARS_ODY_GRS_GLOBAL_WEH_MAP",
        "target_body": "Mars",
        "scientific_category": "Resource & Volatiles Distribution",
        "sub_category": "Water-Equivalent Hydrogen (WEH) Global Map",
        "target_feature": "Global Mars Subsurface Hydrogen (Top 1 Meter)",
        "mission": "2001 Mars Odyssey",
        "instrument": "Gamma Ray Spectrometer Suite (GRS / MONS / HEND)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "h2o_sr_5x5.tab",
        "product_title": "Mars Odyssey GRS Global Water-Equivalent Hydrogen (H2O wt%) Smoothed 5x5 Map",
        "data_format": "PDS3 ASCII Table / TAB",
        "min_lat": -90.0,
        "max_lat": 90.0,
        "min_lon": -180.0,
        "max_lon": 180.0,
        "spatial_resolution_m": 300000.0,
        "map_scale_desc": "5x5 degrees (~300 km/pixel)",
        "projection": "Simple Cylindrical (Center 0° Lon)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/ody/ody-m-grs-5-elements-v1/odgm_xxxx/data/smoothed/h2o_sr_5x5.tab",
        "direct_label_url": "https://pds-geosciences.wustl.edu/ody/ody-m-grs-5-elements-v1/odgm_xxxx/data/smoothed/h2o_sr_5x5.lbl",
        "ancillary_urls_json": json.dumps({
            "epithermal_table": "https://pds-geosciences.wustl.edu/ody/ody-m-grs-5-elements-v1/odgm_xxxx/data/smoothed/epithermal_sr_5x5.tab"
        }),
        "description": "Quantified water-equivalent hydrogen concentration in weight percent across top 1 meter of Martian soil, combining GRS 2.223 MeV gamma rays and MONS neutron suppression.",
        "scientific_significance": "Discovered vast polar subsurface permafrost ice sheets (> 50-70 wt% H2O) poleward of 60° latitude and equatorial hydrated minerals (2-10 wt%)."
    },
    {
        "raster_id": "MARS_MRO_CRISM_JEZERO_MINERAL_PARAMS",
        "target_body": "Mars",
        "scientific_category": "Resource & Volatiles Distribution",
        "sub_category": "Hyperspectral Mineral & Hydrated Sulfate Parameters",
        "target_feature": "Jezero Crater Delta & Margin Carbonates (FRT000047A3)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "instrument": "Compact Reconnaissance Imaging Spectrometer for Mars (CRISM)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "frt000047a3_07_su166j_mtr3.img",
        "product_title": "CRISM Jezero Delta MTRDR Mineral Summary Parameter Cube (18 m/pixel)",
        "data_format": "PDS3/VICAR Spectral Cube / IMG (32-bit floating point)",
        "min_lat": 18.15,
        "max_lat": 18.70,
        "min_lon": 77.10,
        "max_lon": 77.75,
        "spatial_resolution_m": 18.0,
        "map_scale_desc": "18 meters/pixel (Targeted Mode)",
        "projection": "Equirectangular (Center lat 18.42°, standard parallel 18.42°)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/mro/mro-m-crism-5-rdr-mptargeted-v1/mrocr_4001/mtrdr/2007/2007_057/frt000047a3/frt000047a3_07_su166j_mtr3.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/mro/mro-m-crism-5-rdr-mptargeted-v1/mrocr_4001/mtrdr/2007/2007_057/frt000047a3/frt000047a3_07_su166j_mtr3.lbl",
        "ancillary_urls_json": json.dumps({
            "calibrated_cube_if": "https://pds-geosciences.wustl.edu/mro/mro-m-crism-5-rdr-mptargeted-v1/mrocr_4001/mtrdr/2007/2007_057/frt000047a3/frt000047a3_07_if166j_mtr3.img"
        }),
        "description": "Multi-band summary parameter cube (MTR3) containing pre-calculated spectral band indices: SINDEX (polyhydrated sulfates), BD1900 (H2O/H2O ice), BD2100 (monohydrated sulfates), and D2300 (Mg/Fe phyllosilicates).",
        "scientific_significance": "Definitive evidence of smectite clays, Fe/Mg carbonates, and aqueous sulfate deposition that guided selection of Jezero Crater as Mars 2020 landing site."
    },
    {
        "raster_id": "MARS_MRO_CRISM_GALE_MINERAL_PARAMS",
        "target_body": "Mars",
        "scientific_category": "Resource & Volatiles Distribution",
        "sub_category": "Hyperspectral Mineral & Clay Parameters",
        "target_feature": "Gale Crater Mount Sharp Basal Stratigraphy (HRL00003010)",
        "mission": "Mars Reconnaissance Orbiter (MRO)",
        "instrument": "Compact Reconnaissance Imaging Spectrometer for Mars (CRISM)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "hrl00003010_07_su181j_mtr3.img",
        "product_title": "CRISM Gale Crater Mount Sharp Mineral Summary Parameter Cube (18 m/pixel)",
        "data_format": "PDS3/VICAR Spectral Cube / IMG",
        "min_lat": -5.3,
        "max_lat": -4.2,
        "min_lon": 137.0,
        "max_lon": 137.8,
        "spatial_resolution_m": 18.0,
        "map_scale_desc": "18 meters/pixel",
        "projection": "Equirectangular (Center lat -4.75°)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/mro/mro-m-crism-5-rdr-mptargeted-v1/mrocr_4001/mtrdr/2006/2006_319/hrl00003010/hrl00003010_07_su181j_mtr3.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/mro/mro-m-crism-5-rdr-mptargeted-v1/mrocr_4001/mtrdr/2006/2006_319/hrl00003010/hrl00003010_07_su181j_mtr3.xml",
        "ancillary_urls_json": json.dumps({
            "ode_product_id": "HRL00003010",
            "if_calibrated_cube": "https://pds-geosciences.wustl.edu/mro/mro-m-crism-5-rdr-mptargeted-v1/mrocr_4001/mtrdr/2006/2006_319/hrl00003010/hrl00003010_07_if181j_mtr3.img"
        }),
        "description": "CRISM summary parameter cube documenting the stratigraphic transition from clay-bearing (nontronite/saponite) strata to hydrated sulfate (kieserite/gypsum) units up Mount Sharp.",
        "scientific_significance": "Records Mars' global planetary climate transition from habitable, neutral pH aqueous environments to hyperarid, acidic conditions."
    },

    # =========================================================================
    # SECTION 4: THERMAL & ILLUMINATION REGIMES
    # =========================================================================
    # Moon: LRO Diviner & LOLA Illumination / Peak-of-Eternal-Light
    {
        "raster_id": "MOON_LRO_DIVINER_SOUTH_POLAR_TEMP",
        "target_body": "Moon",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Polar Radiometric Surface Temperature",
        "target_feature": "Lunar South Polar Region (80°S - 90°S)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Diviner Lunar Radiometer Experiment (DLRE)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "pcp_avg_tbol_pols_ls030_slon01_240.tab",
        "product_title": "LRO Diviner Polar Cumulative Product (PCP) Average Bolometric Temperature (240 m/pix)",
        "data_format": "PDS4 ASCII Table / TAB",
        "min_lat": -90.0,
        "max_lat": -80.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 240.0,
        "map_scale_desc": "240 meters/pixel (Polar Stereographic)",
        "projection": "Polar Stereographic (South Pole centered, standard parallel -90°)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/seasonal/slon/pols/pcp_avg_tbol_pols_ls030_slon01_240.tab",
        "direct_label_url": "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/seasonal/slon/pols/pcp_avg_tbol_pols_ls030_slon01_240.xml",
        "ancillary_urls_json": json.dumps({
            "north_pole_counterpart": "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/seasonal/slon/poln/pcp_avg_tbol_poln_ls030_slon01_240.tab"
        }),
        "description": "Multi-year binned surface bolometric brightness temperatures (Kelvin) across solar longitude bin Ls 30°-60°. Captures extreme cryogenic temperatures in PSRs (< 40 K / -233°C).",
        "scientific_significance": "Defines thermal stability zones where water ice, CO2, ammonia, and organic volatiles can persist for billions of years."
    },
    {
        "raster_id": "MOON_LRO_LOLA_SOUTH_POLAR_ILLUMINATION",
        "target_body": "Moon",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Illumination % & Peak-of-Eternal-Light Map",
        "target_feature": "Lunar South Pole (65°S - 90°S)",
        "mission": "Lunar Reconnaissance Orbiter (LRO)",
        "instrument": "Lunar Orbiter Laser Altimeter (LOLA)",
        "archive_agency": "NASA PDS Geosciences Node",
        "product_id": "avgvisib_65s_240m_201608.img",
        "product_title": "LRO LOLA South Pole Average Solar Visibility & Illumination Map (240 m/pixel)",
        "data_format": "PDS3/IMG (16-bit unsigned integer, visibility fraction * 10,000)",
        "min_lat": -90.0,
        "max_lat": -65.0,
        "min_lon": 0.0,
        "max_lon": 360.0,
        "spatial_resolution_m": 240.0,
        "map_scale_desc": "240 meters/pixel (Polar Stereographic)",
        "projection": "Polar Stereographic (South Pole centered, standard parallel -90°)",
        "direct_data_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/avgvisib_65s_240m_201608.img",
        "direct_label_url": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/avgvisib_65s_240m_201608.lbl",
        "ancillary_urls_json": json.dumps({
            "north_pole_illumination": "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/avgvisib_65n_240m_201608.img"
        }),
        "description": "Simulated multi-year percentage solar visibility derived from ray-tracing LOLA topographic horizons over an 18.6-year lunar precession cycle. Identifies 'Peaks of Eternal Light' with > 85-92% annual illumination.",
        "scientific_significance": "Crucial for solar power sizing, battery storage requirements, and thermal survival architecture for Artemis basecamp."
    },

    # Mars: Odyssey THEMIS Daytime & Nighttime IR (Thermal Inertia)
    {
        "raster_id": "MARS_ODY_THEMIS_SYRTIS_MAJOR_NIGHT_IR",
        "target_body": "Mars",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Thermal Inertia & Nighttime IR Mosaic",
        "target_feature": "Syrtis Major Quadrangle (MC-13) / Jezero Crater",
        "mission": "2001 Mars Odyssey",
        "instrument": "Thermal Emission Imaging System (THEMIS IR) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "mc13_syrtis_major_nir.tif",
        "product_title": "USGS Controlled THEMIS Nighttime IR Mosaic GeoTIFF - Syrtis Major (100 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 8-bit unsigned integer brightness temp)",
        "min_lat": 0.0,
        "max_lat": 30.0,
        "min_lon": 45.0,
        "max_lon": 90.0,
        "spatial_resolution_m": 100.0,
        "map_scale_desc": "100 meters/pixel (1/512 degrees/pixel)",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc13_syrtis_major_nir/mc13_syrtis_major_nir.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "daytime_ir_counterpart": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc13_syrtis_major_dir/mc13_syrtis_major_dir.tif"
        }),
        "description": "Geodetically controlled band 9 (12.57 µm) nighttime infrared brightness temperature mosaic. Nighttime temperature is a direct proxy for surface thermal inertia (J m^-2 K^-1 s^-0.5).",
        "scientific_significance": "Differentiates fine unconsolidated dust (low thermal inertia, cools rapidly at night) from competent bedrock and indurated duricrust (high thermal inertia, stays warm at night) around Jezero Crater."
    },
    {
        "raster_id": "MARS_ODY_THEMIS_SYRTIS_MAJOR_DAY_IR",
        "target_body": "Mars",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Daytime IR Albedo & Thermophysical Mosaic",
        "target_feature": "Syrtis Major Quadrangle (MC-13) / Jezero Crater",
        "mission": "2001 Mars Odyssey",
        "instrument": "Thermal Emission Imaging System (THEMIS IR) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "mc13_syrtis_major_dir.tif",
        "product_title": "USGS Controlled THEMIS Daytime IR Mosaic GeoTIFF - Syrtis Major (100 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 8-bit unsigned integer)",
        "min_lat": 0.0,
        "max_lat": 30.0,
        "min_lon": 45.0,
        "max_lon": 90.0,
        "spatial_resolution_m": 100.0,
        "map_scale_desc": "100 meters/pixel",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc13_syrtis_major_dir/mc13_syrtis_major_dir.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "nighttime_ir_counterpart": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc13_syrtis_major_nir/mc13_syrtis_major_nir.tif"
        }),
        "description": "Geodetically controlled daytime thermal infrared mosaic capturing local midday thermal responses, modulated by topographic slope aspect and visual albedo.",
        "scientific_significance": "Complementary day/night pairs enable exact numerical inversion of the thermal inertia equation to solve for surface grain sizes."
    },
    {
        "raster_id": "MARS_ODY_THEMIS_AEOLIS_NIGHT_IR",
        "target_body": "Mars",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Thermal Inertia & Nighttime IR Mosaic",
        "target_feature": "Aeolis Quadrangle (MC-23) / Gale Crater",
        "mission": "2001 Mars Odyssey",
        "instrument": "Thermal Emission Imaging System (THEMIS IR) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "mc23_aeolis_nir.tif",
        "product_title": "USGS Controlled THEMIS Nighttime IR Mosaic GeoTIFF - Aeolis / Gale (100 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 8-bit unsigned integer)",
        "min_lat": -30.0,
        "max_lat": 0.0,
        "min_lon": 135.0,
        "max_lon": 180.0,
        "spatial_resolution_m": 100.0,
        "map_scale_desc": "100 meters/pixel",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc23_aeolis_nir/mc23_aeolis_nir.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "daytime_ir_counterpart": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc23_aeolis_dir/mc23_aeolis_dir.tif"
        }),
        "description": "Controlled THEMIS nighttime infrared mosaic across Aeolis quadrangle encompassing Gale Crater, Peace Vallis fan, and Medusae Fossae Formation.",
        "scientific_significance": "Revealed competent sandstone and conglomerate outcrops along Curiosity's path versus fine drift sand."
    },
    {
        "raster_id": "MARS_ODY_THEMIS_AEOLIS_DAY_IR",
        "target_body": "Mars",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Daytime IR Albedo & Thermophysical Mosaic",
        "target_feature": "Aeolis Quadrangle (MC-23) / Gale Crater",
        "mission": "2001 Mars Odyssey",
        "instrument": "Thermal Emission Imaging System (THEMIS IR) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "mc23_aeolis_dir.tif",
        "product_title": "USGS Controlled THEMIS Daytime IR Mosaic GeoTIFF - Aeolis / Gale (100 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 8-bit unsigned integer)",
        "min_lat": -30.0,
        "max_lat": 0.0,
        "min_lon": 135.0,
        "max_lon": 180.0,
        "spatial_resolution_m": 100.0,
        "map_scale_desc": "100 meters/pixel",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc23_aeolis_dir/mc23_aeolis_dir.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "nighttime_ir_counterpart": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc23_aeolis_nir/mc23_aeolis_nir.tif"
        }),
        "description": "Daytime thermal infrared mosaic over Gale Crater, demonstrating distinct thermal inertia boundaries between the floor dunes and Mount Sharp stratigraphy.",
        "scientific_significance": "Thermophysical classification of rover trafficability terrain types."
    },
    {
        "raster_id": "MARS_ODY_THEMIS_DIACRIA_NIGHT_IR",
        "target_body": "Mars",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Thermal Inertia & Nighttime IR Mosaic",
        "target_feature": "Diacria Quadrangle (MC-02) / North-West Arcadia",
        "mission": "2001 Mars Odyssey",
        "instrument": "Thermal Emission Imaging System (THEMIS IR) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "mc02_diacria_nir.tif",
        "product_title": "USGS Controlled THEMIS Nighttime IR Mosaic GeoTIFF - Diacria (100 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 8-bit unsigned integer)",
        "min_lat": 30.0,
        "max_lat": 65.0,
        "min_lon": 180.0,
        "max_lon": 240.0,
        "spatial_resolution_m": 100.0,
        "map_scale_desc": "100 meters/pixel (MC-02 controlled)",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc02_diacria_nir/mc02_diacria_nir.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "stac_item": "https://stac.astrogeology.usgs.gov/api/collections/themis_controlled/items/mc02_diacria_nir"
        }),
        "description": "Controlled nighttime thermal infrared mosaic across the Diacria quadrangle mapping low thermal inertia mantling over shallow ice.",
        "scientific_significance": "Thermophysical characterization of the ice-cemented regolith mantle for SpaceX Starship / NASA human landing site candidate."
    },
    {
        "raster_id": "MARS_ODY_THEMIS_ARCADIA_NIGHT_IR",
        "target_body": "Mars",
        "scientific_category": "Thermal & Illumination Regimes",
        "sub_category": "Thermal Inertia & Nighttime IR Mosaic",
        "target_feature": "Arcadia Quadrangle (MC-03) / Central Arcadia Planitia",
        "mission": "2001 Mars Odyssey",
        "instrument": "Thermal Emission Imaging System (THEMIS IR) / USGS Processing",
        "archive_agency": "USGS Astrogeology ARD",
        "product_id": "mc03_arcadia_nir.tif",
        "product_title": "USGS Controlled THEMIS Nighttime IR Mosaic GeoTIFF - Arcadia (100 m/pix)",
        "data_format": "GeoTIFF (Cloud-Optimized, 8-bit unsigned integer)",
        "min_lat": 30.0,
        "max_lat": 65.0,
        "min_lon": 240.0,
        "max_lon": 300.0,
        "spatial_resolution_m": 100.0,
        "map_scale_desc": "100 meters/pixel (MC-03 controlled)",
        "projection": "Equirectangular (Mars 2000 datum)",
        "direct_data_url": "https://astrogeo-ard.s3.us-west-2.amazonaws.com/mars/mo/themis/controlled_mosaics/mc03_arcadia_nir/mc03_arcadia_nir.tif",
        "direct_label_url": None,
        "ancillary_urls_json": json.dumps({
            "stac_item": "https://stac.astrogeology.usgs.gov/api/collections/themis_controlled/items/mc03_arcadia_nir"
        }),
        "description": "Controlled nighttime thermal infrared mosaic across Arcadia quadrangle, displaying surface temperature variations correlated with buried sheet ice and lobate debris aprons.",
        "scientific_significance": "Key thermophysical constraint for shallow permafrost ice extraction and lander pad dust erosion modeling."
    }
]

def verify_raster_endpoints():
    print(f"\n[1/4] Verifying direct HTTP endpoints for {len(RASTERS)} remote sensing raster products...")
    verified = 0
    for r in RASTERS:
        url = r["direct_data_url"]
        try:
            resp = requests.head(url, timeout=12, headers={"User-Agent": "NASA-ETL-Bot/1.0"})
            if resp.status_code == 200:
                print(f"  ✓ [{resp.status_code}] {r['raster_id']:<35} -> {r['product_id']}")
                verified += 1
            elif resp.status_code == 403:
                # Some servers return 403 for HEAD, try range GET 0-100
                resp2 = requests.get(url, headers={"Range": "bytes=0-100", "User-Agent": "NASA-ETL-Bot/1.0"}, timeout=12)
                if resp2.status_code in (200, 206):
                    print(f"  ✓ [{resp2.status_code} Range] {r['raster_id']:<35} -> {r['product_id']}")
                    verified += 1
                else:
                    print(f"  ✗ [{resp2.status_code}] {r['raster_id']:<35} -> {url}")
            else:
                print(f"  ✗ [{resp.status_code}] {r['raster_id']:<35} -> {url}")
        except Exception as e:
            print(f"  ✗ [ERR] {r['raster_id']:<35} -> {e}")
    print(f"Endpoint verification complete: {verified}/{len(RASTERS)} directly reachable.\n")

def populate_database():
    print(f"[2/4] Integrating rasters into SQLite master database '{DB_PATH}'...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS remote_sensing_rasters (
        raster_id TEXT PRIMARY KEY,
        target_body TEXT NOT NULL,
        scientific_category TEXT NOT NULL,
        sub_category TEXT NOT NULL,
        target_feature TEXT NOT NULL,
        mission TEXT NOT NULL,
        instrument TEXT NOT NULL,
        archive_agency TEXT NOT NULL,
        product_id TEXT NOT NULL,
        product_title TEXT NOT NULL,
        data_format TEXT NOT NULL,
        min_lat REAL NOT NULL,
        max_lat REAL NOT NULL,
        min_lon REAL NOT NULL,
        max_lon REAL NOT NULL,
        spatial_resolution_m REAL,
        map_scale_desc TEXT,
        projection TEXT NOT NULL,
        direct_data_url TEXT NOT NULL,
        direct_label_url TEXT,
        ancillary_urls_json TEXT,
        description TEXT NOT NULL,
        scientific_significance TEXT NOT NULL,
        FOREIGN KEY (target_body) REFERENCES celestial_bodies(body_id)
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_rs_body ON remote_sensing_rasters(target_body);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rs_category ON remote_sensing_rasters(scientific_category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rs_format ON remote_sensing_rasters(data_format);")

    # Clear old entries in this table
    cur.execute("DELETE FROM remote_sensing_rasters;")
    
    # Insert new entries
    for r in RASTERS:
        cur.execute("""
        INSERT INTO remote_sensing_rasters (
            raster_id, target_body, scientific_category, sub_category, target_feature,
            mission, instrument, archive_agency, product_id, product_title,
            data_format, min_lat, max_lat, min_lon, max_lon,
            spatial_resolution_m, map_scale_desc, projection,
            direct_data_url, direct_label_url, ancillary_urls_json,
            description, scientific_significance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            r["raster_id"], r["target_body"], r["scientific_category"], r["sub_category"], r["target_feature"],
            r["mission"], r["instrument"], r["archive_agency"], r["product_id"], r["product_title"],
            r["data_format"], r["min_lat"], r["max_lat"], r["min_lon"], r["max_lon"],
            r["spatial_resolution_m"], r["map_scale_desc"], r["projection"],
            r["direct_data_url"], r["direct_label_url"], r["ancillary_urls_json"],
            r["description"], r["scientific_significance"]
        ))

    # Also update FTS5 search index
    cur.execute("DELETE FROM fts_planetary_search WHERE entity_type = 'REMOTE_SENSING_RASTER';")
    cur.execute("""
    INSERT INTO fts_planetary_search (entity_type, entity_id, body, title, category, content)
    SELECT 'REMOTE_SENSING_RASTER', raster_id, target_body, product_title, scientific_category,
           product_title || ' ' || target_feature || ' Mission: ' || mission || ' Instrument: ' || instrument ||
           ' Agency: ' || archive_agency || ' Format: ' || data_format || ' Res: ' || spatial_resolution_m || 'm. ' ||
           description || ' ' || scientific_significance
    FROM remote_sensing_rasters;
    """)

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM remote_sensing_rasters;")
    count = cur.fetchone()[0]
    conn.close()
    print(f"Successfully populated 'remote_sensing_rasters' table with {count} records and updated FTS5 index.\n")

def export_multiformat():
    print("[3/4] Exporting raster catalog to CSV, JSON, and Parquet...")
    os.makedirs("data/processed/csv", exist_ok=True)
    os.makedirs("data/processed/json", exist_ok=True)
    os.makedirs("data/processed/parquet", exist_ok=True)

    csv_path = "data/processed/csv/remote_sensing_rasters.csv"
    json_path = "data/processed/json/remote_sensing_rasters.json"
    parquet_path = "data/processed/parquet/remote_sensing_rasters.parquet"

    # CSV
    keys = list(RASTERS[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(RASTERS)
    print(f"  • CSV:     {csv_path} ({os.path.getsize(csv_path):,} bytes)")

    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(RASTERS, f, indent=2, ensure_ascii=False)
    print(f"  • JSON:    {json_path} ({os.path.getsize(json_path):,} bytes)")

    # Parquet
    table = pa.Table.from_pylist(RASTERS)
    pq.write_table(table, parquet_path)
    print(f"  • Parquet: {parquet_path} ({os.path.getsize(parquet_path):,} bytes)\n")

def print_summary():
    print("[4/4] Remote Sensing Raster Catalog Overview:")
    print("=" * 80)
    for r in RASTERS:
        print(f"[{r['target_body']:<5}] [{r['scientific_category']:<30}] {r['product_title']}")
        print(f"        Res: {r['spatial_resolution_m']:>7.1f} m/pix | BBox: Lat [{r['min_lat']:>6.1f}°, {r['max_lat']:>6.1f}°], Lon [{r['min_lon']:>6.1f}°, {r['max_lon']:>6.1f}°]")
        print(f"        Format: {r['data_format']:<18} | Agency: {r['archive_agency']}")
        print(f"        Direct URL: {r['direct_data_url']}")
        if r['direct_label_url']:
            print(f"        Label URL:  {r['direct_label_url']}")
        print("-" * 80)

def main():
    verify_raster_endpoints()
    populate_database()
    export_multiformat()
    print_summary()

if __name__ == "__main__":
    main()
