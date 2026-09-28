/**
 * Section registry for the info panel.
 *
 * The panel renders these in order; each section decides from the entry
 * whether it has anything to show (return null if not). To support a new
 * kind of content, add a field to cellData.js and a section here — no other
 * file needs to change.
 */
import { Suspense } from 'react';
import { customPanels } from '../../panels/index.js';

const Heading = ({ children }) => (
  <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400">{children}</h3>
);

function Description({ entry }) {
  if (!entry.description?.length) return null;
  return (
    <section className="space-y-3 text-[15px] leading-relaxed text-slate-300">
      {entry.description.map((p, i) => (
        <p key={i}>{p}</p>
      ))}
    </section>
  );
}

function Markers({ entry }) {
  if (!entry.markers?.length) return null;
  return (
    <section>
      <Heading>Markers</Heading>
      <ul className="flex flex-wrap gap-1.5">
        {entry.markers.map((m) => (
          <li key={m.name} className="rounded-md bg-white/5 px-2 py-1 text-xs text-slate-200 ring-1 ring-white/10">
            {m.name}
            {m.note && <span className="ml-1 text-slate-500">· {m.note}</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}

function CustomPanel({ entry, id }) {
  const Panel = entry.customPanel && customPanels[entry.customPanel];
  if (!Panel) return null;
  return (
    <section>
      <Suspense fallback={<div className="h-40 animate-pulse rounded-lg bg-white/5" />}>
        <Panel id={id} entry={entry} />
      </Suspense>
    </section>
  );
}

function CircuitDiagram({ entry }) {
  const url = entry.assets?.circuitDiagramUrl;
  if (!url) return null;
  return (
    <section>
      <Heading>Circuit diagram</Heading>
      <img src={url} alt={`Circuit diagram for ${entry.title}`} className="w-full rounded-lg bg-white/5 ring-1 ring-white/10" />
    </section>
  );
}

function Media({ entry }) {
  const images = entry.assets?.images ?? [];
  const videos = entry.assets?.videos ?? [];
  if (!images.length && !videos.length) return null;
  return (
    <section className="space-y-3">
      <Heading>Media</Heading>
      {images.map((img) => (
        <figure key={img.src}>
          <img src={img.src} alt={img.caption ?? ''} className="w-full rounded-lg ring-1 ring-white/10" />
          {img.caption && <figcaption className="mt-1 text-xs text-slate-500">{img.caption}</figcaption>}
        </figure>
      ))}
      {videos.map((v) => (
        <figure key={v.src}>
          <video src={v.src} controls className="w-full rounded-lg ring-1 ring-white/10" />
          {v.caption && <figcaption className="mt-1 text-xs text-slate-500">{v.caption}</figcaption>}
        </figure>
      ))}
    </section>
  );
}

function Papers({ entry }) {
  if (!entry.papers?.length) return null;
  return (
    <section>
      <Heading>Research</Heading>
      <ul className="space-y-2">
        {entry.papers.map((p) => (
          <li key={p.url}>
            <a
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group block rounded-lg bg-white/[0.03] p-3 ring-1 ring-white/10 transition hover:bg-white/[0.07] hover:ring-amber-300/40"
            >
              <span className="flex items-start justify-between gap-3">
                <span className="text-sm font-medium text-slate-100 group-hover:text-amber-200">{p.title}</span>
                <svg viewBox="0 0 20 20" className="mt-0.5 h-4 w-4 shrink-0 text-slate-500 group-hover:text-amber-200" fill="currentColor" aria-hidden>
                  <path d="M11 3h6v6h-2V6.41l-6.29 6.3-1.42-1.42L13.59 5H11V3zM5 5h4v2H5v8h8v-4h2v6H3V5h2z" />
                </svg>
              </span>
              {(p.authors || p.journal || p.year) && (
                <span className="mt-1 block text-xs text-slate-500">
                  {[p.authors, p.journal, p.year].filter(Boolean).join(' · ')}
                </span>
              )}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

export const sections = [Description, Markers, CustomPanel, CircuitDiagram, Media, Papers];
