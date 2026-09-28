import { cellData, knownIds } from '../data/cellData.js';

// Longest first so "graft_axon" wins over a hypothetical "graft".
const idsByLength = [...knownIds].sort((a, b) => b.length - a.length);

function matchId(candidate) {
  if (!candidate) return null;
  const key = String(candidate).trim();
  if (cellData[key]) return key;
  const lower = key.toLowerCase();
  // Prefix match handles Blender duplicates: "astrocyte.012" (sanitized by
  // three.js to "astrocyte012"), "astrocyte_012", "astrocyte-012".
  return idsByLength.find((id) => lower.startsWith(id)) ?? null;
}

/**
 * Walk from a clicked mesh up through its ancestors and return the first
 * { id, object } that maps to an entry in cellData — `object` is the node that
 * carried the ID, so the camera frames the whole tagged group.
 */
export function resolveMeshId(object) {
  let node = object;
  while (node) {
    const id = matchId(node.userData?.id) ?? matchId(node.name);
    if (id) return { id, object: node };
    node = node.parent;
  }
  return null;
}
