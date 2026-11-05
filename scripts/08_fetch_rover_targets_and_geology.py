import json
import csv
import os
import pyarrow as pa
import pyarrow.parquet as pq

os.makedirs("data/processed/json", exist_ok=True)
os.makedirs("data/processed/csv", exist_ok=True)
os.makedirs("data/processed/parquet", exist_ok=True)

# 1. Mars In-Situ Rover Science Targets (Curiosity & Perseverance Drills & Caches)
rover_targets = [
    {
        "target_id": "MSL-TGT-001",
        "rover": "Curiosity (MSL)",
        "target_name": "John Klein",
        "sol": 182,
        "site_feature": "Yellowknife Bay (Gale Crater)",
        "formation_or_member": "Sheepbed Member / Yellowknife Bay formation",
        "rock_type": "Lacustrine Mudstone (Siltstone/Claystone)",
        "tools_used": "Percussion Drill, CheMin XRD, SAM GC-MS, APXS, ChemCam",
        "mineralogy": "Smectite clay minerals (~20 wt%), magnetite, anhydrite, bassanite, olivine, pyroxene",
        "organic_molecules": "Chlorobenzene, dichloroalkanes (released during SAM pyrolysis from Martian chlorate reaction)",
        "scientific_significance": "HISTORIC FIRST EVIDENCE OF A HABITABLE LAKE ENVIRONMENT ON MARS. Neutral pH, low salinity, and essential bio-elements (C, H, N, O, P, S).",
        "sample_cache_status": "Analyzed in onboard laboratories"
    },
    {
        "target_id": "MSL-TGT-002",
        "rover": "Curiosity (MSL)",
        "target_name": "Cumberland",
        "sol": 279,
        "site_feature": "Yellowknife Bay",
        "formation_or_member": "Sheepbed Member",
        "rock_type": "Lacustrine Mudstone",
        "tools_used": "Percussion Drill, CheMin, SAM",
        "mineralogy": "Smectite clays (saponite), plagioclase, augite, pigeonite, pyrrhotite, akaganeite",
        "organic_molecules": "Chlorobenzene, chloroform, dichloromethane",
        "scientific_significance": "FIRST RADIOMETRIC K-Ar DATING ON ANOTHER PLANET: 4.21 ± 0.35 billion years crystallization age; 78 ± 30 million years surface exposure age.",
        "sample_cache_status": "Analyzed in onboard laboratories"
    },
    {
        "target_id": "MSL-TGT-003",
        "rover": "Curiosity (MSL)",
        "target_name": "Windjana",
        "sol": 621,
        "site_feature": "The Kimberley",
        "formation_or_member": "Kimberley Formation",
        "rock_type": "Basaltic Sandstone / Siltstone",
        "tools_used": "Percussion Drill, CheMin, APXS",
        "mineralogy": "Potassium feldspar (orthoclase ~21%), augite, pigeonite, hematite, magnetite",
        "organic_molecules": "None detected",
        "scientific_significance": "Discovered high alkali feldspar concentrations indicating unusual potassic magmatic differentiation on early Mars.",
        "sample_cache_status": "Analyzed in onboard laboratories"
    },
    {
        "target_id": "MSL-TGT-004",
        "rover": "Curiosity (MSL)",
        "target_name": "Confidence Hills",
        "sol": 759,
        "site_feature": "Pahrump Hills (Mount Sharp Base)",
        "formation_or_member": "Murray Formation",
        "rock_type": "Laminated Mudstone",
        "tools_used": "Percussion Drill, CheMin, SAM",
        "mineralogy": "Clay minerals, jarosite, hematite, quartz/cristobalite, plagioclase",
        "organic_molecules": "Trace chlorinated hydrocarbons",
        "scientific_significance": "Proved the base of Mount Sharp consists of lacustrine mudstones deposited over tens of millions of years in a recurring lake.",
        "sample_cache_status": "Analyzed in onboard laboratories"
    },
    {
        "target_id": "MSL-TGT-005",
        "rover": "Curiosity (MSL)",
        "target_name": "Buckskin",
        "sol": 1060,
        "site_feature": "Marias Pass (Mount Sharp)",
        "formation_or_member": "Murray Formation",
        "rock_type": "High-Silica Mudstone",
        "tools_used": "Percussion Drill, CheMin, SAM, ChemCam",
        "mineralogy": "Tridymite (~14 wt%), cristobalite, amorphous silica, bassanite",
        "organic_molecules": "Trace organics",
        "scientific_significance": "UNEXPECTED DETECTION OF TRIDYMITE: proof of high-temperature silicic volcanism on Mars (rhyolitic/andesitic magma evolution).",
        "sample_cache_status": "Analyzed in onboard laboratories"
    },
    {
        "target_id": "MSL-TGT-006",
        "rover": "Curiosity (MSL)",
        "target_name": "Kilmarie",
        "sol": 2391,
        "site_feature": "Glen Torridon (Clay-Bearing Unit)",
        "formation_or_member": "Murray Formation (Glen Torridon)",
        "rock_type": "Clay-Rich Lacustrine Mudstone",
        "tools_used": "Percussion Drill, CheMin, SAM",
        "mineralogy": "Ferric saponite and montmorillonite clay minerals (>30 wt%), plagioclase, hematite",
        "organic_molecules": "Sulfur-bearing heterocyclic aromatics (thiophenes, alkylthiol chains)",
        "scientific_significance": "Highest clay concentration detected anywhere on Mars, confirming orbital CRISM detections from ground truth.",
        "sample_cache_status": "Analyzed in onboard laboratories"
    },
    {
        "target_id": "MSL-TGT-007",
        "rover": "Curiosity (MSL)",
        "target_name": "Mary Anning",
        "sol": 2921,
        "site_feature": "Glen Torridon",
        "formation_or_member": "Murray Formation",
        "rock_type": "Lacustrine Siltstone",
        "tools_used": "Percussion Drill, CheMin, SAM (Wet Chemistry TMAH / MTBSTFA derivatization)",
        "mineralogy": "Clays, bassanite, hematite",
        "organic_molecules": "Benzoic acid, ammonia, alkyl compounds preserved within clay-mineral matrices",
        "scientific_significance": "Successful wet chemistry extraction confirming complex indigenous Martian organic molecules preserved for 3.5 billion years.",
        "sample_cache_status": "Analyzed in onboard laboratories"
    },
    {
        "target_id": "M2020-TGT-001",
        "rover": "Perseverance (Mars 2020)",
        "target_name": "Montdenier",
        "sol": 190,
        "site_feature": "Séítah formation / Artuby ridge (Jezero Crater)",
        "formation_or_member": "Séítah formation",
        "rock_type": "Igneous Olivine-Rich Cumulate Basalt",
        "tools_used": "Rotary Percussive Coring Drill, PIXL, SHERLOC, SuperCam",
        "mineralogy": "Coarse olivine crystals (~65%), pyroxene, plagioclase, carbonate, sulfate veins",
        "organic_molecules": "Trace carbon-bearing phases associated with sulfate grains",
        "scientific_significance": "PRISTINE MARTIAN CORE CACHED. Coarse olivine cumulate from a thick magma body or lava lake, ideal for high-precision radiometric geochronology on Earth.",
        "sample_cache_status": "Sealed in Hermetic Sample Tube #266 (Cached in Rover Internal Belly)"
    },
    {
        "target_id": "M2020-TGT-002",
        "rover": "Perseverance (Mars 2020)",
        "target_name": "Salette",
        "sol": 262,
        "site_feature": "South Séítah (Bastide rock)",
        "formation_or_member": "Séítah formation",
        "rock_type": "Igneous Olivine Cumulate with Aqueous Alteration",
        "tools_used": "Rotary Percussive Coring Drill, PIXL, SHERLOC",
        "mineralogy": "Olivine, carbonates, perchlorate, phyllosilicates",
        "organic_molecules": "Aromatic carbon detections via SHERLOC deep-UV fluorescence",
        "scientific_significance": "Demonstrates multiple episodes of liquid water interaction altering primary volcanic minerals into carbonates and salts.",
        "sample_cache_status": "Sealed in Hermetic Sample Tube #267 (Cached in Rover Internal Belly)"
    },
    {
        "target_id": "M2020-TGT-003",
        "rover": "Perseverance (Mars 2020)",
        "target_name": "Swift Run",
        "sol": 490,
        "site_feature": "Jezero Western Fan Delta (Skinner Ridge)",
        "formation_or_member": "Shenandoah formation (Delta front)",
        "rock_type": "Fine-Grained Lacustrine Mudstone / Sandstone",
        "tools_used": "Rotary Percussive Drill, PIXL, SHERLOC, Mastcam-Z",
        "mineralogy": "Phyllosilicate clays, calcium sulfate, detrital quartz/feldspar",
        "organic_molecules": "ABUNDANT AROMATIC HYDROCARBONS detected by SHERLOC Raman spectrometry",
        "scientific_significance": "HIGHEST PRIORITY ASTROBIOLOGY SAMPLE: Deposited in quiet waters of delta front, offering optimal preservation environment for potential biosignatures.",
        "sample_cache_status": "Sealed in Hermetic Sample Tube #262 (Cached in Rover Internal Belly)"
    },
    {
        "target_id": "M2020-TGT-004",
        "rover": "Perseverance (Mars 2020)",
        "target_name": "Bearwallow",
        "sol": 535,
        "site_feature": "Wildcat Ridge (Jezero Delta Front)",
        "formation_or_member": "Shenandoah formation",
        "rock_type": "Organic-Rich Siltstone",
        "tools_used": "Rotary Percussive Drill, PIXL, SHERLOC",
        "mineralogy": "Sulfate salts (anhydrite/gypsum), iron oxides, clays",
        "organic_molecules": "SHERLOC detected strong spatial correlation between sulfate minerals and aromatic organic compounds",
        "scientific_significance": "Sulfates precipitate rapidly in drying saline waters, known on Earth to entomb and preserve ancient microorganisms and biomolecules.",
        "sample_cache_status": "Sealed in Hermetic Sample Tube #258 (Three Forks Depot Surface Cache - Deposited on Ground Sol 674)"
    },
    {
        "target_id": "M2020-TGT-005",
        "rover": "Perseverance (Mars 2020)",
        "target_name": "Cheyava Falls",
        "sol": 1220,
        "site_feature": "Bright Angel / Neretva Vallis ancient river canyon",
        "formation_or_member": "Bright Angel Formation",
        "rock_type": "Mudstone with Chemical Alteration Reaction Halos ('Leopard Spots')",
        "tools_used": "Abrasion Tool, PIXL, SHERLOC, SuperCam",
        "mineralogy": "Calcium sulfate veins, iron phosphate (vivianite-like), vivianite/hematite alteration rings",
        "organic_molecules": "Significant carbonaceous signatures across alteration zones",
        "scientific_significance": "POTENTIAL BIOSIGNATURE CANDIDATE: White sulfate halos with black iron-phosphate rims ('leopard spots') resemble terrestrial microbial redox reduction of ferric iron.",
        "sample_cache_status": "Sealed in Hermetic Core Sample Tube (Rover Internal Belly for Earth Return)"
    }
]

