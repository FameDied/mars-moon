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

# 7. Artemis Lunar South Pole Candidate Landing Sites Multi-Constraint Evaluation
print_section("ARTEMIS SOUTH POLE CANDIDATE SITES SAFETY EVALUATION")
cursor.execute("""
SELECT site_name, macro_slope_deg, elevation_mola_m, rock_abundance_percent,
       dte_visibility_fraction, ice_overburden_depth_m, plume_scour_risk_index
FROM site_engineering_safety
WHERE body = 'Moon' AND center_lat <= -80.0
ORDER BY dte_visibility_fraction DESC, macro_slope_deg ASC
LIMIT 6;
""")
for r in cursor.fetchall():
    ice = f"{r['ice_overburden_depth_m']:.2f} m" if r['ice_overburden_depth_m'] else "None"
    print(f"• {r['site_name']:<42} | Slope: {r['macro_slope_deg']:>4.1f}° | Rocks: {r['rock_abundance_percent']:>4.1f}% | DTE LoS: {r['dte_visibility_fraction']*100:>5.1f}% | Ice: {ice:<6} | Scour: {r['plume_scour_risk_index']:.2f}")

# 8. Mars EDL Atmospheric Deceleration Qualification (Elevation <= -1500m MOLA & Slope <= 5°)
print_section("MARS CANDIDATE SITES: ENTRY, DESCENT & LANDING (EDL) QUALIFICATION")
cursor.execute("""
SELECT site_name, elevation_mola_m, macro_slope_deg, rock_abundance_percent,
       CASE WHEN elevation_mola_m <= -1500.0 THEN 'QUALIFIED (EDL AIR PASS)' ELSE 'DISQUALIFIED (AIR TOO THIN)' END as edl_status,
       ice_overburden_depth_m
FROM site_engineering_safety
WHERE body = 'Mars' AND macro_slope_deg <= 5.0
ORDER BY elevation_mola_m ASC
LIMIT 6;
""")
for r in cursor.fetchall():
    ice = f"{r['ice_overburden_depth_m']:.2f} m" if r['ice_overburden_depth_m'] else "Deep/None"
    print(f"• {r['site_name']:<42} | MOLA: {r['elevation_mola_m']:>+6.0f} m | [{r['edl_status']}] | Slope: {r['macro_slope_deg']:.1f}° | Ice: {ice}")

# 9. Lander Engineering Envelope Constraints
print_section("LANDER ENGINEERING ENVELOPES (FOOTPRINT, SLOPE, ROCK CLEARANCE)")
cursor.execute("""
SELECT target_body, lander_name, footprint_span_m, touchdown_mass_kg, max_tolerable_slope_deg,
       max_tolerable_rock_height_m, edl_architecture
FROM lander_engineering_constraints
WHERE lander_id IN ('STARSHIP_HLS', 'NOVA_C', 'BLUE_MOON_MK1', 'PERSEVERANCE_SKYCRANE', 'INSIGHT_LANDER')
ORDER BY target_body, touchdown_mass_kg DESC;
""")
for r in cursor.fetchall():
    print(f"[{r['target_body']:<4}] {r['lander_name']:<35} | Span: {r['footprint_span_m']:>4.1f}m | Mass: {r['touchdown_mass_kg']:>7,.0f}kg | Slope Limit: <= {r['max_tolerable_slope_deg']:>4.1f}° | Rock Clear: {r['max_tolerable_rock_height_m']:.2f}m")

# 10. Regolith Geotechnics & Plume Scour Risk
print_section("REGOLITH GEOTECHNICS & PLUME-SURFACE INTERACTION (PSI)")
cursor.execute("""
SELECT body, terrain_name, cohesion_kpa, internal_friction_angle_deg, bearing_capacity_kpa,
       fine_component_thermal_inertia_si, plume_scour_risk_index
FROM regolith_geotechnics_psi
ORDER BY plume_scour_risk_index DESC
LIMIT 5;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['terrain_name'][:38]:<38} | Cohesion: {r['cohesion_kpa']:>4.2f} kPa | φ: {r['internal_friction_angle_deg']:>4.1f}° | Bearing: {r['bearing_capacity_kpa']:>5.1f} kPa | Scour Index: {r['plume_scour_risk_index']:.2f}")



# =============================================================================
# 9 ADVANCED PLANETARY ENGINEERING & SCIENCE DOMAIN QUERY DEMONSTRATIONS
# =============================================================================

# 11. Domain 1: GNC Optical Navigation (TRN Texture Entropy & Gravity Anomalies)
print_section("DOMAIN 1: GNC TRN OPTICAL ENTROPY & GRAVITY ANOMALIES (GRAIL/MRO)")
cursor.execute("""
SELECT body, site_name, trn_visual_entropy_score, solar_incidence_glare_risk,
       free_air_gravity_anomaly_mgal, local_vertical_deflection_arcsec
FROM site_engineering_safety
WHERE trn_visual_entropy_score >= 0.70
ORDER BY trn_visual_entropy_score DESC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['site_name']:<42} | TRN Entropy: {r['trn_visual_entropy_score']:.2f} | Deflection: {r['local_vertical_deflection_arcsec']:>5.1f}\" | Free-Air: {r['free_air_gravity_anomaly_mgal']:>+6.1f} mGal | Glare: {r['solar_incidence_glare_risk'][:30]}")

