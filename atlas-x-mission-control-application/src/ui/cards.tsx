import { useEffect, useState } from 'react';
import {
  PHYSICS, computePower, coverage, craneOffloadPct, cryoDeltaK, findSplitTwin, fmt1, radiationMsvYr, radiationVsEarth, tubeWidthEarthEquiv,
  type AtlasDataset, type BodyId, type PlanetarySite, type SiteEval, type SplitTwinMatch, type Weights,
} from '../data/atlasData';
import { Expander, Pill, Tip, useTween } from './Hud';

const fmtCoord = (v: number, pos: string, neg: string) => `${Math.abs(v).toFixed(2)}°${v >= 0 ? pos : neg}`;

/* ───────────────────────── Card 1 · Site brief ───────────────────────── */
export function SiteBriefBody({ site, ev, weights }: { site: PlanetarySite; ev: SiteEval | undefined; weights: Weights }) {
  const [phys, setPhys] = useState(false);
  const [receipt, setReceipt] = useState(false);
  const go = ev?.go ?? false;
  const sensor = PHYSICS.bodies[site.body].terrainSensor;
  const prov = (k: 'elevation' | 'slope' | 'rock') => {
    const p = site.provenance[k];
    return (<><b className="text-white font-medium">{p.instrument}</b><br />Sensor: {sensor}<br />±1.96σ Taylor uncertainty: ±{p.sigma196}{p.unit}</>);
  };
  const hero = [
    { k: 'U_BASE', v: (ev?.u ?? 0).toFixed(3), sub: 'MCDA score', tip: <>Weighted mean of EDL, ISRU, Solar and Astrobiology sub-scores using your current priority sliders.</> },
    { k: 'SLOPE', v: `${site.slopeDeg.toFixed(1)}°`, sub: 'lander tilt', tip: prov('slope'), bad: !!ev?.reasons.some((r) => r.startsWith('Slope')) },
    { k: 'ROCKS', v: `${site.rockPct.toFixed(1)}%`, sub: 'surface cover', tip: prov('rock'), bad: !!ev?.reasons.some((r) => r.startsWith('Rocks')) },
  ];
  const wsum = weights.edl + weights.isru + weights.solar + weights.astro || 1;
  const subs: { k: keyof Weights; label: string }[] = [
    { k: 'edl', label: 'EDL Safety' }, { k: 'isru', label: 'ISRU Water' }, { k: 'solar', label: 'Solar / Comms' }, { k: 'astro', label: 'Astrobiology' },
  ];
  return (
    <div>
      <div className="font-display text-[15px] font-semibold leading-tight text-white">{site.name}</div>
      <div className="mono text-[10.5px] text-[#9aa6b5] mt-1">
        <Tip label={<>{prov('elevation')}</>}>
          <span className="cursor-help border-b border-dotted border-white/30">{fmtCoord(site.lat, 'N', 'S')}, {fmtCoord(site.lon, 'E', 'W')} · {site.elevationM.toLocaleString('en-US')} m</span>
        </Tip>
      </div>
      <div className="flex flex-wrap gap-1.5 mt-2.5">
        <Pill tone={go ? 'go' : 'nogo'}><span className="pulse">●</span> {go ? 'GO' : 'NO-GO'}</Pill>
        <Tip label={site.cospar.note}><Pill tone={site.cospar.special ? 'solar' : 'neutral'} className="cursor-help">⚑ {site.cospar.label}</Pill></Tip>
        {site.highlight && <Pill tone="orbit">★ {site.highlight}</Pill>}
      </div>
      <p className="text-[12.5px] leading-[1.5] text-[#d5dbe5] mt-3">{site.insight}</p>
      {!go && ev && (
        <ul className="mt-2 space-y-0.5">
          {ev.reasons.map((r) => (<li key={r} className="mono text-[10px] text-[#fca5a5]">✕ {r}</li>))}
        </ul>
      )}
      <div className="grid grid-cols-3 gap-px mt-3 bg-white/10 border border-white/10">
        {hero.map((h) => (
          <Tip key={h.k} label={h.tip} className="bg-[#080c13] block">
            <div className="px-2.5 py-2 cursor-help">
              <div className="mono text-[8.5px] tracking-[0.14em] text-[#7c8797]">{h.k}</div>
              <div className={`mono text-[18px] leading-tight mt-0.5 ${h.bad ? 'text-[#fca5a5]' : 'text-white'}`}>{h.v}</div>
              <div className="text-[9.5px] text-[#7c8797]">{h.sub}</div>
            </div>
          </Tip>
        ))}
      </div>

      <Expander open={receipt} onToggle={() => setReceipt(!receipt)} label="Ground-Truth Sample Receipt" tone="go" />
      {receipt && (
        <div className="mono text-[10.5px] leading-[1.6] text-[#c9d2de] pb-1" style={{ animation: 'fadeUp .3s' }}>
          {site.sample.sample} • Aitchison d_A = {site.sample.dA.toFixed(3)}{' '}
          <span className={site.sample.passed ? 'text-[#6ee7b7]' : 'text-[#fca5a5]'}>[{site.sample.passed ? 'PASSED' : 'FAILED'}]</span>
          <div className="text-[#7c8797]">threshold d_A ≤ {site.sample.threshold.toFixed(2)} · compositional (CLR) distance</div>
        </div>
      )}

      <Expander open={phys} onToggle={() => setPhys(!phys)} label="Inspect Physics & Provenance" />
      {phys && (
        <div className="space-y-2 pb-1" style={{ animation: 'fadeUp .3s' }}>
          <div className="space-y-1.5">
            {subs.map((s) => (
              <div key={s.k} className="flex items-center gap-2">
                <span className="text-[10.5px] w-[88px] text-[#aab4c2]">{s.label}</span>
                <div className="flex-1 h-[3px] bg-white/10 relative"><div className="absolute inset-y-0 left-0 bg-[#38BDF8]" style={{ width: `${site.scores[s.k] * 100}%` }} /></div>
                <span className="mono text-[10.5px] w-[34px] text-right">{site.scores[s.k].toFixed(2)}</span>
                <span className="mono text-[9px] w-[30px] text-right text-[#6b7686]">w{Math.round((weights[s.k] / wsum) * 100)}</span>
              </div>
            ))}
          </div>
          <div className="mono text-[10px] text-[#7c8797] leading-[1.6] border-t border-white/10 pt-2">
            U_base = Σ wᵢ·sᵢ / Σ wᵢ<br />
            H3 res-7 pad cell: <span className="text-[#c9d2de]">{site.h3}</span><br />
            Elevation ±{site.provenance.elevation.sigma196} m · Slope ±{site.provenance.slope.sigma196}° · Rock ±{site.provenance.rock.sigma196}% (1.96σ)<br />
            Program: {site.program}
          </div>
        </div>
      )}
    </div>
  );
}

