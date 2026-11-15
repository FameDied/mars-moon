import { useAtlas, type CardId } from '../state/AtlasContext';
import { CardFrame, Hud } from './Hud';
import { PowerBody, RadarBody, ShieldBody, SiteBriefBody } from './cards';

export const CARD_META: Record<CardId, { title: string; eyebrow: string; tab: string }> = {
  brief: { title: 'Site Brief', eyebrow: '01 · Plain-English Takeaway', tab: 'SITE BRIEF' },
  radar: { title: 'Split-Twin Radar', eyebrow: '02 · Earth Analog Coverage', tab: 'SPLIT-TWIN' },
  shield: { title: 'Lava Tube Shield Simulator', eyebrow: '03 · Hardware Limits', tab: 'TUBE SHIELD' },
  power: { title: 'Survival & Power Sizing', eyebrow: '04 · Permanent Presence', tab: 'POWER' },
};
export const CARD_ORDER: CardId[] = ['brief', 'radar', 'shield', 'power'];

export function CardBody({ id, compact = false }: { id: CardId; compact?: boolean }) {
  const a = useAtlas();
  if (!a.dataset || !a.selected) return <div className="mono text-[11px] text-[#7c8797] py-6 text-center">Loading dataset…</div>;
  const body = a.selected.body;
  switch (id) {
    case 'brief': return <SiteBriefBody site={a.selected} ev={a.evalMap.get(a.selected.id)} weights={a.weights} />;
    case 'radar': return a.twin ? <RadarBody dataset={a.dataset} body={body} twin={a.twin} openOnly={a.openOnly} setOpenOnly={a.setOpenOnly} compact={compact} /> : null;
    case 'shield': return <ShieldBody site={a.selected} tube={a.tube} setTube={a.setTube} />;
    case 'power': return <PowerBody dataset={a.dataset} body={body} />;
  }
}

export function Inspector() {
  const a = useAtlas();
  const visible = CARD_ORDER.filter((c) => !a.docked.includes(c));
  const on = a.stage === 'workspace';
  return (
    <div
      data-tour="telemetry"
      className="absolute right-4 top-[60px] w-[340px] transition-all duration-[900ms]"
      style={{ transform: on ? 'none' : 'translateX(380px)', opacity: on ? 1 : 0, transitionDelay: on ? '1000ms' : '0ms', transitionTimingFunction: 'var(--ease)', pointerEvents: on ? 'auto' : 'none' }}
    >
      <Hud>
        <div className="flex items-center justify-between px-3.5 h-9 border-b border-white/10">
          <span className="eyebrow !text-[#c4ccd8]">Telemetry Inspector</span>
          <button className="btn-ghost !px-2 !py-[2px]" onClick={() => a.setRightOpen(!a.rightOpen)} aria-label="Toggle inspector">{a.rightOpen ? '⌃' : '⌄'}</button>
        </div>
        {a.rightOpen && (
          <div className="thin-scroll overflow-y-auto" style={{ maxHeight: 'min(calc(100vh - 150px), 640px)' }}>
            {visible.length === 0 && <div className="mono text-[11px] text-[#7c8797] p-5 text-center">All cards docked to tray ↓</div>}
            {visible.map((c) => (
              <CardFrame key={c} title={CARD_META[c].title} eyebrow={CARD_META[c].eyebrow} onDock={() => a.dock(c)}>
                <CardBody id={c} />
              </CardFrame>
            ))}
          </div>
        )}
      </Hud>
    </div>
  );
}
