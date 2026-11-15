import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';

export function Hud({ className = '', style, children, ticks = true, ...rest }: { className?: string; style?: CSSProperties; children: ReactNode; ticks?: boolean } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`hud ${className.includes('absolute') || className.includes('fixed') ? '' : 'relative'} ${className}`} style={style} {...rest}>
      {ticks && (<><i className="hud-tick tl">+</i><i className="hud-tick tr">+</i><i className="hud-tick bl">+</i><i className="hud-tick br">+</i></>)}
      {children}
    </div>
  );
}

export function Tip({ label, children, right = false, className = '' }: { label: ReactNode; children: ReactNode; right?: boolean; className?: string }) {
  return (
    <span className={`tip ${right ? 'tip-right' : ''} ${className}`}>
      {children}
      <span className="tip-body">{label}</span>
    </span>
  );
}

export function Slider({ label, value, min, max, step = 1, onChange, display, fill = '#38BDF8', marks, hint }: {
  label: string; value: number; min: number; max: number; step?: number; onChange: (v: number) => void; display: string; fill?: string;
  marks?: { value: number; label: string }[]; hint?: ReactNode;
}) {
  const p = ((value - min) / (max - min)) * 100;
  return (
    <div className="py-[7px]">
      <div className="flex items-baseline justify-between">
        <span className="text-[11.5px] text-[#c4ccd8] tracking-[0.01em]">{label}</span>
        <span className="mono text-[11.5px] text-white">{display}</span>
      </div>
      <input
        type="range" className="atlas-range" min={min} max={max} step={step} value={value}
        style={{ ['--p' as string]: `${p}%`, ['--fill' as string]: fill } as CSSProperties}
        onChange={(e) => onChange(parseFloat(e.target.value))} aria-label={label}
      />
      {marks && (
        <div className="relative h-3 -mt-0.5">
          {marks.map((m) => (
            <span key={m.value} className="mono absolute text-[8.5px] text-[#6b7686] -translate-x-1/2" style={{ left: `${((m.value - min) / (max - min)) * 100}%` }}>{m.label}</span>
          ))}
        </div>
      )}
      {hint && <div className="mono text-[9.5px] mt-0.5 text-[#6ee7b7]">{hint}</div>}
    </div>
  );
}

/** Tween an array of numbers toward new targets (used for radar polygons & gauges). */
export function useTween(target: number[], ms = 650) {
  const [val, setVal] = useState(target);
  const ref = useRef(target);
  const key = target.join('|');
  useEffect(() => {
    const from = ref.current.slice();
    const to = target.slice();
    const t0 = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const u = Math.min(1, (now - t0) / ms);
      const e = 1 - Math.pow(1 - u, 3);
      const cur = to.map((v, i) => (from[i] ?? v) + (v - (from[i] ?? v)) * e);
      ref.current = cur; setVal(cur);
      if (u < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, ms]);
  return val;
}

export function Pill({ children, tone = 'neutral', className = '' }: { children: ReactNode; tone?: 'go' | 'nogo' | 'orbit' | 'solar' | 'neutral'; className?: string }) {
  const tones = {
    go: 'text-[#6ee7b7] border-[#10B981]/55 bg-[#10B981]/10',
    nogo: 'text-[#fca5a5] border-[#EF4444]/60 bg-[#EF4444]/10',
    orbit: 'text-[#7dd3fc] border-[#38BDF8]/55 bg-[#38BDF8]/10',
    solar: 'text-[#fcd34d] border-[#F59E0B]/55 bg-[#F59E0B]/10',
    neutral: 'text-[#b6c0cd] border-white/15 bg-white/[0.03]',
  };
  return <span className={`mono inline-flex items-center gap-1 border px-2 py-[3px] text-[9.5px] tracking-[0.08em] uppercase ${tones[tone]} ${className}`}>{children}</span>;
}

export function CardFrame({ title, eyebrow, docked, onDock, onClose, children }: {
  title: string; eyebrow: string; docked?: boolean; onDock?: () => void; onClose?: () => void; children: ReactNode;
}) {
  return (
    <section className="border-t border-white/10 first:border-t-0">
      <header className="flex items-start justify-between px-3.5 pt-3">
        <div>
          <div className="eyebrow">{eyebrow}</div>
          <h3 className="font-display text-[13.5px] font-semibold text-white mt-0.5">{title}</h3>
        </div>
        {docked ? (
          <button className="btn-ghost !px-2 !py-[3px]" onClick={onClose} aria-label={`Close ${title}`}>×</button>
        ) : (
          <button className="btn-ghost !px-2 !py-[3px]" onClick={onDock}>↗ DOCK</button>
        )}
      </header>
      <div className="px-3.5 pb-3.5 pt-2">{children}</div>
    </section>
  );
}

export function Expander({ open, onToggle, label, tone = 'orbit' }: { open: boolean; onToggle: () => void; label: string; tone?: 'orbit' | 'go' }) {
  return (
    <button onClick={onToggle} className={`mono w-full text-left text-[10px] tracking-[0.1em] uppercase py-1.5 border-t border-white/10 mt-2 transition-colors ${tone === 'go' ? 'text-[#6ee7b7] hover:text-[#a7f3d0]' : 'text-[#7dd3fc] hover:text-white'}`}>
      [ {open ? '−' : '+'} {label} ]
    </button>
  );
}
