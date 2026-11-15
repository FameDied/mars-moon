/**
 * ATLAS-X — Data Adapter Contract
 * ---------------------------------------------------------------------------
 * THIS IS THE ONLY MODULE THAT KNOWS WHERE NUMBERS COME FROM.
 *
 * Every planetary record, analog score, physics constant and formula used by the
 * UI lives here behind strict TypeScript interfaces. The seeded generator below
 * is a *mock adapter*; to plug in the Python / SQLite / Parquet backend
 * (`planetary_moon_mars.db`) replace the body of `loadAtlasDataset()` with a
 * fetch of the JSON export (same `AtlasDataset` shape). No UI file imports
 * anything except from this module for scientific content.
 */
import { areNeighborCells, cellToBoundary, cellToLatLng, gridDisk, latLngToCell } from 'h3-js';
import realDataset from './realAtlasDataset.json';

/* ───────────────────────────── Types ───────────────────────────── */

export type BodyId = 'moon' | 'mars';
export type CelestialId = BodyId | 'earth';
export type AxisKey = 'A' | 'B' | 'C' | 'D';
export type ScoreKey = 'edl' | 'isru' | 'solar' | 'astro';

export interface AxisScores { A: number; B: number; C: number; D: number }
export type SiteScores = Record<ScoreKey, number>;

export interface MetricProvenance {
  instrument: string;
  /** half-width of the ±1.96σ Taylor-propagated interval, in `unit` */
  sigma196: number;
  unit: string;
}

export interface CosparInfo {
  category: string;
  label: string;
  note: string;
  special: boolean;
}

export interface SampleReceipt {
  sample: string;
  /** Aitchison distance between site geochemistry and returned-sample composition */
  dA: number;
  threshold: number;
  passed: boolean;
}

export interface PlanetarySite {
  id: string;
  name: string;
  shortName: string;
  body: BodyId;
  program: string;
  lat: number;
  lon: number;
  elevationM: number;
  slopeDeg: number;
  rockPct: number;
  scores: SiteScores;
  /** Uber H3 resolution-7 index of the site centre (pad hex) */
  h3: string;
  cospar: CosparInfo;
  insight: string;
  sample: SampleReceipt;
  provenance: Record<'elevation' | 'slope' | 'rock' | 'radiation', MetricProvenance>;
  hasSubsurfaceVoid: boolean;
  voidVerified: boolean;
  tubeWidthM: number;
  haulElevationGainM: number;
  /** Optional narrative highlight used by presets */
  highlight?: string;
  seeded: boolean;
}

export interface EarthAnalog {
  id: string;
  name: string;
  region: string;
  lat: number;
  lon: number;
  fieldAccess: 'open-bilateral' | 'remote-sensing-benchmark';
  tags: string[];
  /** per-target-body axis scores in % (A geomorphology, B geochemistry, C thermophysics, D volatiles/void) */
  axes: Record<BodyId, AxisScores>;
}

export interface SplitTwinMatch {
  id: string;
  body: BodyId;
  openOnly: boolean;
  analogIds: [string, string];
  combinedAxes: AxisScores;
  combinedCoverage: number;
  bestSingleId: string;
  bestSingleAxes: AxisScores;
  bestSingleCoverage: number;
}

export interface TriadCell {
  role: 'pad' | 'hab' | 'isru';
  h3: string;
  centerKm: [number, number];
  vertsKm: [number, number][];
}

export interface BaseTopologyTriad {
  siteId: string;
  resolution: 7;
  cells: TriadCell[];
  psiRadiusKm: number;
  haul: {
    distanceM: number;
    jPerKg: number;
    kWhPerTon: number;
    kettleMinutes: number;
    plainEnglish: string;
  };
}

export interface PowerSurvivalSpec {
  body: BodyId;
  kind: 'polar-night' | 'dust-storm';
  loadKwe: number;
  // polar night
  shadowHours?: number;
  liIonWhPerKg?: number;
  rfcWhPerKg?: number;
  // dust storm
  tau?: number;
  extinctionK?: number;
  kilopowerUnits?: number;
  kilopowerKwe?: number;
  kilopowerUnitMassT?: number;
}

export interface PowerResult {
  headline: string;
  rows: { label: string; value: string; tone?: 'ok' | 'bad' | 'warn' | 'info' }[];
  bars: { label: string; value: number; max: number; tone: 'ok' | 'bad' | 'warn' | 'info'; display: string }[];
}

export interface MissionPreset {
  id: string;
  label: string;
  body: BodyId;
  siteId: string;
  weights: Weights;
  /** camera distance as a multiple of body radius */
  zoomRadii: number;
  callout: { title: string; body: string; tone: 'ok' | 'info' | 'warn' };
}

export interface AtlasDataset {
  sites: PlanetarySite[];
  analogs: EarthAnalog[];
  splitTwins: SplitTwinMatch[];
  power: PowerSurvivalSpec[];
  presets: MissionPreset[];
  meta: { source: 'mock-seed' | 'sqlite-export'; version: string; totalCandidates: number; defaultSiteId: Record<BodyId, string> };
}

export interface Weights { edl: number; isru: number; solar: number; astro: number }
export interface Cutoffs { slope: number; rock: number; marsLat: number }
export interface SiteEval { u: number; go: boolean; reasons: string[] }

/* ───────────────────────── Physics & formulas ───────────────────────── */

