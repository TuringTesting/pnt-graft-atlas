"""
PNT Graft Atlas — Blender starter scene
=======================================

Run ONCE in a fresh Blender file (File > New > General):
  Scripting tab > Open > this file > Run Script (or Alt+P with the mouse over the text).

It builds a correctly tagged, correctly scaled starting scene that matches the web app:
  * graft runs along the X axis, centred on the origin, 7 m long, 0.9 m radius
  * every clickable object carries a custom property  id = "<key in cellData.js>"
  * objects are grouped into collections: Host, Interface, Graft
Everything here is a starting point — reshape, sculpt, re-colour and duplicate freely.
The only rule: every object you want clickable keeps an `id` that matches cellData.js.
(Shift+D / Alt+D duplicates copy the id automatically.)

Scale note: 1 Blender metre = 1 scene unit in the app. Keep the overall layout about this
size so the app's fixed "Reset view" camera frames it well.
"""

import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

random.seed(7)  # same layout every run

GRAFT_LENGTH = 7.0
GRAFT_RADIUS = 0.9

# Colours mirror src/data/cellData.js so the model and the UI swatches agree.
PALETTE = {
    "substantia_nigra":       ("#64748b", 0.08),  # (hex colour, alpha)
    "pnt_graft":              ("#e8b04a", 0.20),
    "graft_axon":             ("#fde68a", 1.0),
    "repair_schwann_cell":    ("#f5d06f", 1.0),
    "graft_macrophage":       ("#f97362", 1.0),
    "endoneurial_fibroblast": ("#c4a1ff", 1.0),
    "graft_vasculature":      ("#ef4444", 1.0),
    "nigral_da_neuron":       ("#8b5a2b", 1.0),
    "da_neurite_in_graft":    ("#b07a45", 1.0),
    "microglia":              ("#38bdf8", 1.0),
    "astrocyte":              ("#34d399", 1.0),
}


# ---------------------------------------------------------------------------
# Safety: refuse to run on a file that already has work in it
# ---------------------------------------------------------------------------
DEFAULT_NAMES = {"Cube", "Camera", "Light"}
existing = {o.name for o in bpy.data.objects}
if existing - DEFAULT_NAMES:
    raise RuntimeError(
        "This file already contains objects. Run the starter script only in a new file "
        "(File > New > General) so nothing of yours is deleted."
    )
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def hex_to_rgba(hex_str, alpha=1.0):
    h = hex_str.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # Blender colour sockets are linear; convert from sRGB so colours match the web UI.
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, alpha)


_materials = {}


def material(key, roughness=0.55):
    """One shared material per cell type, named after its id."""
    if key in _materials:
        return _materials[key]
    hex_col, alpha = PALETTE[key]
    mat = bpy.data.materials.new(name=f"mat_{key}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_to_rgba(hex_col)
    bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = "BLENDED"  # translucent in the viewport and on export
        mat.use_backface_culling = False
    mat.diffuse_color = hex_to_rgba(hex_col, alpha)  # colour in Solid viewport mode
    _materials[key] = mat
    return mat


def collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def make_object(name, mesh, cell_id, col, location=(0, 0, 0)):
    """Create an object, tag it with its id, give it its material, put it in a collection."""
    obj = bpy.data.objects.new(name, mesh)
    obj["id"] = cell_id                      # <-- the link to cellData.js
    obj.location = location
    if not mesh.materials:
        mesh.materials.append(material(cell_id))
    col.objects.link(obj)
    return obj


def mesh_from_bmesh(name, build, smooth=True):
    bm = bmesh.new()
    build(bm)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        mesh.shade_smooth()
    return mesh


def ico(bm, radius, subdiv=2, matrix=None):
    geom = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=geom["verts"])
    return geom


