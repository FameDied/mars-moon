import { useMemo } from 'react';
import { useAtlas } from '../state/AtlasContext';
import { Hud, Slider } from './Hud';

export function MissionDirector() {
  const a = useAtlas();
  const on = a.stage === 'workspace';
  const unlocked = useMemo(() => {
    if (!a.dataset) return 0;
    return a.dataset.sites.filter((s) => s.body === 'mars' && Math.abs(s.lat) > 45 && a.evalMap.get(s.id)?.go).length;
  }, [a.dataset, a.evalMap]);
  const W = a.weights, C = a.cutoffs;
  return (
    <div
      data-tour="tradespace"
      className="absolute left-4 top-[60px] w-[290px] transition-all duration-[900ms]"
      style={{ transform: on ? 'none' : 'translateX(-330px)', opacity: on ? 1 : 0, transitionDelay: on ? '900ms' : '0ms', transitionTimingFunction: 'var(--ease)', pointerEvents: on ? 'auto' : 'none' }}
    >
      <Hud>
        <div className="flex items-center justify-between px-3.5 h-9 border-b border-white/10">
          <span className="eyebrow !text-[#c4ccd8]">Mission Director</span>
          <button className="btn-ghost !px-2 !py-[2px]" onClick={() => a.setLeftOpen(!a.leftOpen)} aria-label="Toggle drawer">{a.leftOpen ? '⌃' : '⌄'}</button>
        </div>
        {a.leftOpen && (
          <div className="thin-scroll overflow-y-auto px-3.5 pb-3" style={{ maxHeight: 'calc(100vh - 150px)' }}>
            <div className="eyebrow pt-3 pb-1.5">Magic-Moment Presets</div>
            <div className="grid gap-1.5">
              {(a.dataset?.presets ?? []).map((p) => (
                <button key={p.id} className={`btn-ghost go text-left ${a.activePreset === p.id ? 'active' : ''}`} onClick={() => a.applyPreset(p.id)}>
                  [ {p.label} ]
                </button>
              ))}
            </div>

            <div className="eyebrow pt-4 pb-0.5">Priority Weights · MCDA</div>
            <Slider label="EDL Safety & Payload" value={W.edl} min={0} max={100} onChange={(v) => a.setWeight('edl', v)} display={`${W.edl}%`} />
            <Slider label="ISRU Water Access" value={W.isru} min={0} max={100} onChange={(v) => a.setWeight('isru', v)} display={`${W.isru}%`} />
            <Slider label="Solar / Comms Horizon" value={W.solar} min={0} max={100} onChange={(v) => a.setWeight('solar', v)} display={`${W.solar}%`} />
            <Slider label="Astrobiology / Science" value={W.astro} min={0} max={100} onChange={(v) => a.setWeight('astro', v)} display={`${W.astro}%`} />

            <div className="eyebrow pt-4 pb-0.5">Hard No-Go Cutoffs</div>
            <Slider label="Max Lander Slope" value={C.slope} min={4} max={10} step={0.1} onChange={(v) => a.setCutoff('slope', v)} display={`${C.slope.toFixed(1)}°`} fill="#cfd6e0"
              marks={[{ value: 4, label: '4.0°' }, { value: 10, label: '10.0°' }]} />
            <Slider label="Max Rock Abundance" value={C.rock} min={1} max={5} step={0.1} onChange={(v) => a.setCutoff('rock', v)} display={`${C.rock.toFixed(1)}%`} fill="#cfd6e0"
              marks={[{ value: 1, label: '1.0%' }, { value: 5, label: '5.0%' }]} />
            <Slider label="Mars Max Latitude (SWIM Ice)" value={C.marsLat} min={30} max={60} step={1} onChange={(v) => a.setCutoff('marsLat', v)} display={`${C.marsLat.toFixed(0)}°`} fill="#cfd6e0"
              marks={[{ value: 45, label: '45°' }, { value: 55, label: '55°' }]}
              hint={C.marsLat > 45 ? `▲ ${unlocked} high-latitude ice hexes unlocked (Arcadia / Utopia)` : undefined} />
            <div className="flex gap-3 mono text-[9px] text-[#7c8797] pt-3 border-t border-white/10 mt-3">
              <span><i className="inline-block w-2 h-2 bg-[#10B981] mr-1" />GO</span>
              <span><i className="inline-block w-2 h-2 bg-[#EF4444] mr-1" />NO-GO</span>
              <span><i className="inline-block w-2 h-2 bg-[#38BDF8] mr-1" />SELECTED</span>
            </div>
          </div>
        )}
      </Hud>
    </div>
  );
}
