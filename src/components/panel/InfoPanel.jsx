import { useEffect, useState } from 'react';
import { cellData, categories } from '../../data/cellData.js';
import { sections } from './sections.jsx';

/**
 * InfoPanel — right-hand sliding panel. Fully data-driven: it looks up the
 * selected ID in cellData and renders every registered section.
 * Keeps the last entry mounted while sliding out so content doesn't vanish mid-animation.
 */
export default function InfoPanel({ selectedId, onClose }) {
  const [shownId, setShownId] = useState(selectedId);
  useEffect(() => {
    if (selectedId) setShownId(selectedId);
  }, [selectedId]);

  const open = Boolean(selectedId);
  const entry = shownId ? cellData[shownId] : null;

  return (
    <aside
      aria-hidden={!open}
      className={`pointer-events-auto fixed inset-y-0 right-0 z-20 flex w-full max-w-md flex-col border-l border-white/10 bg-slate-950/85 shadow-2xl backdrop-blur-xl transition-transform duration-300 ease-out ${
        open ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {entry && (
        <>
          <header className="flex items-start gap-3 border-b border-white/10 px-6 pb-5 pt-6">
            <span className="mt-1.5 h-3 w-3 shrink-0 rounded-full ring-2 ring-white/20" style={{ background: entry.color }} />
            <div className="min-w-0 flex-1">
              {entry.category && (
                <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-amber-300/80">
                  {categories[entry.category] ?? entry.category}
                </p>
              )}
              <h2 className="mt-1 text-xl font-semibold leading-tight text-white">{entry.title}</h2>
              {entry.summary && <p className="mt-2 text-sm leading-snug text-slate-400">{entry.summary}</p>}
              <p className="mt-2 font-mono text-[11px] text-slate-600">id: {shownId}</p>
            </div>
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white"
              aria-label="Close panel"
            >
              <svg viewBox="0 0 20 20" className="h-5 w-5" fill="currentColor" aria-hidden>
                <path d="M5.3 4.3a1 1 0 011.4 0L10 7.6l3.3-3.3a1 1 0 111.4 1.4L11.4 9l3.3 3.3a1 1 0 01-1.4 1.4L10 10.4l-3.3 3.3a1 1 0 01-1.4-1.4L8.6 9 5.3 5.7a1 1 0 010-1.4z" />
              </svg>
            </button>
          </header>

          <div className="panel-scroll flex-1 space-y-7 overflow-y-auto px-6 py-6">
            {sections.map((Section, i) => (
              <Section key={i} entry={entry} id={shownId} />
            ))}
          </div>
        </>
      )}
    </aside>
  );
}
