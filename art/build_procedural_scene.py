"""
PNT Graft / Substantia Nigra Procedural Scene Generator
=======================================================

Purpose:
    Generate a procedural, scientifically inspired 3D representation of an
    autologous peripheral nerve tissue (PNT) graft within the substantia nigra.

    The scene includes:
        - Central PNT graft corridor
        - Winding intragraft vasculature
        - Schwann cells
        - Endoneurial fibroblasts
        - Infiltrating macrophages
        - COL1A1+ collagen fibrils
        - Nigral dopaminergic neurons and penetrating neurites
        - Reactive and homeostatic astrocytes
        - Microglia
        - Oligodendrocytes
        - Optional host-volume boundary

    All major components are organized under named parent empties for
    straightforward visibility toggling in a Three.js / React application.

Compatibility:
    Blender 4.2+ (tested on Blender 5.0)

Export:
    <repo>/public/models/graft_environment.glb   (read directly by the web app)

Scientific note:
    This is a procedural anatomical visualization, not a histologically
    validated reconstruction. Cell morphology, densities, and spatial
    distributions are illustrative and can be calibrated against imaging data.

Usage:
    1. Open Blender > File > New > General.
    2. File > Save As >  <repo>/art/graft_environment.blend
       (saving FIRST lets the script export straight into the app).
    3. Scripting tab > Open > art/build_procedural_scene.py
    4. Adjust CONFIG values below if desired.
    5. Run Script. Wait for "PNT GRAFT SCENE GENERATED" in the console
       (Window > Toggle System Console on Windows).

ADAPTATIONS FOR THE PNT GRAFT ATLAS WEB APP
-------------------------------------------
The biology, geometry and parameters are unchanged. What was added:

    * Every clickable structure carries a custom property `id` that matches
      a key in src/data/cellData.js (see APP_IDS below). This is what the
      app uses to open the right info panel and fly the camera.
    * One cell = one object. Each cell's parts (soma, processes, branches,
      vacuoles) are baked from curves to mesh and joined into a single
      object, so clicking any part of a cell selects and frames that whole
      cell. This also cuts several thousand objects down to a few hundred,
      which keeps the model fast on phones.
    * Penetrating neurites become their own clickable structure
      (`da_neurite_in_graft`); host-directed neurites stay part of their
      parent neuron.
    * All COL1A1 fibrils form one clickable collagen structure.
    * Reactive and homeostatic astrocytes are named distinctly.
    * Transparent materials use Blender's "Blended" render method, which the
      glTF exporter writes as true transparency.
    * Bug fix: the original parenting helper reset every sphere-based cell
      (Schwann cells, somata, macrophages, fibroblast bodies, paddles) to a
      full-size radius-1 sphere. Cells now keep their intended size.
    * Speed: spheres are built directly as mesh data instead of with
      Blender's "add primitive" operators (identical geometry; the full
      scene now builds in well under a minute instead of ~6 minutes).
    * The script refuses to run on a file that already has work in it.
    * The GLB is exported into the app's public/models folder automatically
      when the .blend is saved in the repo's art/ folder.

Orientation: the graft runs along Blender's Z axis, which the exporter
converts to the web's vertical (Y) axis, so the graft stands upright in
the app.
"""

import bpy
import bmesh
import itertools
import math
import random
import os

from mathutils import Vector
from math import sin, cos, pi, exp, sqrt


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    "seed": 42,

    # Overall anatomical scale in Blender units.
    # The graft runs along the Z axis.
    "graft_radius": 0.72,
    "graft_height": 6.5,
    "host_radius": 4.8,
    "host_height": 8.0,

    # Vascular network.
    "vessel_count": 7,
    "vessel_radius": 0.045,

    # Graft cellular composition.
    "schwann_cell_count": 110,
    "fibroblast_count": 48,
    "macrophage_count": 24,
    "collagen_fibril_count": 220,

    # Host cellular composition.
    "dopaminergic_neuron_count": 9,
    "homeostatic_astrocyte_count": 100,
    "reactive_astrocyte_count": 55,
    "microglia_count": 55,
    "oligodendrocyte_count": 55,

    # Astrocyte phenotype transition distance from graft boundary.
    "reactive_boundary_distance": 0.95,

    # Neurite configuration.
    "neurites_per_neuron": 5,
    "neurite_radius": 0.018,
    "neurite_min_graft_penetration": 0.5,

    # Export configuration.
    "export_filename": "graft_environment.glb",
    "export_apply_modifiers": True,
    "export_animations": False,
    "export_lights": False,
    "export_cameras": False,

    # Set False to omit the transparent host-volume boundary.
    "include_host_boundary": True,

    # Increase for a denser scene, decrease for faster iteration.
    "geometry_subdivisions": 1,
}


random.seed(CONFIG["seed"])


# ============================================================
# WEB APP IDS
# ============================================================
# Each structure type -> its key in src/data/cellData.js.
# Change a value here only together with the matching key in cellData.js.

APP_IDS = {
    "graft_corridor": "pnt_graft",
    "vessel": "graft_vasculature",
    "schwann": "repair_schwann_cell",
    "fibroblast": "endoneurial_fibroblast",
    "macrophage": "graft_macrophage",
    "collagen": "col1a1_collagen",
    "da_neuron": "nigral_da_neuron",
    "penetrating_neurite": "da_neurite_in_graft",
    "reactive_astrocyte": "astrocyte",
    "homeostatic_astrocyte": "homeostatic_astrocyte",
    "microglia": "microglia",
    "oligodendrocyte": "oligodendrocyte",
    "host_volume": "substantia_nigra",
}


# ============================================================
# CELL TAGGING
# ============================================================
# While a cell is being built, every object created is stamped with the
# cell it belongs to. After generation, consolidate_cells() joins each
# cell's parts into one object carrying the app `id`.

_CELL = {"uid": None, "app_id": None}
_cell_counter = itertools.count()


def begin_cell(kind):
    """Start a new cell of the given APP_IDS kind; returns its uid."""
    _CELL["uid"] = next(_cell_counter)
    _CELL["app_id"] = APP_IDS[kind]
    return _CELL["uid"]


def resume_cell(uid, kind):
    """Go back to adding parts to an earlier cell (e.g. a neuron's dendrites)."""
    _CELL["uid"] = uid
    _CELL["app_id"] = APP_IDS[kind]


def end_cell():
    _CELL["uid"] = None
    _CELL["app_id"] = None


# ============================================================
# MATERIALS
# ============================================================