/* ───────────────────────── Card 2 · Split-twin radar ───────────────────────── */
const AXES: { k: 'A' | 'B' | 'C' | 'D'; name: string; short: string }[] = [
  { k: 'A', name: 'Geomorphology', short: 'A · GEOMORPH' },
  { k: 'B', name: 'Geochemistry', short: 'B · GEOCHEM' },
  { k: 'C', name: 'Thermophysics', short: 'C · THERMO' },
  { k: 'D', name: 'Volatiles / Void', short: 'D · VOID' },
];

export function RadarBody({ dataset, body, twin, openOnly, setOpenOnly, compact }: {
  dataset: AtlasDataset; body: BodyId; twin: SplitTwinMatch; openOnly: boolean; setOpenOnly: (v: boolean) => void; compact?: boolean;
}) {
  const [hov, setHov] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  const byId = new Map(dataset.analogs.map((a) => [a.id, a]));
  const A = byId.get(twin.analogIds[0])!, B = byId.get(twin.analogIds[1])!, S = byId.get(twin.bestSingleId)!;
  const targets = [
    ...AXES.map((a) => twin.bestSingleAxes[a.k]),
    ...AXES.map((a) => twin.combinedAxes[a.k]),
  ];
  const tw = useTween(targets);
  const single = tw.slice(0, 4), comb = tw.slice(4, 8);
  const cx = 130, cy = 108, R = 76;
  const ang = (i: number) => -Math.PI / 2 + (i * Math.PI) / 2;
  const pt = (i: number, v: number) => [cx + Math.cos(ang(i)) * R * (v / 100), cy + Math.sin(ang(i)) * R * (v / 100)];
  const poly = (vals: number[]) => vals.map((v, i) => pt(i, v).map((n) => n.toFixed(1)).join(',')).join(' ');
  const open2 = findSplitTwin(dataset.analogs, body, true), all2 = findSplitTwin(dataset.analogs, body, false);
  const lift = twin.combinedCoverage - twin.bestSingleCoverage;
  const labelPos = [[cx, cy - R - 14, 'middle'], [cx + R + 8, cy + 3, 'start'], [cx, cy + R + 20, 'middle'], [cx - R - 8, cy + 3, 'end']] as const;
  const hasBench = [A, B].some((x) => x.fieldAccess === 'remote-sensing-benchmark');
  return (
    <div>
      <div className="grid grid-cols-3 gap-px bg-white/10 border border-white/10">
        <div className="bg-[#080c13] px-2.5 py-2"><div className="mono text-[8.5px] tracking-[0.14em] text-[#7c8797]">BEST SINGLE</div><div className="mono text-[17px] text-[#fcd34d]">{twin.bestSingleCoverage.toFixed(1)}%</div></div>
        <div className="bg-[#080c13] px-2.5 py-2"><div className="mono text-[8.5px] tracking-[0.14em] text-[#7c8797]">SPLIT-TWIN</div><div className="mono text-[17px] text-[#6ee7b7]">{twin.combinedCoverage.toFixed(1)}%</div></div>
        <div className="bg-[#080c13] px-2.5 py-2"><div className="mono text-[8.5px] tracking-[0.14em] text-[#7c8797]">COVERAGE GAIN</div><div className="mono text-[17px] text-white">+{lift.toFixed(1)}<span className="text-[10px] text-[#7c8797]"> pts</span></div></div>
      </div>
      <svg viewBox="-24 0 308 226" className="w-full mt-1" style={{ maxHeight: compact ? 190 : 250 }}>
        <defs>
          <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3.5" /></filter>
        </defs>
        {[25, 50, 75, 100].map((r) => (
          <polygon key={r} points={poly([r, r, r, r])} fill="none" stroke="rgba(255,255,255,.1)" strokeWidth={r === 100 ? 0 : 1} />
        ))}
        {AXES.map((a, i) => {
          const [x, y] = pt(i, 100);
          return <line key={a.k} x1={cx} y1={cy} x2={x} y2={y} stroke={hov === i ? 'rgba(255,255,255,.5)' : 'rgba(255,255,255,.14)'} />;
        })}
        <polygon points={poly([100, 100, 100, 100])} fill="rgba(56,189,248,.04)" stroke="#38BDF8" strokeWidth={1.2} strokeDasharray="4 3" className="dash-flow" />
        <polygon points={poly(comb)} fill="rgba(16,185,129,.22)" stroke="#10B981" strokeWidth={6} opacity={0.4} filter="url(#glow)" />
        <polygon points={poly(comb)} fill="rgba(16,185,129,.2)" stroke="#34d399" strokeWidth={1.8} />
        <polygon points={poly(single)} fill="rgba(245,158,11,.22)" stroke="#F59E0B" strokeWidth={1.6} />
        {AXES.map((a, i) => {
          const [x, y] = pt(i, comb[i]);
          return <circle key={a.k} cx={x} cy={y} r={hov === i ? 4 : 2.6} fill="#10B981" stroke="#04070b" />;
        })}
        {AXES.map((a, i) => (
          <g key={a.k} onMouseEnter={() => setHov(i)} onMouseLeave={() => setHov(null)} style={{ cursor: 'pointer' }}>
            <text x={labelPos[i][0]} y={labelPos[i][1]} textAnchor={labelPos[i][2]} fontSize="8.5" fill={hov === i ? '#fff' : '#9aa6b5'} fontFamily="JetBrains Mono, monospace" letterSpacing="0.6">{a.short}</text>
            <rect x={labelPos[i][0] - 40} y={labelPos[i][1] - 12} width="80" height="16" fill="transparent" transform={labelPos[i][2] === 'start' ? 'translate(34,0)' : labelPos[i][2] === 'end' ? 'translate(-34,0)' : ''} />
          </g>
        ))}
      </svg>
      <div className="mono text-[10.5px] h-[30px] border border-white/10 px-2 flex items-center justify-between text-[#c9d2de]">
        {hov === null ? (
          <span className="text-[#7c8797]">Hover an axis to compare coverage</span>
        ) : (
          <>
            <span>{AXES[hov].name}</span>
            <span><span className="text-[#fcd34d]">{twin.bestSingleAxes[AXES[hov].k].toFixed(1)}</span> → <span className="text-[#6ee7b7]">{twin.combinedAxes[AXES[hov].k].toFixed(1)}</span> / 100</span>
          </>
        )}
      </div>
      <div className="mt-2.5 space-y-1 mono text-[10px]">
        <div className="flex items-center gap-2 text-[#9fd8f5]"><i className="inline-block w-4 border-t border-dashed border-[#38BDF8]" />Ideal target base (100%)</div>
        <div className="flex items-center gap-2 text-[#fcd34d]"><i className="inline-block w-4 h-[3px] bg-[#F59E0B]" />Best single · {S.name}</div>
        <div className="flex items-center gap-2 text-[#6ee7b7]"><i className="inline-block w-4 h-[3px] bg-[#10B981]" />Split-Twin · {A.name} + {B.name}</div>
      </div>
      <button onClick={() => setOpenOnly(!openOnly)} className="mt-3 w-full flex items-center justify-between gap-2 border border-white/12 px-2.5 py-2 hover:border-white/30 transition-colors text-left" aria-pressed={openOnly}>
        <span className="mono text-[9.5px] tracking-[0.06em] text-[#c4ccd8] leading-snug">Field-Access Filter:<br />Open Bilateral Sites Only</span>
        <span className={`switch ${openOnly ? 'on' : ''}`} />
      </button>
      <div className="mono text-[10px] text-[#7c8797] mt-1.5 leading-[1.5]">
        {body === 'mars'
          ? <>Open-field {open2.combinedCoverage.toFixed(1)}% · incl. Qaidam benchmark {all2.combinedCoverage.toFixed(1)}%</>
          : <>Open-field {open2.combinedCoverage.toFixed(1)}% · all sites {all2.combinedCoverage.toFixed(1)}%</>}
        {hasBench && !openOnly && <div className="text-[#9aa7b8]">Qaidam Basin = remote-sensing benchmark (no field access)</div>}
      </div>
      <Expander open={open} onToggle={() => setOpen(!open)} label="Inspect Axis Math" />
      {open && (
        <div className="mono text-[10px] text-[#9aa6b5] leading-[1.7] pb-1" style={{ animation: 'fadeUp .3s' }}>
          coverage = mean₍A–D₎ ( max(site₁ᵢ , site₂ᵢ) )<br />
          {AXES.map((a) => (
            <div key={a.k} className="flex justify-between"><span>{a.k} · {a.name}</span><span>{A.axes[body][a.k].toFixed(1)} | {B.axes[body][a.k].toFixed(1)} → <span className="text-[#6ee7b7]">{twin.combinedAxes[a.k].toFixed(1)}</span></span></div>
          ))}
          <div className="flex justify-between border-t border-white/10 mt-1 pt-1"><span>Σ/4</span><span className="text-[#6ee7b7]">{coverage(twin.combinedAxes).toFixed(1)}%</span></div>
        </div>
      )}
    </div>
  );
}

