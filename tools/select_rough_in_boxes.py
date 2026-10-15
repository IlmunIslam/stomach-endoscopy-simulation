"""Select rough/spiky vertices of the active object that project into camera-pixel boxes (1280x720 frame).

Rough = deviation from a Taubin-smoothed copy > thr. Selection is dilated `dilate` rings, then
tools/smooth_selected_patch.py flattens it with the boundary pinned. Run in Edit Mode.
"""
import bpy, bmesh, numpy as np, mathutils
from bpy_extras.object_utils import world_to_camera_view


def run(boxes, thr=0.02, maxdist=6.0, dilate=2, W=1280, H=720):
    bpy.ops.object.mode_set(mode='OBJECT')
    ob = bpy.context.view_layer.objects.active
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(n, 3)
    ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
    cnt = np.maximum(np.bincount(ed.ravel(), minlength=n).astype(float), 1)

    def lap(p):
        a = np.zeros_like(p); np.add.at(a, ed[:, 0], p[ed[:, 1]]); np.add.at(a, ed[:, 1], p[ed[:, 0]])
        return a / cnt[:, None] - p
    p = co.copy()
    for _ in range(20):
        p = p + 0.5 * lap(p); p = p - 0.53 * lap(p)
    d = np.linalg.norm(co - p, axis=1)
    mw = np.array(ob.matrix_world); w = co @ mw[:3, :3].T + mw[:3, 3]
    sc = bpy.context.scene; cam = sc.camera
    dc = np.linalg.norm(w - np.array(cam.matrix_world.translation), axis=1)
    keep = []
    for v in np.where((dc < maxdist) & (d > thr))[0]:
        c = world_to_camera_view(sc, cam, mathutils.Vector(w[v]))
        if c.z <= 0: continue
        x, y = c.x * W, (1 - c.y) * H
        if any(a <= x <= b and cc <= y <= dd for a, b, cc, dd in boxes): keep.append(int(v))
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data); bm.verts.ensure_lookup_table()
    for v in bm.verts: v.select = False
    S = set(keep)
    for _ in range(dilate):
        S |= {e.other_vert(bm.verts[i]).index for i in S for e in bm.verts[i].link_edges}
    for i in S: bm.verts[i].select = True
    bm.select_flush_mode(); bmesh.update_edit_mesh(ob.data)
    return {"kept": len(keep), "selected": len(S)}
