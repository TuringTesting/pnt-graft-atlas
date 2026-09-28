import { useCallback, useEffect, useState } from 'react';
import GraftCanvas from './components/GraftCanvas.jsx';
import InfoPanel from './components/panel/InfoPanel.jsx';
import StructureIndex from './components/StructureIndex.jsx';
import { cellData } from './data/cellData.js';

/**
 * App — owns selection state and composes the 3D canvas with the HTML overlays.
 * Selection shape: { id, object?, nonce }  (nonce lets you re-fly to the same ID)
 */
export default function App() {
  const [selection, setSelection] = useState(null);
  const [presentIds, setPresentIds] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [homeSignal, setHomeSignal] = useState(0);

  const select = useCallback((id, object = null) => {
    if (!cellData[id]) return;
    setSelection({ id, object, nonce: Date.now() });
  }, []);

  const handleCanvasSelect = useCallback(({ id, object }) => select(id, object), [select]);

  const close = useCallback(() => setSelection(null), []);
  const goHome = useCallback(() => {
    setSelection(null);
    setHomeSignal((n) => n + 1);
  }, []);

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && goHome();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [goHome]);

  return (
    <div className="relative h-full w-full font-sans text-slate-100">
      <GraftCanvas
        selection={selection}
        onSelect={handleCanvasSelect}
        onRegistry={setPresentIds}
        onModelStatus={setModelStatus}
        homeSignal={homeSignal}
      />

      {/* Overlays: pointer-events-none container so the canvas stays interactive */}
      <div className="pointer-events-none absolute inset-0 z-10 flex flex-col justify-between p-5">
        <header className="pointer-events-auto max-w-sm">
          <h1 className="text-lg font-semibold tracking-tight text-white">PNT Graft Atlas</h1>
          <p className="text-sm text-slate-400">Autologous peripheral nerve tissue graft in the substantia nigra</p>
          {modelStatus === 'placeholder' && (
            <p className="mt-2 inline-block rounded-md bg-amber-400/10 px-2 py-1 text-xs text-amber-200 ring-1 ring-amber-300/20">
              Showing placeholder geometry — add <code className="font-mono">public/models/graft_environment.glb</code>
            </p>
          )}
        </header>

        <div className="flex items-end gap-3">
          <StructureIndex presentIds={presentIds} selectedId={selection?.id} onPick={(id) => select(id)} />
          <button
            onClick={goHome}
            className="pointer-events-auto rounded-lg bg-slate-950/70 px-3 py-2 text-sm text-slate-300 ring-1 ring-white/10 backdrop-blur-md transition hover:text-white"
          >
            Reset view
          </button>
        </div>
      </div>

      <InfoPanel selectedId={selection?.id ?? null} onClose={close} />
    </div>
  );
}