# 12. Domain 2: Active Tectonics & Seismic Hazard (Lobate Scarps & PGA Shaking)
print_section("DOMAIN 2: ACTIVE TECTONICS & SEISMIC HAZARD (LOBATE SCARPS <50 Ma)")
cursor.execute("""
SELECT body, site_name, nearest_fault_scarp_dist_km, peak_ground_acceleration_pga_g,
       landslide_runout_susceptibility
FROM site_engineering_safety
WHERE nearest_fault_scarp_dist_km <= 15.0
ORDER BY peak_ground_acceleration_pga_g DESC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['site_name']:<42} | Scarp Dist: {r['nearest_fault_scarp_dist_km']:>5.1f} km | PGA Hazard: {r['peak_ground_acceleration_pga_g']:>4.2f}g | Runout: {r['landslide_runout_susceptibility'][:32]}")

# 13. Domain 3: Power & Cryogenic Survival (Worst-Case Night Eclipse Duration)
print_section("DOMAIN 3: POWER & CRYOGENIC SURVIVAL (WORST-CASE ECLIPSE & TEMP)")
cursor.execute("""
SELECT body, site_name, max_continuous_night_hours, min_winter_bolometric_temp_k,
       diurnal_thermal_shock_k_per_hr
FROM site_engineering_safety
WHERE body = 'Moon' AND max_continuous_night_hours <= 120.0
ORDER BY max_continuous_night_hours ASC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['site_name']:<42} | Eclipse Shadow: {r['max_continuous_night_hours']:>5.1f} hrs | Min Temp: {r['min_winter_bolometric_temp_k']:>5.1f} K | Shock: {r['diurnal_thermal_shock_k_per_hr']:>4.1f} K/hr")

# 14. Domain 4: Electrostatic Dust Levitation & Crustal Mini-Magnetospheres
print_section("DOMAIN 4: ELECTROSTATIC DUST CHARGING & CRUSTAL B-FIELDS")
cursor.execute("""
SELECT body, site_name, crustal_magnetic_field_nt, terminator_surface_potential_v,
       electrostatic_dust_levitation_risk
FROM site_engineering_safety
WHERE crustal_magnetic_field_nt >= 20.0 OR terminator_surface_potential_v <= -1500.0
ORDER BY crustal_magnetic_field_nt DESC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['site_name']:<42} | Crustal B: {r['crustal_magnetic_field_nt']:>6.1f} nT | Surface V: {r['terminator_surface_potential_v']:>+6.0f} V | Dust Risk: {r['electrostatic_dust_levitation_risk'][:30]}")

# 15. Domain 5: Topographic Sky-View Factor (SVF) & Subsurface Lava Tube Proximity
print_section("DOMAIN 5: TOPOGRAPHIC RADIATION SHIELDING (SVF) & LAVA TUBES")
cursor.execute("""
SELECT body, site_name, sky_view_factor_steradians, gcr_dose_equivalent_msv_yr,
       albedo_neutron_flux, nearest_lava_tube_skylight_km
FROM site_engineering_safety
WHERE nearest_lava_tube_skylight_km <= 50.0 OR sky_view_factor_steradians <= 4.5
ORDER BY nearest_lava_tube_skylight_km ASC
LIMIT 6;
""")
for r in cursor.fetchall():
    svf_pct = (r['sky_view_factor_steradians'] / 6.283185) * 100.0
    print(f"[{r['body']:<4}] {r['site_name']:<42} | Lava Tube: {r['nearest_lava_tube_skylight_km']:>5.1f} km | SVF: {r['sky_view_factor_steradians']:>4.2f} sr ({svf_pct:>4.1f}%) | GCR: {r['gcr_dose_equivalent_msv_yr']:>5.1f} mSv/yr")

# 16. Domain 6: Mars Atmospheric Dynamics (MCD Wind Gusts & Dust Deposition)
print_section("DOMAIN 6: MARS BOUNDARY LAYER DYNAMICS (WIND SHEAR & DUST)")
cursor.execute("""
SELECT site_name, mcd_99pct_wind_gust_ms, vertical_wind_shear_s_inv,
       climatological_dust_optical_depth_tau, annual_dust_deposition_rate_microns_sol
FROM site_engineering_safety
WHERE body = 'Mars'
ORDER BY mcd_99pct_wind_gust_ms DESC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"• {r['site_name']:<44} | Gust: {r['mcd_99pct_wind_gust_ms']:>4.1f} m/s | Shear: {r['vertical_wind_shear_s_inv']:>5.3f} s^-1 | Tau: {r['climatological_dust_optical_depth_tau']:>4.2f} | Dust Dep: {r['annual_dust_deposition_rate_microns_sol']:>4.2f} µm/sol")