def create_material(
    name,
    color,
    metallic=0.0,
    roughness=0.45,
    alpha=1.0,
    emission_color=None,
    emission_strength=0.0,
):
    """
    Create a glTF-compatible Principled BSDF material.

    Base colors are authored in linear Blender shader inputs.
    Alpha transparency is configured for the glTF exporter.
    """

    material = bpy.data.materials.new(name=name)
    material.diffuse_color = (
        color[0],
        color[1],
        color[2],
        alpha,
    )

    material.use_nodes = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (320, 0)

    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (0, 0)

    shader.inputs["Base Color"].default_value = (
        color[0],
        color[1],
        color[2],
        alpha,
    )
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Alpha"].default_value = alpha

    if emission_color is not None:
        if "Emission Color" in shader.inputs:
            shader.inputs["Emission Color"].default_value = (
                emission_color[0],
                emission_color[1],
                emission_color[2],
                1.0,
            )
        elif "Emission" in shader.inputs:
            shader.inputs["Emission"].default_value = (
                emission_color[0],
                emission_color[1],
                emission_color[2],
                1.0,
            )

        if "Emission Strength" in shader.inputs:
            shader.inputs["Emission Strength"].default_value = (
                emission_strength
            )

    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    # GLB-compatible transparency settings ("Blended" exports as glTF BLEND).
    if alpha < 0.999:
        try:
            material.surface_render_method = "BLENDED"
        except AttributeError:
            try:
                material.blend_method = "BLEND"
            except AttributeError:
                pass
        material.use_backface_culling = False

    return material


MATERIALS = {
    # Peripheral nerve graft.
    "mat_graft_boundary": create_material(
        "mat_graft_boundary",
        (0.26, 0.40, 0.48),
        roughness=0.7,
        alpha=0.10,
    ),

    "mat_graft_vessel": create_material(
        "mat_graft_vessel",
        (0.72, 0.13, 0.20),
        roughness=0.3,
        alpha=0.88,
        emission_color=(0.16, 0.015, 0.025),
        emission_strength=0.15,
    ),

    "mat_schwann": create_material(
        "mat_schwann",
        (0.95, 0.56, 0.19),
        roughness=0.38,
    ),

    "mat_fibroblast": create_material(
        "mat_fibroblast",
        (0.32, 0.80, 0.64),
        roughness=0.48,
    ),

    "mat_macrophage": create_material(
        "mat_macrophage",
        (0.75, 0.35, 0.64),
        roughness=0.48,
    ),

    "mat_col1a1": create_material(
        "mat_col1a1",
        (0.38, 0.82, 0.40),
        roughness=0.6,
    ),

    # CNS host environment.
    "mat_dopamine_neuron": create_material(
        "mat_dopamine_neuron",
        (0.08, 0.46, 1.0),
        roughness=0.32,
        emission_color=(0.015, 0.12, 0.8),
        emission_strength=0.22,
    ),

    "mat_neurite": create_material(
        "mat_neurite",
        (0.08, 0.58, 1.0),
        roughness=0.32,
        emission_color=(0.01, 0.15, 0.9),
        emission_strength=0.28,
    ),

    "mat_astrocyte_homeostatic": create_material(
        "mat_astrocyte_homeostatic",
        (0.35, 0.58, 0.88),
        roughness=0.55,
    ),

    "mat_astrocyte_reactive": create_material(
        "mat_astrocyte_reactive",
        (0.10, 0.82, 1.0),
        roughness=0.4,
        emission_color=(0.01, 0.15, 0.3),
        emission_strength=0.18,
    ),

    "mat_microglia": create_material(
        "mat_microglia",
        (0.70, 0.76, 0.90),
        roughness=0.55,
    ),

    "mat_oligodendrocyte": create_material(
        "mat_oligodendrocyte",
        (0.80, 0.72, 0.46),
        roughness=0.5,
    ),
}


# ============================================================
# SCENE RESET AND COLLECTIONS
# ============================================================

def clear_scene():
    """Remove the default scene objects and unused object data."""

    # Safety: never wipe a file that already contains real work.
    default_names = {"Cube", "Camera", "Light"}
    existing = {obj.name for obj in bpy.data.objects}
    if existing - default_names:
        raise RuntimeError(
            "This file already contains objects. Run this script in a new "
            "file (File > New > General), saved into the repo's art/ folder, "
            "so nothing of yours is deleted."
        )

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def create_collection(name):
    """Create a dedicated collection for one anatomical layer."""

    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def create_parent(name, collection):
    """
    Create a named Empty used as the layer root.

    Objects are parented to this Empty so the web application can
    identify and control each anatomical layer independently.
    """

    parent = bpy.data.objects.new(name, None)
    collection.objects.link(parent)

    parent.empty_display_type = "PLAIN_AXES"
    parent.empty_display_size = 0.12

    # Keep organizational objects out of the exported asset.
    parent["export_role"] = "layer_root"

    return parent


def link_object(obj, collection, parent=None):
    """
    Move an object into the requested collection and optionally
    parent it without changing its world-space transform.
    """

    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)

    collection.objects.link(obj)

    # Stamp the object with the cell currently being built (see CELL TAGGING).
    if _CELL["uid"] is not None:
        obj["_cell"] = _CELL["uid"]
        obj["_app_id"] = _CELL["app_id"]

    if parent is not None:
        # Parent while keeping the object's own location/rotation/scale.
        # (Copying obj.matrix_world here would use a stale matrix that Blender
        # hasn't recomputed yet, silently resetting every cell's scale to 1.)
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()

    return obj


clear_scene()

COLLECTIONS = {}
PARENTS = {}

LAYER_NAMES = [
    "PNT_Graft_Corridor",
    "Graft_Vasculature",
    "Schwann_Cells",
    "Endoneurial_Fibroblasts",
    "Graft_Macrophages",
    "Collagen_Fibrils",
    "Dopaminergic_Neurons",
    "Axonal_Profiles",
    "Reactive_Astrocytes",
    "Homeostatic_Astrocytes",
    "Microglia",
    "Oligodendrocytes",
    "Host_Volume",
]

for layer_name in LAYER_NAMES:
    COLLECTIONS[layer_name] = create_collection(layer_name)
    PARENTS[layer_name] = create_parent(
        layer_name,
        COLLECTIONS[layer_name],
    )


# ============================================================
# GENERAL PROCEDURAL GEOMETRY HELPERS
# ============================================================

def new_mesh_object(name, location, build):
    """
    Create a mesh object directly from data (no bpy.ops call).

    Blender's "add primitive" operators slow down as the scene grows; with
    thousands of parts that turns a seconds-long build into minutes.
    Building the same primitive with bmesh gives identical geometry at
    constant speed.
    """

    bm = bmesh.new()
    build(bm)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    return obj


def assign_material(obj, material):
    if obj.data is not None and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(material)


def smooth_mesh(obj):
    if obj.type != "MESH":
        return

    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def create_uv_sphere(
    name,
    location,
    scale,
    material,
    collection,
    parent,
    segments=12,
    rings=8,
    subdivisions=0,
):
    """
    Create a compact UV sphere and apply nonuniform scale.

    Low polygon counts keep the exported GLB manageable.
    """

    obj = new_mesh_object(
        name,
        location,
        lambda bm: bmesh.ops.create_uvsphere(
            bm, u_segments=segments, v_segments=rings, radius=1.0,
        ),
    )

    obj.scale = scale

    assign_material(obj, material)
    smooth_mesh(obj)

    if subdivisions > 0:
        modifier = obj.modifiers.new(
            name="Surface_Smoothing",
            type="SUBSURF",
        )
        modifier.levels = subdivisions
        modifier.render_levels = subdivisions

    link_object(obj, collection, parent)

    return obj


