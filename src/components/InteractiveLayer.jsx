import { createContext, useCallback, useContext, useEffect, useRef } from 'react';
import { Color } from 'three';
import { cellData } from '../data/cellData.js';
import { resolveMeshId } from '../lib/resolveMeshId.js';

const RescanContext = createContext(() => {});
/** Scene components call this after their meshes mount so the layer can index them. */
export const useSceneRescan = () => useContext(RescanContext);

const HOVER = new Color('#60a5fa');
const SELECT = new Color('#fbbf24');

/**
 * InteractiveLayer — wraps ANY scene (the real .glb or the placeholder) and adds:
 *  - ID resolution on click / hover (via resolveMeshId + cellData)
 *  - click-priority rules so background volumes don't swallow clicks
 *  - emissive highlighting of the hovered / selected structure
 *  - a registry of id -> Object3D[] for programmatic focusing
 */
export default function InteractiveLayer({ children, selectedId, hoveredId, onHover, onSelect, onRegistry }) {
  const group = useRef();
  const meshes = useRef([]); // [{ mesh, id }]

  const rescan = useCallback(() => {
    const root = group.current;
    if (!root) return;
    const list = [];
    const registry = new Map();
    const materialCache = new Map(); // `${materialUuid}:${id}` -> cloned material

    root.traverse((obj) => {
      if (!obj.isMesh) return;
      const hit = resolveMeshId(obj);
      if (!hit) return;

      // Give each (material, id) pair its own material so highlighting one
      // structure never bleeds into another that shared the original material.
      if (!obj.userData.__cloned) {
        const cloneOne = (m) => {
          const key = `${m.uuid}:${hit.id}`;
          if (!materialCache.has(key)) {
            const c = m.clone();
            c.userData.__baseEmissive = c.emissive ? c.emissive.clone() : null;
            c.userData.__baseIntensity = c.emissiveIntensity ?? 1;
            materialCache.set(key, c);
          }
          return materialCache.get(key);
        };
        obj.material = Array.isArray(obj.material) ? obj.material.map(cloneOne) : cloneOne(obj.material);
        obj.userData.__cloned = true;
      }

      list.push({ mesh: obj, id: hit.id });
      const arr = registry.get(hit.id) ?? [];
      if (!arr.includes(hit.object)) arr.push(hit.object);
      registry.set(hit.id, arr);
    });

    meshes.current = list;
    onRegistry?.(registry);
  }, [onRegistry]);

  useEffect(() => {
    rescan();
  }, [rescan]);

  // Highlight
  useEffect(() => {
    for (const { mesh, id } of meshes.current) {
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      for (const m of mats) {
        if (!m.emissive) continue;
        if (id === selectedId) {
          m.emissive.copy(SELECT);
          m.emissiveIntensity = 0.45;
        } else if (id === hoveredId) {
          m.emissive.copy(HOVER);
          m.emissiveIntensity = 0.35;
        } else {
          if (m.userData.__baseEmissive) m.emissive.copy(m.userData.__baseEmissive);
          m.emissiveIntensity = m.userData.__baseIntensity;
        }
      }
    }
  }, [selectedId, hoveredId]);

  // Pick the nearest foreground structure; fall back to a background volume.
  const pick = (e) => {
    let background = null;
    for (const ix of e.intersections) {
      const hit = resolveMeshId(ix.object);
      if (!hit) continue;
      if (cellData[hit.id]?.pickPriority === 'background') {
        background ??= hit;
        continue;
      }
      return hit;
    }
    return background;
  };

  return (
    <RescanContext.Provider value={rescan}>
      <group
        ref={group}
        onClick={(e) => {
          e.stopPropagation();
          if (e.delta > 5) return; // it was an orbit drag, not a click
          const hit = pick(e);
          if (hit) onSelect?.(hit);
        }}
        onPointerMove={(e) => {
          e.stopPropagation();
          const id = pick(e)?.id ?? null;
          if (id !== hoveredId) onHover?.(id);
        }}
        onPointerOut={() => onHover?.(null)}
      >
        {children}
      </group>
    </RescanContext.Provider>
  );
}
