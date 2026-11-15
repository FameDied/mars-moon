import { useAtlas } from '../state/AtlasContext';
import { Hud } from './Hud';

export function Callout() {
  const { callout, dismissCallout, stage } = useAtlas();
  if (!callout || stage !== 'workspace') return null;
  const col = { ok: '#10B981', info: '#38BDF8', warn: '#F59E0B' }[callout.tone];
  return (
    <div key={callout.key} className="pointer-events-auto absolute left-1/2 top-[58px] -translate-x-1/2 z-30 w-[min(440px,calc(100vw-760px))] min-w-[300px]" style={{ animation: 'fadeUp .5s var(--ease)' }}>
      <Hud style={{ borderColor: `${col}66` }}>
        <div className="flex items-start gap-3 px-3.5 py-2.5">
          <i className="mt-1 w-1.5 h-1.5 flex-none pulse" style={{ background: col }} />
          <div className="flex-1">
            <div className="mono text-[10px] tracking-[0.12em] uppercase" style={{ color: col }}>{callout.title}</div>
            <div className="text-[12.5px] text-[#d5dbe5] mt-1 leading-[1.45]">{callout.body}</div>
          </div>
          <button className="text-[#7c8797] hover:text-white text-[15px] leading-none" onClick={dismissCallout} aria-label="Dismiss">×</button>
        </div>
      </Hud>
    </div>
  );
}
