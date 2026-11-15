import { useEffect, useMemo, useRef, useState, type RefObject } from 'react';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import {
  AdditiveBlending, BackSide, BufferGeometry, Color, DoubleSide, Float32BufferAttribute, Group, Points, PointsMaterial, Quaternion,
  SRGBColorSpace, ShaderMaterial, TextureLoader, Vector3, type Mesh, type Texture,
} from 'three';
import { useLoader } from '@react-three/fiber';
import {
  buildTriad, latLonToUnit, type BodyId, type CelestialId, type EarthAnalog, type PlanetarySite, type SiteEval, type SplitTwinMatch,
} from '../data/atlasData';
import { HexLayer, surfaceBasis } from './HexLayer';
import { Triad } from './Triad';
import { Tag } from './Tag';
import { POS, RADII, SUN, camDirFor, centerQuat, motion } from './layout';
import type { FlyTo } from '../state/AtlasContext';

import earthDayUrl from '../assets/earth_atmos_2048.jpg';
import earthSpecUrl from '../assets/earth_specular_2048.jpg';
import earthNightUrl from '../assets/earth_lights_2048.png';
import earthCloudUrl from '../assets/earth_clouds_1024.png';
import moonUrl from '../assets/moon_1024.jpg';
import marsUrl from '../assets/marsmap1k.jpg';
import marsBumpUrl from '../assets/marsbump1k.jpg';

const srgb = (t: Texture) => { t.colorSpace = SRGBColorSpace; t.anisotropy = 8; t.needsUpdate = true; return t; };

/* ───────────── Starfield ───────────── */
export function Starfield() {
  const pts = useMemo(() => {
    const N = 4200;
    const pos = new Float32Array(N * 3), col = new Float32Array(N * 3);
    let seed = 7;
    const r = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (let i = 0; i < N; i++) {
      const u = r() * 2 - 1, th = r() * Math.PI * 2, s = Math.sqrt(1 - u * u);
      pos.set([s * Math.cos(th) * 700, u * 700, s * Math.sin(th) * 700], i * 3);
      const b = Math.pow(r(), 3.2) * 0.85 + 0.12;
      const tint = r();
      col.set([b * (tint > 0.85 ? 1 : 0.88), b * 0.92, b * (tint < 0.3 ? 1 : 0.9)], i * 3);
    }
    const g = new BufferGeometry();
    g.setAttribute('position', new Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new Float32BufferAttribute(col, 3));
    const p = new Points(g, new PointsMaterial({ size: 1.35, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false, fog: false }));
    p.renderOrder = -10; p.frustumCulled = false;
    return p;
  }, []);
  return <primitive object={pts} />;
}

