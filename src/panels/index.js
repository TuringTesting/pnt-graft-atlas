import { lazy } from 'react';

/**
 * Custom panel registry — the escape hatch for rich, bespoke content.
 *
 * Map a key to a lazily-loaded React component, then set
 * `customPanel: '<key>'` on any entry in cellData.js. The component receives
 * { id, entry }. Lazy loading keeps heavy diagrams out of the initial bundle.
 */
export const customPanels = {
  nigrostriatal: lazy(() => import('./NigrostriatalCircuit.jsx')),
};
