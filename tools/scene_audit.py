"""Read-only scene audit. Writes docs/state/scene_state.json and scene_state.md.

Run inside Blender (MCP execute_blender_code / Text Editor) or headless:
    blender -b <file>.blend --python tools/scene_audit.py

Output is deterministic (sorted keys, rounded floats, no timestamps). It never
saves the .blend and never modifies scene data.
"""
import collections
import json
import os

import bpy


def r(v, n=4):
    return round(float(v), n)


def vec(v, n=4):
    return [r(x, n) for x in v]


def image_info(img):
    ap = bpy.path.abspath(img.filepath) if img.filepath else ""
    return {
        "name": img.name,
        "source": img.source,
        "filepath": img.filepath,
        "exists_on_disk": os.path.exists(ap) if ap else None,
        "has_data": bool(img.has_data),
        "size": list(img.size),
        "packed": img.packed_file is not None,
        "colorspace": img.colorspace_settings.name,
    }


def material_info(m):
    d = {"name": m.name, "users": m.users, "use_nodes": bool(m.use_nodes)}
    if not m.use_nodes or not m.node_tree:
        return d
    nt = m.node_tree
    d["node_counts"] = dict(sorted(collections.Counter(n.bl_idname.replace("ShaderNode", "") for n in nt.nodes).items()))
    d["textures"] = sorted(n.image.name for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage" and n.image)
    for n in nt.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            p = {}
            for k in ("Roughness", "Metallic", "IOR", "Specular IOR Level", "Coat Weight", "Coat Roughness",
                      "Subsurface Weight", "Transmission Weight", "Emission Strength", "Alpha"):
                if k in n.inputs:
                    s = n.inputs[k]
                    p[k] = {"value": r(s.default_value), "linked": s.is_linked}
            d["principled"] = p
            break
    return d


def action_fcurve_paths(a):
    try:
        return sorted({f.data_path for f in a.fcurves})
    except AttributeError:  # layered actions (Blender 4.4+/5.x)
        paths = set()
        for layer in a.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    paths.update(f.data_path for f in cb.fcurves)
        return sorted(paths)


def collect():
    sc = bpy.context.scene
    rd = sc.render
    vl = bpy.context.view_layer
    S = {"blend_file": os.path.basename(bpy.data.filepath), "blender_version": bpy.app.version_string}

    objs = []
    for o in sorted(bpy.data.objects, key=lambda x: x.name):
        d = {
            "name": o.name, "type": o.type, "data": o.data.name if o.data else None,
            "parent": o.parent.name if o.parent else None,
            "hide_viewport": o.hide_viewport, "hide_render": o.hide_render, "hide_get": o.hide_get(),
            "location": vec(o.location), "rotation_mode": o.rotation_mode, "scale": vec(o.scale),
            "modifiers": [{"name": m.name, "type": m.type} for m in o.modifiers],
            "materials": [s.material.name if s.material else None for s in o.material_slots],
        }
        if o.type == "MESH":
            d["vertices"] = len(o.data.vertices)
            d["faces"] = len(o.data.polygons)
            d["shape_keys"] = [k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []
        objs.append(d)
    S["object_counts"] = dict(sorted(collections.Counter(o.type for o in bpy.data.objects).items()))
    S["objects"] = objs

    S["materials"] = [material_info(m) for m in sorted(bpy.data.materials, key=lambda x: x.name)]
    S["images"] = [image_info(i) for i in sorted(bpy.data.images, key=lambda x: x.name)]
    S["render_filepath"] = rd.filepath
    S["render_filepath_exists"] = os.path.exists(bpy.path.abspath(rd.filepath)) if rd.filepath else None

    S["lights"] = [{
        "name": o.name, "type": o.data.type, "energy": r(o.data.energy), "color": vec(o.data.color),
        "radius": r(getattr(o.data, "shadow_soft_size", 0)), "location": vec(o.location),
        "parent": o.parent.name if o.parent else None, "hide_viewport": o.hide_viewport, "hide_render": o.hide_render,
    } for o in sorted(bpy.data.objects, key=lambda x: x.name) if o.type == "LIGHT"]

    cams = []
    for o in sorted(bpy.data.objects, key=lambda x: x.name):
        if o.type != "CAMERA":
            continue
        c = o.data
        cams.append({
            "name": o.name, "active": sc.camera == o, "type": c.type, "lens": r(c.lens), "fov_deg": r(c.angle * 57.29578, 2),
            "sensor": [r(c.sensor_width), r(c.sensor_height)], "sensor_fit": c.sensor_fit,
            "clip": [r(c.clip_start, 6), r(c.clip_end)], "dof": c.dof.use_dof,
            "focus_distance": r(c.dof.focus_distance), "fstop": r(c.dof.aperture_fstop),
            "parent": o.parent.name if o.parent else None,
        })
    S["cameras"] = cams

    w = sc.world
    world = {"name": w.name if w else None}
    if w and w.use_nodes:
        for n in w.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBackground":
                world["color"] = vec(n.inputs["Color"].default_value)
                world["strength"] = r(n.inputs["Strength"].default_value)
        world["node_types"] = sorted(n.bl_idname for n in w.node_tree.nodes)
    S["world"] = world

    c = sc.cycles
    ev = sc.eevee
    S["render"] = {
        "engine": rd.engine, "resolution": [rd.resolution_x, rd.resolution_y, rd.resolution_percentage],
        "fps": rd.fps, "file_format": rd.image_settings.file_format, "film_transparent": rd.film_transparent,
        "view_transform": sc.view_settings.view_transform, "look": sc.view_settings.look,
        "exposure": r(sc.view_settings.exposure), "gamma": r(sc.view_settings.gamma),
        "display_device": sc.display_settings.display_device,
        "cycles": {"device": c.device, "samples": c.samples, "use_denoising": c.use_denoising, "denoiser": c.denoiser,
                   "max_bounces": c.max_bounces, "diffuse": c.diffuse_bounces, "glossy": c.glossy_bounces,
                   "transmission": c.transmission_bounces, "volume": c.volume_bounces,
                   "clamp_indirect": r(c.sample_clamp_indirect)},
        "eevee": {"taa_render_samples": ev.taa_render_samples, "use_raytracing": ev.use_raytracing,
                  "use_shadows": ev.use_shadows, "use_fast_gi": ev.use_fast_gi,
                  "gi_diffuse_bounces": ev.gi_diffuse_bounces, "volumetric_samples": ev.volumetric_samples},
        "compositor_nodes": len(sc.compositing_node_group.nodes) if getattr(sc, "compositing_node_group", None) else 0,
    }

    S["animation"] = {
        "frame_start": sc.frame_start, "frame_end": sc.frame_end, "frame_current": sc.frame_current,
        "animated_objects": [{"object": o.name,
                              "action": o.animation_data.action.name if o.animation_data.action else None}
                             for o in sorted(bpy.data.objects, key=lambda x: x.name) if o.animation_data],
        "actions": [{"name": a.name, "users": a.users, "frame_range": [r(a.frame_range[0], 1), r(a.frame_range[1], 1)],
                     "paths": action_fcurve_paths(a)} for a in sorted(bpy.data.actions, key=lambda x: x.name)],
    }
    return S


def summary(S):
    objs = S["objects"]
    meshes = sorted((o for o in objs if o["type"] == "MESH"), key=lambda o: -o["vertices"])[:3]
    miss = [i["name"] for i in S["images"] if i["exists_on_disk"] is False]
    cam = next((c for c in S["cameras"] if c["active"]), None)
    rr = S["render"]
    lines = [
        "# Scene state (generated by tools/scene_audit.py)",
        "",
        "- File: {} (Blender {})".format(S["blend_file"], S["blender_version"]),
        "- Objects: {}".format(", ".join("{} {}".format(k, v) for k, v in S["object_counts"].items())),
        "- Heaviest meshes: " + "; ".join("{} {:,}v".format(m["name"], m["vertices"]) for m in meshes),
        "- Materials: {}; images: {}; images missing on disk: {}".format(len(S["materials"]), len(S["images"]), len(miss)),
        "- Render filepath exists: {}".format(S["render_filepath_exists"]),
        "- Engine: {} {}x{} @{}%, {} fps, {}".format(rr["engine"], *rr["resolution"], rr["fps"], rr["view_transform"]),
        "- EEVEE samples {}, raytracing {}, fast GI {}".format(rr["eevee"]["taa_render_samples"], rr["eevee"]["use_raytracing"], rr["eevee"]["use_fast_gi"]),
        "- Cycles (stored): {} spp, device {}".format(rr["cycles"]["samples"], rr["cycles"]["device"]),
        "- Lights: {} ({} render-enabled)".format(len(S["lights"]), sum(1 for l in S["lights"] if not l["hide_render"])),
    ]
    if cam:
        lines.append("- Active camera: {} {} mm, FOV {} deg, clip {}-{}, DOF {}".format(
            cam["name"], cam["lens"], cam["fov_deg"], cam["clip"][0], cam["clip"][1], cam["dof"]))
    lines.append("- World: color {} strength {}".format(S["world"].get("color"), S["world"].get("strength")))
    a = S["animation"]
    lines.append("- Frames {}-{} (current {}); animated objects: {}".format(
        a["frame_start"], a["frame_end"], a["frame_current"], ", ".join(x["object"] for x in a["animated_objects"])))
    lines.append("- Compositor nodes: {}".format(rr["compositor_nodes"]))
    return lines[:30]


def main():
    root = os.path.dirname(bpy.data.filepath)
    out = os.path.join(root, "docs", "state")
    os.makedirs(out, exist_ok=True)
    S = collect()
    with open(os.path.join(out, "scene_state.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(S, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out, "scene_state.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(summary(S)) + "\n")
    return out


result = main()