def create_ico_cell(
    name,
    location,
    scale,
    material,
    collection,
    parent,
    subdivisions=1,
    irregularity=0.0,
):
    """
    Create a cell body using an icosphere.

    Irregularity is introduced by moving each vertex radially from
    the sphere center. This creates a simple amoeboid or lobulated form.
    """

    obj = new_mesh_object(
        name,
        location,
        lambda bm: bmesh.ops.create_icosphere(
            bm, subdivisions=subdivisions, radius=1.0,
        ),
    )

    if irregularity:
        for vertex in obj.data.vertices:
            factor = random.uniform(
                1.0 - irregularity,
                1.0 + irregularity,
            )
            vertex.co *= factor

    obj.scale = scale

    assign_material(obj, material)
    smooth_mesh(obj)

    link_object(obj, collection, parent)

    return obj


def create_curve(
    name,
    points,
    radius,
    material,
    collection,
    parent,
    resolution=2,
    cyclic=False,
    radii=None,
):
    """
    Create a continuous 3D Bezier curve with round bevel geometry.

    points:
        Iterable of Vector or 3D coordinate tuples.

    radii:
        Optional per-spline-point radius values. Blender interpolates
        these values along the curve, allowing tapered processes.
    """

    if len(points) < 2:
        return None

    curve_data = bpy.data.curves.new(
        name=f"{name}_CurveData",
        type="CURVE",
    )

    curve_data.dimensions = "3D"
    curve_data.resolution_u = 8
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 1
    curve_data.resolution_u = max(4, resolution)

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)

    for index, point in enumerate(points):
        bp = spline.bezier_points[index]
        bp.co = Vector(point)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"

        if radii is not None and index < len(radii):
            bp.radius = radii[index]

    spline.use_cyclic_u = cyclic

    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)

    assign_material(obj, material)
    link_object(obj, collection, parent)

    return obj


def create_polyline_tube(
    name,
    points,
    radius,
    material,
    collection,
    parent,
    resolution=1,
):
    """
    Use a polyline spline for fine collagen fibrils.

    Polyline splines are less expensive than Bezier splines when
    many individual fibers are needed.
    """

    if len(points) < 2:
        return None

    curve_data = bpy.data.curves.new(
        name=f"{name}_CurveData",
        type="CURVE",
    )

    curve_data.dimensions = "3D"
    curve_data.resolution_u = 1
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 0

    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)

    for index, point in enumerate(points):
        spline.points[index].co = (
            point[0],
            point[1],
            point[2],
            1.0,
        )

    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)

    assign_material(obj, material)
    link_object(obj, collection, parent)

    return obj


def random_unit_vector():
    """Return a uniformly distributed direction on the unit sphere."""

    z = random.uniform(-1.0, 1.0)
    theta = random.uniform(0.0, 2.0 * pi)
    r = sqrt(max(0.0, 1.0 - z * z))

    return Vector((
        r * cos(theta),
        r * sin(theta),
        z,
    ))


def random_point_in_host():
    """Sample a point inside a cylindrical host volume."""

    radius = CONFIG["host_radius"]
    height = CONFIG["host_height"]

    r = radius * sqrt(random.random())
    theta = random.uniform(0.0, 2.0 * pi)
    z = random.uniform(-height / 2.0, height / 2.0)

    return Vector((
        r * cos(theta),
        r * sin(theta),
        z,
    ))


def random_point_in_graft():
    """Sample a point inside the central graft corridor."""

    radius = CONFIG["graft_radius"]
    height = CONFIG["graft_height"]

    r = radius * sqrt(random.random())
    theta = random.uniform(0.0, 2.0 * pi)
    z = random.uniform(-height / 2.0, height / 2.0)

    return Vector((
        r * cos(theta),
        r * sin(theta),
        z,
    ))


def random_graft_periphery():
    """Sample a point near the outer region of the graft."""

    radius = CONFIG["graft_radius"]
    height = CONFIG["graft_height"]

    r = radius * random.uniform(0.72, 0.97)
    theta = random.uniform(0.0, 2.0 * pi)
    z = random.uniform(-height / 2.0, height / 2.0)

    return Vector((
        r * cos(theta),
        r * sin(theta),
        z,
    ))


def distance_from_graft_axis(point):
    """Radial distance to the vertical graft axis."""

    return sqrt(point.x * point.x + point.y * point.y)


# ============================================================
# CENTRAL PNT GRAFT CORRIDOR
# ============================================================

def create_graft_corridor():
    """
    Create a subtle transparent cylindrical boundary.

    This is a spatial reference rather than a claim that peripheral
    nerve tissue forms a perfectly cylindrical biological structure.
    """

    if not CONFIG["include_host_boundary"]:
        return

    begin_cell("graft_corridor")

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48,
        radius=CONFIG["graft_radius"],
        depth=CONFIG["graft_height"],
        location=(0.0, 0.0, 0.0),
    )

    obj = bpy.context.object
    obj.name = "PNT_Graft_Corridor_Boundary"

    assign_material(
        obj,
        MATERIALS["mat_graft_boundary"],
    )

    smooth_mesh(obj)

    # Retain a smooth transparent shell with no heavy modifiers.
    link_object(
        obj,
        COLLECTIONS["PNT_Graft_Corridor"],
        PARENTS["PNT_Graft_Corridor"],
    )

    obj["anatomical_role"] = "graft_spatial_boundary"


create_graft_corridor()


# ============================================================
# INTRAGRAFT VASCULATURE
# ============================================================

def generate_vessel_points(angle, radial_offset, phase):
    """
    Generate a vertically oriented, gently winding vascular path.

    Each vessel has a persistent angular trajectory with small,
    smooth perturbations in radius and phase.
    """

    points = []

    z_min = -CONFIG["graft_height"] * 0.47
    z_max = CONFIG["graft_height"] * 0.47

    steps = 12

    for i in range(steps):
        t = i / (steps - 1)
        z = z_min + (z_max - z_min) * t

        theta = (
            angle
            + 0.28 * sin(z * 1.35 + phase)
            + 0.09 * sin(z * 2.2 + phase * 1.7)
        )

        r = (
            radial_offset
            + 0.07 * sin(z * 1.1 + phase)
            + 0.035 * cos(z * 2.0 + phase)
        )

        points.append(Vector((
            r * cos(theta),
            r * sin(theta),
            z,
        )))

    return points