/* ───────────── Rayleigh limb scattering shell ───────────── */
const ATMO_VERT = /* glsl */ `
varying vec3 vN; varying vec3 vW;
void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position,1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const ATMO_FRAG = /* glsl */ `
uniform vec3 sunDir; uniform vec3 color; uniform float power; uniform float intensity; uniform float limbC;
varying vec3 vN; varying vec3 vW;
void main(){
  vec3 N = normalize(vN); vec3 V = normalize(cameraPosition - vW);
  float f = pow(clamp(-dot(N,V) / limbC, 0.0, 1.0), power);
  float ndl = dot(N, sunDir);
  float lit = smoothstep(-0.30, 0.45, ndl);
  float dusk = (1.0 - smoothstep(0.0, 0.42, ndl)) * smoothstep(-0.32, 0.02, ndl);
  vec3 tint = mix(color, vec3(1.0, 0.52, 0.26), dusk * 0.65);
  gl_FragColor = vec4(tint * f * intensity * (0.12 + lit), 1.0);
}`;

function Atmosphere({ R, scale, color, power, intensity }: { R: number; scale: number; color: string; power: number; intensity: number }) {
  const mat = useMemo(
    () => new ShaderMaterial({
      vertexShader: ATMO_VERT, fragmentShader: ATMO_FRAG, side: BackSide, transparent: true, blending: AdditiveBlending, depthWrite: false,
      uniforms: { sunDir: { value: SUN }, color: { value: new Color(color) }, power: { value: power }, intensity: { value: intensity }, limbC: { value: Math.sqrt(1 - 1 / (scale * scale)) } },
    }),
    [color, power, intensity, scale],
  );
  return (
    <mesh renderOrder={1} raycast={() => null}>
      <sphereGeometry args={[R * scale, 96, 64]} />
      <primitive object={mat} attach="material" />
    </mesh>
  );
}

/* ───────────── Earth day / night shader ───────────── */
const EARTH_VERT = /* glsl */ `
varying vec2 vUv; varying vec3 vN; varying vec3 vW;
void main(){ vUv = uv; vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position,1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const EARTH_FRAG = /* glsl */ `
uniform sampler2D dayMap; uniform sampler2D nightMap; uniform sampler2D specMap; uniform vec3 sunDir;
varying vec2 vUv; varying vec3 vN; varying vec3 vW;
void main(){
  vec3 N = normalize(vN); vec3 V = normalize(cameraPosition - vW);
  float ndl = dot(N, sunDir);
  float dayAmt = smoothstep(-0.06, 0.14, ndl);
  vec3 day = texture2D(dayMap, vUv).rgb;
  vec3 night = texture2D(nightMap, vUv).rgb;
  float oceanSpec = texture2D(specMap, vUv).r;
  vec3 lit = day * (0.035 + 1.10 * max(ndl, 0.0));
  vec3 dark = day * vec3(0.012, 0.02, 0.04) + night * vec3(1.0, 0.74, 0.42) * 1.6;
  vec3 col = mix(dark, lit, dayAmt);
  vec3 H = normalize(sunDir + V);
  float s = pow(max(dot(N, H), 0.0), 85.0) * oceanSpec * smoothstep(0.0, 0.25, ndl);
  col += vec3(0.85, 0.93, 1.0) * s * 0.85;
  float tw = smoothstep(-0.02, 0.08, ndl) * (1.0 - smoothstep(0.08, 0.3, ndl));
  col += vec3(0.55, 0.20, 0.06) * tw * 0.09;
  float fr = pow(1.0 - max(dot(N, V), 0.0), 3.2);
  col += vec3(0.16, 0.42, 1.0) * fr * 0.75 * smoothstep(-0.25, 0.4, ndl);
  gl_FragColor = vec4(col, 1.0);
  #include <colorspace_fragment>
}`;

/* ───────────── shared rotation behaviour ───────────── */
function useBodyMotion(key: CelestialId, ref: RefObject<Group | null>, autoSpeed: () => number) {
  useEffect(() => { motion.groups[key] = ref.current; return () => { motion.groups[key] = null; }; }, [key, ref]);
  useFrame((_, dt) => {
    const g = ref.current; if (!g) return;
    const tq = motion.targets[key];
    if (tq) {
      g.quaternion.slerp(tq, 1 - Math.exp(-dt * 3.4));
      if (g.quaternion.angleTo(tq) < 0.002) { g.quaternion.copy(tq); motion.targets[key] = null; }
    } else {
      const s = autoSpeed();
      if (s) g.rotateY(dt * s);
    }
  });
}

/* ───────────── Earth ───────────── */
interface EarthProps {
  focus: CelestialId; stage: 'hero' | 'workspace';
  analogs: EarthAnalog[]; twin: SplitTwinMatch | null; openOnly: boolean; body: BodyId;
  selectedAnalogId: string | null; onSelectAnalog: (id: string | null) => void; onFocusEarth: () => void;
}

const GOLD = '#F5B83D';

export function EarthBody({ focus, stage, analogs, twin, openOnly, body, selectedAnalogId, onSelectAnalog, onFocusEarth }: EarthProps) {
  const R = RADII.earth;
  const grp = useRef<Group>(null);
  const clouds = useRef<Mesh>(null);
  const [day, spec, night, cloud] = useLoader(TextureLoader, [earthDayUrl, earthSpecUrl, earthNightUrl, earthCloudUrl]);
  useMemo(() => { srgb(day); srgb(night); srgb(cloud); }, [day, night, cloud]);
  const mat = useMemo(() => new ShaderMaterial({
    vertexShader: EARTH_VERT, fragmentShader: EARTH_FRAG,
    uniforms: { dayMap: { value: day }, nightMap: { value: night }, specMap: { value: spec }, sunDir: { value: SUN } },
  }), [day, night, spec]);
  const center = POS.earth;
  const earthFocus = focus === 'earth' && stage === 'workspace';

  // initial orientation: tilt axis + Eurasia/Africa toward camera
  useEffect(() => {
    const g = grp.current; if (!g) return;
    g.quaternion.setFromAxisAngle(new Vector3(0, 0, 1), -0.41);
    g.rotateY(-((90 + 38) * Math.PI) / 180);
  }, []);

  useBodyMotion('earth', grp, () => (earthFocus || motion.userRotated ? 0 : stage === 'hero' ? 0.035 : 0.02));
  useFrame((_, dt) => { if (clouds.current) clouds.current.rotation.y += dt * 0.004; });

  const byId = useMemo(() => new Map(analogs.map((a) => [a.id, a])), [analogs]);
  const A = twin ? byId.get(twin.analogIds[0]) : undefined;
  const B = twin ? byId.get(twin.analogIds[1]) : undefined;
  const nA = useMemo(() => (A ? new Vector3(...latLonToUnit('earth', A.lat, A.lon)) : null), [A]);
  const nB = useMemo(() => (B ? new Vector3(...latLonToUnit('earth', B.lat, B.lon)) : null), [B]);

  // center the globe on the twin midpoint when Earth is focused
  useEffect(() => {
    if (!earthFocus || !grp.current || !nA || !nB) return;
    const mid = nA.clone().add(nB);
    if (mid.lengthSq() < 0.05) mid.copy(nA);
    motion.targets.earth = centerQuat(grp.current, mid.normalize(), 'earth');
    motion.userRotated = false;
  }, [earthFocus, nA, nB]);

  const arc = useMemo(() => {
    if (!nA || !nB) return null;
    const theta = Math.acos(Math.min(1, Math.max(-1, nA.dot(nB))));
    const q = new Quaternion().setFromUnitVectors(nA, nB);
    const id = new Quaternion();
    const k = 0.16 + 0.5 * Math.pow(theta / Math.PI, 0.8);
    const pts: Vector3[] = [];
    for (let i = 0; i <= 96; i++) {
      const t = i / 96;
      const v = nA.clone().applyQuaternion(new Quaternion().slerpQuaternions(id, q, t));
      pts.push(v.multiplyScalar(R * (1.012 + k * Math.sin(Math.PI * t))));
    }
    return pts;
  }, [nA, nB, R]);
  const dashRef = useRef<{ material: { dashOffset: number } } | null>(null);
  useFrame((_, dt) => { if (dashRef.current) dashRef.current.material.dashOffset -= dt * 0.35; });

  const onSphereClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    if (e.delta > 6) return;
    if (stage === 'workspace' && focus !== 'earth') onFocusEarth();
    else onSelectAnalog(null);
  };
  const canFocus = stage === 'workspace' && focus !== 'earth';

  return (
    <group position={POS.earth}>
      <group ref={grp}>
        <mesh onClick={onSphereClick}
          onPointerOver={(e) => { e.stopPropagation(); if (canFocus) document.body.style.cursor = 'pointer'; }}
          onPointerOut={() => { document.body.style.cursor = ''; }}>
          <sphereGeometry args={[R, 128, 96]} />
          <primitive object={mat} attach="material" />
        </mesh>
        <mesh ref={clouds} raycast={() => null}>
          <sphereGeometry args={[R * 1.008, 96, 64]} />
          <meshStandardMaterial map={cloud} alphaMap={cloud} transparent opacity={0.62} depthWrite={false} roughness={1} />
        </mesh>

        {earthFocus && analogs.map((a) => {
          const n = new Vector3(...latLonToUnit('earth', a.lat, a.lon));
          const isTwin = twin?.analogIds.includes(a.id) ?? false;
          const bench = a.fieldAccess === 'remote-sensing-benchmark';
          const dim = bench && openOnly;
          const color = isTwin ? GOLD : bench ? '#9AA7B8' : '#E6EDF5';
          const basis = surfaceBasis(n);
          const sel = selectedAnalogId === a.id;
          return (
            <group key={a.id} position={n.clone().multiplyScalar(R * 1.004)} quaternion={basis.quat}>
              <mesh
                onClick={(e) => { e.stopPropagation(); if (e.delta < 6) onSelectAnalog(sel ? null : a.id); }}
                onPointerOver={(e) => { e.stopPropagation(); document.body.style.cursor = 'pointer'; }}
                onPointerOut={() => { document.body.style.cursor = ''; }}>
                {bench ? <ringGeometry args={[0.05, 0.075, 6]} /> : <circleGeometry args={[0.062, 24]} />}
                <meshBasicMaterial color={color} transparent opacity={dim ? 0.35 : 1} toneMapped={false} side={DoubleSide} depthWrite={false} />
              </mesh>
              {isTwin && (
                <mesh raycast={() => null}>
                  <ringGeometry args={[0.1, 0.118, 40]} />
                  <meshBasicMaterial color={GOLD} transparent opacity={0.8} toneMapped={false} side={DoubleSide} depthWrite={false} />
                </mesh>
              )}
              <Tag position={[0, 0, 0.02]} center={center} offset={-20}>
                <span className={`tag-chip ${isTwin ? 'tag-gold' : bench ? 'tag-bench' : 'tag-silver'}`} style={{ opacity: dim ? 0.55 : 1 }}>
                  {a.name}{bench ? ' · REMOTE-SENSING BENCHMARK' : ''}
                  {sel && (
                    <em> &nbsp;A {a.axes[body].A.toFixed(0)} · B {a.axes[body].B.toFixed(0)} · C {a.axes[body].C.toFixed(0)} · D {a.axes[body].D.toFixed(0)}</em>
                  )}
                </span>
              </Tag>
            </group>
          );
        })}
        {earthFocus && arc && (
          <>
            <Line points={arc} color={GOLD} lineWidth={7} transparent opacity={0.18} depthWrite={false} />
            <Line ref={dashRef as never} points={arc} color={GOLD} lineWidth={2.2} dashed dashSize={0.16} gapSize={0.1} transparent depthWrite={false} />
          </>
        )}
      </group>
      <Atmosphere R={R} scale={1.075} color="#3C86FF" power={2.0} intensity={1.5} />
    </group>
  );
}

