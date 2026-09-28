# Art pipeline (Blender → web)

This folder holds the **source** of the 3D model. The web app only ever reads the exported
`public/models/graft_environment.glb`.

| File | What it is |
|------|------------|
| `graft_environment.blend` | The Blender working file — the thing you edit |
| `build_starter_scene.py` | Builds a correctly tagged starter scene in a **new** Blender file (run once) |
| `export_glb.py` | Exports the open `.blend` to `public/models/graft_environment.glb` with the right settings |

## The one rule

Every object you want clickable has a **custom property `id`** whose value is a key in
`src/data/cellData.js` (e.g. `repair_schwann_cell`). Duplicating an object (Shift+D / Alt+D)
copies its `id`. Objects without an `id` still render — they're just not clickable.
Object *names* don't matter to the app; keep them readable.

## Conventions

- **Axes:** the graft runs along Blender's **X** axis, centred on the origin. Blender is Z-up;
  the exporter converts to the web's Y-up automatically.
- **Scale:** 1 Blender metre = 1 app unit. Graft ≈ 7 m long, 0.9 m radius; host volume ≈ 13 × 10 × 10 m.
  Staying near this size keeps the app's "Reset view" framing right.
- **Collections:** `Host - substantia nigra`, `Interface`, `Graft` — organisation only; not used by the app.
- **Materials:** use the **Principled BSDF** only — Base Color, Roughness, Metallic, Alpha, and image textures
  export. Procedural texture nodes (Noise, Voronoi…) do **not** export unless baked to an image.
- **Translucent objects:** Principled BSDF → Alpha < 1, and Material → Settings → Render Method: **Blended**.
- **Budget:** keep the `.glb` under ~20 MB and the scene under ~500k triangles
  (Viewport Overlays ▾ → Statistics). Linked duplicates (Alt+D) are almost free.

## Loop

1. Edit in Blender, **Ctrl+S**.
2. Scripting tab → run `export_glb.py`.
3. Refresh the browser tab running `npm run dev` (F5).
4. `git add .` → `git commit -m "..."` → `git push`.

## Adding a new structure (e.g. perineurium)

1. Model it in Blender and give it `id = perineurium`.
2. Add a `perineurium: { title, category, color, ... }` entry to `src/data/cellData.js`.
3. Export, check locally, commit.