# 2. Planetary Stratigraphy & Geological Eras
stratigraphy = [
    # Moon
    {
        "body": "Moon",
        "era_name": "Pre-Nectarian Era",
        "start_ga": 4.53,
        "end_ga": 3.92,
        "duration_ma": 610.0,
        "defining_events": "Giant impact origin of the Earth-Moon system (Theia collision); Lunar Magma Ocean (LMO); flotation of anorthosite crust; formation of 30+ giant impact basins including South Pole-Aitken (SPA, 2,500 km diameter).",
        "key_formations_and_rocks": "Ferroan Anorthosite (FAN), primordial crustal suites (Mg-suite troctolites/norites), South Pole-Aitken Basin floor ejecta.",
        "seismic_and_thermal_state": "High internal radiogenic heat flow, partial core dynamo active, extreme bombardment rate."
    },
    {
        "body": "Moon",
        "era_name": "Nectarian Period",
        "start_ga": 3.92,
        "end_ga": 3.85,
        "duration_ma": 70.0,
        "defining_events": "Formation of the Nectaris impact basin (type locality); formation of Serenitatis, Crisium, Humorum, and Humboldtianum multi-ring basins.",
        "key_formations_and_rocks": "Janssen Formation (Nectaris ejecta), Apollo 16 Descartes breccias, impact melt sheets.",
        "seismic_and_thermal_state": "Initial cryptomaria basalt flows; mantle melting triggered by depressurization under giant basins."
    },
    {
        "body": "Moon",
        "era_name": "Early Imbrian Epoch",
        "start_ga": 3.85,
        "end_ga": 3.80,
        "duration_ma": 50.0,
        "defining_events": "Cataclysmic Imbrium basin impact (1,160 km diameter); widespread blanketing of the lunar nearside; formation of Orientale multi-ring basin (youngest giant basin).",
        "key_formations_and_rocks": "Fra Mauro Formation (Apollo 14 sampled Imbrium ejecta), Hevelius Formation (Orientale ejecta), Montes Apenninus uplift.",
        "seismic_and_thermal_state": "Peak of Late Heavy Bombardment (LHB); deep crustal fractures provided conduits for mantle magma ascent."
    },
    {
        "body": "Moon",
        "era_name": "Late Imbrian Epoch",
        "start_ga": 3.80,
        "end_ga": 3.20,
        "duration_ma": 600.0,
        "defining_events": "Peak epoch of lunar mare volcanism. Massive flood basalt flows filling Imbrium, Tranquillitatis, Serenitatis, and Oceanus Procellarum basins.",
        "key_formations_and_rocks": "Mare basalts (high-Ti and low-Ti basalts, KREEP basalts - potassium, rare-earth elements, phosphorus), pyroclastic glass deposits.",
        "seismic_and_thermal_state": "Active lunar dynamo generating surface magnetic fields (up to 50 µT); thick lithosphere growth."
    },
    {
        "body": "Moon",
        "era_name": "Eratosthenian Period",
        "start_ga": 3.20,
        "end_ga": 1.10,
        "duration_ma": 2100.0,
        "defining_events": "Gradual cessation of mare flood volcanism (young basalts in Procellarum dated to ~2.0 Ga by Chang'e 5); crater degradation; ray systems darkened by space weathering.",
        "key_formations_and_rocks": "Eratosthenes crater (type specimen), Mons Rümker volcanic domes, Chang'e 5 basalts, Marius Hills cinder cones.",
        "seismic_and_thermal_state": "Core dynamo shutdown; global thermal contraction and lithospheric thickening to >800 km."
    },
    {
        "body": "Moon",
        "era_name": "Copernican Period",
        "start_ga": 1.10,
        "end_ga": 0.00,
        "duration_ma": 1100.0,
        "defining_events": "Youngest lunar period characterized by impact craters possessing bright, prominent, optically immature ray systems visible across the disk.",
        "key_formations_and_rocks": "Copernicus crater (~800 Ma), Tycho crater (~108 Ma), Aristarchus, Jackson, Giordano Bruno (~800-year-old candidate); fresh impact melt pools.",
        "seismic_and_thermal_state": "Tectonically quiescent; lobate scarp thrust faults indicate slow ongoing global contraction; micro-meteorite bombardment and solar wind space weathering."
    },

    # Mars
    {
        "body": "Mars",
        "era_name": "Pre-Noachian Era",
        "start_ga": 4.50,
        "end_ga": 4.10,
        "duration_ma": 400.0,
        "defining_events": "Core-mantle-crust differentiation; core dynamo generates strong magnetic field; formation of Crustal Dichotomy (Borealis Basin impact); giant impact basins (Hellas, Utopia, Argyre, Isidis).",
        "key_formations_and_rocks": "Ancient crustal orthopyroxenites (represented by Martian meteorite ALH84001, dated to ~4.09 Ga); magnetized southern highland crust.",
        "seismic_and_thermal_state": "Vigorous mantle convection; high geothermal gradient; primary outgassing of thick CO2-H2O proto-atmosphere."
    },
    {
        "body": "Mars",
        "era_name": "Noachian Period",
        "start_ga": 4.10,
        "end_ga": 3.70,
        "duration_ma": 400.0,
        "defining_events": "Warm and wet early climate; high atmospheric surface pressure (>1 bar); dendritic river valley networks; precipitation/rainfall or snowmelt; open-basin paleolakes (Jezero, Gale, Eberswalde); Tharsis volcanic rise begins.",
        "key_formations_and_rocks": "Widespread phyllosilicates (smectite clays, Fe/Mg-rich clays), layered crater floor deposits, heavily cratered southern highlands (Noachis Terra).",
        "seismic_and_thermal_state": "Core dynamo ceases (~3.9 Ga); solar wind stripping begins to accelerate atmospheric escape; neutral-to-alkaline groundwater chemistry."
    },
    {
        "body": "Mars",
        "era_name": "Hesperian Period",
        "start_ga": 3.70,
        "end_ga": 3.00,
        "duration_ma": 700.0,
        "defining_events": "Climatic transition to colder, hyper-arid conditions. Global sulfur volcanism; colossal episodic groundwater discharge carving massive Outflow Channels (Kasei Valles, Ares Vallis, Mangala Valles); Tharsis volcanism reaches apex.",
        "key_formations_and_rocks": "Extensive flood basalt plains (Hesperia Planum); hydrated sulfate minerals (jarosite, gypsum, kieserite); Valles Marineris canyon rifting initiated.",
        "seismic_and_thermal_state": "Atmospheric acidification; thin atmosphere; cold dry conditions interspersed with catastrophic sub-glacial or hydrothermal flooding."
    },
    {
        "body": "Mars",
        "era_name": "Amazonian Period",
        "start_ga": 3.00,
        "end_ga": 0.00,
        "duration_ma": 3000.0,
        "defining_events": "Hyper-arid, freezing global desert lasting 3 billion years. Dominance of eolian (wind) erosion, sand dune migration (undae), and dust transport; chaotic obliquity variations (15° to 45°) driving ice migration between poles and mid-latitudes.",
        "key_formations_and_rocks": "Olympus Mons and Tharsis volcano calderas; North and South Polar Layered Deposits (NPLD, SPLD); Medusae Fossae Formation; ferric oxide (nanophase hematite) dust imparting red color.",
        "seismic_and_thermal_state": "Thick lithosphere (>200 km); localized volcanism into geologically recent times (<50 Ma); ongoing low-level seismicity (Cerberus Fossae marsquakes detected by InSight)."
    }
]

