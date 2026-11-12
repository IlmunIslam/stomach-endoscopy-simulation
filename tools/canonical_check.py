"""Regression snapshots plus an animated-camera path check for the live Blender session.

Frames listed in project_config.json ("frames", default below) are rendered from the scene camera as small OpenGL
renders and get numbers: luminance stats, dark and blown-out shares, firefly proxy, camera pose, per-object
vert/face counts. snapshot() also runs path_check() when the camera is animated. compare() diffs two snapshots
(images, numbers, camera path) and writes a timestamped JSON result that the Stop hook looks for.

Run inside Blender (execute_blender_code), never saved to the .blend:

    import sys; sys.path.insert(0, r"<project>/tools")
    import canonical_check as cc
    cc.snapshot("before")                 # start of task
    ...edit...
    cc.snapshot("after")                  # end of task
    print(cc.compare("before", "after"))  # verdicts + image paths + path verdict + result file

    cc.path_check()                       # camera path alone (every 10 frames), writes path_check_<ts>.json

Settings: <project>/project_config.json (keys below in _DEFAULTS); environment variable CANONICAL_RESULTS_DIR
overrides the results folder. Snapshots live in <tempdir>/canonical_check/<tag>/; results in
<results_dir>/{compare,path_check}_<YYYYmmdd_HHMMSS>.json (default <tempdir>/canonical_check/results).
Every scene property touched (frame, render filepath, resolution, format) is restored. Nothing here saves the .blend
or changes geometry.
"""
import datetime
import hashlib
import json
import math
import os
import tempfile
import time

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CONFIG_NAME = "project_config.json"
_DEFAULTS = {
    "frames": [361, 531, 731, 971],
    "snapshot_size": [480, 270],
    "camera_object": "",              # empty: use scene.camera
    "path_check_step": 10,
    "clearance_min": 0.02,            # scene units; ring-ray wall distance below this is flagged
    "turn_rate_max_deg_per_frame": 3.0,
    "roll_step_max_deg_per_frame": 3.0,
    "results_dir": "",
}

# compare thresholds
LUM_DELTA = 0.05          # mean luminance change that is worth a flag
DARK_DELTA = 0.01         # growth in share of near-black pixels
BLOWN_DELTA = 0.01        # growth in share of near-white pixels
FIREFLY_DELTA = 5         # growth in firefly proxy count
IMG_DIFF = 0.04           # mean abs pixel difference (0..1) between frames
CAM_MOVE = 1e-4           # camera pose change flagged as a change
CLEAR_DROP = 0.20         # relative drop of the minimum wall clearance flagged as a regression
RATE_DELTA = 0.5          # growth (deg/frame) of the max turn or roll rate flagged
RING_RAYS = 8


def _config():
    cfg = dict(_DEFAULTS)
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(os.path.dirname(here), CONFIG_NAME), encoding="utf-8") as f:
            cfg.update({k: v for k, v in json.load(f).items() if k in _DEFAULTS and v not in ("", None, [])})
    except (OSError, ValueError):
        pass
    return cfg


def _root():
    return os.path.join(tempfile.gettempdir(), "canonical_check")


def _dir(tag):
    return os.path.join(_root(), tag)


def results_dir():
    d = os.environ.get("CANONICAL_RESULTS_DIR") or _config()["results_dir"] or os.path.join(_root(), "results")
    os.makedirs(d, exist_ok=True)
    return d


def _stamp():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d_%H%M%S"), now.isoformat(timespec="seconds"), now.timestamp()


def _write_result(kind, payload):
    ts, iso, ep = _stamp()
    payload = dict(payload, kind=kind, timestamp=iso, epoch=ep, blend=bpy.data.filepath)
    path = os.path.join(results_dir(), "%s_%s.json" % (kind, ts))
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1)
    return path


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


