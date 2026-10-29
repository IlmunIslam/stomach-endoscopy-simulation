"""Four-frame before/after snapshot for the live Blender session.

Frames 361, 531, 731 and 971 are rendered from the scene (endoscope) camera as
small OpenGL renders, and each gets numbers: luminance stats, dark and blown-out
shares, firefly proxy, camera pose and per-object vert/face counts. A later
snapshot is compared against the first one.

Run inside Blender (execute_blender_code), never saved to the .blend:

    import sys; sys.path.insert(0, r"<project>/tools")
    import canonical_check as cc
    cc.snapshot("before")                 # start of task
    ...edit...
    cc.snapshot("after")                  # end of task
    print(cc.compare("before", "after"))  # per-frame verdicts + image paths

Snapshots live in <tempdir>/canonical_check/<tag>/ (frame_NNN.png, stats.json),
outside the project. Every scene property touched (frame, render filepath,
resolution, percentage, format, engine override is NOT used) is restored.
Nothing here saves the .blend or changes geometry.
"""
import json
import os
import tempfile

import bpy
import numpy as np

FRAMES = (361, 531, 731, 971)
SIZE = (480, 270)
ROOT = os.path.join(tempfile.gettempdir(), "canonical_check")

# compare thresholds
LUM_DELTA = 0.05          # mean luminance change that is worth a flag
DARK_DELTA = 0.01         # growth in share of near-black pixels
BLOWN_DELTA = 0.01        # growth in share of near-white pixels
FIREFLY_DELTA = 5         # growth in firefly proxy count
IMG_DIFF = 0.04           # mean abs pixel difference (0..1) between frames
CAM_MOVE = 1e-4           # camera pose change flagged as a change


def _dir(tag):
    return os.path.join(ROOT, tag)


def _image_stats(path):
    img = bpy.data.images.load(path, check_existing=False)
    try:
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
    finally:
        bpy.data.images.remove(img)
    px = px.reshape(h, w, 4)
    lum = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    pad = np.pad(lum, 1, mode="edge")
    neigh = np.stack([pad[y:y + h, x:x + w] for y in range(3) for x in range(3) if (y, x) != (1, 1)])
    fire = (lum >= 0.5) & (lum > 4.0 * neigh.max(axis=0))
    stats = {
        "mean": float(lum.mean()),
        "p1": float(np.percentile(lum, 1)),
        "p50": float(np.percentile(lum, 50)),
        "p99": float(np.percentile(lum, 99)),
        "dark": float((lum <= 0.02).mean()),
        "blown": float((lum >= 0.98).mean()),
        "fireflies": int(fire.sum()),
    }
    return stats, px[..., :3].copy()


def _scene_numbers(scene):
    cam = scene.camera
    pose = None
    if cam is not None:
        mw = cam.matrix_world
        pose = [round(float(v), 6) for row in mw for v in row]
    return pose


def _mesh_counts():
    return {o.name: [len(o.data.vertices), len(o.data.polygons)]
            for o in bpy.data.objects if o.type == 'MESH'}


def snapshot(tag, frames=FRAMES, size=SIZE):
    """Render the canonical frames to <tmp>/canonical_check/<tag>/ and return the stats dict."""
    scene = bpy.context.scene
    out = _dir(tag)
    os.makedirs(out, exist_ok=True)
    r = scene.render
    saved = (scene.frame_current, r.filepath, r.resolution_x, r.resolution_y,
             r.resolution_percentage, r.image_settings.file_format, r.image_settings.color_mode)
    result = {"tag": tag, "size": list(size), "frames": {}, "meshes": _mesh_counts(),
              "blend": bpy.data.filepath, "dirty": bool(bpy.data.is_dirty)}
    try:
        r.resolution_x, r.resolution_y, r.resolution_percentage = size[0], size[1], 100
        r.image_settings.file_format = 'PNG'
        r.image_settings.color_mode = 'RGBA'
        for f in frames:
            scene.frame_set(f)
            path = os.path.join(out, "frame_%03d.png" % f)
            r.filepath = path
            bpy.ops.render.opengl(write_still=True, view_context=False)
            stats, _ = _image_stats(path)
            stats["camera"] = _scene_numbers(scene)
            stats["image"] = path
            result["frames"][str(f)] = stats
    finally:
        (scene.frame_current, r.filepath, r.resolution_x, r.resolution_y,
         r.resolution_percentage, r.image_settings.file_format, r.image_settings.color_mode) = saved
        scene.frame_set(saved[0])
    with open(os.path.join(out, "stats.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    return result


def load(tag):
    with open(os.path.join(_dir(tag), "stats.json")) as fh:
        return json.load(fh)


def compare(before="before", after="after"):
    """Compare two snapshots. Returns {'verdict', 'frames': {frame: {...}}, 'mesh_changes'}.

    Verdict is REGRESSION when any frame shows a flagged worsening (more black,
    more blown-out, more fireflies), CHANGED when only luminance, pose or the
    pixel difference moved, SAME otherwise. The numbers decide nothing about
    whether the change is wanted; read the paths and look.
    """
    a, b = load(before), load(after)
    frames, worst = {}, "SAME"
    rank = {"SAME": 0, "CHANGED": 1, "REGRESSION": 2}
    for f, sa in a["frames"].items():
        sb = b["frames"].get(f)
        if sb is None:
            continue
        _, pa = _image_stats(sa["image"])
        _, pb = _image_stats(sb["image"])
        diff = float(np.abs(pa - pb).mean()) if pa.shape == pb.shape else None
        flags = []
        if sb["dark"] - sa["dark"] > DARK_DELTA:
            flags.append("more black (%.3f -> %.3f)" % (sa["dark"], sb["dark"]))
        if sb["blown"] - sa["blown"] > BLOWN_DELTA:
            flags.append("more blown-out (%.3f -> %.3f)" % (sa["blown"], sb["blown"]))
        if sb["fireflies"] - sa["fireflies"] > FIREFLY_DELTA:
            flags.append("fireflies %d -> %d" % (sa["fireflies"], sb["fireflies"]))
        changes = []
        if abs(sb["mean"] - sa["mean"]) > LUM_DELTA:
            changes.append("mean luminance %.3f -> %.3f" % (sa["mean"], sb["mean"]))
        if diff is None or diff > IMG_DIFF:
            changes.append("image diff %s" % ("n/a" if diff is None else "%.3f" % diff))
        ca, cb = sa["camera"], sb["camera"]
        if ca is None or cb is None or max(abs(x - y) for x, y in zip(ca, cb)) > CAM_MOVE:
            changes.append("camera pose changed")
        level = "REGRESSION" if flags else ("CHANGED" if changes else "SAME")
        worst = max(worst, level, key=rank.get)
        frames[f] = {"level": level, "flags": flags, "changes": changes,
                     "image_diff": diff, "before": sa["image"], "after": sb["image"]}
    mesh_changes = {n: {"before": a["meshes"].get(n), "after": b["meshes"].get(n)}
                    for n in sorted(set(a["meshes"]) | set(b["meshes"]))
                    if a["meshes"].get(n) != b["meshes"].get(n)}
    return {"verdict": worst, "frames": frames, "mesh_changes": mesh_changes}