def create_vasculature():
    """
    Create winding vessel centerlines and subtle adventitial cells.

    Curves are used instead of densely tessellated meshes so the
    network remains compact when exported to GLB.
    """

    collection = COLLECTIONS["Graft_Vasculature"]
    parent = PARENTS["Graft_Vasculature"]

    for i in range(CONFIG["vessel_count"]):
        begin_cell("vessel")
        angle = (2.0 * pi * i) / CONFIG["vessel_count"]
        radial_offset = random.uniform(0.08, 0.40)
        phase = random.uniform(0.0, 2.0 * pi)

        points = generate_vessel_points(
            angle,
            radial_offset,
            phase,
        )

        vessel = create_curve(
            name=f"Graft_Vessel_{i + 1:02d}",
            points=points,
            radius=CONFIG["vessel_radius"] * random.uniform(0.7, 1.2),
            material=MATERIALS["mat_graft_vessel"],
            collection=collection,
            parent=parent,
            resolution=3,
        )

        if vessel is not None:
            vessel["anatomical_role"] = "intragraft_vascular_profile"


create_vasculature()


# ============================================================
# SCHWANN CELLS
# ============================================================

def create_schwann_cells():
    """
    Create elongated spindle-shaped Schwann cell bodies.

    Each cell is aligned approximately with the graft's longitudinal
    axis. Small angular and axial offsets create a fascicle-like
    arrangement instead of a rigid, evenly spaced grid.
    """

    collection = COLLECTIONS["Schwann_Cells"]
    parent = PARENTS["Schwann_Cells"]

    for i in range(CONFIG["schwann_cell_count"]):
        begin_cell("schwann")
        center = random_graft_periphery()

        # Slightly perturb the longitudinal coordinate and position.
        center.x += random.uniform(-0.08, 0.08)
        center.y += random.uniform(-0.08, 0.08)

        length = random.uniform(0.24, 0.48)
        width = random.uniform(0.045, 0.085)

        cell = create_uv_sphere(
            name=f"Schwann_Cell_{i + 1:03d}",
            location=center,
            scale=(width, width * 0.75, length),
            material=MATERIALS["mat_schwann"],
            collection=collection,
            parent=parent,
            segments=10,
            rings=6,
        )

        # Align the spindle with a gently angled local axonal vector.
        cell.rotation_euler[0] = random.uniform(-0.15, 0.15)
        cell.rotation_euler[1] = random.uniform(-0.15, 0.15)
        cell.rotation_euler[2] = random.uniform(0.0, 2.0 * pi)

        cell["markers"] = "NGFR;MPZ;S100B"
        cell["anatomical_role"] = "Schwann_cell"


create_schwann_cells()


# ============================================================
# ENDONEURIAL FIBROBLASTS
# ============================================================

def create_fibroblast(center, index):
    """
    Create a flattened elongated fibroblast body with wing-like
    cellular extensions.

    The body is a flattened ellipsoid. Two thin curves form broad,
    branching extensions that approximate a web-like endoneurial
    morphology without generating an excessively dense mesh.
    """

    collection = COLLECTIONS["Endoneurial_Fibroblasts"]
    parent = PARENTS["Endoneurial_Fibroblasts"]

    begin_cell("fibroblast")

    angle = random.uniform(0.0, 2.0 * pi)
    length = random.uniform(0.25, 0.42)
    width = random.uniform(0.06, 0.11)
    thickness = random.uniform(0.018, 0.035)

    body = create_uv_sphere(
        name=f"Endoneurial_Fibroblast_{index:03d}",
        location=center,
        scale=(length, width, thickness),
        material=MATERIALS["mat_fibroblast"],
        collection=collection,
        parent=parent,
        segments=10,
        rings=6,
    )

    body.rotation_euler[2] = angle

    direction = Vector((
        cos(angle),
        sin(angle),
        random.uniform(-0.18, 0.18),
    ))

    side = Vector((
        -sin(angle),
        cos(angle),
        random.uniform(-0.15, 0.15),
    ))

    for wing_index, sign in enumerate((-1.0, 1.0)):
        root = center + direction * (length * 0.4)

        wing_points = [
            root,
            root + direction * 0.12 + side * (sign * 0.10),
            root + direction * 0.22 + side * (sign * 0.20),
            root + direction * 0.30 + side * (sign * 0.23),
        ]

        create_curve(
            name=f"Fibroblast_{index:03d}_Wing_{wing_index + 1}",
            points=wing_points,
            radius=0.012,
            material=MATERIALS["mat_fibroblast"],
            collection=collection,
            parent=parent,
            resolution=2,
            radii=[1.0, 1.2, 0.8, 0.25],
        )


def create_fibroblasts():
    for i in range(CONFIG["fibroblast_count"]):
        center = random_point_in_graft()
        create_fibroblast(center, i + 1)


create_fibroblasts()


# ============================================================
# INFILTRATING MACROPHAGES
# ============================================================

def create_macrophages():
    """
    Generate irregular amoeboid cell bodies.

    A deformed low-poly icosphere approximates the uneven cell surface.
    Additional small spheres represent intracellular vacuole-like
    structures. They are illustrative inclusions, not organelle models.
    """

    collection = COLLECTIONS["Graft_Macrophages"]
    parent = PARENTS["Graft_Macrophages"]

    for i in range(CONFIG["macrophage_count"]):
        begin_cell("macrophage")
        center = random_point_in_graft()

        size = random.uniform(0.11, 0.19)

        cell = create_ico_cell(
            name=f"Graft_Macrophage_{i + 1:03d}",
            location=center,
            scale=(size, size * 0.92, size * 0.82),
            material=MATERIALS["mat_macrophage"],
            collection=collection,
            parent=parent,
            subdivisions=2,
            irregularity=0.22,
        )

        cell["anatomical_role"] = "infiltrating_macrophage"

        # Small internal inclusions add visible surface complexity.
        # These are kept within the approximate cell-body envelope.
        for v in range(random.randint(2, 4)):
            offset = random_unit_vector() * size * random.uniform(0.12, 0.45)

            vacuole_size = size * random.uniform(0.08, 0.16)

            create_uv_sphere(
                name=f"Macrophage_{i + 1:03d}_Vacuole_{v + 1}",
                location=center + offset,
                scale=(
                    vacuole_size,
                    vacuole_size,
                    vacuole_size,
                ),
                material=MATERIALS["mat_graft_boundary"],
                collection=collection,
                parent=parent,
                segments=8,
                rings=5,
            )


create_macrophages()


# ============================================================
# COL1A1+ COLLAGEN FIBRILS
# ============================================================