export const PHYSICS = {
  G_EARTH: 9.80665,
  EARTH_RADIATION_MSV_YR: 2.82,
  LOX_BOIL_K: 90.2,
  TUBE_SHIELD_FRACTION: 0.9,
  CREW_SAFE_MSV_YR: 35,
  KETTLE_KW: 1.25,
  HAUL_DISTANCE_M: 2100,
  HAUL_EFFICIENCY: 0.7,
  /** H3 cells are normalised to the Earth-sphere definition (≈5.16 km² at Res-7) on every body. */
  H3_NORMALISING_RADIUS_KM: 6371.0088,
  bodies: {
    moon: { name: 'Moon', symbol: '☾', radiusKm: 1737.4, g: 1.62, ambientK: 304.0, radiationMsvYr: 207.2, rollingMu: 0.1, terrainSensor: 'LRO Diviner / LOLA' },
    mars: { name: 'Mars', symbol: '♂', radiusKm: 3389.5, g: 3.72076, ambientK: 215.9, radiationMsvYr: 184.5, rollingMu: 0.14, terrainSensor: 'MRO HiRISE / CRISM' },
  },
} as const;

export const craneOffloadPct = (b: BodyId) => (1 - PHYSICS.bodies[b].g / PHYSICS.G_EARTH) * 100;
export const cryoDeltaK = (b: BodyId) => PHYSICS.bodies[b].ambientK - PHYSICS.LOX_BOIL_K;
export const radiationMsvYr = (b: BodyId, inTube: boolean) =>
  PHYSICS.bodies[b].radiationMsvYr * (inTube ? 1 - PHYSICS.TUBE_SHIELD_FRACTION : 1);
export const radiationVsEarth = (msv: number) => msv / PHYSICS.EARTH_RADIATION_MSV_YR;
/** W_Earth_equiv = W_tube · g_body / g_Earth (roof-stress-equivalent terrestrial span) */
export const tubeWidthEarthEquiv = (site: PlanetarySite) =>
  (site.tubeWidthM * PHYSICS.bodies[site.body].g) / PHYSICS.G_EARTH;
/** E = g·(μ·d + Δh) / η   [J/kg] */
export function haulEnergyJPerKg(body: BodyId, dhM: number, distM = PHYSICS.HAUL_DISTANCE_M) {
  const g = PHYSICS.bodies[body].g;
  return (g * (PHYSICS.bodies[body].rollingMu * distM + dhM)) / PHYSICS.HAUL_EFFICIENCY;
}
export function haulSummary(body: BodyId, dhM: number) {
  const jPerKg = haulEnergyJPerKg(body, dhM);
  const kWhPerTon = (jPerKg * 1000) / 3.6e6;
  const kettleMinutes = (kWhPerTon / PHYSICS.KETTLE_KW) * 60;
  const plainEnglish = `${jPerKg.toFixed(1)} J/kg • ${kWhPerTon.toFixed(2)} kWh/ton — like boiling a kettle for ${Math.round(kettleMinutes)} mins`;
  return { distanceM: PHYSICS.HAUL_DISTANCE_M, jPerKg, kWhPerTon, kettleMinutes, plainEnglish };
}

export const coverage = (a: AxisScores) => (a.A + a.B + a.C + a.D) / 4;
export const combineAxes = (a: AxisScores, b: AxisScores): AxisScores => ({
  A: Math.max(a.A, b.A), B: Math.max(a.B, b.B), C: Math.max(a.C, b.C), D: Math.max(a.D, b.D),
});

export function findSplitTwin(analogs: EarthAnalog[], body: BodyId, openOnly: boolean): SplitTwinMatch {
  const pool = analogs.filter((a) => !openOnly || a.fieldAccess === 'open-bilateral');
  let best: { a: EarthAnalog; b: EarthAnalog; axes: AxisScores; cov: number } | null = null;
  for (let i = 0; i < pool.length; i++)
    for (let j = i + 1; j < pool.length; j++) {
      const axes = combineAxes(pool[i].axes[body], pool[j].axes[body]);
      const cov = coverage(axes);
      if (!best || cov > best.cov) best = { a: pool[i], b: pool[j], axes, cov };
    }
  const single = pool.reduce((p, c) => (coverage(c.axes[body]) > coverage(p.axes[body]) ? c : p));
  return {
    id: `TWIN_${body.toUpperCase()}_${openOnly ? 'OPEN' : 'ALL'}`,
    body, openOnly,
    analogIds: [best!.a.id, best!.b.id],
    combinedAxes: best!.axes,
    combinedCoverage: best!.cov,
    bestSingleId: single.id,
    bestSingleAxes: single.axes[body],
    bestSingleCoverage: coverage(single.axes[body]),
  };
}

export function evaluateSite(site: PlanetarySite, w: Weights, c: Cutoffs): SiteEval {
  const wsum = w.edl + w.isru + w.solar + w.astro;
  const s = site.scores;
  const u = wsum > 0 ? (w.edl * s.edl + w.isru * s.isru + w.solar * s.solar + w.astro * s.astro) / wsum : 0;
  const reasons: string[] = [];
  if (site.slopeDeg > c.slope) reasons.push(`Slope ${site.slopeDeg.toFixed(1)}° > ${c.slope.toFixed(1)}° lander limit`);
  if (site.rockPct > c.rock) reasons.push(`Rocks ${site.rockPct.toFixed(1)}% > ${c.rock.toFixed(1)}% hazard limit`);
  if (site.body === 'mars' && Math.abs(site.lat) > c.marsLat)
    reasons.push(`|Lat| ${Math.abs(site.lat).toFixed(1)}° > ${c.marsLat.toFixed(0)}° SWIM ice limit`);
  return { u, go: reasons.length === 0, reasons };
}

