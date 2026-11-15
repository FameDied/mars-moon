import { Suspense, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Quaternion, Vector3 } from 'three';
import { useAtlas } from '../state/AtlasContext';
import { Starfield, EarthBody, RockyBody } from './Bodies';
import { DEFAULT_DIST, POS, RADII, SUN, motion, poseFor, type PoseKey } from './layout';
import type { CelestialId } from '../data/atlasData';

const easeInOutCubic = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const UP = new Vector3(0, 1, 0);

function Rig({ poseKey, onSettled }: { poseKey: PoseKey; onSettled: (k: string) => void }) {
  const { camera, size } = useThree();
  const st = useMemo(() => ({
    init: false, key: poseKey as PoseKey, t0: 0, dur: 1.8, fromPos: new Vector3(), fromLook: new Vector3(), ctrl: new Vector3(), look: new Vector3(), settled: false,
  }), []); // eslint-disable-line react-hooks/exhaustive-deps
  const tmp = useMemo(() => ({ a: new Vector3(), b: new Vector3(), p: new Vector3() }), []);

  useFrame(({ clock }, dt) => {
    (Object.keys(motion.dist) as CelestialId[]).forEach((k) => {
      motion.dist[k] += (motion.zoom[k] - motion.dist[k]) * (1 - Math.exp(-dt * 4.5));
    });
    const distFor = (k: PoseKey) => (k === 'hero' ? 0 : motion.dist[k]);
    if (!st.init) {
      const p = poseFor(poseKey, distFor(poseKey));
      camera.position.copy(p.pos); st.look.copy(p.look); camera.lookAt(p.look);
      st.init = true; st.key = poseKey; motion.rig.to = poseKey; motion.rig.from = poseKey;
      return;
    }
    if (st.key !== poseKey) {
      motion.rig.from = st.key; motion.rig.to = poseKey; motion.rig.active = true;
      st.fromPos.copy(camera.position); st.fromLook.copy(st.look);
      st.t0 = clock.elapsedTime; st.key = poseKey; st.settled = false;
      const target = poseFor(poseKey, distFor(poseKey)).pos;
      st.ctrl.copy(st.fromPos).add(target).multiplyScalar(0.5);
      const span = st.fromPos.distanceTo(target);
      st.ctrl.add(tmp.a.set(span * 0.12, span * 0.1 + 1.2, span * 0.08));
    }
    const to = poseFor(poseKey, distFor(poseKey));
    if (motion.rig.active) {
      const u = Math.min(1, (clock.elapsedTime - st.t0) / st.dur);
      const e = easeInOutCubic(u);
      // quadratic bezier through a lifted control point → damped orbital spline
      tmp.a.copy(st.fromPos).lerp(st.ctrl, e);
      tmp.b.copy(st.ctrl).lerp(to.pos, e);
      camera.position.copy(tmp.a.lerp(tmp.b, e));
      st.look.copy(st.fromLook).lerp(to.look, e);
      if (u >= 1) { motion.rig.active = false; if (!st.settled) { st.settled = true; onSettled(poseKey); } }
    } else {
      camera.position.copy(to.pos); st.look.copy(to.look);
    }
    camera.lookAt(st.look);

    // Earth's projected position/size for onboarding overlays
    tmp.p.copy(POS.earth).project(camera);
    const d = camera.position.distanceTo(POS.earth);
    const fov = ((camera as unknown as { fov: number }).fov * Math.PI) / 360;
    motion.earthScreen.x = (tmp.p.x + 1) / 2;
    motion.earthScreen.y = (1 - tmp.p.y) / 2;
    motion.earthScreen.r = (RADII.earth / Math.max(d, 0.01)) / Math.tan(fov) / 2 * (size.height / size.width);
    motion.earthScreen.visible = tmp.p.z < 1;
  });
  return null;
}

