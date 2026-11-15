import { useEffect, useState } from 'react';
import { useAtlas, type CardId } from '../state/AtlasContext';
import { Hud } from './Hud';
import { CARD_META, CardBody } from './Inspector';

export function DockTray() {
  const a = useAtlas();
  const [min, setMin] = useState(false);
  const [active, setActive] = useState<CardId | null>(null);
  useEffect(() => { if (a.docked.length && (!active || !a.docked.includes(active))) setActive(a.docked[a.docked.length - 1]); }, [a.docked, active]);
  if (a.stage !== 'workspace' || a.docked.length === 0) return null;
  return (
    <div
      className="absolute bottom-4 z-20"
      style={{ left: a.leftOpen ? 322 : 16, right: a.rightOpen ? 372 : 16, display: 'flex', justifyContent: 'center', pointerEvents: 'none', animation: 'fadeUp .45s var(--ease)' }}
    >
      <Hud className="max-w-full" style={{ pointerEvents: 'auto' }}>
        <div className="flex items-stretch border-b border-white/10">
          <div className="eyebrow px-3 flex items-center !text-[#c4ccd8]">Dock</div>
          <div className="flex flex-1">
            {a.docked.map((c) => (
              <div key={c} className={`flex items-center border-l border-white/10 ${active === c ? 'bg-white/[0.06]' : ''}`}>
                <button className={`mono text-[10px] tracking-[0.1em] px-3 py-2 ${active === c ? 'text-[#7dd3fc]' : 'text-[#9aa6b5] hover:text-white'}`} onClick={() => { setActive(c); setMin(false); }}>{CARD_META[c].tab}</button>
                <button className="text-[#7c8797] hover:text-white pr-2.5 text-[14px] leading-none" onClick={() => a.undock(c)} aria-label={`Close ${CARD_META[c].tab}`}>×</button>
              </div>
            ))}
          </div>
          <button className="btn-ghost !border-0 !border-l" onClick={() => setMin(!min)} aria-label="Toggle tray">{min ? '⌃' : '⌄'}</button>
        </div>
        {!min && (
          <div className="thin-scroll overflow-auto flex" style={{ maxHeight: 'min(30vh, 300px)', maxWidth: '100%' }}>
            {a.docked.map((c) => (
              <div key={c} className={`w-[320px] flex-none px-3.5 py-3 border-l first:border-l-0 border-white/10 ${active === c ? '' : 'opacity-90'}`}>
                <div className="eyebrow mb-1.5">{CARD_META[c].eyebrow}</div>
                <CardBody id={c} compact />
              </div>
            ))}
          </div>
        )}
      </Hud>
    </div>
  );
}
