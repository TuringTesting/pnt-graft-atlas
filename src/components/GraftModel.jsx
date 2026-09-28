import { useEffect } from 'react';
import { useGLTF } from '@react-three/drei';
import { useSceneRescan } from './InteractiveLayer.jsx';

/**
 * Loads the .glb and drops its scene graph in as-is. All interactivity is
 * handled by <InteractiveLayer>, so this component stays a dumb loader.
 * For large files, enable Draco:  useGLTF(url, true)
 */
export default function GraftModel({ url, onLoaded }) {
  const { scene } = useGLTF(url);
  const rescan = useSceneRescan();

  useEffect(() => {
    rescan();
    onLoaded?.();
  }, [scene, rescan, onLoaded]);

  return <primitive object={scene} />;
}