# 3. Internal Structure & Geophysics
internal_structure = [
    # Moon
    {
        "body": "Moon",
        "layer_name": "Regolith & Megaregolith",
        "depth_min_km": 0.0,
        "depth_max_km": 2.0,
        "composition": "Fragmented rock powder, glass agglutinates, impact ejecta breccia",
        "density_g_cm3": 1.9,
        "physical_state": "Unconsolidated porous particulate",
        "seismic_p_velocity_kms": 0.3,
        "discovery_notes": "Apollo Active Seismic Experiments (ASE) and penetrometers"
    },
    {
        "body": "Moon",
        "layer_name": "Upper Anorthositic Crust",
        "depth_min_km": 2.0,
        "depth_max_km": 20.0,
        "composition": "Ferroan Anorthosite (>90% plagioclase feldspar), troctolite",
        "density_g_cm3": 2.75,
        "physical_state": "Fractured Solid Silicate",
        "seismic_p_velocity_kms": 5.1,
        "discovery_notes": "Apollo Passive Seismic & GRAIL dual-spacecraft gravity mapping (mean thickness ~34-43 km nearside)"
    },
    {
        "body": "Moon",
        "layer_name": "Lower Crust",
        "depth_min_km": 20.0,
        "depth_max_km": 43.0,
        "composition": "Noritic and gabbroic rocks, richer in pyroxene and iron",
        "density_g_cm3": 3.05,
        "physical_state": "Solid Crystalline Rock",
        "seismic_p_velocity_kms": 6.8,
        "discovery_notes": "GRAIL gravity models and Apollo seismic inversion"
    },
    {
        "body": "Moon",
        "layer_name": "Upper & Middle Mantle",
        "depth_min_km": 43.0,
        "depth_max_km": 1200.0,
        "composition": "Olivine, orthopyroxene, clinopyroxene, ilmenite-rich cumulates",
        "density_g_cm3": 3.35,
        "physical_state": "Rigid Solid Silicate Mantle",
        "seismic_p_velocity_kms": 8.0,
        "discovery_notes": "Deep Moonquake source zone (~700-1100 km depth) triggered by Earth tidal stresses (Apollo PSE)"
    },
    {
        "body": "Moon",
        "layer_name": "Partial Melt Boundary Zone",
        "depth_min_km": 1200.0,
        "depth_max_km": 1400.0,
        "composition": "Silicate mantle with 5-30% partial melt fraction, enriched in titanium/iron",
        "density_g_cm3": 3.40,
        "physical_state": "Viscoelastic / Partially Molten",
        "seismic_p_velocity_kms": 7.2,
        "discovery_notes": "Strong attenuation of seismic shear waves detected by Apollo seismic network reanalyses (Weber et al. 2011)"
    },
    {
        "body": "Moon",
        "layer_name": "Outer Liquid Core",
        "depth_min_km": 1400.0,
        "depth_max_km": 1500.0,
        "composition": "Molten iron-nickel alloy with ~5-6% sulfur",
        "density_g_cm3": 6.9,
        "physical_state": "Liquid Metallic Alloy",
        "seismic_p_velocity_kms": 4.1,
        "discovery_notes": "Radius ~330 km, discovered by Apollo seismic and Lunar Prospector/GRAIL laser ranging libration analyses"
    },
    {
        "body": "Moon",
        "layer_name": "Inner Solid Core",
        "depth_min_km": 1500.0,
        "depth_max_km": 1737.4,
        "composition": "Solid metallic crystalline iron (Fe-Ni)",
        "density_g_cm3": 7.8,
        "physical_state": "Solid Metallic Sphere",
        "seismic_p_velocity_kms": 4.3,
        "discovery_notes": "Radius ~240 km, confirmed by NASA GRAIL and French CNRS seismic array re-evaluations (Brossier et al. 2023)"
    },

    # Mars
    {
        "body": "Mars",
        "layer_name": "Sedimentary & Fractured Regolith",
        "depth_min_km": 0.0,
        "depth_max_km": 10.0,
        "composition": "Basaltic sands, clays, sulfates, heavily altered impact-brecciated rock",
        "density_g_cm3": 2.4,
        "physical_state": "Porous Fractured Rock (high porosity ~25%)",
        "seismic_p_velocity_kms": 2.8,
        "discovery_notes": "InSight SEIS P-to-S receiver functions (Knapmeyer-Endrun et al. 2021)"
    },
    {
        "body": "Mars",
        "layer_name": "Middle Crust",
        "depth_min_km": 10.0,
        "depth_max_km": 24.0,
        "composition": "Denser basaltic and andesitic crystalline igneous rock",
        "density_g_cm3": 2.85,
        "physical_state": "Solid Crystalline Silicate",
        "seismic_p_velocity_kms": 5.4,
        "discovery_notes": "InSight SEIS mid-crustal seismic interface"
    },
    {
        "body": "Mars",
        "layer_name": "Lower Crust",
        "depth_min_km": 24.0,
        "depth_max_km": 42.0,
        "composition": "Gabbroic, noritic, and felsic underplated lower crust",
        "density_g_cm3": 3.1,
        "physical_state": "Solid Ductile Silicate",
        "seismic_p_velocity_kms": 6.6,
        "discovery_notes": "Global crustal thickness varies from ~20 km beneath Isidis to >70 km beneath Tharsis bulge (mean ~39-48 km)"
    },
    {
        "body": "Mars",
        "layer_name": "Upper & Transition Mantle",
        "depth_min_km": 42.0,
        "depth_max_km": 1050.0,
        "composition": "Iron-rich olivine and pyroxenes (FeO ~18 wt% - twice as rich in iron as Earth's mantle)",
        "density_g_cm3": 3.55,
        "physical_state": "Solid Convecting Silicate Mantle",
        "seismic_p_velocity_kms": 7.9,
        "discovery_notes": "InSight SEIS deep mantle teleseismic phases"
    },
    {
        "body": "Mars",
        "layer_name": "Lower Mantle / Basal Thermal Layer",
        "depth_min_km": 1050.0,
        "depth_max_km": 1560.0,
        "composition": "Ringwoodite, majorite garnet, and silicate perovskite (bridgmanite absent or very thin)",
        "density_g_cm3": 4.1,
        "physical_state": "Viscoelastic Dense Silicate",
        "seismic_p_velocity_kms": 8.5,
        "discovery_notes": "Discovered molten silicate basal layer wrapping core boundary (Khan et al., Samuel et al. 2023)"
    },
    {
        "body": "Mars",
        "layer_name": "Liquid Metallic Core",
        "depth_min_km": 1560.0,
        "depth_max_km": 3389.5,
        "composition": "Liquid iron-nickel alloy enriched with ~18-21 wt% light elements (sulfur, oxygen, carbon, hydrogen)",
        "density_g_cm3": 6.1,
        "physical_state": "Liquid Metallic Core",
        "seismic_p_velocity_kms": 4.8,
        "discovery_notes": "Core radius determined by InSight core-reflected seismic waves (SKS, ScS) to be 1,780 to 1,830 km; completely molten with no solid inner core detected."
    }
]