def _camera(scene, cfg=None):
    cfg = cfg or _config()
    if cfg["camera_object"]:
        return bpy.data.objects.get(cfg["camera_object"])
    return scene.camera


def _scene_numbers(scene):
    cam = _camera(scene)
    if cam is None:
        return None
    return [round(float(v), 6) for row in cam.matrix_world for v in row]


def _mesh_counts():
    return {o.name: [len(o.data.vertices), len(o.data.polygons)]
            for o in bpy.data.objects if o.type == 'MESH'}


# ---------------------------------------------------------------- camera path

def _animated(cam):
    ad = cam.animation_data
    return bool(ad and ad.action)


def _bvh_for(ob, dg, cache):
    """World-space BVH of the evaluated mesh; reused while its coordinates are unchanged between samples."""
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        me.calc_loop_triangles()
        co = np.empty(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get("co", co)
        tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
        me.loop_triangles.foreach_get("vertices", tri)
        m = np.array(ob.matrix_world, dtype=np.float64)
        key = hashlib.md5(co.tobytes() + m.tobytes() + tri.tobytes()).hexdigest()
        hit = cache.get(ob.name)
        if hit and hit[0] == key:
            return hit[1]
        w = co.reshape(-1, 3).astype(np.float64) @ m[:3, :3].T + m[:3, 3]
        bvh = BVHTree.FromPolygons(w.tolist(), tri.reshape(-1, 3).tolist())
        cache[ob.name] = (key, bvh)
        return bvh
    finally:
        ev.to_mesh_clear()


def _twist_deg(qa, qb, fa, fb):
    """Rotation about the forward axis between two camera poses once the minimal turn fa->fb is removed."""
    rel = qb @ qa.inverted()
    res = fa.rotation_difference(fb).inverted() @ rel
    axis, ang = res.to_axis_angle()
    t = math.degrees(ang) if axis.dot(fb) >= 0 else -math.degrees(ang)
    return (t + 180.0) % 360.0 - 180.0


def path_check(step=None, start=None, end=None, write=True):
    """Sample the animated scene camera every `step` frames: wall clearance (8 perpendicular rays + forward ray against
    every visible mesh, BVH rebuilt when a mesh changed), turn rate and roll twist per frame. Returns a compact dict
    (summary + flagged samples + result file); all samples are in the JSON file."""
    cfg = _config()
    scene = bpy.context.scene
    cam = _camera(scene, cfg)
    if cam is None:
        raise RuntimeError("no camera: set camera_object in project_config.json or scene.camera")
    step = int(step or cfg["path_check_step"])
    start = int(scene.frame_start if start is None else start)
    end = int(scene.frame_end if end is None else end)
    frames = list(range(start, end + 1, step))
    if frames[-1] != end:
        frames.append(end)
    t_start, saved = time.time(), scene.frame_current
    cache, samples, prev = {}, [], None
    try:
        for f in frames:
            scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            mw = cam.matrix_world.copy()
            pos, q = mw.translation.copy(), mw.to_quaternion()
            fwd, right, up = q @ Vector((0, 0, -1)), q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
            bvhs = [(ob.name, _bvh_for(ob, dg, cache)) for ob in scene.objects
                    if ob.type == 'MESH' and ob.visible_get() and not ob.hide_render]
            clear, clear_ob = float("inf"), None
            for k in range(RING_RAYS):
                a = 2 * math.pi * k / RING_RAYS
                d = (right * math.cos(a) + up * math.sin(a)).normalized()
                for name, bvh in bvhs:
                    h = bvh.ray_cast(pos, d)
                    if h[0] is not None and h[3] < clear:
                        clear, clear_ob = h[3], name
            ahead = float("inf")
            for name, bvh in bvhs:
                h = bvh.ray_cast(pos, fwd)
                if h[0] is not None and h[3] < ahead:
                    ahead = h[3]
            s = {"frame": f, "pos": [round(v, 4) for v in pos], "clearance": None if math.isinf(clear) else round(clear, 4),
                 "clearance_object": clear_ob, "ahead": None if math.isinf(ahead) else round(ahead, 4),
                 "turn_deg_per_frame": 0.0, "roll_deg_per_frame": 0.0, "roll_cum_deg": 0.0, "flags": []}
            if prev:
                df = max(1, f - prev["frame"])
                s["turn_deg_per_frame"] = round(math.degrees(prev["fwd"].angle(fwd)) / df, 3)
                tw = _twist_deg(prev["q"], q, prev["fwd"], fwd)
                s["roll_deg_per_frame"] = round(tw / df, 3)
                s["roll_cum_deg"] = round(prev["cum"] + tw, 2)
            cum = s["roll_cum_deg"]
            if s["clearance"] is not None and s["clearance"] < cfg["clearance_min"]:
                s["flags"].append("clearance %.3f < %.3f" % (s["clearance"], cfg["clearance_min"]))
            if s["turn_deg_per_frame"] > cfg["turn_rate_max_deg_per_frame"]:
                s["flags"].append("turn %.2f deg/frame" % s["turn_deg_per_frame"])
            if abs(s["roll_deg_per_frame"]) > cfg["roll_step_max_deg_per_frame"]:
                s["flags"].append("roll %.2f deg/frame" % s["roll_deg_per_frame"])
            samples.append(s)
            prev = {"frame": f, "q": q, "fwd": fwd, "cum": cum}
    finally:
        scene.frame_set(saved)
    cl = [s for s in samples if s["clearance"] is not None]
    low = min(cl, key=lambda s: s["clearance"]) if cl else None
    summary = {
        "camera": cam.name, "step": step, "frames": [frames[0], frames[-1]], "samples": len(samples),
        "min_clearance": low["clearance"] if low else None, "min_clearance_frame": low["frame"] if low else None,
        "min_clearance_object": low["clearance_object"] if low else None,
        "max_turn_deg_per_frame": max(s["turn_deg_per_frame"] for s in samples),
        "max_roll_deg_per_frame": max(abs(s["roll_deg_per_frame"]) for s in samples),
        "roll_total_deg": samples[-1]["roll_cum_deg"],
        "flagged_samples": sum(1 for s in samples if s["flags"]),
        "seconds": round(time.time() - t_start, 1),
        "thresholds": {k: cfg[k] for k in ("clearance_min", "turn_rate_max_deg_per_frame", "roll_step_max_deg_per_frame")},
    }
    summary["verdict"] = "FLAGS" if summary["flagged_samples"] else "OK"
    out = {"summary": summary, "flagged": [s for s in samples if s["flags"]][:20]}
    if write:
        out["file"] = _write_result("path_check", {"summary": summary, "samples": samples})
    return out


# ---------------------------------------------------------------- snapshots

def snapshot(tag, frames=None, size=None, path=True):
    """Render the regression frames to <tmp>/canonical_check/<tag>/ and return the stats dict.
    With path=True and an animated camera, path_check() runs too and its summary is stored."""
    cfg = _config()
    frames = tuple(frames or cfg["frames"])
    size = tuple(size or cfg["snapshot_size"])
    if not frames:
        raise RuntimeError("no frames: set \"frames\" in project_config.json (run init_project.py)")
    scene = bpy.context.scene
    out = _dir(tag)
    os.makedirs(out, exist_ok=True)
    r = scene.render
    saved = (scene.frame_current, r.filepath, r.resolution_x, r.resolution_y,
             r.resolution_percentage, r.image_settings.file_format, r.image_settings.color_mode)
    result = {"tag": tag, "size": list(size), "frames": {}, "meshes": _mesh_counts(),
              "blend": bpy.data.filepath, "dirty": bool(bpy.data.is_dirty), "path_check": None}
    try:
        r.resolution_x, r.resolution_y, r.resolution_percentage = size[0], size[1], 100
        r.image_settings.file_format = 'PNG'
        r.image_settings.color_mode = 'RGBA'
        for f in frames:
            scene.frame_set(f)
            p = os.path.join(out, "frame_%03d.png" % f)
            r.filepath = p
            bpy.ops.render.opengl(write_still=True, view_context=False)
            stats, _ = _image_stats(p)
            stats["camera"] = _scene_numbers(scene)
            stats["image"] = p
            result["frames"][str(f)] = stats
    finally:
        (scene.frame_current, r.filepath, r.resolution_x, r.resolution_y,
         r.resolution_percentage, r.image_settings.file_format, r.image_settings.color_mode) = saved
        scene.frame_set(saved[0])
    cam = _camera(scene, cfg)
    if path and cam is not None and _animated(cam):
        result["path_check"] = path_check(write=False)["summary"]
    with open(os.path.join(out, "stats.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    return result


def load(tag):
    with open(os.path.join(_dir(tag), "stats.json")) as fh:
        return json.load(fh)


_RANK = {"SAME": 0, "CHANGED": 1, "REGRESSION": 2}


def _compare_paths(pa, pb):
    """Diff two path_check summaries. Returns None when either snapshot has none."""
    if not pa or not pb:
        return None
    flags, changes = [], []
    ca, cb = pa["min_clearance"], pb["min_clearance"]
    if ca and cb is not None and cb < ca * (1 - CLEAR_DROP):
        flags.append("min wall clearance %.4f -> %.4f" % (ca, cb))
    elif ca is not None and cb is not None and abs(cb - ca) > 0.05 * ca:
        changes.append("min wall clearance %.4f -> %.4f" % (ca, cb))
    if pb["flagged_samples"] > pa["flagged_samples"]:
        flags.append("flagged samples %d -> %d" % (pa["flagged_samples"], pb["flagged_samples"]))
    for key, label in (("max_turn_deg_per_frame", "turn"), ("max_roll_deg_per_frame", "roll")):
        d = pb[key] - pa[key]
        if d > RATE_DELTA:
            flags.append("max %s %.2f -> %.2f deg/frame" % (label, pa[key], pb[key]))
        elif abs(d) > RATE_DELTA / 2:
            changes.append("max %s %.2f -> %.2f deg/frame" % (label, pa[key], pb[key]))
    level = "REGRESSION" if flags else ("CHANGED" if changes else "SAME")
    return {"level": level, "flags": flags, "changes": changes, "before": pa, "after": pb}


def compare(before="before", after="after"):
    """Compare two snapshots. Returns {'verdict', 'frames', 'mesh_changes', 'path', 'file'}.

    Verdict is REGRESSION when any frame (or the camera path) shows a flagged worsening, CHANGED when only
    luminance, pose, the pixel difference or path numbers moved, SAME otherwise. The numbers decide nothing about
    whether the change is wanted; read the paths and look. A timestamped compare_<ts>.json is written to results_dir().
    """
    a, b = load(before), load(after)
    frames, worst = {}, "SAME"
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
        worst = max(worst, level, key=_RANK.get)
        frames[f] = {"level": level, "flags": flags, "changes": changes,
                     "image_diff": diff, "before": sa["image"], "after": sb["image"]}
    path = _compare_paths(a.get("path_check"), b.get("path_check"))
    if path:
        worst = max(worst, path["level"], key=_RANK.get)
    mesh_changes = {n: {"before": a["meshes"].get(n), "after": b["meshes"].get(n)}
                    for n in sorted(set(a["meshes"]) | set(b["meshes"]))
                    if a["meshes"].get(n) != b["meshes"].get(n)}
    result = {"verdict": worst, "frames": frames, "mesh_changes": mesh_changes,
              "path": path if path else "no path_check in one or both snapshots (camera not animated?)"}
    result["file"] = _write_result("compare", dict(result, before=before, after=after))
    return result
