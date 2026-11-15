import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { motion } from './layout';
import { AdditiveBlending, CircleGeometry, Color, DoubleSide, InstancedMesh, Matrix4, Mesh, Object3D, Quaternion, RingGeometry, Vector3 } from 'three';
import { latLonToUnit, type BodyId, type PlanetarySite, type SiteEval } from '../data/atlasData';
import { Tag } from './Tag';

const Y = new Vector3(0, 1, 0);
export function surfaceBasis(n: Vector3) {
  let east = new Vector3().crossVectors(Y, n);
  if (east.lengthSq() < 1e-6) east = new Vector3(1, 0, 0);
  east.normalize();
  const north = new Vector3().crossVectors(n, east);
  return { east, north, quat: new Quaternion().setFromRotationMatrix(new Matrix4().makeBasis(east, north, n)) };
}

const C_GO = new Color('#10B981'), C_NOGO = new Color('#EF4444'), C_SEL = new Color('#38BDF8'), C_TOP = new Color('#B6F5DC');

interface Props {
  body: BodyId;
  R: number;
  sites: PlanetarySite[];
  evalMap: Map<string, SiteEval>;
  selectedId: string | null;
  topId: string | null;
  center: Vector3;
  onSelect: (id: string) => void;
}

export function HexLayer({ body, R, sites, evalMap, selectedId, topId, center, onSelect }: Props) {
  const fill = useRef<InstancedMesh>(null);
  const ring = useRef<InstancedMesh>(null);
  const beaconTop = useRef<Mesh>(null);
  const beaconSel = useRef<Mesh>(null);
  const [hover, setHover] = useState<number | null>(null);
  const [near, setNear] = useState(false);
  const hexR = R * 0.03;
  const geo = useMemo(() => ({ fill: new CircleGeometry(1, 6), ring: new RingGeometry(0.78, 1, 6, 1), beacon: new RingGeometry(0.92, 1, 6, 1) }), []);
  const normals = useMemo(() => sites.map((s) => new Vector3(...latLonToUnit(body, s.lat, s.lon))), [sites, body]);
  const bases = useMemo(() => normals.map(surfaceBasis), [normals]);
  const idxOf = useMemo(() => new Map(sites.map((s, i) => [s.id, i])), [sites]);
  const cur = useRef(new Float32Array(sites.length * 3));
  const tgt = useRef(new Float32Array(sites.length * 3));
  const dirty = useRef(true);

  // geometry placement
  useLayoutEffect(() => {
    const o = new Object3D();
    const selI = selectedId ? idxOf.get(selectedId) : undefined;
    const topI = topId ? idxOf.get(topId) : undefined;
    normals.forEach((n, i) => {
      o.position.copy(n).multiplyScalar(R * 1.003);
      o.quaternion.copy(bases[i].quat);
      const k = i === selI ? 1.5 : i === topI ? 1.3 : 1;
      o.scale.setScalar(hexR * k);
      o.updateMatrix();
      fill.current?.setMatrixAt(i, o.matrix);
      ring.current?.setMatrixAt(i, o.matrix);
    });
    if (fill.current) { fill.current.instanceMatrix.needsUpdate = true; fill.current.computeBoundingSphere(); }
    if (ring.current) ring.current.instanceMatrix.needsUpdate = true;
  }, [normals, bases, selectedId, topId, idxOf, R, hexR]);

  // target colours (GO / NO-GO flip)
  useLayoutEffect(() => {
    const c = new Color();
    sites.forEach((s, i) => {
      const e = evalMap.get(s.id);
      if (s.id === selectedId) c.copy(C_SEL);
      else if (s.id === topId) c.copy(C_TOP);
      else if (e?.go) c.copy(C_GO).multiplyScalar(0.55 + 0.45 * e.u);
      else c.copy(C_NOGO).multiplyScalar(0.7);
      tgt.current.set([c.r, c.g, c.b], i * 3);
    });
    dirty.current = true;
  }, [sites, evalMap, selectedId, topId]);

  useLayoutEffect(() => {
    // allocate instanceColor attributes
    const c = new Color('#ffffff');
    for (let i = 0; i < sites.length; i++) { fill.current?.setColorAt(i, c); ring.current?.setColorAt(i, c); }
    cur.current.set(tgt.current);
  }, [sites]);

  useFrame(({ clock }, dt) => {
    if (dirty.current && fill.current?.instanceColor && ring.current?.instanceColor) {
      const a = 1 - Math.exp(-dt * 11);
      let maxd = 0;
      const cc = cur.current, tt = tgt.current;
      for (let i = 0; i < cc.length; i++) { const d = tt[i] - cc[i]; cc[i] += d * a; maxd = Math.max(maxd, Math.abs(d)); }
      (fill.current.instanceColor.array as Float32Array).set(cc);
      (ring.current.instanceColor.array as Float32Array).set(cc);
      fill.current.instanceColor.needsUpdate = true;
      ring.current.instanceColor.needsUpdate = true;
      if (maxd < 0.002) dirty.current = false;
    }
    const isNear = motion.dist[body] < R * 3.9;
    if (isNear !== near) setNear(isNear);
    const t = clock.elapsedTime;
    const pulse = (m: Mesh | null, i: number | undefined, base: number, speed: number) => {
      if (!m) return;
      if (i === undefined) { m.visible = false; return; }
      m.visible = true;
      m.position.copy(normals[i]).multiplyScalar(R * 1.0045);
      m.quaternion.copy(bases[i].quat);
      const ph = (t * speed) % 1;
      m.scale.setScalar(hexR * (base + ph * 1.6));
      (m.material as { opacity: number }).opacity = 0.9 * (1 - ph);
    };
    pulse(beaconTop.current, topId ? idxOf.get(topId) : undefined, 1.4, 0.55);
    pulse(beaconSel.current, selectedId ? idxOf.get(selectedId) : undefined, 1.7, 0.8);
  });

  const click = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    if (e.delta > 6 || e.instanceId === undefined) return;
    onSelect(sites[e.instanceId].id);
  };
  const hoverSite = hover !== null ? sites[hover] : null;
  const hoverEval = hoverSite ? evalMap.get(hoverSite.id) : null;
  const topSite = topId ? sites[idxOf.get(topId)!] : null;
  const selSite = selectedId ? sites[idxOf.get(selectedId) ?? -1] : null;

  return (
    <group>
      <instancedMesh ref={fill} args={[geo.fill, undefined, sites.length]} renderOrder={2} frustumCulled={false}
        onClick={click}
        onPointerOver={(e) => { e.stopPropagation(); setHover(e.instanceId ?? null); document.body.style.cursor = 'pointer'; }}
        onPointerMove={(e) => { e.stopPropagation(); if (e.instanceId !== undefined) setHover(e.instanceId); }}
        onPointerOut={() => { setHover(null); document.body.style.cursor = ''; }}>
        <meshBasicMaterial transparent opacity={0.34} blending={AdditiveBlending} depthWrite={false} side={DoubleSide} toneMapped={false} polygonOffset polygonOffsetFactor={-2} />
      </instancedMesh>
      <instancedMesh ref={ring} args={[geo.ring, undefined, sites.length]} renderOrder={3} frustumCulled={false} raycast={() => null}>
        <meshBasicMaterial transparent opacity={0.95} depthWrite={false} side={DoubleSide} toneMapped={false} polygonOffset polygonOffsetFactor={-3} />
      </instancedMesh>
      <mesh ref={beaconTop} geometry={geo.beacon} renderOrder={4} raycast={() => null}>
        <meshBasicMaterial color="#B6F5DC" transparent depthWrite={false} side={DoubleSide} toneMapped={false} />
      </mesh>
      <mesh ref={beaconSel} geometry={geo.beacon} renderOrder={4} raycast={() => null}>
        <meshBasicMaterial color="#38BDF8" transparent depthWrite={false} side={DoubleSide} toneMapped={false} />
      </mesh>
      {topSite && topSite.id !== selectedId && (
        <Tag position={normals[idxOf.get(topSite.id)!].clone().multiplyScalar(R * 1.01)} center={center} offset={-22}>
          <span className="tag-chip tag-top">#1 · U {evalMap.get(topSite.id)?.u.toFixed(3)}</span>
        </Tag>
      )}
      {selSite && !near && (
        <Tag position={normals[idxOf.get(selSite.id)!].clone().multiplyScalar(R * 1.01)} center={center} offset={-24}>
          <span className="tag-chip tag-sel">{selSite.shortName}</span>
        </Tag>
      )}
      {hoverSite && hoverSite.id !== selectedId && (
        <Tag position={normals[hover!].clone().multiplyScalar(R * 1.01)} center={center} offset={22}>
          <span className={`tag-chip ${hoverEval?.go ? 'tag-go' : 'tag-nogo'}`}>
            {hoverSite.shortName} · {hoverEval?.go ? 'GO' : 'NO-GO'} · U {hoverEval?.u.toFixed(3)}
          </span>
        </Tag>
      )}
    </group>
  );
}
