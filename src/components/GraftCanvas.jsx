import { Suspense, useCallback, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import GraftModel from './GraftModel.jsx';
import PlaceholderScene from './PlaceholderScene.jsx';
import InteractiveLayer from './InteractiveLayer.jsx';
import CameraRig from './CameraRig.jsx';
import ModelErrorBoundary from './ModelErrorBoundary.jsx';

// BASE_URL keeps the path correct wherever the site is hosted (see vite.config.js)
export const MODEL_URL = `${import.meta.env.BASE_URL}models/graft_environment.glb`;
const HOME = { position: [9, 5, 11], target: [0, 0, 0] };

/**
 * GraftCanvas — owns everything inside WebGL.
 *
 * Props
 *  selection       { id, object?, nonce } | null  — what to fly to
 *  onSelect(sel)   called with { id, object } when a mesh is clicked
 *  onRegistry(ids) called once the scene is scanned, with the IDs present
 *  onModelStatus   'loaded' | 'placeholder'
 *  homeSignal      number — bump to fly back to the home view
 */
export default function GraftCanvas({ selection, onSelect, onRegistry, onModelStatus, homeSignal }) {
  // id -> Object3D[]; lets the structure index focus things that weren't clicked
  const registry = useRef(new Map());
  const [hoveredId, setHoveredId] = useState(null);

  const handleRegistry = useCallback(
    (map) => {
      registry.current = map;
      onRegistry?.([...map.keys()]);
    },
    [onRegistry]
  );
  // Stable callbacks so the model's mount effect doesn't re-fire on every render
  const handleLoaded = useCallback(() => onModelStatus?.('loaded'), [onModelStatus]);
  const handleModelError = useCallback(() => onModelStatus?.('placeholder'), [onModelStatus]);

  return (
    <Canvas
      camera={{ position: HOME.position, fov: 45, near: 0.01, far: 500 }}
      dpr={[1, 2]}
      gl={{ antialias: true }}
      style={{ cursor: hoveredId ? 'pointer' : 'grab' }}
    >
      <color attach="background" args={['#05070d']} />
      <fog attach="fog" args={['#05070d', 25, 60]} />

      <ambientLight intensity={0.55} />
      <hemisphereLight args={['#cbd5e1', '#1e293b', 0.5]} />
      <directionalLight position={[8, 12, 6]} intensity={1.6} />
      <directionalLight position={[-6, -4, -8]} intensity={0.4} color="#8ab4ff" />

      <Suspense fallback={<Loader />}>
        <InteractiveLayer
          selectedId={selection?.id ?? null}
          hoveredId={hoveredId}
          onHover={setHoveredId}
          onSelect={onSelect}
          onRegistry={handleRegistry}
        >
          <ModelErrorBoundary fallback={<PlaceholderScene />} onError={handleModelError}>
            <GraftModel url={MODEL_URL} onLoaded={handleLoaded} />
          </ModelErrorBoundary>
        </InteractiveLayer>
      </Suspense>

      <OrbitControls makeDefault enableDamping dampingFactor={0.08} minDistance={0.3} maxDistance={60} target={HOME.target} />
      <CameraRig selection={selection} registry={registry} home={HOME} homeSignal={homeSignal} />
    </Canvas>
  );
}

function Loader() {
  return (
    <Html center>
      <div className="whitespace-nowrap rounded-full bg-slate-900/80 px-4 py-2 text-sm text-slate-300 ring-1 ring-white/10">
        Loading model…
      </div>
    </Html>
  );
}
