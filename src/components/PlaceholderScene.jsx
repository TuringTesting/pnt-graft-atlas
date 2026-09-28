import { useEffect, useMemo } from 'react';
import { CatmullRomCurve3, Quaternion, Vector3 } from 'three';
import { cellData } from '../data/cellData.js';
import { useSceneRescan } from './InteractiveLayer.jsx';

/**
 * PlaceholderScene — a procedural stand-in shown until public/models/graft_environment.glb
 * exists. It is built exactly the way your real model should be tagged: every
 * cell is a named group with userData.id matching a key in cellData.js.
 *
 * Geometry is schematic only (not to scale): graft runs along the X axis.
 */

const GRAFT_LENGTH = 7;
const GRAFT_RADIUS = 0.9;
const UP = new Vector3(0, 1, 0);

// Deterministic RNG so the layout is stable across reloads
function rng(seed) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32);
}
const color = (id) => cellData[id]?.color ?? '#999';
const tag = (id, i) => ({ name: `${id}_${String(i).padStart(3, '0')}`, userData: { id } });

// Point in a cylindrical shell around the X axis
function around(r, rMin, rMax, xSpread = GRAFT_LENGTH / 2 - 0.3) {
  const a = r() * Math.PI * 2;
  const rad = rMin + r() * (rMax - rMin);
  return [(r() * 2 - 1) * xSpread, Math.cos(a) * rad, Math.sin(a) * rad];
}
function randomDir(r) {
  return new Vector3(r() * 2 - 1, r() * 2 - 1, r() * 2 - 1).normalize();
}

/** A soma with radiating processes — used for neurons, microglia, astrocytes. */
function Ramified({ id, index, position, somaRadius, processes, processLength, processRadius, somaGeometry = 'sphere', r }) {
  const procs = useMemo(
    () =>
      Array.from({ length: processes }, () => {
        const dir = randomDir(r);
        const len = processLength * (0.6 + r() * 0.6);
        return {
          quaternion: new Quaternion().setFromUnitVectors(UP, dir),
          position: dir.clone().multiplyScalar(somaRadius + len / 2).toArray(),
          len,
        };
      }),
    [] // eslint-disable-line react-hooks/exhaustive-deps
  );
  return (
    <group position={position} {...tag(id, index)}>
      <mesh>
        {somaGeometry === 'ico' ? <icosahedronGeometry args={[somaRadius, 0]} /> : <sphereGeometry args={[somaRadius, 16, 16]} />}
        <meshStandardMaterial color={color(id)} roughness={0.55} />
      </mesh>
      {procs.map((p, i) => (
        <mesh key={i} position={p.position} quaternion={p.quaternion}>
          <cylinderGeometry args={[processRadius * 0.4, processRadius, p.len, 6]} />
          <meshStandardMaterial color={color(id)} roughness={0.6} />
        </mesh>
      ))}
    </group>
  );
}