/* ───────────────────────── Card 3 · Lava-tube shield simulator ───────────────────────── */
function ArcGauge({ value, max, color, label, big, sub, tip }: { value: number; max: number; color: string; label: string; big: string; sub: string; tip: React.ReactNode }) {
  const frac = Math.min(1, Math.max(0, value / max));
  const r = 30, c = Math.PI * r;
  const sx = 40 - r, ex = 40 + r;
  return (
    <Tip label={tip} className="block">
      <div className="text-center cursor-help">
        <svg viewBox="0 0 80 50" className="w-full">
          <path d={`M ${sx} 42 A ${r} ${r} 0 0 1 ${ex} 42`} fill="none" stroke="rgba(255,255,255,.12)" strokeWidth="4" />
          <path d={`M ${sx} 42 A ${r} ${r} 0 0 1 ${ex} 42`} fill="none" stroke={color} strokeWidth="4" strokeDasharray={`${c * frac} ${c}`} />
          <text x="40" y="38" textAnchor="middle" fontSize="11" fill="#fff" fontFamily="JetBrains Mono, monospace" fontWeight="500">{big}</text>
        </svg>
        <div className="mono text-[8.5px] tracking-[0.1em] text-[#9aa6b5] -mt-1 leading-tight">{label}</div>
        <div className="mono text-[9px] text-[#7c8797]">{sub}</div>
      </div>
    </Tip>
  );
}

