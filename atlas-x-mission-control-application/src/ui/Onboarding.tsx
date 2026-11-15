import { useEffect, useState } from 'react';
import { useAtlas } from '../state/AtlasContext';
import { motion } from '../scene/layout';

const STEPS = [
  { target: 'tradespace', title: '1. Play Mission Director', body: 'Drag safety cutoffs or mission priorities to filter landing zones live.' },
  { target: 'globe', title: '2. Dual-Body Navigation', body: 'Switch between Moon and Mars, or click Earth in the background to inspect matching terrestrial test sites.' },
  { target: 'telemetry', title: '3. Unvarnished Physics', body: 'Compare single Earth analogs against our Split-Twin pairing and test subsurface lava tube radiation shielding.' },
] as const;

type Hole = { kind: 'rect'; x: number; y: number; w: number; h: number } | { kind: 'circle'; x: number; y: number; r: number };

export function Onboarding() {
  const { tour, setTour, setLeftOpen, setRightOpen } = useAtlas();
  const [, force] = useState(0);
  useEffect(() => {
    if (tour === null) return;
    setLeftOpen(true); setRightOpen(true);
    const on = () => force((n) => n + 1);
    const iv = setInterval(on, 250);
    window.addEventListener('resize', on);
    return () => { clearInterval(iv); window.removeEventListener('resize', on); };
  }, [tour, setLeftOpen, setRightOpen]);
  if (tour === null) return null;

  const vw = window.innerWidth, vh = window.innerHeight;
  const step = STEPS[tour];
  const holes: Hole[] = [];
  let tipX = 0, tipY = 0;
  const TW = 310;
  if (step.target === 'globe') {
    const w = Math.min(vw * 0.34, vh * 0.78), h = Math.min(vh * 0.74, w * 1.05);
    const x = vw / 2 - w / 2, y = vh * 0.5 - h / 2 + 10;
    holes.push({ kind: 'rect', x, y, w, h });
    const e = motion.earthScreen;
    if (e.visible) holes.push({ kind: 'circle', x: e.x * vw, y: e.y * vh, r: Math.max(26, e.r * vw + 14) });
    tipX = vw / 2 - TW / 2; tipY = y + h + 14;
  } else {
    const el = document.querySelector(`[data-tour="${step.target}"]`) as HTMLElement | null;
    const r = el?.getBoundingClientRect();
    if (r) {
      holes.push({ kind: 'rect', x: r.left - 6, y: r.top - 6, w: r.width + 12, h: r.height + 12 });
      tipY = r.top + 28;
      tipX = step.target === 'tradespace' ? r.right + 20 : r.left - TW - 20;
    }
  }
  tipX = Math.max(12, Math.min(vw - TW - 12, tipX));
  tipY = Math.max(60, Math.min(vh - 210, tipY));
  const next = () => (tour >= STEPS.length - 1 ? setTour(null) : setTour(tour + 1));

  return (
    <div className="fixed inset-0 z-50 pointer-events-none" style={{ animation: 'fadeUp .5s var(--ease)' }}>
      <svg className="absolute inset-0 w-full h-full">
        <defs>
          <mask id="tour-mask">
            <rect width="100%" height="100%" fill="white" />
            {holes.map((h, i) => (h.kind === 'rect'
              ? <rect key={i} x={h.x} y={h.y} width={h.w} height={h.h} fill="black" rx={h.h > 400 ? 18 : 3} />
              : <circle key={i} cx={h.x} cy={h.y} r={h.r} fill="black" />))}
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="rgba(4,6,9,0.58)" mask="url(#tour-mask)" />
        {holes.map((h, i) => (h.kind === 'rect'
          ? <rect key={i} x={h.x} y={h.y} width={h.w} height={h.h} fill="none" stroke="#38BDF8" strokeOpacity=".7" strokeDasharray={step.target === 'globe' ? '5 5' : undefined} rx={h.h > 400 ? 18 : 3} />
          : <circle key={i} cx={h.x} cy={h.y} r={h.r} fill="none" stroke="#38BDF8" strokeOpacity=".8" strokeDasharray="4 4" className="dash-flow" />))}
      </svg>
      <div
        key={tour}
        className="hud absolute pointer-events-auto"
        style={{ left: tipX, top: tipY, width: TW, borderColor: 'rgba(56,189,248,.45)', animation: 'fadeUp .45s var(--ease)' }}
      >
        <i className="hud-tick tl">+</i><i className="hud-tick br">+</i>
        <div className="px-4 pt-3.5 pb-3">
          <div className="flex items-center justify-between">
            <span className="mono text-[9.5px] tracking-[0.16em] text-[#7dd3fc]">QUICK TOUR · {tour + 1}/{STEPS.length}</span>
            <span className="flex gap-1">{STEPS.map((_, i) => <i key={i} className="w-4 h-[2px]" style={{ background: i <= tour ? '#38BDF8' : 'rgba(255,255,255,.2)' }} />)}</span>
          </div>
          <div className="font-display text-[15px] font-semibold text-white mt-2">{step.title}</div>
          <p className="text-[12.5px] leading-[1.55] text-[#c4ccd8] mt-1">— {step.body}</p>
          <div className="flex justify-between items-center mt-3.5">
            <button className="mono text-[10px] tracking-[0.1em] text-[#7c8797] hover:text-white" onClick={() => setTour(null)}>[ SKIP TOUR ]</button>
            <button className="btn-ghost active" onClick={next}>[ {tour >= STEPS.length - 1 ? 'DONE' : 'NEXT'} ]</button>
          </div>
        </div>
      </div>
    </div>
  );
}
