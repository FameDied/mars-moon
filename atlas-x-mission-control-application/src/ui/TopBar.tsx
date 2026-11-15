import { useAtlas } from '../state/AtlasContext';

export function TopBar() {
  const a = useAtlas();
  const on = a.stage === 'workspace';
  const mode = a.focus === 'earth' ? 'EARTH ANALOG SURVEY' : 'ORBITAL TELEMETRY';
  return (
    <div
      className="absolute top-0 inset-x-0 h-12 flex items-center justify-between px-4 gap-4 z-30 transition-all duration-[900ms]"
      style={{
        background: 'linear-gradient(180deg, rgba(4,6,9,.82), rgba(4,6,9,0))', transform: on ? 'none' : 'translateY(-56px)', opacity: on ? 1 : 0,
        transitionDelay: on ? '800ms' : '0ms', transitionTimingFunction: 'var(--ease)', pointerEvents: on ? 'auto' : 'none',
      }}
    >
      <div className="flex items-center gap-4">
        <div className="font-display font-bold text-[13px] tracking-[0.18em] text-white">ATLAS<span className="text-[#7c8797]">-X</span></div>
        <div className="flex border border-white/12 bg-black/30 backdrop-blur-md" role="tablist" aria-label="Celestial body">
          {(['moon', 'mars'] as const).map((b) => (
            <button key={b} role="tab" aria-selected={a.focus === b} onClick={() => a.focusBody(b)}
              className={`mono text-[10.5px] tracking-[0.12em] px-3.5 py-[7px] transition-colors ${a.focus === b ? 'bg-[#38BDF8]/15 text-[#7dd3fc]' : 'text-[#9aa6b5] hover:text-white'}`}>
              {b === 'moon' ? '☾ MOON' : '♂ MARS'}
            </button>
          ))}
        </div>
      </div>

      <div className="hidden lg:flex items-center gap-3 mono text-[10px] tracking-[0.1em] text-[#9aa6b5] uppercase whitespace-nowrap overflow-hidden">
        <span>Qualified Sites: <b className="text-[#6ee7b7] font-medium">{a.qualified}</b> / {a.total}</span>
        <span className="text-white/20">•</span>
        <span className="hidden xl:inline">Active Target: <b className="text-[#7dd3fc] font-medium">{a.selected?.shortName ?? '—'}</b></span>
        <span className="text-white/20 hidden xl:inline">•</span>
        <span>Mode: <b className="text-white font-medium">{mode}</b></span>
      </div>

      <div className="flex items-center gap-2">
        <button className={`btn-ghost ${a.focus === 'earth' ? 'active' : ''}`} onClick={a.focusEarth}>🌍 Focus Earth Analogs</button>
        <button className="btn-ghost" onClick={() => a.setRepoOpen(true)}>&lt;/&gt; Repo</button>
        <a
          href="./atlas-x-architecture.pdf"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost !text-[#f59e0b] !border-[#f59e0b]/40 hover:!bg-[#f59e0b]/10 flex items-center gap-1.5"
          title="Open Project Architecture & Research Paper PDF"
        >
          <span>📄 PDF</span>
          <span className="text-[11px]">↗</span>
        </a>
        <a
          href="https://github.com/FameDied/mars-moon"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost !text-[#38BDF8] !border-[#38BDF8]/40 hover:!bg-[#38BDF8]/10 flex items-center gap-1.5"
          title="Open repository on GitHub in a new tab"
        >
          <span>View GitHub Repo</span>
          <span className="text-[11px]">↗</span>
        </a>
      </div>
    </div>
  );
}
