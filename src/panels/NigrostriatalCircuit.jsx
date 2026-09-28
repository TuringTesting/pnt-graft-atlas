/**
 * Example custom panel: a schematic nigrostriatal circuit.
 * Placeholder to show the extension point — replace with your own diagram
 * (hand-built SVG, D3, an embedded Xenium plot, etc.).
 * Highlights the node that corresponds to the selected structure.
 */
export default function NigrostriatalCircuit({ id }) {
  const active = id === 'nigral_da_neuron' ? 'snc' : 'sn';
  const node = (key) =>
    key === active || (active === 'sn' && (key === 'snc' || key === 'snr'))
      ? { fill: 'rgba(251,191,36,0.15)', stroke: '#fbbf24' }
      : { fill: 'rgba(148,163,184,0.08)', stroke: 'rgba(148,163,184,0.5)' };

  return (
    <div>
      <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400">Circuit context</h3>
      <div className="rounded-lg bg-white/[0.03] p-3 ring-1 ring-white/10">
        <svg viewBox="0 0 340 190" className="w-full" role="img" aria-label="Schematic nigrostriatal circuit">
          <defs>
            <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M0 0L10 5L0 10z" fill="#94a3b8" />
            </marker>
          </defs>
          {/* Striatum */}
          <rect x="120" y="14" width="100" height="42" rx="8" fill="rgba(148,163,184,0.08)" stroke="rgba(148,163,184,0.5)" />
          <text x="170" y="40" textAnchor="middle" fontSize="12" fill="#cbd5e1">Striatum</text>
          {/* Thalamus / cortex hint */}
          <rect x="250" y="80" width="80" height="36" rx="8" fill="rgba(148,163,184,0.05)" stroke="rgba(148,163,184,0.35)" />
          <text x="290" y="102" textAnchor="middle" fontSize="11" fill="#94a3b8">Thalamus</text>
          {/* SNc */}
          <rect x="20" y="136" width="110" height="40" rx="8" {...node('snc')} />
          <text x="75" y="160" textAnchor="middle" fontSize="12" fill="#e2e8f0">SNc (DA)</text>
          {/* SNr */}
          <rect x="150" y="136" width="90" height="40" rx="8" {...node('snr')} />
          <text x="195" y="160" textAnchor="middle" fontSize="12" fill="#e2e8f0">SNr</text>

          {/* SNc -> striatum (dopamine) */}
          <path d="M75 136 C 75 90, 130 80, 140 58" fill="none" stroke="#fbbf24" strokeWidth="1.6" markerEnd="url(#arr)" />
          <text x="46" y="98" fontSize="10" fill="#fbbf24">dopamine</text>
          {/* Striatum -> SNr */}
          <path d="M190 56 L 195 134" fill="none" stroke="#94a3b8" strokeWidth="1.3" markerEnd="url(#arr)" />
          <text x="200" y="100" fontSize="10" fill="#94a3b8">GABA</text>
          {/* SNr -> thalamus */}
          <path d="M240 150 C 270 150, 290 135, 290 118" fill="none" stroke="#94a3b8" strokeWidth="1.3" markerEnd="url(#arr)" />
        </svg>
        <p className="mt-2 text-xs text-slate-500">Schematic placeholder — swap in your own circuit diagram component.</p>
      </div>
    </div>
  );
}