function Controls({ focus, enabled }: { focus: CelestialId; enabled: boolean }) {
  const { gl, camera } = useThree();
  useEffect(() => {
    const el = gl.domElement;
    let drag = false, lx = 0, ly = 0;
    const down = (e: PointerEvent) => { if (!enabled) return; drag = true; lx = e.clientX; ly = e.clientY; };
    const up = () => { drag = false; el.style.cursor = ''; };
    const move = (e: PointerEvent) => {
      if (!drag || !enabled) return;
      const dx = e.clientX - lx, dy = e.clientY - ly; lx = e.clientX; ly = e.clientY;
      if (Math.abs(dx) + Math.abs(dy) > 0) el.style.cursor = 'grabbing';
      const g = motion.groups[focus]; if (!g) return;
      const k = 0.0042 * Math.min(1.3, Math.max(0.12, (motion.dist[focus] / RADII[focus] - 1) / 4));
      const right = new Vector3().setFromMatrixColumn(camera.matrixWorld, 0).normalize();
      g.quaternion.premultiply(new Quaternion().setFromAxisAngle(UP, dx * k)).premultiply(new Quaternion().setFromAxisAngle(right, dy * k));
      motion.targets[focus] = null; motion.userRotated = true;
    };
    const wheel = (e: WheelEvent) => {
      if (!enabled) return;
      e.preventDefault();
      const R = RADII[focus];
      motion.zoom[focus] = Math.min(R * 7.5, Math.max(R * 1.55, motion.zoom[focus] * Math.exp(e.deltaY * 0.0012)));
    };
    el.addEventListener('pointerdown', down); window.addEventListener('pointerup', up); window.addEventListener('pointermove', move);
    el.addEventListener('wheel', wheel, { passive: false });
    return () => {
      el.removeEventListener('pointerdown', down); window.removeEventListener('pointerup', up); window.removeEventListener('pointermove', move);
      el.removeEventListener('wheel', wheel);
    };
  }, [gl, camera, focus, enabled]);
  return null;
}

function Ready({ onReady }: { onReady: () => void }) {
  useEffect(() => { onReady(); }, [onReady]);
  return null;
}

function World() {
  const a = useAtlas();
  const { dataset } = a;
  const poseKey: PoseKey = a.stage === 'hero' ? 'hero' : a.focus;
  const moonSites = useMemo(() => dataset?.sites.filter((s) => s.body === 'moon') ?? [], [dataset]);
  const marsSites = useMemo(() => dataset?.sites.filter((s) => s.body === 'mars') ?? [], [dataset]);

  // reset zoom to the default framing when focus changes; then honour any preset fly-to zoom
  useEffect(() => { motion.zoom[a.focus] = DEFAULT_DIST[a.focus]; }, [a.focus]);
  useEffect(() => {
    if (!a.flyTo) return;
    const s = dataset?.sites.find((x) => x.id === a.flyTo!.siteId);
    if (!s) return;
    if (a.flyTo.zoomRadii) motion.zoom[s.body] = RADII[s.body] * a.flyTo.zoomRadii;
  }, [a.flyTo?.nonce]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <color attach="background" args={['#040609']} />
      <directionalLight position={[SUN.x * 60, SUN.y * 60, SUN.z * 60]} intensity={3.3} />
      <ambientLight intensity={0.1} />
      <Starfield />
      <Rig poseKey={poseKey} onSettled={a.onSettled} />
      <Controls focus={a.focus} enabled={a.stage === 'workspace'} />
      <Suspense fallback={null}>
        <EarthBody
          focus={a.focus} stage={a.stage} analogs={dataset?.analogs ?? []} twin={a.twin} openOnly={a.openOnly} body={a.body}
          selectedAnalogId={a.selectedAnalogId} onSelectAnalog={a.setSelectedAnalogId} onFocusEarth={a.focusEarth}
        />
        {dataset && (
          <>
            <RockyBody id="moon" sites={moonSites} allSites={dataset.sites} evalMap={a.evalMap} selectedId={a.selectedId} selected={a.selected}
              topId={a.topIds.moon} flyTo={a.flyTo} initialSiteId={dataset.meta.defaultSiteId.moon} onSelect={a.selectSite} />
            <RockyBody id="mars" sites={marsSites} allSites={dataset.sites} evalMap={a.evalMap} selectedId={a.selectedId} selected={a.selected}
              topId={a.topIds.mars} flyTo={a.flyTo} initialSiteId={dataset.meta.defaultSiteId.mars} onSelect={a.selectSite} />
          </>
        )}
        <Ready onReady={a.onSceneReady} />
      </Suspense>
    </>
  );
}

export default function Scene() {
  return (
    <div className="absolute inset-0 z-0 isolate" data-tour="globe-layer">
      <Canvas flat dpr={[1, 2]} camera={{ fov: 45, near: 0.05, far: 2000, position: [0, 0, 6] }} gl={{ antialias: true, powerPreference: 'high-performance' }} style={{ touchAction: 'none' }}>
        <World />
      </Canvas>
    </div>
  );
}