export function evaluateAll(sites: PlanetarySite[], w: Weights, c: Cutoffs) {
  const map = new Map<string, SiteEval>();
  for (const s of sites) map.set(s.id, evaluateSite(s, w, c));
  return map;
}

export function computePower(spec: PowerSurvivalSpec): PowerResult {
  if (spec.kind === 'polar-night') {
    const kwh = spec.loadKwe * (spec.shadowHours ?? 0);
    const liT = kwh / ((spec.liIonWhPerKg ?? 1) / 1000) / 1000;
    const rfcT = kwh / ((spec.rfcWhPerKg ?? 1) / 1000) / 1000;
    return {
      headline: `Save ${(liT - rfcT).toFixed(2)} t`,
      rows: [
        { label: 'Polar-night shadow', value: `${spec.shadowHours!.toFixed(1)} hr`, tone: 'info' },
        { label: 'Energy to bridge', value: `${kwh.toFixed(0)} kWh @ ${spec.loadKwe} kWe`, tone: 'info' },
        { label: 'Li-Ion mass', value: `${liT.toFixed(2)} t (${spec.liIonWhPerKg} Wh/kg)`, tone: 'bad' },
        { label: 'Regenerative Fuel Cell', value: `${rfcT.toFixed(2)} t (${spec.rfcWhPerKg} Wh/kg)`, tone: 'ok' },
      ],
      bars: [
        { label: 'Li-Ion', value: liT, max: liT, tone: 'bad', display: `${liT.toFixed(2)} t` },
        { label: 'RFC', value: rfcT, max: liT, tone: 'ok', display: `${rfcT.toFixed(2)} t` },
      ],
    };
  }
  const tau = spec.tau ?? 0;
  const trans = Math.exp(-(spec.extinctionK ?? 0.9) * tau);
  const loss = (1 - trans) * 100;
  const n = spec.kilopowerUnits ?? 2;
  const kwe = n * (spec.kilopowerKwe ?? 10);
  return {
    headline: `−${loss.toFixed(1)}% solar`,
    rows: [
      { label: 'Dust-storm opacity', value: `τ = ${tau.toFixed(1)}`, tone: 'warn' },
      { label: 'PV output remaining', value: `${(trans * 100).toFixed(1)}%`, tone: 'bad' },
      { label: 'Fission backup', value: `${n}× ${spec.kilopowerKwe} kWe Kilopower = ${kwe} kWe`, tone: 'ok' },
      { label: 'Backup mass', value: `${(n * (spec.kilopowerUnitMassT ?? 1.5)).toFixed(1)} t`, tone: 'info' },
    ],
    bars: [
      { label: 'Solar', value: trans * spec.loadKwe, max: spec.loadKwe, tone: 'bad', display: `${(trans * spec.loadKwe).toFixed(2)} kWe` },
      { label: 'Fission', value: kwe, max: Math.max(kwe, spec.loadKwe), tone: 'ok', display: `${kwe} kWe` },
    ],
  };
}

/* ───────────────────────── Earth analog seed records ───────────────────────── */

const ax = (A: number, B: number, C: number, D: number): AxisScores => ({ A, B, C, D });

const EARTH_ANALOGS: EarthAnalog[] = [
  { id: 'EA_SVALBARD', name: 'Svalbard', region: 'Bockfjorden volcanic complex, Norway', lat: 79.4, lon: 13.55, fieldAccess: 'open-bilateral', tags: ['basalt', 'permafrost', 'polar'], axes: { moon: ax(41, 38, 45, 33), mars: ax(66, 55, 58, 66) } },
  { id: 'EA_PILBARA', name: 'Pilbara', region: 'Dresser Formation, Western Australia', lat: -21.15, lon: 119.4, fieldAccess: 'open-bilateral', tags: ['Archean', 'biosignatures'], axes: { moon: ax(52, 31, 28, 12), mars: ax(62, 78, 30, 38) } },
  { id: 'EA_DANAKIL', name: 'Danakil Depression', region: 'Afar Triangle, Ethiopia', lat: 14.24, lon: 40.3, fieldAccess: 'open-bilateral', tags: ['hydrothermal', 'evaporite', 'basalt'], axes: { moon: ax(38, 41, 22, 15), mars: ax(80, 82, 41, 52) } },
  { id: 'EA_SAMAIL', name: 'Samail Ophiolite', region: 'Hajar Mountains, Oman', lat: 23.1, lon: 58.2, fieldAccess: 'open-bilateral', tags: ['ultramafic', 'serpentinization'], axes: { moon: ax(35, 58, 27, 10), mars: ax(48, 70, 35, 25) } },
  { id: 'EA_LONAR', name: 'Lonar Crater', region: 'Deccan Traps, India', lat: 19.98, lon: 76.51, fieldAccess: 'open-bilateral', tags: ['basaltic impact', 'regolith'], axes: { moon: ax(62, 66, 58, 12), mars: ax(70, 64, 28, 22) } },
  { id: 'EA_EL_MALPAIS', name: 'El Malpais', region: 'Zuni–Bandera field, New Mexico', lat: 34.95, lon: -108.0, fieldAccess: 'open-bilateral', tags: ['lava tubes', 'basalt'], axes: { moon: ax(30, 34, 36, 60), mars: ax(52, 50, 38, 60) } },
  { id: 'EA_QAIDAM', name: 'Qaidam Basin', region: 'Tibetan Plateau, China', lat: 37.3, lon: 94.4, fieldAccess: 'remote-sensing-benchmark', tags: ['hyper-arid', 'yardang', 'salars'], axes: { moon: ax(30, 35, 40, 28), mars: ax(45, 86.4, 80, 76) } },
  { id: 'EA_ATACAMA', name: 'Atacama · Yungay', region: 'Antofagasta, Chile', lat: -24.07, lon: -69.89, fieldAccess: 'open-bilateral', tags: ['hyper-arid', 'perchlorates'], axes: { moon: ax(33, 29, 36, 8), mars: ax(40, 52, 48, 30) } },
  { id: 'EA_RIO_TINTO', name: 'Río Tinto', region: 'Huelva, Spain', lat: 37.7, lon: -6.55, fieldAccess: 'open-bilateral', tags: ['acid brines', 'jarosite'], axes: { moon: ax(28, 33, 20, 9), mars: ax(58, 74, 36, 34) } },
  { id: 'EA_DEVON', name: 'Devon Island · Haughton', region: 'Nunavut, Canada', lat: 75.4, lon: -89.85, fieldAccess: 'open-bilateral', tags: ['impact crater', 'polar desert'], axes: { moon: ax(50, 36, 48, 30), mars: ax(55, 60, 74, 74) } },
  { id: 'EA_ASKJA', name: 'Askja', region: 'Highlands, Iceland', lat: 65.03, lon: -16.75, fieldAccess: 'open-bilateral', tags: ['basaltic', 'tephra'], axes: { moon: ax(55, 49, 33, 22), mars: ax(64, 58, 46, 40) } },
  { id: 'EA_KILAUEA', name: 'Kīlauea · Mauna Ulu', region: 'Hawaiʻi, USA', lat: 19.4, lon: -155.28, fieldAccess: 'open-bilateral', tags: ['basaltic', 'lava tubes'], axes: { moon: ax(44, 52, 29, 46), mars: ax(60, 56, 40, 45) } },
];