# 4. Polar & Subsurface Ice Reservoirs
ice_reservoirs = [
    # Moon
    {
        "body": "Moon",
        "reservoir_name": "Cabeus Crater South Polar Cold Trap",
        "latitude_deg": -84.9,
        "longitude_deg": 324.5,
        "area_km2": 950.0,
        "ice_purity_pct": 5.6,
        "estimated_volume_km3": 0.05,
        "depth_m": 2.0,
        "temperature_k": 42.0,
        "detection_method": "LCROSS Kinetic Impact (2009) & LRO Diviner Thermal Infrared",
        "description": "LCROSS Centaur stage impact excavated ~155 kg of water vapor and water ice, plus volatiles: CO, methane, ammonia, and silver."
    },
    {
        "body": "Moon",
        "reservoir_name": "Shackleton Crater South Pole Cold Trap",
        "latitude_deg": -89.9,
        "longitude_deg": 0.0,
        "area_km2": 330.0,
        "ice_purity_pct": 3.5,
        "estimated_volume_km3": 0.08,
        "depth_m": 1.5,
        "temperature_k": 40.0,
        "detection_method": "LRO LOLA Albedo Anomalies, ShadowCam (Danuri), Clementine Bistatic Radar",
        "description": "Permanently shadowed crater interior at the South Pole with surface frost and subsurface deposits; rim receives near-continuous solar illumination."
    },
    {
        "body": "Moon",
        "reservoir_name": "Faustini & Shoemaker Craters",
        "latitude_deg": -87.7,
        "longitude_deg": 65.0,
        "area_km2": 1800.0,
        "ice_purity_pct": 4.0,
        "estimated_volume_km3": 0.12,
        "depth_m": 2.5,
        "temperature_k": 45.0,
        "detection_method": "LRO LAMP Lyman-Alpha Albedo & Lunar Prospector Neutron Spectrometry",
        "description": "Large cold-trap crater floors permanently shielded from direct sunlight for billions of years; primary exploration targets for NASA Artemis VIPER rover."
    },
    {
        "body": "Moon",
        "reservoir_name": "Hermite Crater North Polar Cold Trap",
        "latitude_deg": 86.0,
        "longitude_deg": 270.1,
        "area_km2": 820.0,
        "ice_purity_pct": 3.0,
        "estimated_volume_km3": 0.04,
        "depth_m": 1.0,
        "temperature_k": 26.0,
        "detection_method": "LRO Diviner Radiometer",
        "description": "COLDEST MEASURED SPOT IN THE SOLAR SYSTEM: 26 Kelvin (-247°C). Capable of cold-trapping not only H2O but even nitrogen, argon, and methane."
    },

    # Mars
    {
        "body": "Mars",
        "reservoir_name": "Planum Boreum (North Polar Layered Deposits - NPLD)",
        "latitude_deg": 85.0,
        "longitude_deg": 0.0,
        "area_km2": 1000000.0,
        "ice_purity_pct": 95.0,
        "estimated_volume_km3": 1600000.0,
        "depth_m": 3000.0,
        "temperature_k": 150.0,
        "detection_method": "MGS MOLA, MRO SHARAD Radar Sounding, Mars Express HRSC",
        "description": "Enormous water ice cap up to 3 km thick. Water ice purity ~95% mixed with 5% atmospheric dust; equivalent to ~30% of Greenland Ice Sheet. Cap is covered seasonally by 1 meter of dry ice (CO2)."
    },
    {
        "body": "Mars",
        "reservoir_name": "Planum Australe (South Polar Layered Deposits - SPLD)",
        "latitude_deg": -85.0,
        "longitude_deg": 0.0,
        "area_km2": 1500000.0,
        "ice_purity_pct": 85.0,
        "estimated_volume_km3": 1600000.0,
        "depth_m": 3700.0,
        "temperature_k": 140.0,
        "detection_method": "Mars Express MARSIS Subsurface Sounder & MRO SHARAD",
        "description": "Massive dome of water ice up to 3.7 km thick capped by permanent 8-meter slab of solid CO2 dry ice. MARSIS detected strong basal reflections interpreted as potential subglacial hypersaline brines."
    },
    {
        "body": "Mars",
        "reservoir_name": "Deuteronilus & Protonilus Mensae Subsurface Glaciers",
        "latitude_deg": 43.5,
        "longitude_deg": 33.0,
        "area_km2": 85000.0,
        "ice_purity_pct": 85.0,
        "estimated_volume_km3": 45000.0,
        "depth_m": 800.0,
        "temperature_k": 190.0,
        "detection_method": "MRO SHARAD Radar Sounding & HiRISE lobate morphology",
        "description": "Debris-covered glaciers (Lobate Debris Aprons). Vast sheets of 85% pure water ice preserved under 1-5 meters of protective rock debris at accessible mid-latitudes."
    },
    {
        "body": "Mars",
        "reservoir_name": "Utopia Planitia Subsurface Ice Sheet",
        "latitude_deg": 41.0,
        "longitude_deg": 82.0,
        "area_km2": 315000.0,
        "ice_purity_pct": 75.0,
        "estimated_volume_km3": 14300.0,
        "depth_m": 170.0,
        "temperature_k": 195.0,
        "detection_method": "MRO SHARAD Ground-Penetrating Radar (Stuurman et al. 2016)",
        "description": "Widespread underground water-ice deposit containing as much water as Lake Superior, shielded beneath 1 to 10 meters of regolith."
    },
    {
        "body": "Mars",
        "reservoir_name": "Medusae Fossae Formation (MFF) Deep Radar Deposits",
        "latitude_deg": -1.5,
        "longitude_deg": 195.0,
        "area_km2": 200000.0,
        "ice_purity_pct": 80.0,
        "estimated_volume_km3": 500000.0,
        "depth_m": 3700.0,
        "temperature_k": 210.0,
        "detection_method": "Mars Express MARSIS Re-evaluation (Watters et al. 2024)",
        "description": "Radar signals penetrate up to 3.7 km deep with dielectric properties matching compacted water ice mixed with dust; if pure ice, it would cover all of Mars in an ocean 1.5 to 2.7 meters deep."
    }
]