def create_collagen_fibrils():
    """
    Create a dense longitudinal array of fine collagen-like fibers.

    Each fiber follows a mostly vertical path with low-amplitude
    lateral undulations. A collection of thin polyline tubes is used
    to preserve individual fiber trajectories in the exported model.

    For very high fiber counts, consider combining the curves into
    fewer curves with multiple splines or baking them into meshes.
    """

    collection = COLLECTIONS["Collagen_Fibrils"]
    parent = PARENTS["Collagen_Fibrils"]

    radius = CONFIG["graft_radius"]
    height = CONFIG["graft_height"]

    # All fibrils together form one clickable collagen structure.
    begin_cell("collagen")

    for i in range(CONFIG["collagen_fibril_count"]):
        theta = random.uniform(0.0, 2.0 * pi)
        radial_distance = radius * sqrt(random.random()) * 0.94

        x0 = radial_distance * cos(theta)
        y0 = radial_distance * sin(theta)

        phase_x = random.uniform(0.0, 2.0 * pi)
        phase_y = random.uniform(0.0, 2.0 * pi)

        amplitude = random.uniform(0.008, 0.035)
        frequency = random.uniform(0.5, 1.5)

        points = []

        steps = 9

        for j in range(steps):
            t = j / (steps - 1)
            z = -height * 0.48 + height * 0.96 * t

            x = x0 + amplitude * sin(
                z * frequency + phase_x
            )

            y = y0 + amplitude * cos(
                z * frequency + phase_y
            )

            points.append((x, y, z))

        fiber = create_polyline_tube(
            name=f"COL1A1_Fibril_{i + 1:03d}",
            points=points,
            radius=random.uniform(0.0025, 0.0055),
            material=MATERIALS["mat_col1a1"],
            collection=collection,
            parent=parent,
        )

        if fiber is not None:
            fiber["anatomical_role"] = "collagen_fibril"
            fiber["marker"] = "COL1A1"


create_collagen_fibrils()


# ============================================================
# DOPAMINERGIC NEURONS
# ============================================================

def create_neuron_soma(center, index):
    """
    Create a large multipolar neuron body.

    The soma is represented by a slightly elongated, lobulated body.
    Multiple neurites radiate outward from separate soma-associated
    origins, including paths that enter the central graft corridor.
    """

    collection = COLLECTIONS["Dopaminergic_Neurons"]
    parent = PARENTS["Dopaminergic_Neurons"]

    soma_size = random.uniform(0.20, 0.30)

    soma = create_ico_cell(
        name=f"Dopaminergic_Neuron_{index:02d}_Soma",
        location=center,
        scale=(
            soma_size * 1.15,
            soma_size,
            soma_size * 0.85,
        ),
        material=MATERIALS["mat_dopamine_neuron"],
        collection=collection,
        parent=parent,
        subdivisions=2,
        irregularity=0.10,
    )

    soma["cell_type"] = "nigral_dopaminergic_neuron"
    soma["marker"] = "TH"

    return soma, soma_size


def generate_penetrating_neurite(
    soma_center,
    start_direction,
    soma_size,
    neuron_index,
    neurite_index,
):
    """
    Generate a continuous neurite that enters and penetrates the graft.

    The path starts outside the graft, approaches its cylindrical
    boundary, crosses into the graft, and ends at a configurable
    minimum penetration depth.

    A deterministic radial target ensures that at least some
    neurites visibly enter the graft instead of merely pointing
    toward its surface.
    """

    graft_radius = CONFIG["graft_radius"]

    direction_xy = Vector((
        start_direction.x,
        start_direction.y,
        0.0,
    ))

    if direction_xy.length < 0.001:
        direction_xy = Vector((1.0, 0.0, 0.0))

    direction_xy.normalize()

    # Aim at a target inside the graft.
    target_radius = random.uniform(
        0.0,
        max(
            0.08,
            graft_radius - CONFIG["neurite_min_graft_penetration"],
        ),
    )

    target_z = random.uniform(
        -CONFIG["graft_height"] * 0.42,
        CONFIG["graft_height"] * 0.42,
    )

    target = Vector((
        direction_xy.x * target_radius,
        direction_xy.y * target_radius,
        target_z,
    ))

    # Keep the first point attached to the soma surface.
    start = soma_center + start_direction.normalized() * soma_size * 0.85

    # Approach the graft boundary along a path that may curve and twist.
    boundary_point = Vector((
        direction_xy.x * graft_radius * 1.02,
        direction_xy.y * graft_radius * 1.02,
        start.z + (target_z - start.z) * 0.55,
    ))

    control_1 = start.lerp(boundary_point, 0.30)
    control_2 = start.lerp(boundary_point, 0.75)

    control_1.x += random.uniform(-0.18, 0.18)
    control_1.y += random.uniform(-0.18, 0.18)

    control_2.x += random.uniform(-0.10, 0.10)
    control_2.y += random.uniform(-0.10, 0.10)

    inside_control = boundary_point.lerp(target, 0.55)
    inside_control.x += random.uniform(-0.08, 0.08)
    inside_control.y += random.uniform(-0.08, 0.08)

    points = [
        start,
        control_1,
        control_2,
        boundary_point,
        inside_control,
        target,
    ]

    curve = create_curve(
        name=(
            f"Neuron_{neuron_index:02d}_"
            f"Penetrating_Neurite_{neurite_index:02d}"
        ),
        points=points,
        radius=CONFIG["neurite_radius"],
        material=MATERIALS["mat_neurite"],
        collection=COLLECTIONS["Axonal_Profiles"],
        parent=PARENTS["Axonal_Profiles"],
        resolution=3,
        radii=[1.4, 1.1, 0.9, 0.85, 0.6, 0.15],
    )

    if curve is not None:
        curve["anatomical_role"] = "penetrating_neurite"
        curve["host_cell"] = f"Dopaminergic_Neuron_{neuron_index:02d}"


def generate_host_neurite(
    soma_center,
    start_direction,
    soma_size,
    neuron_index,
    neurite_index,
):
    """Generate a neurite that branches through the host environment."""

    start = soma_center + start_direction.normalized() * soma_size * 0.8

    direction = start_direction.normalized()

    length = random.uniform(1.0, 2.4)

    control_1 = start + direction * (length * 0.3)
    control_2 = start + direction * (length * 0.7)
    end = start + direction * length

    for point in (control_1, control_2, end):
        point.x += random.uniform(-0.4, 0.4)
        point.y += random.uniform(-0.4, 0.4)
        point.z += random.uniform(-0.3, 0.3)

    curve = create_curve(
        name=(
            f"Neuron_{neuron_index:02d}_"
            f"Host_Neurite_{neurite_index:02d}"
        ),
        points=[start, control_1, control_2, end],
        radius=CONFIG["neurite_radius"] * 0.8,
        material=MATERIALS["mat_neurite"],
        collection=COLLECTIONS["Axonal_Profiles"],
        parent=PARENTS["Axonal_Profiles"],
        resolution=3,
        radii=[1.2, 0.9, 0.6, 0.15],
    )

    if curve is not None:
        curve["anatomical_role"] = "host_neurite"


