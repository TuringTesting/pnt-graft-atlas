# PNT Graft Atlas

Interactive 3D viewer for an autologous peripheral nerve tissue graft in the substantia nigra.
React + Vite + Tailwind + Three.js / React Three Fiber / drei.

**Live site:** https://YOUR-USERNAME.github.io/pnt-graft-atlas/

## Run locally

```bash
npm install     # once, and again whenever package.json changes
npm run dev     # local preview at http://localhost:5173 — updates on save
```

## Publishing

Every push to `main` rebuilds and publishes the site automatically via
`.github/workflows/deploy.yml` (watch progress in the repo's **Actions** tab).
One-time setup: **Settings → Pages → Source: GitHub Actions**.

To host elsewhere (e.g. a university server), run `npm run build` and upload the
contents of `dist/`. Asset paths are relative, so it works at any address.

## Daily workflow

```bash
git pull                          # get the latest (if you edit on more than one computer)
# ...edit files, check in npm run dev...
git add .
git commit -m "Describe what changed"
git push                          # publishes to the live site in ~1–2 minutes
```

## Dropping in your model

Put your file at `public/models/graft_environment.glb`. Until it exists, a procedural
placeholder scene is shown (and a banner says so).

Each clickable mesh needs an ID that matches a key in `src/data/cellData.js`. Either:

- **Recommended:** in Blender, add a Custom Property named `id` (e.g. `repair_schwann_cell`)
  to the object — or to a parent Empty, and every child inherits it. Export glTF with
  *Include → Custom Properties* checked; it arrives as `userData.id`.
- **Or** name the object so it starts with the ID: `repair_schwann_cell.014`,
  `astrocyte_03`, etc. The resolver prefix-matches, longest ID first.

Meshes with no matching ID are rendered but not clickable.

## Project layout

```
src/
  App.jsx                       selection state, overlays
  data/cellData.js              ALL content: titles, text, markers, papers, asset paths
  lib/resolveMeshId.js          mesh → ID resolution (userData.id, name, parents)
  components/
    GraftCanvas.jsx             <Canvas>, lights, OrbitControls, Suspense, fallback
    GraftModel.jsx              useGLTF loader
    PlaceholderScene.jsx        procedural stand-in (tagged the same way your .glb should be)
    InteractiveLayer.jsx        click/hover picking, highlighting, ID registry
    CameraRig.jsx               eased camera + target tween
    StructureIndex.jsx          left-hand list of structures present in the scene
    panel/InfoPanel.jsx         sliding right panel
    panel/sections.jsx          section registry — one component per content field
  panels/
    index.js                    custom panel registry (lazy-loaded)
    NigrostriatalCircuit.jsx    example custom panel
```

## Extending content

| You want to…                              | Do this |
|-------------------------------------------|---------|
| Add a structure                           | Add an entry to `cellData.js`; tag meshes with its key |
| Add a circuit diagram image               | Set `assets.circuitDiagramUrl: '/assets/foo.svg'` (file in `public/assets/`) |
| Add images / videos                       | Push `{ src, caption }` into `assets.images` / `assets.videos` |
| Add a new *kind* of field (e.g. Xenium gene list) | Add the field to entries, write a section component in `panel/sections.jsx`, add it to the `sections` array |
| Add a fully bespoke interactive panel     | Create a component in `src/panels/`, register it in `panels/index.js`, set `customPanel: '<key>'` on the entry |
| Keep a large volume from blocking clicks  | Set `pickPriority: 'background'` on its entry |
| Tune how close the camera zooms           | `camera: { distanceScale: 1.5 }` on the entry |

All descriptions and paper links in `cellData.js` are placeholders (PubMed search links).
