"""Render the *actual* Infinity V5 architectural GLB with native FSEQ colors.

Usage: blender --background --python tools/infinity_v5_render_blender.py -- MESH.glb MAP.csv FRAMES.rgb OUT_DIR
No simulated effects, no 2D projection, no stand-in architectural meshes.
"""
from __future__ import annotations
import csv, json, math, sys
from collections import defaultdict
from pathlib import Path
from mathutils import Vector, kdtree
import bpy
import numpy as np

def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 4:
        raise SystemExit("expected MESH.glb MAP.csv FRAMES.rgb OUT_DIR")
    mesh_path, csv_path, binary_path, out_path = map(Path, args)
    out_path.mkdir(parents=True, exist_ok=True)
    entries = defaultdict(list)
    with csv_path.open(newline="") as file:
        for r in csv.DictReader(file):
            channel = int(r["red_channel"])
            if (int(r["green_channel"]), int(r["blue_channel"])) != (channel + 1, channel + 2):
                raise ValueError("RGB channel triplet is not consecutive")
            entries[r["model"]].append((channel, Vector((float(r["x_m"]), float(r["y_m"]), float(r["z_m"])))))
    ordered = sorted(c for group in entries.values() for c, _ in group)
    if ordered != list(range(1, 90721, 3)) or len(entries) != 202:
        raise ValueError("V5 channel map inventory mismatch")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(mesh_path.resolve()))
    atlas_width, atlas_height = 512, 60
    image = bpy.data.images.new("HELIX_V5_NATIVE_FSEQ_ATLAS", width=atlas_width,
                                height=atlas_height, alpha=True, float_buffer=False)
    image.colorspace_settings.name = "sRGB"
    mat = bpy.data.materials.new("HELIX_V5_NATIVE_RGB_EMISSION")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = "HELIX_V5_PIXEL_UV"
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    tex.extension = "CLIP"
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 3.0
    output = nodes.new("ShaderNodeOutputMaterial")
    links = mat.node_tree.links
    links.new(uv.outputs["UV"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], em.inputs["Color"])
    links.new(em.outputs["Emission"], output.inputs["Surface"])
    used = set()
    max_distance = 0.
    vertices_mapped = 0
    for obj in list(bpy.data.objects):
        if obj.type != "MESH":
            continue
        model = obj.name if obj.name in entries else obj.data.name if obj.data.name in entries else None
        if model is None:
            continue
        if model in used:
            raise ValueError("Duplicate imported illuminated model " + model)
        used.add(model)
        candidates = entries[model]
        tree = kdtree.KDTree(len(candidates))
        for n, (_, xyz) in enumerate(candidates):
            tree.insert(xyz, n)
        tree.balance()
        mesh = obj.data
        pixel_of_vertex = []
        obj.matrix_world.copy()
        for vertex in mesh.vertices:
            world = obj.matrix_world @ vertex.co
            _, closest, distance = tree.find(world)
            max_distance = max(max_distance, distance)
            if distance >= 0.26:
                raise ValueError(f"Mesh misalignment {model}: nearest pixel {distance:.3f} metres")
            pixel_of_vertex.append((candidates[closest][0] - 1) // 3)
        texture_uv = mesh.uv_layers.get("HELIX_V5_PIXEL_UV") or mesh.uv_layers.new(name="HELIX_V5_PIXEL_UV")
        for polygon_loop in mesh.loops:
            index = pixel_of_vertex[polygon_loop.vertex_index]
            texture_uv.data[polygon_loop.index].uv = (
                ((index % atlas_width) + .5) / atlas_width,
                ((index // atlas_width) + .5) / atlas_height)
        mesh.materials.clear()
        mesh.materials.append(mat)
        vertices_mapped += len(mesh.vertices)
    missing = sorted(set(entries) - used)
    if missing:
        raise ValueError(f"Missing {len(missing)} actual V5 illuminated meshes: {missing[:12]}")
    # Retain untouched 3D architecture, terrain and decorative geometry.
    bpy.ops.object.camera_add(location=(180, -210, 155))
    cam = bpy.context.object
    cam.rotation_euler = (Vector((0, 0, 6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 240
    bpy.context.scene.camera = cam
    world = bpy.data.worlds.new("HELIX_NIGHT")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.009, 0.014, 0.03, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="AREA", location=(20, -30, 100))
    lamp = bpy.context.object
    lamp.data.energy = 15000
    lamp.data.shape = "DISK"
    lamp.data.size = 150
    scene = bpy.context.scene
    engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else (
        "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "CYCLES")
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = 8
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    # Atlas updates replace only actual native RGB channels, with the FSEQ's exact values.
    count = 30240
    rgba = np.zeros((atlas_width * atlas_height, 4), dtype=np.float32)
    rgba[:, 3] = 1.
    rgb_width = count * 3
    binary_size = binary_path.stat().st_size
    if binary_size != 90 * rgb_width:
        raise ValueError(f"Expected 90 native 30-fps frames: got {binary_size} bytes")
    with binary_path.open("rb") as file:
        for index in range(90):
            payload = file.read(rgb_width)
            rgb = np.frombuffer(payload, dtype=np.uint8).reshape((-1, 3))
            rgba[:count, :3] = rgb / 255.
            image.pixels.foreach_set(rgba.reshape(-1))
            image.update()
            scene.frame_set(index + 1)
            scene.render.filepath = str((out_path / f"frame_{index:06d}.png").resolve())
            bpy.ops.render.render(write_still=True)
            print(f"HELIX_V5_RENDER_FRAME {index + 1}/90", flush=True)
    report = {"source_mesh": str(mesh_path), "source_map": str(csv_path),
              "lighting_models": len(used), "lighting_vertices": vertices_mapped,
              "pixels": count, "channels": rgb_width, "maximum_binding_distance_m": max_distance,
              "frames_rendered": 90, "geometry": "actual V5 GLB, not flat approximation",
              "owner_approved": False}
    (out_path / "mesh_render_receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
