import { cellData, categories } from '../data/cellData.js';

/**
 * StructureIndex — lists every structure that is BOTH in cellData and present
 * in the loaded scene, grouped by category. Lets users reach small cells
 * without hunting for them in 3D.
 */
export default function StructureIndex({ presentIds, selectedId, onPick }) {
  const groups = Object.entries(categories)
    .map(([key, label]) => ({
      key,
      label,
      ids: presentIds.filter((id) => cellData[id]?.category === key),
    }))
    .filter((g) => g.ids.length);

  const uncategorized = presentIds.filter((id) => !categories[cellData[id]?.category]);
  if (uncategorized.length) groups.push({ key: 'other', label: 'Other', ids: uncategorized });

  if (!groups.length) return null;

  return (
    <nav className="pointer-events-auto w-60 rounded-xl bg-slate-950/70 p-3 ring-1 ring-white/10 backdrop-blur-md">
      {groups.map((g) => (
        <div key={g.key} className="mb-2 last:mb-0">
          <p className="px-2 pb-1 pt-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{g.label}</p>
          <ul>
            {g.ids.map((id) => (
              <li key={id}>
                <button
                  onClick={() => onPick(id)}
                  className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition ${
                    id === selectedId ? 'bg-amber-300/10 text-amber-100' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: cellData[id].color }} />
                  <span className="truncate">{cellData[id].title}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