/* ───────────── Moon / Mars ───────────── */
interface RockyProps {
  id: BodyId; sites: PlanetarySite[]; evalMap: Map<string, SiteEval>; selectedId: string | null; selected: PlanetarySite | null;
  topId: string | null; flyTo: FlyTo | null; initialSiteId: string; onSelect: (id: string) => void; allSites: PlanetarySite[];
}

export function RockyBody({ id, sites, evalMap, selectedId, selected, topId, flyTo, initialSiteId, onSelect, allSites }: RockyProps) {
  const R = RADII[id];
  const grp = useRef<Group>(null);
  const outer = useRef<Group>(null);
  const [vis, setVis] = useState(false);
  const moonTex = useLoader(TextureLoader, id === 'moon' ? [moonUrl] : [marsUrl, marsBumpUrl]);
  useMemo(() => { srgb(moonTex[0]); }, [moonTex]);
  const bump = id === 'moon' ? moonTex[0] : moonTex[1];
  const center = POS[id];

  useEffect(() => {
    const g = grp.current; const s = allSites.find((x) => x.id === initialSiteId);
    if (!g || !s) return;
    const n = new Vector3(...latLonToUnit(id, s.lat, s.lon));
    g.quaternion.setFromUnitVectors(n, camDirFor(id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useBodyMotion(id, grp, () => 0);

  useEffect(() => {
    if (!flyTo || !grp.current) return;
    const s = allSites.find((x) => x.id === flyTo.siteId);
    if (!s || s.body !== id) return;
    motion.targets[id] = centerQuat(grp.current, new Vector3(...latLonToUnit(id, s.lat, s.lon)), id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flyTo?.nonce]);

  useFrame(() => {
    const want = motion.rig.to === id || (motion.rig.active && motion.rig.from === id);
    if (outer.current) outer.current.visible = want;
    if (want !== vis) setVis(want);
  });

  const triad = useMemo(() => (selected && selected.body === id ? buildTriad(selected) : null), [selected, id]);

  return (
    <group ref={outer} position={POS[id]} visible={false}>
      <group ref={grp}>
        <mesh onClick={(e) => e.stopPropagation()} onPointerOver={(e) => e.stopPropagation()} onPointerMove={(e) => e.stopPropagation()}>
          <sphereGeometry args={[R, 160, 120]} />
          <meshStandardMaterial map={moonTex[0]} bumpMap={bump} bumpScale={id === 'moon' ? 1.6 : 1.2} roughness={0.96} metalness={0} />
        </mesh>
        {vis && (
          <>
            <HexLayer body={id} R={R} sites={sites} evalMap={evalMap} selectedId={selectedId} topId={topId} center={center} onSelect={onSelect} />
            {triad && selected && <Triad triad={triad} site={selected} body={id} R={R} center={center} />}
          </>
        )}
      </group>
      {id === 'mars' && <Atmosphere R={R} scale={1.045} color="#E9A57A" power={2.4} intensity={0.55} />}
    </group>
  );
}