def create_dopaminergic_neurons():
    """
    Position neuron somata outside the graft and distribute their
    processes through the host space.

    A fraction of neurites is explicitly directed through the graft
    boundary to make the host-graft interface unambiguous.
    """

    graft_radius = CONFIG["graft_radius"]
    host_radius = CONFIG["host_radius"]

    for i in range(CONFIG["dopaminergic_neuron_count"]):
        angle = random.uniform(0.0, 2.0 * pi)

        radial_distance = random.uniform(
            graft_radius + 0.35,
            min(host_radius * 0.82, graft_radius + 2.5),
        )

        z = random.uniform(
            -CONFIG["graft_height"] * 0.40,
            CONFIG["graft_height"] * 0.40,
        )

        center = Vector((
            radial_distance * cos(angle),
            radial_distance * sin(angle),
            z,
        ))

        neuron_uid = begin_cell("da_neuron")
        soma, soma_size = create_neuron_soma(center, i + 1)

        neurite_count = CONFIG["neurites_per_neuron"]

        # Ensure at least two neurites per neuron enter the graft
        # when possible, while retaining other host-directed processes.
        penetration_count = min(
            2,
            max(1, neurite_count // 2),
        )

        for j in range(neurite_count):
            direction = random_unit_vector()

            if j < penetration_count:
                # Direct the main axis toward the graft, adding a
                # small vertical component for 3D variation.
                toward_graft = Vector((
                    -cos(angle),
                    -sin(angle),
                    random.uniform(-0.35, 0.35),
                ))

                toward_graft.normalize()

                # Each penetrating neurite is its own clickable structure.
                begin_cell("penetrating_neurite")
                generate_penetrating_neurite(
                    soma_center=center,
                    start_direction=toward_graft,
                    soma_size=soma_size,
                    neuron_index=i + 1,
                    neurite_index=j + 1,
                )

            else:
                # Avoid an overly uniform radial star by combining
                # random directions with the local outward direction.
                outward = Vector((
                    cos(angle),
                    sin(angle),
                    random.uniform(-0.5, 0.5),
                )).normalized()

                direction = (
                    outward * random.uniform(0.1, 0.7)
                    + direction * random.uniform(0.3, 0.9)
                ).normalized()

                # Host-directed neurites belong to their parent neuron.
                resume_cell(neuron_uid, "da_neuron")
                generate_host_neurite(
                    soma_center=center,
                    start_direction=direction,
                    soma_size=soma_size,
                    neuron_index=i + 1,
                    neurite_index=j + 1,
                )


create_dopaminergic_neurons()


# ============================================================
# ASTROCYTES: HOMEOSTATIC AND REACTIVE STATES
# ============================================================

def create_astrocyte(
    center,
    index,
    reactive,
):
    """
    Create a star-like astrocyte using a soma and radial branching
    processes.

    Homeostatic cells:
        - Smaller soma
        - Thin, relatively uniform processes
        - Limited secondary branching

    Reactive cells:
        - Enlarged soma
        - More processes
        - Thicker proximal processes
        - More secondary branches

    Reactive morphology is assigned using distance to the graft
    boundary. It is a visual approximation of a reactive gradient,
    not a claim that radial distance alone determines astrocyte state.
    """

    if reactive:
        collection_name = "Reactive_Astrocytes"
        material = MATERIALS["mat_astrocyte_reactive"]

        soma_radius = random.uniform(0.095, 0.145)
        process_count = random.randint(8, 12)
        process_length = random.uniform(0.42, 0.72)
        process_radius = random.uniform(0.018, 0.032)
        secondary_branch_probability = 0.75

    else:
        collection_name = "Homeostatic_Astrocytes"
        material = MATERIALS["mat_astrocyte_homeostatic"]

        soma_radius = random.uniform(0.045, 0.075)
        process_count = random.randint(6, 8)
        process_length = random.uniform(0.28, 0.52)
        process_radius = random.uniform(0.006, 0.012)
        secondary_branch_probability = 0.25

    collection = COLLECTIONS[collection_name]
    parent = PARENTS[collection_name]

    begin_cell("reactive_astrocyte" if reactive else "homeostatic_astrocyte")
    prefix = "Reactive" if reactive else "Homeostatic"

    soma = create_uv_sphere(
        name=f"{prefix}_Astrocyte_{index:03d}_Soma",
        location=center,
        scale=(
            soma_radius,
            soma_radius,
            soma_radius * random.uniform(0.9, 1.2),
        ),
        material=material,
        collection=collection,
        parent=parent,
        segments=10,
        rings=6,
    )

    soma["cell_type"] = "astrocyte"
    soma["phenotype"] = "reactive" if reactive else "homeostatic"

    for process_index in range(process_count):
        direction = random_unit_vector()

        # Avoid every process lying almost parallel to the Z axis.
        if abs(direction.z) > 0.92:
            direction.x += random.uniform(-0.25, 0.25)
            direction.y += random.uniform(-0.25, 0.25)
            direction.normalize()

        start = center + direction * soma_radius * 0.65

        bend_direction = random_unit_vector()

        control_1 = (
            start
            + direction * process_length * 0.33
            + bend_direction * process_length * 0.10
        )

        control_2 = (
            start
            + direction * process_length * 0.68
            + bend_direction * process_length * 0.20
        )

        end = (
            start
            + direction * process_length
            + bend_direction * process_length * 0.24
        )

        create_curve(
            name=(
                f"{prefix}_Astrocyte_{index:03d}_"
                f"Process_{process_index + 1:02d}"
            ),
            points=[start, control_1, control_2, end],
            radius=process_radius,
            material=material,
            collection=collection,
            parent=parent,
            resolution=2,
            radii=(
                [1.5, 1.0, 0.7, 0.08]
                if reactive
                else [1.0, 0.75, 0.45, 0.06]
            ),
        )

        # Reactive astrocytes have a higher probability of forming
        # secondary branches from their major processes.
        if random.random() < secondary_branch_probability:
            branch_origin = control_2

            branch_direction = (
                direction * 0.4
                + random_unit_vector() * 0.8
            ).normalized()

            branch_length = process_length * random.uniform(0.30, 0.58)

            branch_points = [
                branch_origin,
                branch_origin + branch_direction * branch_length * 0.45,
                branch_origin + branch_direction * branch_length,
            ]

            create_curve(
                name=(
                    f"{prefix}_Astrocyte_{index:03d}_"
                    f"Secondary_{process_index + 1:02d}"
                ),
                points=branch_points,
                radius=process_radius * (0.75 if reactive else 0.55),
                material=material,
                collection=collection,
                parent=parent,
                resolution=2,
                radii=[1.1, 0.55, 0.04],
            )


def create_astrocyte_population():
    """
    Distribute astrocytes across the host volume.

    Radial distance is measured from the graft axis. The distance
    to the graft boundary is:

        abs(radial_distance - graft_radius)

    Host cells within reactive_boundary_distance of that boundary
    are assigned the reactive morphology.

    The configured homeostatic/reactive counts serve as a soft target:
    proximity takes precedence, so final counts may differ.
    """

    target_total = (
        CONFIG["homeostatic_astrocyte_count"]
        + CONFIG["reactive_astrocyte_count"]
    )

    graft_radius = CONFIG["graft_radius"]
    boundary_distance = CONFIG["reactive_boundary_distance"]

    homeostatic_count = 0
    reactive_count = 0

    attempts = 0
    max_attempts = target_total * 8

    while (
        homeostatic_count + reactive_count < target_total
        and attempts < max_attempts
    ):
        attempts += 1

        center = random_point_in_host()

        radial_distance = distance_from_graft_axis(center)

        # Cells well outside the graft and near its interface can be
        # selected. Exclude cells placed deeply inside the graft lumen.
        if radial_distance < graft_radius + 0.10:
            continue

        distance_to_boundary = abs(
            radial_distance - graft_radius
        )

        reactive = distance_to_boundary <= boundary_distance

        if reactive:
            if reactive_count >= CONFIG["reactive_astrocyte_count"]:
                reactive = False

        if not reactive:
            if homeostatic_count >= CONFIG["homeostatic_astrocyte_count"]:
                # If the homeostatic target has been reached, continue
                # searching for an interface location when possible.
                if distance_to_boundary > boundary_distance:
                    continue
                reactive = True

        if reactive:
            if reactive_count >= CONFIG["reactive_astrocyte_count"]:
                continue

            reactive_count += 1
            index = reactive_count

        else:
            if homeostatic_count >= CONFIG["homeostatic_astrocyte_count"]:
                continue

            homeostatic_count += 1
            index = homeostatic_count

        create_astrocyte(
            center=center,
            index=index,
            reactive=reactive,
        )

    print(
        "Astrocyte population created: "
        f"{homeostatic_count} homeostatic, "
        f"{reactive_count} reactive."
    )


create_astrocyte_population()


# ============================================================
# MICROGLIA
# ============================================================

def create_microglia():
    """
    Create small microglial somata with fine thorny processes.

    Thin processes radiate irregularly from each soma. Their lengths,
    directions, and curvature are varied to avoid a uniform star pattern.
    """

    collection = COLLECTIONS["Microglia"]
    parent = PARENTS["Microglia"]

    for i in range(CONFIG["microglia_count"]):
        begin_cell("microglia")
        center = random_point_in_host()

        # Keep the majority of host glia outside the graft corridor.
        if distance_from_graft_axis(center) < CONFIG["graft_radius"] + 0.12:
            center.x += CONFIG["graft_radius"] + 0.20

        soma_size = random.uniform(0.045, 0.075)

        soma = create_ico_cell(
            name=f"Microglia_{i + 1:03d}_Soma",
            location=center,
            scale=(
                soma_size,
                soma_size * 0.9,
                soma_size,
            ),
            material=MATERIALS["mat_microglia"],
            collection=collection,
            parent=parent,
            subdivisions=1,
            irregularity=0.15,
        )

        soma["cell_type"] = "microglia"

        process_count = random.randint(6, 10)

        for j in range(process_count):
            direction = random_unit_vector()

            length = random.uniform(0.20, 0.48)

            start = center + direction * soma_size * 0.7

            control = (
                start
                + direction * length * 0.55
                + random_unit_vector() * length * 0.18
            )

            end = (
                start
                + direction * length
                + random_unit_vector() * length * 0.15
            )

            create_curve(
                name=f"Microglia_{i + 1:03d}_Process_{j + 1:02d}",
                points=[start, control, end],
                radius=random.uniform(0.004, 0.009),
                material=MATERIALS["mat_microglia"],
                collection=collection,
                parent=parent,
                resolution=2,
                radii=[1.1, 0.55, 0.04],
            )

            # Add occasional short thorn-like branches.
            if random.random() < 0.55:
                branch_direction = random_unit_vector()
                branch_length = random.uniform(0.06, 0.14)

                create_curve(
                    name=(
                        f"Microglia_{i + 1:03d}_"
                        f"Thorn_{j + 1:02d}"
                    ),
                    points=[
                        control,
                        control + branch_direction * branch_length,
                    ],
                    radius=0.004,
                    material=MATERIALS["mat_microglia"],
                    collection=collection,
                    parent=parent,
                    resolution=1,
                    radii=[0.8, 0.02],
                )


create_microglia()


# ============================================================
# OLIGODENDROCYTES
# ============================================================

def create_oligodendrocytes():
    """
    Create round oligodendrocyte somata with a few flattened,
    paddle-like extensions.

    The extensions are modeled as flattened ellipsoids. They provide
    a simple visual cue for oligodendrocyte processes and membrane
    expansions rather than a literal reconstruction of compact myelin.
    """

    collection = COLLECTIONS["Oligodendrocytes"]
    parent = PARENTS["Oligodendrocytes"]

    for i in range(CONFIG["oligodendrocyte_count"]):
        begin_cell("oligodendrocyte")
        center = random_point_in_host()

        if distance_from_graft_axis(center) < CONFIG["graft_radius"] + 0.12:
            center.x += CONFIG["graft_radius"] + 0.20

        soma_size = random.uniform(0.055, 0.085)

        soma = create_uv_sphere(
            name=f"Oligodendrocyte_{i + 1:03d}_Soma",
            location=center,
            scale=(soma_size, soma_size, soma_size),
            material=MATERIALS["mat_oligodendrocyte"],
            collection=collection,
            parent=parent,
            segments=10,
            rings=6,
        )

        soma["cell_type"] = "oligodendrocyte"

        process_count = random.randint(3, 5)

        for j in range(process_count):
            direction = random_unit_vector()

            length = random.uniform(0.20, 0.38)

            paddle_center = (
                center
                + direction * length * 0.75
            )

            paddle_length = length * random.uniform(0.35, 0.60)
            paddle_width = random.uniform(0.055, 0.10)
            paddle_thickness = random.uniform(0.012, 0.025)

            paddle = create_uv_sphere(
                name=(
                    f"Oligodendrocyte_{i + 1:03d}_"
                    f"Paddle_{j + 1:02d}"
                ),
                location=paddle_center,
                scale=(
                    paddle_length,
                    paddle_width,
                    paddle_thickness,
                ),
                material=MATERIALS["mat_oligodendrocyte"],
                collection=collection,
                parent=parent,
                segments=8,
                rings=5,
            )

            # Point the long paddle axis approximately along the
            # corresponding cellular process.
            paddle.rotation_mode = "QUATERNION"
            paddle.rotation_quaternion = direction.to_track_quat("X", "Z")

            # A narrow connector links the soma to the extension.
            connector_end = (
                center
                + direction * (length * 0.68)
            )

            create_curve(
                name=(
                    f"Oligodendrocyte_{i + 1:03d}_"
                    f"Connector_{j + 1:02d}"
                ),
                points=[center, connector_end],
                radius=0.009,
                material=MATERIALS["mat_oligodendrocyte"],
                collection=collection,
                parent=parent,
                resolution=1,
                radii=[1.0, 0.25],
            )


create_oligodendrocytes()


# ============================================================
# HOST VOLUME BOUNDARY
# ============================================================

def create_host_volume():
    """
    Add a subtle, transparent cylindrical host-volume reference.

    The mesh is optional and can be disabled from the Host_Volume
    layer in the web application. A transparent shell is preferable
    to a dense solid volume for a GLB viewed in a standard renderer.
    """

    if not CONFIG["include_host_boundary"]:
        return

    collection = COLLECTIONS["Host_Volume"]
    parent = PARENTS["Host_Volume"]

    begin_cell("host_volume")

    host_material = create_material(
        "mat_host_volume",
        (0.20, 0.34, 0.52),
        roughness=0.85,
        alpha=0.045,
    )

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=CONFIG["host_radius"],
        depth=CONFIG["host_height"],
        location=(0.0, 0.0, 0.0),
    )

    obj = bpy.context.object
    obj.name = "Substantia_Nigra_Host_Volume"

    assign_material(obj, host_material)

    link_object(obj, collection, parent)

    obj["anatomical_role"] = "host_spatial_boundary"


