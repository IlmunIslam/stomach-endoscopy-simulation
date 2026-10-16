"""Add a large submucosal vein (trunk + branches) on the PART_W5_Antrum wall as a separate mesh object
'PART_W5_Antrum_Vein' (own material 'MAT_W5_Antrum_Vein'). Antrum itself is untouched.

Paths are drawn as pixel polylines in the Cam_Endoscope view at `frame`, smoothed (Catmull-Rom), ray-cast onto the Antrum
surface, pushed a little into the wall along the surface normal and lofted into a tapered tube. Object Mode, data API only
(no selection/active change). Never saves. Re-running replaces the previous vein object.
"""
import bpy, numpy as np, mathutils

# (name, pixels in a 960x540 view, start radius, end radius)  radius in world units
PATHS = [
    ("trunk", [(610, 10), (595, 70), (570, 120), (550, 160), (538, 192), (530, 208)], 0.085, 0.016),
    ("b1", [(592, 78), (650, 104), (700, 124), (738, 160)], 0.048, 0.020),
    ("b2", [(562, 138), (500, 124), (445, 116), (395, 126), (350, 152)], 0.048, 0.020),
    ("b3", [(540, 185), (590, 205), (640, 218)], 0.026, 0.012),
]


def catmull(pts, per=8):
    P = np.array(pts, float); P = np.vstack([P[0], P, P[-1]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2]); return np.array(out)


def wiggle(dense, seed, amp=9.0):
    """Gentle vessel tortuosity: perpendicular sine wobble in pixel space, zero at both ends so branches stay attached."""
    rng = np.random.default_rng(seed); n = len(dense)
    tg = np.gradient(dense, axis=0); tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9)
    nm = np.stack([-tg[:, 1], tg[:, 0]], 1); s = np.linspace(0, 1, n)
    w = 0.6 * np.sin(2 * np.pi * (1.3 * s + rng.random())) + 0.4 * np.sin(2 * np.pi * (3.1 * s + rng.random()))
    return dense + nm * (amp * w * np.sin(np.pi * s))[:, None]


def run(frame=760, sink=0.7, apply=True, name="PART_W5_Antrum_Vein"):
    sc = bpy.context.scene; f0 = sc.frame_current; sc.frame_set(frame)
    cam = sc.camera; cm = cam.matrix_world
    fr = [cm @ v for v in cam.data.view_frame(scene=sc)]; tr, br, bl, tl = [np.array(v) for v in fr]
    C = np.array(cm.translation)
    ant = bpy.data.objects['PART_W5_Antrum']; mi = ant.matrix_world.inverted(); mw = ant.matrix_world
    dg = bpy.context.evaluated_depsgraph_get()
    curve = bpy.data.curves.new(name + "_tmp", 'CURVE'); curve.dimensions = '3D'; curve.bevel_depth = 1.0; curve.bevel_resolution = 4
    curve.use_fill_caps = True; curve.resolution_u = 2
    info = {}
    for nm, pix, r0, r1 in PATHS:
        dense = wiggle(catmull(pix, 8), seed=len(nm) * 7 + ord(nm[-1])); pts3 = []; rad = []
        for k, (px, py) in enumerate(dense):
            p = tl + (tr - tl) * px / 960 + (bl - tl) * py / 540; d = p - C; d /= np.linalg.norm(d)
            hit, loc, nrm, idx = ant.ray_cast(mi @ mathutils.Vector(C), mi.to_3x3() @ mathutils.Vector(d), depsgraph=dg)
            if not hit: continue
            wl = mw @ loc; wn = (mw.to_3x3() @ nrm).normalized()
            if wn.dot(mathutils.Vector(-d)) < 0: wn = -wn            # face the camera
            t = k / max(len(dense) - 1, 1); r = r0 + (r1 - r0) * t
            pts3.append(np.array(wl - wn * (sink * r))); rad.append(r)  # centre slightly inside the wall
        info[nm] = dict(samples=len(dense), hit=len(pts3))
        if len(pts3) < 3: continue
        sp = curve.splines.new('POLY'); sp.points.add(len(pts3) - 1)
        for pt, q, r in zip(sp.points, pts3, rad): pt.co = (*q, 1.0); pt.radius = r
    if not apply:
        bpy.data.curves.remove(curve); sc.frame_set(f0); return info
    tmp = bpy.data.objects.new(name + "_tmp", curve); sc.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg), preserve_all_data_layers=False, depsgraph=dg); me.name = name
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(curve)
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old)
    ob = bpy.data.objects.new(name, me)
    for c in ant.users_collection: c.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    mat = bpy.data.materials.get("MAT_W5_Antrum_Vein") or bpy.data.materials.new("MAT_W5_Antrum_Vein")
    mat.use_nodes = True; b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.20, 0.06, 0.13, 1)
    b.inputs['Roughness'].default_value = 0.5
    for k, v in (('Subsurface Weight', 0.25), ('Coat Weight', 0.12), ('Coat Roughness', 0.25)):
        if k in b.inputs: b.inputs[k].default_value = v
    if 'Subsurface Radius' in b.inputs: b.inputs['Subsurface Radius'].default_value = (0.5, 0.15, 0.2)
    me.materials.append(mat)
    sc.frame_set(f0)
    info.update(verts=len(me.vertices), polys=len(me.polygons)); return info