export function ShieldBody({ site, tube, setTube }: { site: PlanetarySite; tube: boolean; setTube: (v: boolean) => void }) {
  const b = site.body;
  const msv = radiationMsvYr(b, tube);
  const msvT = useTween([msv], 900)[0];
  const safe = msv < PHYSICS.CREW_SAFE_MSV_YR;
  const offload = craneOffloadPct(b), cryo = cryoDeltaK(b);
  const wEq = tubeWidthEarthEquiv(site);
  return (
    <div>
      <div className="grid grid-cols-3 gap-1.5">
        <ArcGauge value={offload} max={100} color="#10B981" label="CRANE OFFLOAD" big={`${fmt1(offload)}%`} sub={`g=${PHYSICS.bodies[b].g.toFixed(2)} m/s²`}
          tip={<>Gravity Crane Offload = 1 − g<sub>body</sub>/g<sub>⊕</sub><br />= 1 − {PHYSICS.bodies[b].g.toFixed(2)}/{PHYSICS.G_EARTH.toFixed(3)}<br />Lifting load that nature carries for you.</>} />
        <ArcGauge value={cryo} max={260} color="#F59E0B" label="CRYO-CHILLER Δ" big={`+${fmt1(cryo)}K`} sub={`LOX ${PHYSICS.LOX_BOIL_K}K`}
          tip={<>ΔT = T<sub>reject</sub> − T<sub>LOX</sub><br />= {PHYSICS.bodies[b].ambientK.toFixed(1)} K − {PHYSICS.LOX_BOIL_K} K<br />Heat-lift the chiller must overcome to store oxygen.</>} />
        <ArcGauge value={msvT} max={220} color={safe ? '#10B981' : '#EF4444'} label="IONIZING RAD" big={fmt1(msvT)} sub="mSv/yr"
          tip={<><b className="text-white font-medium">{site.provenance.radiation.instrument}</b><br />±1.96σ: ±{site.provenance.radiation.sigma196} mSv/yr<br />Earth baseline {PHYSICS.EARTH_RADIATION_MSV_YR} mSv/yr</>} />
      </div>
      <div className="mono text-[10.5px] text-center mt-1 text-[#9aa6b5]">
        {fmt1(msv)} mSv/yr <span className="text-white">[{fmt1(radiationVsEarth(msv))}× Earth]</span>
      </div>
      <div className="mt-2 flex justify-center">
        {safe
          ? <Pill tone="go" className="!text-[10px]">✓ CREW SAFE &lt;{PHYSICS.CREW_SAFE_MSV_YR} mSv/yr</Pill>
          : <Pill tone="nogo" className="!text-[10px]"><span className="pulse">▲</span> CRITICAL WARNING</Pill>}
      </div>
      <button onClick={() => setTube(!tube)} aria-pressed={tube} className="mt-3 w-full flex items-center gap-2.5 border border-white/12 px-2.5 py-2 hover:border-white/30 text-left transition-colors">
        <span className={`switch ${tube ? 'on' : ''}`} />
        <span className="mono text-[10px] leading-snug text-[#c4ccd8]">[{tube ? 'x' : ' '}] Deploy Inside Subsurface Lava Tube<br /><span className="text-[#7c8797]">(has_subsurface_void = {tube ? 1 : 0})</span></span>
      </button>
      <div className="mono text-[9.5px] mt-1.5 text-[#7c8797]">
        {site.hasSubsurfaceVoid ? (site.voidVerified ? 'Void evidence: gravity + radar corroborated' : 'Void evidence: gravity-anomaly candidate (unverified)') : 'No void detected — assumes hypothetical tube'}
      </div>
      {tube && (
        <div className="mt-2.5 border border-[#10B981]/35 bg-[#10B981]/[0.05] px-2.5 py-2" style={{ animation: 'fadeUp .4s' }}>
          <div className="mono text-[8.5px] tracking-[0.14em] text-[#6ee7b7]">GRAVITOMETRIC STRUCTURAL TUBE WIDTH</div>
          <div className="mono text-[12px] text-white mt-1">W<sub>Earth_equiv</sub> = <span className="text-[#6ee7b7]">{wEq.toFixed(1)} m</span></div>
          <div className="mono text-[9.5px] text-[#9aa6b5] leading-[1.6] mt-1">
            = W<sub>tube</sub> · g<sub>body</sub>/g<sub>⊕</sub> = {site.tubeWidthM} m × {(PHYSICS.bodies[b].g / PHYSICS.G_EARTH).toFixed(3)}<br />
            Roof stress equals a {wEq.toFixed(0)} m span on Earth (widest known terrestrial tubes ≈ 30 m).
          </div>
        </div>
      )}
    </div>
  );
}

