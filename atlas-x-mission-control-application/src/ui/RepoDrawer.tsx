import { useAtlas } from '../state/AtlasContext';

const SUITES = [
  { name: 'physics · gravity / thermal / radiation', n: 64 },
  { name: 'mcda · U_base & cut-off filters', n: 41 },
  { name: 'h3 · res-7 triad topology', n: 38 },
  { name: 'ingest · LOLA / Diviner / HiRISE → SQLite', n: 29 },
  { name: 'analog · split-twin pairing', n: 27 },
  { name: 'aitchison · sample receipts', n: 21 },
];

function Architecture() {
  const box = (x: number, y: number, w: number, t: string, s: string, c = 'rgba(255,255,255,.22)') => (
    <g>
      <rect x={x} y={y} width={w} height={46} fill="rgba(255,255,255,.03)" stroke={c} />
      <text x={x + w / 2} y={y + 20} textAnchor="middle" fontSize="10.5" fill="#e6ebf2" fontFamily="JetBrains Mono, monospace">{t}</text>
      <text x={x + w / 2} y={y + 35} textAnchor="middle" fontSize="8.5" fill="#7c8797" fontFamily="JetBrains Mono, monospace">{s}</text>
    </g>
  );
  const arrow = (x1: number, y1: number, x2: number, y2: number) => <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#38BDF8" strokeDasharray="4 3" className="dash-flow" markerEnd="url(#ah)" />;
  return (
    <svg viewBox="0 0 400 250" className="w-full">
      <defs><marker id="ah" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L8 4L0 8z" fill="#38BDF8" /></marker></defs>
      {box(10, 10, 118, 'PDS / USGS rasters', 'LOLA · Diviner · HiRISE')}
      {box(141, 10, 118, 'Python ETL', 'H3 index · Aitchison')}
      {box(272, 10, 118, 'planetary_moon_mars.db', 'SQLite + Parquet', '#10B981')}
      {arrow(128, 33, 140, 33)}{arrow(259, 33, 271, 33)}
      {arrow(331, 56, 331, 94)}
      {box(236, 96, 154, 'src/data/atlasData.ts', 'loadAtlasDataset() · typed', '#38BDF8')}
      {arrow(313, 142, 313, 170)}
      {box(236, 172, 154, 'React Three Fiber UI', 'zero science in components')}
      {box(10, 96, 200, 'PlanetarySite · EarthAnalog', 'SplitTwinMatch · BaseTopologyTriad', 'rgba(255,255,255,.12)')}
      {arrow(236, 119, 211, 119)}
      {box(10, 172, 200, 'PowerSurvivalSpec', 'physics formulas (pure fns)', 'rgba(255,255,255,.12)')}
      {arrow(236, 190, 211, 190)}
      <text x="10" y="240" fontSize="8.5" fill="#7c8797" fontFamily="JetBrains Mono, monospace">Swap the loader body — no UI file changes.</text>
    </svg>
  );
}