/* ───────────────────────── Seeded site generation (mock adapter) ───────────────────────── */

function mulberry32(a: number) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const clamp = (x: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
const unit = (lat: number, lon: number): [number, number, number] => {
  const la = (lat * Math.PI) / 180, lo = (lon * Math.PI) / 180;
  return [Math.cos(la) * Math.cos(lo), Math.sin(la), -Math.cos(la) * Math.sin(lo)];
};

const PROVENANCE = (body: BodyId): PlanetarySite['provenance'] =>
  body === 'moon'
    ? {
        elevation: { instrument: 'LRO LOLA 20 m/px DEM', sigma196: 3.2, unit: 'm' },
        slope: { instrument: 'LRO LOLA (Taylor-propagated 20 m baseline)', sigma196: 0.42, unit: '°' },
        rock: { instrument: 'LRO Diviner rock abundance', sigma196: 0.31, unit: '%' },
        radiation: { instrument: 'LRO CRaTER dose model', sigma196: 9.8, unit: 'mSv/yr' },
      }
    : {
        elevation: { instrument: 'MRO CTX/HiRISE DTM · MOLA tie', sigma196: 11.5, unit: 'm' },
        slope: { instrument: 'MRO HiRISE 1 m DTM', sigma196: 0.58, unit: '°' },
        rock: { instrument: 'MRO HiRISE / CRISM rock count', sigma196: 0.41, unit: '%' },
        radiation: { instrument: 'MSL RAD dose model', sigma196: 8.6, unit: 'mSv/yr' },
      };

type Named = Pick<PlanetarySite, 'id' | 'name' | 'shortName' | 'body' | 'program' | 'lat' | 'lon' | 'elevationM' | 'slopeDeg' | 'rockPct' | 'scores' | 'cospar' | 'insight'> &
  Partial<Pick<PlanetarySite, 'highlight' | 'tubeWidthM' | 'haulElevationGainM' | 'voidVerified'>> & { dA?: number };

const COSPAR_MOON: CosparInfo = { category: 'II', label: 'COSPAR Cat. II', note: 'Lunar surface: record-keeping only; no bioburden requirement. Polar ice deposits are flagged for contamination-sensitive science.', special: false };
const cosparMars = (cat: string, special: boolean, note: string): CosparInfo => ({ category: cat, label: `COSPAR Cat. ${cat}${special ? ' · Special Region' : ''}`, note, special });

const NAMED: Named[] = [
  {
    id: 'MOON_ARTEMIS_NOBILE_RIM_1_PAD_10', name: 'Artemis · Nobile Rim-1 · Pad 10', shortName: 'NOBILE RIM (CLPS / ARTEMIS)', body: 'moon', program: 'Artemis III candidate region',
    lat: -85.2, lon: 53.3, elevationM: 1620, slopeDeg: 2.8, rockPct: 0.9, scores: { edl: 0.78, isru: 0.93, solar: 0.88, astro: 0.52 }, cospar: COSPAR_MOON,
    insight: 'Near-continuous sunlight on the rim sits beside permanently shadowed ice — power and rocket-fuel water within a short rover drive of each other.',
    highlight: '3-Hexagon Base Triad', tubeWidthM: 410, haulElevationGainM: 47.76, voidVerified: true, dA: 0.593,
  },
  {
    id: 'MOON_CLPS_GRIFFIN_VIPER_NOBILE', name: 'CLPS Griffin / VIPER · Nobile Region', shortName: 'CLPS GRIFFIN / VIPER (NOBILE)', body: 'moon', program: 'CLPS CP-22 traverse',
    lat: -85.4, lon: 10.0, elevationM: 1205, slopeDeg: 3.6, rockPct: 1.4, scores: { edl: 0.66, isru: 0.9, solar: 0.74, astro: 0.6 }, cospar: COSPAR_MOON,
    insight: 'A rover-proven ice-prospecting corridor: VIPER-class drills can ground-truth the water before any crew commits to the site.', tubeWidthM: 360, haulElevationGainM: 55, voidVerified: false, dA: 0.61,
  },
  {
    id: 'MOON_SHACKLETON_CONNECTING_RIDGE', name: 'Shackleton Rim · Connecting Ridge', shortName: 'SHACKLETON RIM', body: 'moon', program: 'Artemis Base Camp study',
    lat: -89.54, lon: 129.2, elevationM: 2140, slopeDeg: 5.1, rockPct: 1.8, scores: { edl: 0.52, isru: 0.96, solar: 0.91, astro: 0.58 }, cospar: COSPAR_MOON,
    insight: 'The most sunlit ground within reach of the coldest crater on the Moon — a lighthouse for power with a water bank next door.', tubeWidthM: 300, haulElevationGainM: 80, voidVerified: false, dA: 0.64,
  },
  {
    id: 'MOON_CABEUS_RIM', name: 'Cabeus Rim', shortName: 'CABEUS RIM', body: 'moon', program: 'LCROSS impact vicinity',
    lat: -84.9, lon: -35.5, elevationM: 980, slopeDeg: 7.4, rockPct: 2.2, scores: { edl: 0.4, isru: 0.89, solar: 0.45, astro: 0.7 }, cospar: COSPAR_MOON,
    insight: 'Proven water-ice from the LCROSS impact, but the surrounding slopes are too steep for a safe touchdown.', tubeWidthM: 280, haulElevationGainM: 95, voidVerified: false, dA: 0.66,
  },
  {
    id: 'MARS_PAD_HELLAS_DEEP_FLOOR_12', name: 'Hellas Basin · Deep Floor Pad 12', shortName: 'HELLAS BASIN PAD 12', body: 'mars', program: 'Human-class EDL study',
    lat: -38.94, lon: 70.55, elevationM: -7150, slopeDeg: 1.8, rockPct: 0.9, scores: { edl: 0.97, isru: 0.46, solar: 0.62, astro: 0.55 }, cospar: cosparMars('IVa', false, 'Landed Mars hardware without life-detection: ≤3×10⁵ spores total, ≤300 spores/m² (Viking-derived).'),
    insight: 'Deep −7,150 m basin doubles air pressure for parachute braking, saving ~12 tons of landing fuel.',
    highlight: '+45%–60% aerodynamic payload bonus', tubeWidthM: 210, haulElevationGainM: 30, voidVerified: true, dA: 0.542,
  },
  {
    id: 'MARS_ELLIPSE_JEZERO_DELTA_FRONT', name: 'Jezero Crater · Delta Front Ellipse', shortName: 'JEZERO DELTA FRONT', body: 'mars', program: 'Mars 2020 / MSR heritage',
    lat: 18.38, lon: 77.58, elevationM: -2540, slopeDeg: 3.4, rockPct: 2.4, scores: { edl: 0.64, isru: 0.58, solar: 0.7, astro: 0.98 }, cospar: cosparMars('IVb', true, 'Life-detection / sample-caching class: ≤30 spores per sample hardware. Special-Region (Cat. IVc) rules apply to any subsurface wet pockets.'),
    insight: 'An ancient river delta that preserved clays and organics — the best place on Mars to ask if life ever existed, and the place we must keep cleanest.',
    highlight: 'COSPAR Special Region protection', tubeWidthM: 170, haulElevationGainM: 25, voidVerified: false, dA: 0.558,
  },
  {
    id: 'MARS_GALE_FLOOR', name: 'Gale Crater · Aeolis Palus', shortName: 'GALE CRATER FLOOR', body: 'mars', program: 'MSL Curiosity heritage', lat: -5.4, lon: 137.8, elevationM: -4400, slopeDeg: 3.9, rockPct: 2.1,
    scores: { edl: 0.8, isru: 0.4, solar: 0.9, astro: 0.82 }, cospar: cosparMars('IVa', false, 'Heritage landing; bioburden per Cat. IVa.'), insight: 'Proven by Curiosity: smooth floor, a 5 km layered mound of clays to sample, and strong equatorial sun.', tubeWidthM: 150, haulElevationGainM: 40, voidVerified: false,
  },
  {
    id: 'MARS_OXIA_PLANUM', name: 'Oxia Planum', shortName: 'OXIA PLANUM', body: 'mars', program: 'ExoMars Rosalind Franklin', lat: 18.2, lon: -24.6, elevationM: -3000, slopeDeg: 2.2, rockPct: 1.5,
    scores: { edl: 0.83, isru: 0.5, solar: 0.78, astro: 0.9 }, cospar: cosparMars('IVb', true, 'Life-detection class hardware.'), insight: 'Flat, clay-rich plain with a gentle landing ellipse — prized for biosignature drilling.', tubeWidthM: 140, haulElevationGainM: 20, voidVerified: false,
  },
  {
    id: 'MARS_MERIDIANI_PLANUM', name: 'Meridiani Planum', shortName: 'MERIDIANI PLANUM', body: 'mars', program: 'MER Opportunity heritage', lat: -2.0, lon: -5.0, elevationM: -1400, slopeDeg: 1.1, rockPct: 0.8,
    scores: { edl: 0.88, isru: 0.35, solar: 0.95, astro: 0.7 }, cospar: cosparMars('IVa', false, 'Heritage landing; bioburden per Cat. IVa.'), insight: 'One of the flattest places on Mars: a runway-smooth plain with year-round solar power.', tubeWidthM: 120, haulElevationGainM: 10, voidVerified: false,
  },
  {
    id: 'MARS_MAWRTH_VALLIS', name: 'Mawrth Vallis', shortName: 'MAWRTH VALLIS', body: 'mars', program: 'Candidate clay outcrop', lat: 24.0, lon: -19.0, elevationM: -2800, slopeDeg: 8.9, rockPct: 3.8,
    scores: { edl: 0.35, isru: 0.5, solar: 0.7, astro: 0.94 }, cospar: cosparMars('IVb', true, 'Life-detection class hardware.'), insight: 'Stunning clay stratigraphy, but jumbled channels and boulders make a safe landing unlikely.', tubeWidthM: 130, haulElevationGainM: 70, voidVerified: false,
  },
  {
    id: 'MARS_ARCADIA_PLANITIA_ICE', name: 'Arcadia Planitia · Ice Plain', shortName: 'ARCADIA PLANITIA (ICE)', body: 'mars', program: 'SWIM subsurface-ice region', lat: 47.1, lon: -175.4, elevationM: -4100, slopeDeg: 2.1, rockPct: 1.3,
    scores: { edl: 0.74, isru: 0.95, solar: 0.34, astro: 0.62 }, cospar: cosparMars('IVc', true, 'SWIM-mapped shallow ice: Special-Region screening mandatory.'), insight: 'Water ice lies within a metre of the surface on a flat plain — a mine waiting for a base, if you accept weaker sunlight.', tubeWidthM: 160, haulElevationGainM: 12, voidVerified: false,
  },
  {
    id: 'MARS_UTOPIA_PLANITIA_ICE', name: 'Utopia Planitia · Ice Plain', shortName: 'UTOPIA PLANITIA (ICE)', body: 'mars', program: 'SWIM subsurface-ice region', lat: 49.2, lon: 118.0, elevationM: -4300, slopeDeg: 1.6, rockPct: 1.1,
    scores: { edl: 0.76, isru: 0.97, solar: 0.3, astro: 0.58 }, cospar: cosparMars('IVc', true, 'SWIM-mapped shallow ice: Special-Region screening mandatory.'), insight: 'Vast, flat, buried glacier ice at mid-latitude: the richest water prize reachable by a crewed lander.', tubeWidthM: 150, haulElevationGainM: 8, voidVerified: false,
  },
  {
    id: 'MARS_ERIDANIA_BASIN', name: 'Eridania Basin', shortName: 'ERIDANIA BASIN', body: 'mars', program: 'Ancient sea candidate', lat: -32.0, lon: -178.0, elevationM: -1200, slopeDeg: 4.0, rockPct: 4.1,
    scores: { edl: 0.5, isru: 0.55, solar: 0.7, astro: 0.86 }, cospar: cosparMars('IVb', true, 'Life-detection class hardware.'), insight: 'Deep-sea hydrothermal deposits make it scientifically rich, but boulder fields rule it out for now.', tubeWidthM: 180, haulElevationGainM: 45, voidVerified: false,
  },
];

const TOTAL_PER_BODY = 262;
const PASS_PER_BODY = 71;

function buildSeedSites(): PlanetarySite[] {
  const rand = mulberry32(20250607);
  const out: PlanetarySite[] = [];
  const mk = (n: Named, seeded: boolean, extra?: Partial<PlanetarySite>): PlanetarySite => ({
    id: n.id, name: n.name, shortName: n.shortName, body: n.body, program: n.program, lat: n.lat, lon: n.lon,
    elevationM: n.elevationM, slopeDeg: n.slopeDeg, rockPct: n.rockPct, scores: n.scores,
    h3: latLngToCell(n.lat, n.lon, 7), cospar: n.cospar, insight: n.insight,
    sample: sampleFor(n.body, n.dA ?? (n.body === 'moon' ? 0.593 : 0.542), seeded),
    provenance: PROVENANCE(n.body), hasSubsurfaceVoid: true, voidVerified: n.voidVerified ?? false,
    tubeWidthM: n.tubeWidthM ?? 200, haulElevationGainM: n.haulElevationGainM ?? 40, highlight: n.highlight, seeded, ...extra,
  });
  const sampleFor = (body: BodyId, dA: number, _seeded: boolean): SampleReceipt => ({
    sample: body === 'moon' ? "Apollo 14 Breccia 14321 ('Big Bertha')" : 'Shergottite NWA 2990',
    dA, threshold: 0.75, passed: dA <= 0.75,
  });

  for (const body of ['moon', 'mars'] as BodyId[]) {
    const named = NAMED.filter((n) => n.body === body);
    const pos: { lat: number; lon: number; v: [number, number, number]; named?: Named }[] = named.map((n) => ({ lat: n.lat, lon: n.lon, v: unit(n.lat, n.lon), named: n }));
    const generated: typeof pos = [];
    const sampler = (capBias: boolean) => {
      if (body === 'moon' && capBias) {
        const z = -1 + rand() * (1 - Math.sin((68 * Math.PI) / 180)) ; // sin(lat) in [-1,-sin68]
        return { lat: (Math.asin(z) * 180) / Math.PI, lon: rand() * 360 - 180 };
      }
      const lim = Math.sin(((body === 'moon' ? 78 : 72) * Math.PI) / 180);
      return { lat: (Math.asin((rand() * 2 - 1) * lim) * 180) / Math.PI, lon: rand() * 360 - 180 };
    };
    let minSep = 3.95, fails = 0;
    const need = TOTAL_PER_BODY - named.length;
    const capNeed = body === 'moon' ? 58 : 0;
    while (generated.length < need) {
      const cap = generated.length < capNeed;
      const p = sampler(cap);
      const v = unit(p.lat, p.lon);
      const ok = [...pos, ...generated].every((q) => (Math.acos(clamp(q.v[0] * v[0] + q.v[1] * v[1] + q.v[2] * v[2], -1, 1)) * 180) / Math.PI > minSep);
      if (ok) generated.push({ ...p, v });
      else if (++fails % 500 === 0) minSep = Math.max(3.7, minSep * 0.98);
    }

    // Choose which generated candidates qualify at the default cut-offs
    const namedPass = named.filter((n) => n.slopeDeg <= 6 && n.rockPct <= 3 && (body === 'moon' || Math.abs(n.lat) <= 45)).length;
    const eligible = generated.map((_, i) => i).filter((i) => body === 'moon' || Math.abs(generated[i].lat) < 44);
    for (let i = eligible.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [eligible[i], eligible[j]] = [eligible[j], eligible[i]]; }
    const passSet = new Set(eligible.slice(0, PASS_PER_BODY - namedPass));

    generated.forEach((p, i) => {
      const absLat = Math.abs(p.lat);
      const pass = passSet.has(i);
      let slope: number, rock: number;
      const good = () => { slope = 0.6 + rand() * 5.2; rock = 0.2 + rand() * 2.5; };
      const bad = () => {
        const r = rand();
        slope = r < 0.55 ? 6.3 + rand() * 6.5 : 0.8 + rand() * 5;
        rock = r < 0.55 ? 0.3 + rand() * 5 : 3.3 + rand() * 4.2;
        if (r >= 0.55 && rand() < 0.3) slope = 6.3 + rand() * 6;
      };
      slope = 0; rock = 0;
      if (pass) good();
      else if (body === 'mars' && absLat > 45) { if (rand() < 0.62) good(); else bad(); }
      else bad();
      const elev = body === 'mars' ? -4800 + rand() * 8300 : -2500 + rand() * 6300;
      const prox = clamp((absLat - 60) / 30);
      const n = () => (rand() - 0.5);
      const terrain = clamp(1 - slope / 12 - rock / 14 + n() * 0.2);
      let scores: SiteScores;
      if (body === 'moon') {
        scores = { edl: terrain, isru: clamp(0.15 + 0.75 * prox + n() * 0.28), solar: clamp(0.3 + 0.45 * prox + n() * 0.45), astro: clamp(0.25 + 0.55 * rand()) };
      } else {
        scores = {
          edl: clamp(0.35 + 0.5 * terrain + clamp(-elev / 9000) * 0.3 + n() * 0.12),
          isru: clamp(0.12 + 0.82 * clamp(absLat / 62) + n() * 0.22),
          solar: clamp(0.97 - (absLat / 90) * 1.0 + n() * 0.2),
          astro: clamp(0.2 + 0.7 * rand() * rand() + 0.2 * rand()),
        };
      }
      const idx = String(i + 1).padStart(3, '0');
      const tag = body === 'moon' ? 'LUNA' : 'MARS';
      const dom = (Object.entries(scores) as [ScoreKey, number][]).sort((a, b) => b[1] - a[1])[0][0];
      const insightMap: Record<ScoreKey, string> = {
        edl: slope < 3 ? 'Near-level ground with sparse rock gives the lander a forgiving touchdown with plenty of tilt margin.' : 'Moderate terrain still fits the lander envelope, with careful targeting inside the ellipse.',
        isru: body === 'moon' ? 'Cold traps close by hold water ice — fuel and drinking water that never has to be launched from Earth.' : 'Shallow subsurface ice here means water for crew and fuel can be mined on site.',
        solar: 'Sunlight is plentiful here, keeping solar power high and the habitat warm with a modest battery.',
        astro: 'Mineral diversity in reach of a short rover trip makes this a strong science stop.',
      };
      const c = body === 'moon' ? COSPAR_MOON : absLat >= 45 ? cosparMars('IVc', true, 'Latitude band with SWIM-mapped shallow ice: Special-Region screening mandatory.') : cosparMars('IVa', false, 'Landed Mars hardware without life-detection: ≤300 spores/m².');
      const voidFlag = rand() < 0.55;
      out.push(mk({
        id: `${tag}_CAND_${idx}`, name: `${body === 'moon' ? 'Lunar' : 'Martian'} Candidate ${tag}-${idx}`, shortName: `${tag}-${idx}`, body,
        program: 'Mock candidate cell', lat: p.lat, lon: p.lon, elevationM: Math.round(elev), slopeDeg: Math.round(slope * 10) / 10, rockPct: Math.round(rock * 10) / 10,
        scores, cospar: c, insight: insightMap[dom],
        tubeWidthM: Math.round((body === 'moon' ? 180 : 90) + rand() * (body === 'moon' ? 320 : 180)), haulElevationGainM: Math.round(10 + rand() * 90),
        voidVerified: voidFlag && rand() < 0.5, dA: 0.5 + rand() * 0.2,
      }, false, { hasSubsurfaceVoid: voidFlag }));
    });
    for (const n of named) out.push(mk(n, true));
  }
  return out;
}

/* ───────────────────────── Base topology triad (Layer B) ───────────────────────── */

const orthoKm = (lat0: number, lon0: number, lat: number, lon: number): [number, number] => {
  const R = PHYSICS.H3_NORMALISING_RADIUS_KM, d = Math.PI / 180;
  const dl = (lon - lon0) * d;
  return [R * Math.cos(lat * d) * Math.sin(dl), R * (Math.cos(lat0 * d) * Math.sin(lat * d) - Math.sin(lat0 * d) * Math.cos(lat * d) * Math.cos(dl))];
};

export function buildTriad(site: PlanetarySite): BaseTopologyTriad {
  const pad = site.h3;
  const ring = gridDisk(pad, 1).filter((c) => c !== pad);
  let hab = ring[0], isru = ring[1];
  outer: for (const a of ring) for (const b of ring) if (a !== b && areNeighborCells(a, b)) { hab = a; isru = b; break outer; }
  // Orient so the haul runs left→right on screen: put the cell with greater east coordinate as ISRU
  const [pla, plo] = cellToLatLng(pad);
  const east = (c: string) => { const [la, lo] = cellToLatLng(c); return orthoKm(pla, plo, la, lo)[0]; };
  if (east(hab) > east(isru)) [hab, isru] = [isru, hab];
  const mkCell = (role: TriadCell['role'], h3: string): TriadCell => {
    const [la, lo] = cellToLatLng(h3);
    return { role, h3, centerKm: orthoKm(pla, plo, la, lo), vertsKm: cellToBoundary(h3).map(([a, b]) => orthoKm(pla, plo, a, b)) };
  };
  return {
    siteId: site.id, resolution: 7, psiRadiusKm: 1.5,
    cells: [mkCell('pad', pad), mkCell('hab', hab), mkCell('isru', isru)],
    haul: haulSummary(site.body, site.haulElevationGainM),
  };
}

/* ───────────────────────── Presets & power specs ───────────────────────── */

const PRESETS: MissionPreset[] = [
  {
    id: 'max-edl', label: 'MAX EDL SAFETY', body: 'mars', siteId: 'MARS_PAD_HELLAS_DEEP_FLOOR_12', weights: { edl: 100, isru: 25, solar: 30, astro: 20 }, zoomRadii: 3.2,
    callout: { title: 'Hellas Basin Pad 12 · −7,150 m', body: '+45%–60% aerodynamic payload bonus from the thicker air column at the bottom of the basin.', tone: 'ok' },
  },
  {
    id: 'max-astro', label: 'MAX ASTROBIOLOGY', body: 'mars', siteId: 'MARS_ELLIPSE_JEZERO_DELTA_FRONT', weights: { edl: 30, isru: 20, solar: 30, astro: 100 }, zoomRadii: 3.2,
    callout: { title: 'Jezero Delta · COSPAR Special Region', body: 'Life-detection class: ≤30 spores on sample hardware; any subsurface wet pocket triggers Cat. IVc Special-Region protection rules.', tone: 'warn' },
  },
  {
    id: 'max-isru', label: 'MAX ISRU & POWER', body: 'moon', siteId: 'MOON_ARTEMIS_NOBILE_RIM_1_PAD_10', weights: { edl: 30, isru: 100, solar: 85, astro: 20 }, zoomRadii: 3.0,
    callout: { title: 'Nobile Rim · 3-Hexagon Base Triad', body: 'Pad, Habitat and ISRU hexes at Res-7 — ice hauled 2.1 km on a few minutes of kettle-power per ton.', tone: 'info' },
  },
];

const POWER: PowerSurvivalSpec[] = [
  { body: 'moon', kind: 'polar-night', loadKwe: 10, shadowHours: 102.5, liIonWhPerKg: 100, rfcWhPerKg: 600 },
  { body: 'mars', kind: 'dust-storm', loadKwe: 10, tau: 3.0, extinctionK: 0.9, kilopowerUnits: 2, kilopowerKwe: 10, kilopowerUnitMassT: 1.5 },
];

/* ───────────────────────── Loader (live database backend) ───────────────────────── */

export async function loadAtlasDataset(): Promise<AtlasDataset> {
  // Live SQLite / Parquet backend (`planetary_moon_mars.db`)
  return realDataset as unknown as AtlasDataset;
}

/* ───────────────────────── Geometry helpers shared with the 3D layer ───────────────────────── */

/** Convert planetary lat/lon (deg, east-positive) to a unit vector in the texture-aligned body frame. */
export function latLonToUnit(body: CelestialId, lat: number, lon: number): [number, number, number] {
  const lonUsed = body === 'mars' ? ((lon + 360) % 360) - 180 : lon;
  return unit(lat, lonUsed);
}

export const DEFAULT_WEIGHTS: Weights = { edl: 70, isru: 80, solar: 60, astro: 40 };
export const DEFAULT_CUTOFFS: Cutoffs = { slope: 6, rock: 3, marsLat: 45 };

/** Round-half-up one-decimal formatter (avoids binary artefacts such as 18.45 → "18.4"). */
export const fmt1 = (x: number) => (Math.round((x + 1e-9) * 10) / 10).toFixed(1);