create_host_volume()


# ============================================================
# WEB APP INTEGRATION: ONE CELL = ONE OBJECT WITH AN `id`
# ============================================================

end_cell()


def consolidate_cells():
    """
    Bake every tagged part to mesh (curves included, modifiers applied),
    join each cell's parts into one object, and give it the app `id`.

    The joined object's origin is placed at the cell's centre so it can be
    moved, rotated and scaled naturally in Blender afterwards.
    """

    # Make sure every object's world matrix reflects its final location,
    # rotation and scale before baking.
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()

    cells = {}
    for obj in list(bpy.context.scene.objects):
        if "_cell" in obj:
            cells.setdefault(obj["_cell"], []).append(obj)

    per_id_counts = {}
    helper_keys = {"_cell", "_app_id"}

    for uid in sorted(cells):
        parts = cells[uid]
        primary = parts[0]                      # soma / first-built part
        app_id = primary["_app_id"]
        layer_parent = primary.parent
        layer_collection = primary.users_collection[0]

        bm = bmesh.new()
        materials = []

        for part in parts:
            if part.type not in {"MESH", "CURVE"}:
                continue
            evaluated = part.evaluated_get(depsgraph)
            mesh = bpy.data.meshes.new_from_object(evaluated)
            mesh.transform(part.matrix_world)

            slot_map = []
            for slot in part.material_slots:
                if slot.material not in materials:
                    materials.append(slot.material)
                slot_map.append(materials.index(slot.material))

            first_new_face = len(bm.faces)
            bm.from_mesh(mesh)
            bm.faces.ensure_lookup_table()
            for face_index in range(first_new_face, len(bm.faces)):
                face = bm.faces[face_index]
                face.material_index = (
                    slot_map[face.material_index] if slot_map else 0
                )
            bpy.data.meshes.remove(mesh)

        if not bm.verts:
            bm.free()
            continue

        # Origin at the centre of the cell's bounding box.
        xs = [v.co.x for v in bm.verts]
        ys = [v.co.y for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        centre = Vector((
            (min(xs) + max(xs)) / 2.0,
            (min(ys) + max(ys)) / 2.0,
            (min(zs) + max(zs)) / 2.0,
        ))
        bmesh.ops.translate(bm, vec=-centre, verts=bm.verts)

        count = per_id_counts.get(app_id, 0)
        per_id_counts[app_id] = count + 1
        name = f"{app_id}.{count:03d}"

        joined_mesh = bpy.data.meshes.new(name)
        bm.to_mesh(joined_mesh)
        bm.free()
        for material in materials:
            joined_mesh.materials.append(material)
        joined_mesh.shade_smooth()

        cell = bpy.data.objects.new(name, joined_mesh)
        layer_collection.objects.link(cell)

        # Keep descriptive metadata (markers, roles) from the primary part.
        for key in primary.keys():
            if key not in helper_keys:
                cell[key] = primary[key]

        cell["id"] = app_id          # <-- the link to cellData.js
        cell.parent = layer_parent   # layer roots sit at the origin
        cell.location = centre

        for part in parts:
            data = part.data
            bpy.data.objects.remove(part, do_unlink=True)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)

    return per_id_counts


