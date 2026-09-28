"""
PNT Graft Atlas — one-click export
==================================

Exports the open .blend to  public/models/graft_environment.glb  with the settings the app
needs. Save your .blend inside the repo's  art/  folder first, then:
  Scripting tab > Open > this file > Run Script

Equivalent manual export (File > Export > glTF 2.0):
  Format: glTF Binary (.glb) | Include > Data: Custom Properties ON, Cameras OFF,
  Punctual Lights OFF | Transform: +Y Up ON | Mesh: Apply Modifiers ON
"""

import os

import bpy

USE_COMPRESSION = False  # set True once the file grows past ~10 MB (Draco; the app supports it)

blend_path = bpy.data.filepath
if not blend_path:
    raise RuntimeError("Save your .blend file into the repo's art/ folder first (File > Save As).")

repo_root = os.path.dirname(os.path.dirname(blend_path))
models_dir = os.path.join(repo_root, "public", "models")
if not os.path.isdir(models_dir):
    raise RuntimeError(
        f"Couldn't find {models_dir}.\n"
        "Make sure the .blend is saved in <repo>/art/, e.g. "
        r"C:\Users\aresm\Projects\pnt-graft-atlas\art\graft_environment.blend"
    )

out = os.path.join(models_dir, "graft_environment.glb")

untagged = [o.name for o in bpy.data.objects if o.type == "MESH" and "id" not in o]
if untagged:
    print("Note: these meshes have no 'id' and won't be clickable:", ", ".join(untagged[:20]))

bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    export_extras=True,        # custom properties -> userData.id in the app
    export_yup=True,           # Blender Z-up -> web Y-up
    export_apply=True,         # bake modifiers
    export_cameras=False,
    export_lights=False,       # the app supplies its own lighting
    export_draco_mesh_compression_enable=USE_COMPRESSION,
)

size_mb = os.path.getsize(out) / 1e6
print(f"Exported {out} ({size_mb:.1f} MB)")
if size_mb > 20:
    print("Warning: over 20 MB — consider USE_COMPRESSION = True or simplifying meshes.")