# 17. Domain 7: Legal, Heritage & Planetary Protection Keep-Out Zones
print_section("DOMAIN 7: COSPAR PLANETARY PROTECTION & HISTORIC HERITAGE BUFFERS")
cursor.execute("""
SELECT body, site_name, cospar_planetary_protection_cat, heritage_exclusion_buffer_km,
       plume_orbital_contamination_risk
FROM site_engineering_safety
WHERE heritage_exclusion_buffer_km > 0.0 OR cospar_planetary_protection_cat LIKE '%Special%'
ORDER BY heritage_exclusion_buffer_km DESC, cospar_planetary_protection_cat DESC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['site_name']:<42} | Buffer: {r['heritage_exclusion_buffer_km']:>4.1f} km | COSPAR: {r['cospar_planetary_protection_cat'][:28]:<28} | Plume: {r['plume_orbital_contamination_risk'][:25]}")

# 18. Domain 8: ISRU Feedstock & Chemical Toxicity (Ilmenite & Perchlorates)
print_section("DOMAIN 8: ISRU FEEDSTOCK (ILMENITE, HE-3) & PERCHLORATE TOXICITY")
cursor.execute("""
SELECT body, site_name, fe_o_wt_pct, ti_o2_ilmenite_wt_pct, helium3_ppb,
       perchlorate_toxicity_wt_pct, hydrated_mineral_bound_h2o_wt_pct
FROM site_engineering_safety
WHERE ti_o2_ilmenite_wt_pct >= 5.0 OR hydrated_mineral_bound_h2o_wt_pct >= 50.0
ORDER BY ti_o2_ilmenite_wt_pct DESC, hydrated_mineral_bound_h2o_wt_pct DESC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['site_name']:<42} | Ilmenite: {r['ti_o2_ilmenite_wt_pct']:>4.1f}% | He-3: {r['helium3_ppb']:>4.1f} ppb | Bound H2O: {r['hydrated_mineral_bound_h2o_wt_pct']:>4.1f}% | ClO4-: {r['perchlorate_toxicity_wt_pct']:>4.2f}%")

# 19. Domain 9: The Science-vs-Safety Paradox (Stand-off & Stratigraphic Diversity)
print_section("DOMAIN 9: SCIENCE-VS-SAFETY PARADOX (STAND-OFF & DIVERSITY)")
cursor.execute("""
SELECT body, site_name, distance_to_primary_science_km, rover_traverse_energy_wh_per_km,
       contact_stratigraphic_diversity_count, macro_slope_deg, rock_abundance_percent
FROM site_engineering_safety
WHERE contact_stratigraphic_diversity_count >= 3
ORDER BY contact_stratigraphic_diversity_count DESC, distance_to_primary_science_km ASC
LIMIT 6;
""")
for r in cursor.fetchall():
    print(f"[{r['body']:<4}] {r['site_name']:<42} | Diversity: {r['contact_stratigraphic_diversity_count']} epochs | Stand-off: {r['distance_to_primary_science_km']:>4.1f} km | Energy: {r['rover_traverse_energy_wh_per_km']:>5.1f} Wh/km | Slope: {r['macro_slope_deg']:>4.1f}°")

conn.close()