ID_COUNTS = consolidate_cells()


# ============================================================
# EXPORT PREPARATION
# ============================================================

def prepare_scene_for_export():
    """Scene metadata for downstream tools (exported as glTF extras)."""

    scene = bpy.context.scene
    scene["asset_name"] = "PNT_Graft_Substantia_Nigra"
    scene["asset_version"] = "1.1"
    scene["coordinate_axis"] = "Z"
    scene["description"] = (
        "Procedural PNT graft and substantia nigra visualization"
    )

    # Show colours in the viewport straight away.
    screen = bpy.context.screen
    if screen is not None:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces[0].shading.type = "MATERIAL"
                area.spaces[0].clip_end = 200


prepare_scene_for_export()


# ============================================================
# EXPORT GLB
# ============================================================

def find_export_path():
    """
    <repo>/art/graft_environment.blend  ->  <repo>/public/models/graft_environment.glb

    Returns None (and explains why) when the .blend hasn't been saved in
    the repo's art/ folder yet.
    """

    blend_path = bpy.data.filepath
    if not blend_path:
        print("Not exported: save this file into the repo's art/ folder, "
              "then run art/export_glb.py.")
        return None

    repo_root = os.path.dirname(os.path.dirname(blend_path))
    models_dir = os.path.join(repo_root, "public", "models")
    if not os.path.isdir(models_dir):
        print(f"Not exported: {models_dir} not found. Save the .blend in "
              "<repo>/art/ (e.g. C:\\Users\\aresm\\Projects\\pnt-graft-atlas"
              "\\art\\graft_environment.blend), then run art/export_glb.py.")
        return None

    return os.path.join(models_dir, CONFIG["export_filename"])


def export_glb():
    output_path = find_export_path()

    if output_path is not None:
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            export_format="GLB",
            use_selection=False,
            export_apply=CONFIG["export_apply_modifiers"],
            export_materials="EXPORT",
            export_cameras=CONFIG["export_cameras"],
            export_lights=CONFIG["export_lights"],
            export_animations=CONFIG["export_animations"],
            export_extras=True,      # custom properties -> userData.id in the app
            export_yup=True,         # Blender Z-up -> web Y-up
            export_tangents=False,
        )

    triangles = 0
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.calc_loop_triangles()
            triangles += len(obj.data.loop_triangles)

    print("=" * 60)
    print("PNT GRAFT SCENE GENERATED")
    print("=" * 60)
    if output_path is not None:
        size_mb = os.path.getsize(output_path) / 1e6
        print(f"Output: {output_path} ({size_mb:.1f} MB)")
        if size_mb > 20:
            print("Warning: over 20 MB - lower the CONFIG counts for phones.")
    print(f"Objects: {len(bpy.context.scene.objects)}   Triangles: {triangles:,}")
    print("Clickable structures (id: count):")
    for app_id, count in sorted(ID_COUNTS.items()):
        print(f"  - {app_id}: {count}")
    print("=" * 60)

    return output_path


OUTPUT_PATH = export_glb()