def tube_mesh(points, radii, bevel=0.03, resolution=6):
    """A tapered tube through `points` (curve with bevel), baked to a mesh."""
    curve = bpy.data.curves.new("tmp_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    curve.bevel_resolution = 2
    curve.resolution_u = resolution
    curve.use_fill_caps = True
    spline = curve.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for p, co, r in zip(spline.points, points, radii):
        p.co = (*co, 1.0)
        p.radius = r
    spline.use_endpoint_u = True
    spline.order_u = min(4, len(points))
    tmp = bpy.data.objects.new("tmp", curve)
    bpy.context.scene.collection.objects.link(tmp)
    deps = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(tmp.evaluated_get(deps))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(curve)
    return mesh


def merge_meshes(name, meshes, smooth=True):
    """Join several mesh datablocks into one (one cell = one clickable object)."""
    bm = bmesh.new()
    for m in meshes:
        bm.from_mesh(m)  # appends
        bpy.data.meshes.remove(m)
    out = bpy.data.meshes.new(name)
    bm.to_mesh(out)
    bm.free()
    if smooth:
        out.shade_smooth()
    return out


def rand_dir():
    v = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    return v.normalized() if v.length > 1e-6 else Vector((0, 0, 1))


def ramified_cell(name, soma_r, n_processes, length, proc_r, soma_subdiv=2,
                  soma_scale=(1, 1, 1), bias=None):
    """Soma + tapering, slightly wandering processes: neurons, microglia, astrocytes.
    `bias` (a Vector) pulls processes toward a direction, e.g. toward the graft."""
    parts = [mesh_from_bmesh("soma", lambda bm: ico(
        bm, soma_r, soma_subdiv,
        matrix=Matrix.Diagonal((*soma_scale, 1.0))))]
    for _ in range(n_processes):
        d = rand_dir()
        if bias is not None:
            d = (d + bias).normalized()
        L = length * random.uniform(0.6, 1.2)
        start = d * soma_r * 0.8
        mid = start + d * L * 0.5 + rand_dir() * L * 0.15
        end = start + d * L + rand_dir() * L * 0.2
        parts.append(tube_mesh([start, mid, end], [1.0, 0.6, 0.15], bevel=proc_r))
    return merge_meshes(name, parts)


def point_in_graft(r_min, r_max, margin=0.4):
    a = random.uniform(0, math.tau)
    r = random.uniform(r_min, r_max)
    x = random.uniform(-GRAFT_LENGTH / 2 + margin, GRAFT_LENGTH / 2 - margin)
    return Vector((x, math.cos(a) * r, math.sin(a) * r))


def point_around_graft(r_min, r_max, x_extra=0.6):
    return point_in_graft(r_min, r_max, margin=-x_extra)


# ---------------------------------------------------------------------------
# HOST: substantia nigra tissue volume (translucent context, click-through in the app)
# ---------------------------------------------------------------------------
host = collection("Host - substantia nigra")
sn_mesh = mesh_from_bmesh("substantia_nigra", lambda bm: bmesh.ops.create_uvsphere(
    bm, u_segments=48, v_segments=32, radius=1.0))
sn = make_object("substantia_nigra", sn_mesh, "substantia_nigra", host)
sn.scale = (6.5, 5.2, 4.8)

# ---------------------------------------------------------------------------
# GRAFT: the nerve segment itself — an open tube along X
# ---------------------------------------------------------------------------
graft_col = collection("Graft")


def build_graft(bm):
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=GRAFT_RADIUS,
                          radius2=GRAFT_RADIUS, depth=GRAFT_LENGTH)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))


make_object("pnt_graft", mesh_from_bmesh("pnt_graft", build_graft), "pnt_graft", graft_col)

# Axons: gently wavy fibres running the length of the graft
axon_paths = []
for i in range(6):
    a = i / 6 * math.tau + random.uniform(-0.3, 0.3)
    r = random.uniform(0.15, 0.6)
    y0, z0 = math.cos(a) * r, math.sin(a) * r
    pts = [Vector((x, y0 + random.uniform(-0.05, 0.05), z0 + random.uniform(-0.05, 0.05)))
           for x in [-GRAFT_LENGTH / 2 + 0.1 + k * (GRAFT_LENGTH - 0.2) / 5 for k in range(6)]]
    axon_paths.append(pts)
    make_object(f"graft_axon.{i:03d}", tube_mesh(pts, [1] * 6, bevel=0.022),
                "graft_axon", graft_col)

# Repair Schwann cells: ONE mesh, reused by linked duplicates lined up along axons
# (Bands of Büngner). Editing the shared mesh in Edit Mode updates every copy.
schwann_mesh = mesh_from_bmesh("repair_schwann_cell", lambda bm: ico(
    bm, 1.0, 2, matrix=Matrix.Diagonal((0.24, 0.06, 0.05, 1.0))))
n = 0
for pts in axon_paths[:4]:
    for k in range(6):
        x = -GRAFT_LENGTH / 2 + 0.5 + k * 1.1 + random.uniform(-0.1, 0.1)
        # sit just beside the axon at this x
        seg = min(int((x + GRAFT_LENGTH / 2) / GRAFT_LENGTH * 5), 4)
        p = pts[seg].lerp(pts[seg + 1], 0.5)
        obj = make_object(f"repair_schwann_cell.{n:03d}", schwann_mesh, "repair_schwann_cell",
                          graft_col, location=(x, p.y + 0.07, p.z + 0.04))
        obj.rotation_euler = (random.uniform(-0.3, 0.3), 0, random.uniform(-0.08, 0.08))
        n += 1


