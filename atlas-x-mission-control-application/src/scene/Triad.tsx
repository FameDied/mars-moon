import { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import { DoubleSide, QuadraticBezierCurve3, Shape, ShapeGeometry, Vector2, Vector3, type Group, type Mesh } from 'three';
import { latLonToUnit, type BaseTopologyTriad, type BodyId, type PlanetarySite } from '../data/atlasData';
import { surfaceBasis } from './HexLayer';
import { motion } from './layout';
import { Tag } from './Tag';

const KS = 0.13; // exaggerated km → world scale (schematic inset)
const COLORS = { pad: '#F59E0B', hab: '#38BDF8', isru: '#10B981' } as const;
const LABEL = { pad: 'H_pad', hab: 'H_hab', isru: 'H_isru' } as const;
const SUB = { pad: 'LANDING PAD', hab: 'HABITAT CORE', isru: 'ISRU MINING' } as const;

export function Triad({ triad, site, body, R, center }: { triad: BaseTopologyTriad; site: PlanetarySite; body: BodyId; R: number; center: Vector3 }) {
  const grp = useRef<Group>(null);
  const rover = useRef<Mesh>(null);
  const haulRef = useRef<{ material: { dashOffset: number } } | null>(null);
  const psiRef = useRef<{ material: { dashOffset: number } } | null>(null);
  const [shown, setShown] = useState(false);
  const appear = useRef(0);

  const n = useMemo(() => new Vector3(...latLonToUnit(body, site.lat, site.lon)), [body, site]);
  const basis = useMemo(() => surfaceBasis(n), [n]);
  const cells = useMemo(
    () => triad.cells.map((c) => {
      const pts = c.vertsKm.map(([x, y]) => new Vector3(x * KS, y * KS, 0));
      const shape = new Shape(c.vertsKm.map(([x, y]) => new Vector2(x * KS, y * KS)));
      return { ...c, geo: new ShapeGeometry(shape), pts: [...pts, pts[0]], c3: new Vector3(c.centerKm[0] * KS, c.centerKm[1] * KS, 0) };
    }),
    [triad],
  );
  const pad = cells.find((c) => c.role === 'pad')!;
  const hab = cells.find((c) => c.role === 'hab')!;
  const isru = cells.find((c) => c.role === 'isru')!;
  const psi = useMemo(() => {
    const r = triad.psiRadiusKm * KS;
    return Array.from({ length: 121 }, (_, i) => new Vector3(Math.cos((i / 120) * Math.PI * 2) * r, Math.sin((i / 120) * Math.PI * 2) * r, 0.002));
  }, [triad]);
  const curve = useMemo(() => {
    const mid = isru.c3.clone().add(hab.c3).multiplyScalar(0.5);
    // bow away from the pad so the haul reads as a distinct route
    const away = mid.clone().sub(pad.c3).normalize().multiplyScalar(0.07);
    return new QuadraticBezierCurve3(isru.c3.clone().setZ(0.004), mid.add(away).setZ(0.004), hab.c3.clone().setZ(0.004));
  }, [isru, hab, pad]);
  const haulPts = useMemo(() => curve.getPoints(40), [curve]);

  useFrame(({ clock }, dt) => {
    const want = motion.dist[body] < R * 3.9 && motion.rig.to === body;
    appear.current += ((want ? 1 : 0) - appear.current) * (1 - Math.exp(-dt * 7));
    const vis = appear.current > 0.02;
    if (grp.current) {
      grp.current.visible = vis;
      grp.current.scale.setScalar(0.5 + 0.5 * appear.current);
    }
    if (vis !== shown && (appear.current > 0.7 || !vis)) setShown(vis);
    if (haulRef.current) haulRef.current.material.dashOffset -= dt * 0.22;
    if (psiRef.current) psiRef.current.material.dashOffset += dt * 0.05;
    if (rover.current) {
      const t = (clock.elapsedTime * 0.18) % 1;
      rover.current.position.copy(curve.getPoint(t));
    }
  });

  return (
    <group ref={grp} position={n.clone().multiplyScalar(R * 1.008)} quaternion={basis.quat} visible={false}>
      {cells.map((c) => (
        <group key={c.role}>
          <mesh geometry={c.geo} renderOrder={6} raycast={() => null}>
            <meshBasicMaterial color={COLORS[c.role]} transparent opacity={0.26} depthWrite={false} side={DoubleSide} toneMapped={false} polygonOffset polygonOffsetFactor={-6} />
          </mesh>
          <Line points={c.pts} color={COLORS[c.role]} lineWidth={2} transparent depthWrite={false} renderOrder={7} />
          <Tag position={[c.c3.x, c.c3.y, 0.01]} center={center} show={shown}>
            <div className="triad-label" style={{ borderColor: COLORS[c.role], color: COLORS[c.role] }}>
              <b>{LABEL[c.role]}</b>
              <span>{SUB[c.role]}</span>
            </div>
          </Tag>
        </group>
      ))}
      <Line ref={psiRef as never} points={psi} color="#F59E0B" lineWidth={1.6} dashed dashSize={0.02} gapSize={0.014} transparent opacity={0.95} depthWrite={false} renderOrder={8} />
      <Tag position={[0, -triad.psiRadiusKm * KS - 0.012, 0.01]} center={center} show={shown}>
        <span className="tag-chip tag-amber">1.5 km PSI blast-safe radius</span>
      </Tag>
      <Line ref={haulRef as never} points={haulPts} color="#E6FFF5" lineWidth={2.4} dashed dashSize={0.03} gapSize={0.022} transparent depthWrite={false} renderOrder={9} />
      <mesh ref={rover} renderOrder={10} raycast={() => null}>
        <circleGeometry args={[0.018, 16]} />
        <meshBasicMaterial color="#ffffff" depthWrite={false} toneMapped={false} />
      </mesh>
      <Tag position={[curve.getPoint(0.5).x, curve.getPoint(0.5).y, 0.01]} center={center} show={shown} offset={-40}>
        <span className="tag-chip tag-go" style={{ fontSize: 10.5 }}>ROVER HAUL ▸ {triad.haul.plainEnglish}</span>
      </Tag>
    </group>
  );
}
