import { useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Box3, MathUtils, Sphere, Vector3 } from 'three';
import { cellData } from '../data/cellData.js';

const DURATION = 1.1; // seconds
const easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

/**
 * CameraRig — tweens camera position AND the OrbitControls target together,
 * preserving the current viewing direction so the fly-in feels continuous.
 *
 * selection.object present  -> frame that exact object (the one clicked)
 * selection.object missing  -> frame every registered object with that ID
 * Any user drag during a tween cancels it (the user always wins).
 */
export default function CameraRig({ selection, registry, home, homeSignal }) {
  const camera = useThree((s) => s.camera);
  const controls = useThree((s) => s.controls);
  const tween = useRef(null);

  const startTween = (toPos, toTarget) => {
    if (!controls) return;
    tween.current = {
      fromPos: camera.position.clone(),
      fromTarget: controls.target.clone(),
      toPos,
      toTarget,
      t: 0,
    };
  };

  // Fly to selection
  useEffect(() => {
    if (!selection || !controls) return;
    const targets = selection.object ? [selection.object] : registry.current.get(selection.id) ?? [];
    if (!targets.length) return;

    const box = new Box3();
    targets.forEach((o) => box.expandByObject(o));
    if (box.isEmpty()) return;
    const sphere = box.getBoundingSphere(new Sphere());

    const scale = cellData[selection.id]?.camera?.distanceScale ?? 1;
    const fov = MathUtils.degToRad(camera.fov);
    const distance = Math.max((sphere.radius / Math.sin(fov / 2)) * 1.25 * scale, 0.5);

    const dir = camera.position.clone().sub(controls.target);
    if (dir.lengthSq() < 1e-8) dir.set(0, 0, 1);
    dir.normalize();

    startTween(sphere.center.clone().add(dir.multiplyScalar(distance)), sphere.center.clone());
  }, [selection, controls]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fly home
  useEffect(() => {
    if (!homeSignal) return;
    startTween(new Vector3(...home.position), new Vector3(...home.target));
  }, [homeSignal]); // eslint-disable-line react-hooks/exhaustive-deps

  // User interaction cancels an in-flight tween
  useEffect(() => {
    if (!controls) return;
    const cancel = () => (tween.current = null);
    controls.addEventListener('start', cancel);
    return () => controls.removeEventListener('start', cancel);
  }, [controls]);

  useFrame((_, delta) => {
    const tw = tween.current;
    if (!tw || !controls) return;
    tw.t = Math.min(tw.t + delta / DURATION, 1);
    const k = easeInOutCubic(tw.t);
    camera.position.lerpVectors(tw.fromPos, tw.toPos, k);
    controls.target.lerpVectors(tw.fromTarget, tw.toTarget, k);
    controls.update();
    if (tw.t >= 1) tween.current = null;
  });

  return null;
}
