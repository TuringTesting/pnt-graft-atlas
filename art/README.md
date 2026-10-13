# Art pipeline (Blender → web)

This folder holds the **source** of the 3D model. The web app only ever reads the exported
`public/models/graft_environment.glb`.

| File | What it is |
|------|------------|
| `graft_environment.blend` | The Blender working file — the thing you edit |
| `build_procedural_scene.py` | **Main model.** Procedural graft + SN scene with full cell populations; builds, tags and exports in one run (in a **new** file saved in `art/`) |
| `build_starter_scene.py` | Earlier, simpler starter scene (horizontal graft); kept for reference |
| `export_glb.py` | Exports the open `.blend` to `public/models/graft_environment.glb` with the right settings |

## The one rule

Every object you want clickable has a **custom property `id`** whose value is a key in
`src/data/cellData.js` (e.g. `repair_schwann_cell`). Duplicating an object (Shift+D / Alt+D)
copies its `id`. Objects without an `id` still render — they're just not clickable.
Object *names* don't matter to the app; keep them readable.

## Conventions

- **Axes:** the graft runs along Blender's **Z** axis (vertical), centred on the origin. The exporter
  converts Blender's Z-up to the web's Y-up, so the graft stands upright in the app.
- **Scale:** 1 Blender metre = 1 app unit. Graft ≈ 6.5 m tall, 0.72 m radius; host volume ≈ 9.6 m wide × 8 m tall.
  Staying near this size keeps the app's "Reset view" framing right.
- **One cell = one object.** Each cell's soma and processes are joined into a single mesh carrying the `id`,
  so clicking any part of it selects the whole cell.
- **Collections / parent empties** (`Schwann_Cells`, `Microglia`, …) are organisation only; the app ignores them.
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