export default function PlaceholderScene() {
  const rescan = useSceneRescan();
  useEffect(() => {
    rescan();
  }, [rescan]);

  const layout = useMemo(() => {
    const r = rng(42);
    return {
      schwann: Array.from({ length: 48 }, () => ({ pos: around(r, 0.15, 0.78), rot: (r() - 0.5) * 0.3 })),
      axons: Array.from({ length: 14 }, () => {
        const a = r() * Math.PI * 2, rad = r() * 0.7;
        return [0, Math.cos(a) * rad, Math.sin(a) * rad];
      }),
      macrophages: Array.from({ length: 14 }, () => around(r, 0, 0.75)),
      fibroblasts: Array.from({ length: 10 }, () => ({ pos: around(r, 0.2, 0.8), rot: r() * Math.PI })),
      vessels: Array.from({ length: 3 }, (_, k) => {
        const pts = [];
        const phase = r() * Math.PI * 2;
        for (let i = 0; i <= 6; i++) {
          const x = -GRAFT_LENGTH / 2 - 1 + (i / 6) * (GRAFT_LENGTH + 2);
          const a = phase + i * 0.6;
          const rad = i === 0 || i === 6 ? 2.2 : 0.5 + 0.3 * Math.sin(i + k);
          pts.push(new Vector3(x, Math.cos(a) * rad, Math.sin(a) * rad));
        }
        return new CatmullRomCurve3(pts);
      }),
      neurons: Array.from({ length: 26 }, () => around(r, 1.8, 4.2, GRAFT_LENGTH / 2 + 0.5)),
      microglia: Array.from({ length: 30 }, () => around(r, 1.1, 4.5, GRAFT_LENGTH / 2 + 0.8)),
      astrocytes: Array.from({ length: 22 }, () => around(r, 1.05, 1.5)),
      r,
    };
  }, []);

  return (
    <group>
      {/* Host tissue context — translucent, click-through (pickPriority: 'background') */}
      <mesh scale={[6.5, 4.8, 5.2]} {...tag('substantia_nigra', 0)}>
        <sphereGeometry args={[1, 48, 32]} />
        <meshStandardMaterial color={color('substantia_nigra')} transparent opacity={0.08} depthWrite={false} />
      </mesh>

      {/* Graft sheath */}
      <mesh rotation={[0, 0, Math.PI / 2]} {...tag('pnt_graft', 0)}>
        <cylinderGeometry args={[GRAFT_RADIUS, GRAFT_RADIUS, GRAFT_LENGTH, 48, 1, true]} />
        <meshStandardMaterial color={color('pnt_graft')} transparent opacity={0.18} depthWrite={false} side={2} />
      </mesh>

      {layout.axons.map((p, i) => (
        <mesh key={`ax${i}`} position={p} rotation={[0, 0, Math.PI / 2]} {...tag('graft_axon', i)}>
          <cylinderGeometry args={[0.025, 0.025, GRAFT_LENGTH - 0.2, 6]} />
          <meshStandardMaterial color={color('graft_axon')} roughness={0.4} />
        </mesh>
      ))}

      {layout.schwann.map(({ pos, rot }, i) => (
        <mesh key={`sc${i}`} position={pos} rotation={[rot, 0, Math.PI / 2]} {...tag('repair_schwann_cell', i)}>
          <capsuleGeometry args={[0.06, 0.38, 4, 10]} />
          <meshStandardMaterial color={color('repair_schwann_cell')} roughness={0.5} />
        </mesh>
      ))}

      {layout.macrophages.map((p, i) => (
        <mesh key={`mp${i}`} position={p} {...tag('graft_macrophage', i)}>
          <dodecahedronGeometry args={[0.11, 1]} />
          <meshStandardMaterial color={color('graft_macrophage')} roughness={0.7} />
        </mesh>
      ))}

      {layout.fibroblasts.map(({ pos, rot }, i) => (
        <mesh key={`fb${i}`} position={pos} rotation={[rot, 0, 0]} scale={[0.32, 0.05, 0.09]} {...tag('endoneurial_fibroblast', i)}>
          <sphereGeometry args={[1, 16, 12]} />
          <meshStandardMaterial color={color('endoneurial_fibroblast')} roughness={0.6} />
        </mesh>
      ))}

      {layout.vessels.map((curve, i) => (
        <mesh key={`v${i}`} {...tag('graft_vasculature', i)}>
          <tubeGeometry args={[curve, 80, 0.07, 10, false]} />
          <meshStandardMaterial color={color('graft_vasculature')} roughness={0.35} />
        </mesh>
      ))}

      {layout.neurons.map((p, i) => (
        <Ramified key={`n${i}`} id="nigral_da_neuron" index={i} position={p} somaRadius={0.2} processes={4} processLength={0.9} processRadius={0.035} r={layout.r} />
      ))}

      {layout.microglia.map((p, i) => (
        <Ramified key={`mg${i}`} id="microglia" index={i} position={p} somaRadius={0.07} processes={7} processLength={0.3} processRadius={0.015} r={layout.r} />
      ))}

      {layout.astrocytes.map((p, i) => (
        <Ramified key={`as${i}`} id="astrocyte" index={i} position={p} somaRadius={0.09} processes={9} processLength={0.35} processRadius={0.02} somaGeometry="ico" r={layout.r} />
      ))}
    </group>
  );
}