/* ───────────────────────── Card 4 · Survival & power ───────────────────────── */
export function PowerBody({ dataset, body }: { dataset: AtlasDataset; body: BodyId }) {
  const [tab, setTab] = useState<BodyId>(body);
  useEffect(() => setTab(body), [body]);
  const spec = dataset.power.find((p) => p.body === tab)!;
  const r = computePower(spec);
  const tone = { ok: '#10B981', bad: '#EF4444', warn: '#F59E0B', info: '#38BDF8' } as const;
  const bars = useTween(r.bars.map((b) => b.value / b.max));
  return (
    <div>
      <div className="flex gap-px mb-2.5">
        {(['moon', 'mars'] as BodyId[]).map((b) => (
          <button key={b} className={`btn-ghost flex-1 ${tab === b ? 'active' : ''}`} onClick={() => setTab(b)}>
            {PHYSICS.bodies[b].symbol} {b === 'moon' ? 'Polar Night' : 'Dust Storm'}
          </button>
        ))}
      </div>
      <div className="flex items-end justify-between">
        <div>
          <div className="mono text-[8.5px] tracking-[0.14em] text-[#7c8797]">{tab === 'moon' ? 'RFC vs LI-ION MASS' : 'PV OUTPUT AT τ = 3.0'}</div>
          <div className={`mono text-[22px] leading-tight ${tab === 'moon' ? 'text-[#6ee7b7]' : 'text-[#fca5a5]'}`}>{r.headline}</div>
        </div>
        <Pill tone={tab === 'moon' ? 'go' : 'solar'}>{tab === 'moon' ? 'Regen Fuel Cell' : '2× 10 kWe Kilopower'}</Pill>
      </div>
      {tab === 'moon' && (
        <div className="mt-2.5">
          <div className="mono text-[8.5px] tracking-[0.12em] text-[#7c8797] mb-1">LUNAR DAY (708 hr) · SHADOW {spec.shadowHours} hr</div>
          <div className="flex h-[10px] border border-white/15">
            <div className="bg-[#f5d98a]/70" style={{ width: `${100 - ((spec.shadowHours ?? 0) / 708) * 100}%` }} />
            <div className="bg-[#0a0f18] flex-1 relative" style={{ backgroundImage: 'repeating-linear-gradient(45deg, rgba(239,68,68,.35) 0 2px, transparent 2px 5px)' }} />
          </div>
        </div>
      )}
      <div className="mt-3 space-y-2">
        {r.bars.map((bar, i) => (
          <div key={bar.label}>
            <div className="flex justify-between mono text-[10px]"><span className="text-[#aab4c2]">{bar.label}</span><span className="text-white">{bar.display}</span></div>
            <div className="h-[6px] bg-white/10 mt-1"><div className="h-full" style={{ width: `${(bars[i] ?? 0) * 100}%`, background: tone[bar.tone] }} /></div>
          </div>
        ))}
      </div>
      <div className="mt-3 border-t border-white/10 pt-2 space-y-1">
        {r.rows.map((row) => (
          <div key={row.label} className="flex justify-between gap-3 mono text-[10px]"><span className="text-[#7c8797]">{row.label}</span><span style={{ color: tone[row.tone ?? 'info'] }} className="text-right">{row.value}</span></div>
        ))}
      </div>
    </div>
  );
}
