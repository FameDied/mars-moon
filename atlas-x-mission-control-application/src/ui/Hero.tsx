import { useEffect, useState } from 'react';
import { useAtlas } from '../state/AtlasContext';

export function Hero() {
  const a = useAtlas();
  const [mounted, setMounted] = useState(true);
  useEffect(() => {
    if (a.heroVisible) return;
    const t = setTimeout(() => setMounted(false), 900);
    return () => clearTimeout(t);
  }, [a.heroVisible]);
  if (!mounted) return null;
  const ready = a.sceneReady && !!a.dataset;
  const out = !a.heroVisible;
  const ease = 'cubic-bezier(0.65, 0, 0.35, 1)';
  return (
    <div className="absolute inset-0 z-20 pointer-events-none">
      <div className="absolute inset-x-0 top-0 h-[62%]" style={{ background: 'linear-gradient(180deg, rgba(4,6,9,.55), rgba(4,6,9,0))', opacity: out ? 0 : 1, transition: `opacity 600ms ${ease}` }} />

      <button
        className="pointer-events-auto absolute top-5 right-5 btn-ghost"
        style={{ opacity: out ? 0 : 1, transition: `opacity 600ms ${ease}` }}
        onClick={() => a.setRepoOpen(true)}
      >
        &lt;/&gt; Repo & Verification (220 Tests)
      </button>

      <div
        className="absolute inset-x-0 flex flex-col items-center text-center px-6"
        style={{ top: '15vh', opacity: out ? 0 : 1, transform: out ? 'translateY(-24px)' : 'none', transition: `opacity 600ms ${ease}, transform 600ms ${ease}` }}
      >
        <div className="eyebrow !text-[11px] !tracking-[0.22em] max-w-[92vw]" style={{ animation: 'fadeUp 1s .1s both' }}>Planetary Base Architecture &amp; Terrestrial Analog Engine</div>
        <h1 className="font-display font-bold text-white leading-none mt-4 text-[52px] sm:text-[64px] tracking-[0.04em]" style={{ animation: 'fadeUp 1s .25s both' }}>ATLAS-X</h1>
        <p className="mt-5 text-[16px] leading-[1.6] text-[#a9b3c1] max-w-[640px]" style={{ animation: 'fadeUp 1s .4s both' }}>
          Legacy tools fake 99% Earth matches by ignoring gravity and vacuum. We map where humans can actually survive—and where on Earth to prove it.
        </p>
        <button
          disabled={!ready}
          onClick={a.launch}
          className="pointer-events-auto mt-8 mono text-[12px] tracking-[0.2em] uppercase px-8 py-3.5 rounded-full border border-[#10B981] text-[#a7f3d0] bg-[#10B981]/[0.06] hover:bg-[#10B981]/[0.16] hover:shadow-[0_0_28px_rgba(16,185,129,.28)] transition-all disabled:opacity-50 disabled:cursor-wait"
          style={{ animation: 'fadeUp 1s .55s both' }}
        >
          {ready ? '▶ Launch Mission' : 'Loading ephemeris…'}
        </button>
      </div>

      <div className="absolute bottom-4 inset-x-0 text-center mono text-[9.5px] tracking-[0.14em] text-[#8793a3] uppercase" style={{ opacity: out ? 0 : 0.9, transition: `opacity 600ms ${ease}` }}>
        Space Apps Challenge · Permanent Moon Base Locations and Mars
      </div>
    </div>
  );
}
