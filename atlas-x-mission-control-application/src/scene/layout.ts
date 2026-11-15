import { Quaternion, Vector3, type Group } from 'three';
import type { CelestialId } from '../data/atlasData';

export type PoseKey = 'hero' | CelestialId;

export const SUN = new Vector3(1, 0.25, 0.55).normalize();
export const RADII: Record<CelestialId, number> = { earth: 2.4, moon: 1.6, mars: 1.5 };
export const DEFAULT_DIST: Record<CelestialId, number> = { earth: 9.5, moon: 7.2, mars: 7.0 };
export const FWD: Record<CelestialId, Vector3> = {
  earth: new Vector3(0, 0, -1),
  moon: new Vector3(0, 0, -1),
  mars: new Vector3(-0.6, 0, -0.8).normalize(),
};
const UP = new Vector3(0, 1, 0);

/** Place Moon / Mars so that, from their focus camera, Earth floats in the upper-right background. */
function bodyPos(key: 'moon' | 'mars') {
  const f = FWD[key];
  const r = new Vector3().crossVectors(f, UP).normalize();
  const a = 30 - DEFAULT_DIST[key];
  return new Vector3().addScaledVector(f, a).addScaledVector(r, 8).addScaledVector(UP, 5).negate();
}
export const POS: Record<CelestialId, Vector3> = { earth: new Vector3(0, 0, 0), moon: bodyPos('moon'), mars: bodyPos('mars') };

export function poseFor(key: PoseKey, dist: number) {
  if (key === 'hero') return { pos: new Vector3(0, 0, 6), look: new Vector3(0, 3.0, 0) };
  const p = POS[key];
  const pos = p.clone().addScaledVector(FWD[key], -dist);
  pos.y += dist * 0.05;
  return { pos, look: p.clone() };
}

export const camDirFor = (key: CelestialId) => FWD[key].clone().negate().add(new Vector3(0, 0.14, 0)).normalize();

/** Shared mutable scene state (read by UI overlays and by bodies each frame). */
export const motion = {
  groups: {} as Record<string, Group | null>,
  targets: {} as Record<string, Quaternion | null>,
  rig: { to: 'hero' as PoseKey, from: 'hero' as PoseKey, active: false },
  dist: { earth: DEFAULT_DIST.earth, moon: DEFAULT_DIST.moon, mars: DEFAULT_DIST.mars } as Record<CelestialId, number>,
  zoom: { earth: DEFAULT_DIST.earth, moon: DEFAULT_DIST.moon, mars: DEFAULT_DIST.mars } as Record<CelestialId, number>,
  earthScreen: { x: 0.7, y: 0.3, r: 0.05, visible: false },
  userRotated: false,
};

export function centerQuat(group: Group, localNormal: Vector3, key: CelestialId) {
  const nw = localNormal.clone().applyQuaternion(group.quaternion);
  const delta = new Quaternion().setFromUnitVectors(nw, camDirFor(key));
  return delta.multiply(group.quaternion);
}
