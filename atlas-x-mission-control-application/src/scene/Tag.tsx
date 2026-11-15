import { useMemo, useRef, type ReactNode } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { Vector3, type Group } from 'three';

/** HTML label pinned to a surface point; fades when the point rotates behind the limb. */
export function Tag({ position, center, show = true, children, offset = 0 }: {
  position: [number, number, number] | Vector3;
  center: Vector3;
  show?: boolean;
  children: ReactNode;
  offset?: number;
}) {
  const anchor = useRef<Group>(null);
  const el = useRef<HTMLDivElement>(null);
  const v = useMemo(() => new Vector3(), []);
  const n = useMemo(() => new Vector3(), []);
  const c = useMemo(() => new Vector3(), []);
  useFrame(({ camera }) => {
    if (!anchor.current || !el.current) return;
    anchor.current.getWorldPosition(v);
    n.copy(v).sub(center).normalize();
    c.copy(camera.position).sub(v).normalize();
    const facing = n.dot(c) > 0.2;
    el.current.style.opacity = show && facing ? '1' : '0';
  });
  const p = position instanceof Vector3 ? position.toArray() : position;
  return (
    <group ref={anchor} position={p}>
      <Html center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div ref={el} style={{ transition: 'opacity .25s', opacity: 0, whiteSpace: 'nowrap', marginTop: offset }}>{children}</div>
      </Html>
    </group>
  );
}
