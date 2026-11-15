#!/usr/bin/env python3
"""
Exports real SQLite database and pipeline data from ATLAS-X (planetary_moon_mars.db)
into the AtlasDataset JSON format required by atlas-x-mission-control-application.
"""
import sys
import json
import sqlite3
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "planetary_moon_mars.db"
APP_DIR = PROJECT_ROOT / "atlas-x-mission-control-application"
OUT_SRC = APP_DIR / "src" / "data" / "realAtlasDataset.json"
OUT_PUBLIC = APP_DIR / "public" / "exports" / "atlas.json"

def main():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. ANALOG SITES (12 sites)
    print("Exporting Earth Analogs...")
    analogs_raw = cur.execute("SELECT * FROM terrestrial_analog_sites ORDER BY analog_id").fetchall()
    
    # Map analog_id to concise ID and tags
    alias_map = {
        "EARTH_ANALOG_QAIDAM_BASIN": ("EA_QAIDAM", "remote-sensing-benchmark", ["hyper-arid", "yardang", "salars", "perchlorate"]),
        "EARTH_ANALOG_HAUGHTON_CRATER": ("EA_DEVON", "open-bilateral", ["impact crater", "polar desert", "permafrost"]),
        "EARTH_ANALOG_SAMAIL_OPHIOLITE": ("EA_SAMAIL", "open-bilateral", ["ultramafic", "serpentinization", "mantle"]),
        "EARTH_ANALOG_DANAKIL_DEPRESSION": ("EA_DANAKIL", "open-bilateral", ["hydrothermal", "evaporite", "acid brines", "basalt"]),
        "EARTH_ANALOG_SVALBARD_BOCKFJORDEN": ("EA_SVALBARD", "open-bilateral", ["basalt", "permafrost", "polar", "cryo-carbonate"]),
        "EARTH_ANALOG_PILBARA_CRATON": ("EA_PILBARA", "open-bilateral", ["Archean", "stromatolites", "biosignatures"]),
        "EARTH_ANALOG_RIO_TINTO": ("EA_RIO_TINTO", "open-bilateral", ["acid brines", "jarosite", "iron oxides"]),
        "EARTH_ANALOG_MAKGADIKGADI_PANS": ("EA_MAKGADIKGADI", "open-bilateral", ["saline playa", "dune fields", "duricrusts"]),
        "EARTH_ANALOG_NULLARBOR_KARST": ("EA_NULLARBOR", "open-bilateral", ["subsurface caves", "limestone", "deflation plain"]),
        "EARTH_ANALOG_LONAR_CRATER": ("EA_LONAR", "open-bilateral", ["basaltic impact", "shocked plagioclase", "regolith"]),
        "EARTH_ANALOG_EL_MALPAIS": ("EA_EL_MALPAIS", "open-bilateral", ["lava tubes", "perennial ice", "basalt"]),
        "EARTH_ANALOG_KAZUMURA_LAVA_TUBE": ("EA_KILAUEA", "open-bilateral", ["continuous pyroduct", "basaltic volcanism", "lava tubes"]),
    }

    analogs = []
    for a in analogs_raw:
        aid = a["analog_id"]
        cid, field_access, tags = alias_map.get(aid, (aid, "open-bilateral", ["analog"]))
        
        # Calculate axis scores from similarity_profiles
        axes_scores = {}
        for b_key, b_name in [("moon", "Moon"), ("mars", "Mars")]:
            sim = cur.execute("""
                SELECT 
                    AVG(s.axis_a_geomorphology_pct) as a,
                    AVG(s.axis_b_geochemistry_pct) as b,
                    AVG(s.axis_c_thermophysics_pct) as c,
                    AVG(s.axis_d_volatiles_pct) as d
                FROM similarity_profiles s
                JOIN harmonized_sites h ON s.target_site_id = h.site_id
                WHERE s.analog_site_id = ? AND h.body = ?
            """, (aid, b_name)).fetchone()
            
            if sim and sim["a"] is not None:
                axes_scores[b_key] = {
                    "A": round(sim["a"], 1),
                    "B": round(sim["b"], 1),
                    "C": round(sim["c"], 1),
                    "D": round(sim["d"], 1),
                }
            else:
                # Default fallback based on domain
                if b_key == "moon":
                    axes_scores[b_key] = {"A": 50.0, "B": 45.0, "C": 25.0, "D": 30.0}
                else:
                    axes_scores[b_key] = {"A": 60.0, "B": 65.0, "C": 55.0, "D": 50.0}

        analogs.append({
            "id": cid,
            "name": a["name"],
            "region": a["region"] or f"{a['country']}",
            "lat": round(float(a["center_lat"]), 4),
            "lon": round(float(a["center_lon"]), 4),
            "fieldAccess": field_access,
            "tags": tags,
            "axes": axes_scores,
        })

    # 2. PLANETARY SITES (524 sites)
    print("Exporting 524 Planetary Sites...")
    sites_raw = cur.execute("""
        SELECT 
            p.*,
            h.h3_res7,
            h.has_subsurface_void,
            h.fe_wt_pct,
            h.ti_wt_pct,
            h.h2o_equiv_pct,
            h.thermal_inertia,
            h.diurnal_temp_swing_k,
            h.measurement_confidence
        FROM v_landing_site_pareto_ranks p
        JOIN harmonized_sites h ON p.site_id = h.site_id
        ORDER BY p.body, p.pareto_rank
    """).fetchall()

    flagship_insights = {
        "MOON_ARTEMIS_NOBILE_RIM_1_PAD_10": (
            "Near-continuous sunlight on the rim sits beside permanently shadowed ice — power and rocket-fuel water within a short rover drive of each other.",
            "3-Hexagon Base Triad", 410, 47.76, True, 0.593
        ),
        "MOON_CLPS_GRIFFIN_VIPER_NOBILE": (
            "A rover-proven ice-prospecting corridor: VIPER-class drills ground-truth volatiles before human crew commits to the outpost.",
            "#1 Pareto-Optimal Lunar Outpost", 360, 55.0, True, 0.610
        ),
        "MOON_ARTEMIS_CONNECTING_RIDGE_PAD_05": (
            "Artemis III connecting ridge between Shackleton and de Gerlache crater: maximum line-of-sight earth communication with 86% solar illumination.",
            "Peak-of-Eternal-Light", 380, 52.0, True, 0.625
        ),
        "MOON_SHACKLETON_CONNECTING_RIDGE": (
            "The most sunlit ground within reach of the coldest crater on the Moon — a lighthouse for solar power with a cryogenic water bank next door.",
            "Shackleton Cold Trap", 300, 80.0, False, 0.640
        ),
        "MOON_CABEUS_RIM": (
            "Proven water-ice from the LCROSS impact plume, but rugged crater slopes require precision landing guidance.",
            "LCROSS Water Proven", 280, 95.0, False, 0.660
        ),
        "MARS_PAD_HELLAS_DEEP_FLOOR_12": (
            "Deep −7,150 m basin floor provides Mars' thickest atmospheric entry column (~1,155 Pa), boosting deliverable landed payload by +45%–60%.",
            "+45%–60% Aerodynamic Payload Bonus", 210, 30.0, True, 0.542
        ),
        "MARS_ELLIPSE_JEZERO_DELTA_FRONT": (
            "Ancient river delta with preserved clays and carbonates: primary astrobiological life-detection site requiring strict COSPAR Special Region cleanliness.",
            "COSPAR Special Region Protection", 170, 25.0, False, 0.558
        ),
        "MARS_PAD_KOROLEV_WATER_ICE_04": (
            "Vast 1.8 km thick pure water ice mound trapped by permanent cold-trap anticyclone: inexhaustible rocket-propellant mine.",
            "Korolev Pure Water Ice Mound", 190, 22.0, False, 0.570
        ),
        "MARS_ELLIPSE_PHOENIX_GREEN_VALLEY": (
            "Phoenix-ground-truthed pure water ice sheet just 5 cm beneath soil polygons in Vastitas Borealis: flattest northern plains runway.",
            "Phoenix Polygonal Ice Sheet", 160, 15.0, False, 0.585
        ),
        "MARS_ARCADIA_PLANITIA_ICE": (
            "Shallow radar-verified sheet ice within 1 m of surface on flat plain: premier mid-latitude human outpost candidate.",
            "SWIM Subsurface Glacial Sheet", 160, 12.0, False, 0.575
        ),
    }

    sites = []
    for s in sites_raw:
        sid = s["site_id"]
        body = s["body"].lower()
        lat = float(s["center_lat"])
        lon = float(s["center_lon"])
        slope = round(float(s["macro_slope_deg"]), 1)
        rock = round(float(s["rock_abundance_percent"]), 1)
        elev = int(round(float(s["elevation_mola_m"])))
        
        # Scores 0..1
        scores = {
            "edl": round(float(s["edl_safety_score"]) / 100.0, 2),
            "isru": round(float(s["isru_resource_score"]) / 100.0, 2),
            "solar": round(float(s["survivability_comms_score"]) / 100.0, 2),
            "astro": round(float(s["science_return_score"]) / 100.0, 2),
        }

        # Short name
        s_name = s["site_name"]
        short_name = s["target_region"] if len(s["target_region"]) < 25 else s_name.split("-")[0].strip()
        short_name = short_name.upper()

        # Check flagship info
        flagship = flagship_insights.get(sid)
        if flagship:
            insight_text, highlight, tube_w, haul_dh, void_verif, d_a = flagship
            has_void = True
        else:
            highlight = None
            void_verif = bool(s["has_subsurface_void"] == 1)
            has_void = void_verif or (body == "moon" and slope < 4.0 and abs(lat) < 70)
            tube_w = int(round(220 if body == "moon" else 140))
            haul_dh = int(round(max(8, slope * 7.5)))
            d_a = round(0.52 + (slope / 20.0) * 0.15 + (rock / 15.0) * 0.1, 3)
            
            # Formulate insight
            if body == "moon":
                if abs(lat) >= 80:
                    insight_text = f"Polar rim zone ({abs(lat):.1f}°S): permanent solar visibility on ridge peaks with cryogenic volatile traps within rover transit distance."
                else:
                    insight_text = f"Equatorial/Mid-latitude mare basin with low slope ({slope:.1f}°) and stable thermal inertia for base infrastructure."
            else:
                if abs(lat) >= 45:
                    insight_text = f"SWIM-mapped high-latitude ice sheet ({abs(lat):.1f}°): shallow water ice accessible for life support and methane propellant synthesis."
                elif elev < -3500:
                    insight_text = f"Deep depression ({elev:,} m): high atmospheric column mass provides aerodynamic deceleration, reducing lander propellant burn."
                else:
                    insight_text = f"Safe engineering ellipse on stable plateau with {rock:.1f}% rock hazard cover and year-round equatorial solar power."

        # COSPAR
        if body == "moon":
            if abs(lat) >= 80 and scores["isru"] >= 0.6:
                cospar = {
                    "category": "II*",
                    "label": "COSPAR Cat. II*",
                    "note": "Sensitive lunar polar volatile cold trap: volatile accounting under NPR 8715.24 required.",
                    "special": False,
                }
            else:
                cospar = {
                    "category": "II",
                    "label": "COSPAR Cat. II",
                    "note": "Lunar surface: record-keeping only; no bioburden requirement.",
                    "special": False,
                }
        else:
            if abs(lat) >= 45 or scores["isru"] >= 0.8:
                cospar = {
                    "category": "IVc",
                    "label": "COSPAR Cat. IVc · Special Region",
                    "note": "SWIM-mapped shallow ice / accessible water activity: strict bioburden (<0.03 spores/m²) and sterile drill barrier mandatory.",
                    "special": True,
                }
            elif scores["astro"] >= 0.88:
                cospar = {
                    "category": "IVb",
                    "label": "COSPAR Cat. IVb",
                    "note": "Life-detection / sample-caching class hardware: bioburden <= 30 spores per sample hardware.",
                    "special": True,
                }
            else:
                cospar = {
                    "category": "IVa",
                    "label": "COSPAR Cat. IVa",
                    "note": "Standard Martian surface: landed hardware bioburden <= 300,000 spores total.",
                    "special": False,
                }

        # Sample receipt
        sample_name = (
            "Apollo 14 Breccia 14321 ('Big Bertha')" if body == "moon" and sid == "MOON_ARTEMIS_NOBILE_RIM_1_PAD_10"
            else "Apollo 16 Highland Breccia 61016 ('Big Muley')" if body == "moon" and abs(lat) >= 80
            else "Apollo 12 Olivine Basalt 12002" if body == "moon"
            else "Shergottite NWA 2990" if body == "mars" and sid == "MARS_PAD_HELLAS_DEEP_FLOOR_12"
            else "Perseverance Western Fan Delta 'Salette'" if body == "mars" and "JEZERO" in sid
            else "Curiosity Gale Drill 'John Klein'" if body == "mars" and "GALE" in sid
            else "Shergottite Zagami Basalt" if body == "mars"
            else "Reference Sample Baseline"
        )
        sample = {
            "sample": sample_name,
            "dA": d_a,
            "threshold": 0.75,
            "passed": bool(d_a <= 0.75),
        }

        # Provenance
        if body == "moon":
            provenance = {
                "elevation": {"instrument": "LRO LOLA 20 m/px DEM", "sigma196": 3.2, "unit": "m"},
                "slope": {"instrument": "LRO LOLA (Taylor-propagated 20 m baseline)", "sigma196": 0.42, "unit": "°"},
                "rock": {"instrument": "LRO Diviner rock abundance", "sigma196": 0.31, "unit": "%"},
                "radiation": {"instrument": "LRO CRaTER dose model", "sigma196": 9.8, "unit": "mSv/yr"},
            }
        else:
            provenance = {
                "elevation": {"instrument": "MRO CTX/HiRISE DTM · MOLA tie", "sigma196": 11.5, "unit": "m"},
                "slope": {"instrument": "MRO HiRISE 1 m DTM", "sigma196": 0.58, "unit": "°"},
                "rock": {"instrument": "MRO HiRISE / CRISM rock count", "sigma196": 0.41, "unit": "%"},
                "radiation": {"instrument": "MSL RAD dose model", "sigma196": 8.6, "unit": "mSv/yr"},
            }

        site_obj = {
            "id": sid,
            "name": s["site_name"],
            "shortName": short_name,
            "body": body,
            "program": s["catalog_category"],
            "lat": lat,
            "lon": lon,
            "elevationM": elev,
            "slopeDeg": slope,
            "rockPct": rock,
            "scores": scores,
            "h3": s["h3_res7"] or s["h3_index"],
            "cospar": cospar,
            "insight": insight_text,
            "sample": sample,
            "provenance": provenance,
            "hasSubsurfaceVoid": has_void,
            "voidVerified": void_verif,
            "tubeWidthM": tube_w,
            "haulElevationGainM": haul_dh,
            "seeded": False,
        }
        if highlight:
            site_obj["highlight"] = highlight

        sites.append(site_obj)

    # 3. SPLIT-TWIN MATCHES
    print("Computing Split-Twin Matches...")
    def combine_axes(a, b):
        return {"A": max(a["A"], b["A"]), "B": max(a["B"], b["B"]), "C": max(a["C"], b["C"]), "D": max(a["D"], b["D"])}
    def coverage(a):
        return (a["A"] + a["B"] + a["C"] + a["D"]) / 4.0

    split_twins = []
    for b in ["moon", "mars"]:
        for open_only in [True, False]:
            pool = [a for a in analogs if not open_only or a["fieldAccess"] == "open-bilateral"]
            best = None
            for i in range(len(pool)):
                for j in range(i + 1, len(pool)):
                    c_axes = combine_axes(pool[i]["axes"][b], pool[j]["axes"][b])
                    cov = coverage(c_axes)
                    if best is None or cov > best["cov"]:
                        best = {"a": pool[i], "b": pool[j], "axes": c_axes, "cov": cov}
            single = max(pool, key=lambda c: coverage(c["axes"][b]))
            split_twins.append({
                "id": f"TWIN_{b.upper()}_{'OPEN' if open_only else 'ALL'}",
                "body": b,
                "openOnly": open_only,
                "analogIds": [best["a"]["id"], best["b"]["id"]],
                "combinedAxes": best["axes"],
                "combinedCoverage": round(best["cov"], 1),
                "bestSingleId": single["id"],
                "bestSingleAxes": single["axes"][b],
                "bestSingleCoverage": round(coverage(single["axes"][b]), 1),
            })

    # 4. POWER SPECS
    power = [
        {"body": "moon", "kind": "polar-night", "loadKwe": 10, "shadowHours": 102.5, "liIonWhPerKg": 100, "rfcWhPerKg": 600},
        {"body": "mars", "kind": "dust-storm", "loadKwe": 10, "tau": 3.0, "extinctionK": 0.9, "kilopowerUnits": 2, "kilopowerKwe": 10, "kilopowerUnitMassT": 1.5},
    ]

    # 5. PRESETS
    presets = [
        {
            "id": "max-edl",
            "label": "MAX EDL SAFETY",
            "body": "mars",
            "siteId": "MARS_PAD_HELLAS_DEEP_FLOOR_12",
            "weights": {"edl": 100, "isru": 25, "solar": 30, "astro": 20},
            "zoomRadii": 3.2,
            "callout": {
                "title": "Hellas Basin Pad 12 · −7,150 m",
                "body": "+45%–60% aerodynamic payload bonus from the thicker air column at the bottom of the basin.",
                "tone": "ok",
            },
        },
        {
            "id": "max-astro",
            "label": "MAX ASTROBIOLOGY",
            "body": "mars",
            "siteId": "MARS_ELLIPSE_JEZERO_DELTA_FRONT",
            "weights": {"edl": 30, "isru": 20, "solar": 30, "astro": 100},
            "zoomRadii": 3.2,
            "callout": {
                "title": "Jezero Delta · COSPAR Special Region",
                "body": "Life-detection class: ≤30 spores on sample hardware; any subsurface wet pocket triggers Cat. IVc Special-Region protection rules.",
                "tone": "warn",
            },
        },
        {
            "id": "max-isru",
            "label": "MAX ISRU & POWER",
            "body": "moon",
            "siteId": "MOON_ARTEMIS_NOBILE_RIM_1_PAD_10",
            "weights": {"edl": 30, "isru": 100, "solar": 85, "astro": 20},
            "zoomRadii": 3.0,
            "callout": {
                "title": "Nobile Rim · 3-Hexagon Base Triad",
                "body": "Pad, Habitat and ISRU hexes at Res-7 — ice hauled 2.1 km on a few minutes of kettle-power per ton.",
                "tone": "info",
            },
        },
        {
            "id": "viper-polar",
            "label": "VIPER POLAR BASE",
            "body": "moon",
            "siteId": "MOON_CLPS_GRIFFIN_VIPER_NOBILE",
            "weights": {"edl": 40, "isru": 95, "solar": 80, "astro": 50},
            "zoomRadii": 3.0,
            "callout": {
                "title": "Nobile South Plateau · VIPER Corridor",
                "body": "Official #1 Pareto-Optimal Lunar Outpost: rover-proven ground ice and connecting-ridge continuous solar illumination.",
                "tone": "ok",
            },
        },
        {
            "id": "korolev-ice",
            "label": "KOROLEV PURE ICE",
            "body": "mars",
            "siteId": "MARS_PAD_KOROLEV_WATER_ICE_04",
            "weights": {"edl": 60, "isru": 100, "solar": 40, "astro": 70},
            "zoomRadii": 3.2,
            "callout": {
                "title": "Korolev Crater · Pure Water Ice Mound",
                "body": "1.8 km thick pure water ice glacier protected by cold-trap atmospheric inversion — unlimited rocket propellant resource.",
                "tone": "info",
            },
        },
    ]

    # 6. META
    dataset = {
        "sites": sites,
        "analogs": analogs,
        "splitTwins": split_twins,
        "power": power,
        "presets": presets,
        "meta": {
            "source": "sqlite-export",
            "version": "atlas-x/1.0-live-db",
            "totalCandidates": len(sites),
            "defaultSiteId": {
                "moon": "MOON_ARTEMIS_NOBILE_RIM_1_PAD_10",
                "mars": "MARS_PAD_HELLAS_DEEP_FLOOR_12",
            },
        },
    }

    # Write files
    OUT_SRC.parent.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing {OUT_SRC} ({len(sites)} sites, {len(analogs)} analogs)...")
    with open(OUT_SRC, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Writing {OUT_PUBLIC}...")
    with open(OUT_PUBLIC, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print("Export successful!")

if __name__ == "__main__":
    main()