# Macrophages: lumpy, rounded cells (a noise-displaced sphere)
def build_macrophage(bm):
    ico(bm, 0.11, 3)
    for v in bm.verts:
        v.co *= 1 + random.uniform(-0.12, 0.12)


for i in range(6):
    make_object(f"graft_macrophage.{i:03d}", mesh_from_bmesh("macrophage", build_macrophage),
                "graft_macrophage", graft_col, location=point_in_graft(0.0, 0.7))

# Endoneurial fibroblasts: flat spindles with thin tapering ends
for i in range(5):
    body = mesh_from_bmesh("fb", lambda bm: ico(
        bm, 1.0, 2, matrix=Matrix.Diagonal((0.16, 0.05, 0.025, 1.0))))
    tails = [tube_mesh([Vector((s * 0.14, 0, 0)), Vector((s * 0.3, 0.02, 0)),
                        Vector((s * 0.45, 0, 0.01))], [1, 0.5, 0.1], bevel=0.02)
             for s in (-1, 1)]
    obj = make_object(f"endoneurial_fibroblast.{i:03d}",
                      merge_meshes("endoneurial_fibroblast", [body, *tails]),
                      "endoneurial_fibroblast", graft_col, location=point_in_graft(0.3, 0.8))
    obj.rotation_euler = (random.uniform(0, math.pi), 0, random.uniform(-0.2, 0.2))

# ---------------------------------------------------------------------------
# INTERFACE: vessels entering the graft from the host, astrocytes at the boundary
# ---------------------------------------------------------------------------
iface = collection("Interface")

for i, (side, phase) in enumerate([(-1, 0.4), (1, 2.6)]):
    pts = []
    for k in range(7):
        t = k / 6
        x = side * (GRAFT_LENGTH / 2 + 1.5) * (1 - t) + side * -0.5 * t
        r = 2.4 * (1 - t) ** 1.5 + 0.55
        a = phase + t * 1.2
        pts.append(Vector((x, math.cos(a) * r, math.sin(a) * r)))
    make_object(f"graft_vasculature.{i:03d}",
                tube_mesh(pts, [1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7], bevel=0.06, resolution=10),
                "graft_vasculature", iface)

for i in range(10):
    pos = point_around_graft(GRAFT_RADIUS + 0.12, GRAFT_RADIUS + 0.35, x_extra=0.0)
    inward = Vector((0, -pos.y, -pos.z)).normalized() * 0.8  # endfeet reach toward graft
    make_object(f"astrocyte.{i:03d}",
                ramified_cell("astrocyte", 0.08, 9, 0.35, 0.018, soma_subdiv=1, bias=inward),
                "astrocyte", iface, location=pos)

# ---------------------------------------------------------------------------
# HOST CELLS: DA neurons (with one neurite threading into the graft) and microglia
# ---------------------------------------------------------------------------
for i in range(7):
    pos = point_around_graft(2.0, 4.0)
    make_object(f"nigral_da_neuron.{i:03d}",
                ramified_cell("nigral_da_neuron", 0.2, 5, 0.9, 0.035,
                              soma_scale=(1.3, 1.0, 0.9)),
                "nigral_da_neuron", host, location=pos)
    if i < 3:
        # Neurite from this neuron into the graft, then running along it
        entry_x = pos.x * 0.6
        inside = Vector((entry_x, pos.y * 0.15, pos.z * 0.15))
        along = inside + Vector((1.2 if pos.x < 0 else -1.2, 0.05, -0.05))
        pts = [pos, pos.lerp(inside, 0.45) + rand_dir() * 0.3, inside, along]
        make_object(f"da_neurite_in_graft.{i:03d}",
                    tube_mesh(pts, [1.0, 0.8, 0.6, 0.4], bevel=0.02, resolution=10),
                    "da_neurite_in_graft", host)

for i in range(10):
    make_object(f"microglia.{i:03d}",
                ramified_cell("microglia", 0.07, 7, 0.3, 0.014),
                "microglia", host, location=point_around_graft(1.2, 4.5, x_extra=0.8))

# ---------------------------------------------------------------------------
# Viewport niceties (not exported)
# ---------------------------------------------------------------------------
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type == "VIEW_3D":
        area.spaces[0].shading.type = "MATERIAL"
        area.spaces[0].clip_end = 200

print("PNT Graft Atlas starter scene built:",
      len([o for o in bpy.data.objects if "id" in o]), "tagged objects")