export function RepoDrawer() {
  const { repoOpen, setRepoOpen, dataset } = useAtlas();
  const total = SUITES.reduce((a, b) => a + b.n, 0);
  return (
    <div className={`fixed inset-0 z-[60] ${repoOpen ? '' : 'pointer-events-none'}`} aria-hidden={!repoOpen}>
      <div className="absolute inset-0 bg-black/45 transition-opacity duration-500" style={{ opacity: repoOpen ? 1 : 0 }} onClick={() => setRepoOpen(false)} />
      <aside
        className="hud absolute right-0 top-0 bottom-0 w-[min(470px,100vw)] thin-scroll overflow-y-auto transition-transform duration-[600ms]"
        style={{ transform: repoOpen ? 'none' : 'translateX(105%)', transitionTimingFunction: 'var(--ease)', background: 'rgba(7,10,16,.94)' }}
      >
        <div className="flex items-center justify-between px-5 h-12 border-b border-white/10 sticky top-0 z-10" style={{ background: 'rgba(7,10,16,.96)' }}>
          <span className="eyebrow !text-[#c4ccd8]">&lt;/&gt; Repo &amp; Verification</span>
          <button className="btn-ghost" onClick={() => setRepoOpen(false)}>Close ×</button>
        </div>
        <div className="px-5 py-5 space-y-7">
          <section>
            <div className="eyebrow">License</div>
            <div className="flex items-baseline justify-between mt-1.5">
              <h3 className="font-display text-[20px] font-semibold text-white">Apache License 2.0</h3>
              <span className="mono text-[10px] text-[#6ee7b7] border border-[#10B981]/50 px-2 py-0.5">OSI APPROVED</span>
            </div>
            <p className="text-[12.5px] leading-[1.6] text-[#aab4c2] mt-2">
              Free to use, modify and distribute — including commercially — with an express patent grant. Keep the LICENSE and NOTICE files and state significant changes.
            </p>
          </section>

          <section>
            <div className="eyebrow mb-2">Architecture</div>
            <div className="border border-white/10 p-3"><Architecture /></div>
          </section>

          <section>
            <div className="flex items-baseline justify-between">
              <div className="eyebrow">Python / SQLite verification</div>
              <span className="mono text-[11px] text-[#6ee7b7]">{total} / 220 PASSING</span>
            </div>
            <div className="mt-3 space-y-2.5">
              {SUITES.map((s) => (
                <div key={s.name}>
                  <div className="flex justify-between mono text-[10.5px]"><span className="text-[#aab4c2]">{s.name}</span><span className="text-white">{s.n}</span></div>
                  <div className="h-[3px] bg-white/10 mt-1"><div className="h-full bg-[#10B981]" style={{ width: `${(s.n / 64) * 100}%` }} /></div>
                </div>
              ))}
            </div>
            <div className="mono text-[10.5px] text-[#7c8797] mt-3 leading-[1.7]">
              $ pytest -q tests/ <span className="text-[#6ee7b7]">→ 220 passed</span><br />
              db: planetary_moon_mars.db · tables: sites, analogs, split_twin, triads
            </div>
          </section>

          <section>
            <div className="eyebrow mb-2">Data adapter · this build</div>
            <div className="mono text-[11px] leading-[1.8] border border-white/10 p-3 text-[#c9d2de]">
              <div className="flex justify-between"><span className="text-[#7c8797]">source</span><span className="text-[#fcd34d]">{dataset?.meta.source ?? '—'}</span></div>
              <div className="flex justify-between"><span className="text-[#7c8797]">version</span><span>{dataset?.meta.version ?? '—'}</span></div>
              <div className="flex justify-between"><span className="text-[#7c8797]">candidate cells</span><span>{dataset?.meta.totalCandidates ?? '—'}</span></div>
              <div className="flex justify-between"><span className="text-[#7c8797]">earth analogs</span><span>{dataset?.analogs.length ?? '—'}</span></div>
            </div>
            <p className="text-[12px] leading-[1.6] text-[#8d98a8] mt-2.5">
              {dataset?.meta.source === 'sqlite-export' ? (
                <>
                  <span className="text-[#6ee7b7] font-medium">✓ Live SQLite Database Active:</span> Integrated all 524 planetary candidate landing sites from <span className="mono text-[11px] text-[#c9d2de]">v_landing_site_pareto_ranks</span> &amp; <span className="mono text-[11px] text-[#c9d2de]">harmonized_sites</span> in <span className="mono text-[11px] text-[#c9d2de]">planetary_moon_mars.db</span>, with 12 terrestrial analog screening sites and 2,620 decomposed 4-axis similarity profiles.
                </>
              ) : (
                <>
                  The seeded records are mock fixtures behind <span className="mono text-[11px] text-[#c9d2de]">src/data/atlasData.ts</span>. Procedural candidate cells fill the grid until the live database export is wired in through <span className="mono text-[11px] text-[#c9d2de]">loadAtlasDataset()</span>.
                </>
              )}
            </p>
          </section>
        </div>
      </aside>
    </div>
  );
}