print(f"Compiled {len(rover_targets)} rover targets, {len(stratigraphy)} stratigraphy eras, {len(internal_structure)} internal layers, {len(ice_reservoirs)} ice reservoirs.")

# Save Rover Targets
with open("data/processed/json/rover_targets.json", "w", encoding="utf-8") as f:
    json.dump(rover_targets, f, indent=2)
with open("data/processed/csv/rover_targets.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rover_targets[0].keys()))
    writer.writeheader()
    writer.writerows(rover_targets)
pq.write_table(pa.Table.from_pylist(rover_targets), "data/processed/parquet/rover_targets.parquet")

# Save Stratigraphy
with open("data/processed/json/planetary_stratigraphy.json", "w", encoding="utf-8") as f:
    json.dump(stratigraphy, f, indent=2)
with open("data/processed/csv/planetary_stratigraphy.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(stratigraphy[0].keys()))
    writer.writeheader()
    writer.writerows(stratigraphy)
pq.write_table(pa.Table.from_pylist(stratigraphy), "data/processed/parquet/planetary_stratigraphy.parquet")

# Save Internal Structure
with open("data/processed/json/internal_structure.json", "w", encoding="utf-8") as f:
    json.dump(internal_structure, f, indent=2)
with open("data/processed/csv/internal_structure.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(internal_structure[0].keys()))
    writer.writeheader()
    writer.writerows(internal_structure)
pq.write_table(pa.Table.from_pylist(internal_structure), "data/processed/parquet/internal_structure.parquet")

# Save Ice Reservoirs
with open("data/processed/json/ice_reservoirs.json", "w", encoding="utf-8") as f:
    json.dump(ice_reservoirs, f, indent=2)
with open("data/processed/csv/ice_reservoirs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(ice_reservoirs[0].keys()))
    writer.writeheader()
    writer.writerows(ice_reservoirs)
pq.write_table(pa.Table.from_pylist(ice_reservoirs), "data/processed/parquet/ice_reservoirs.parquet")

print("All geology, stratigraphy, internal geophysics, and ice reservoirs successfully processed.")

