"""Close the remaining see-through cracks around the pyloric ring in the user's inside view (live scene, never saves).

Why: the front sheet of the Antrum skirt (normal . axis > 0.2) is double-layered with the bulb-facing back sheet, so cracks have
edges with two faces and plain open-edge searches miss them. The fix is to pick the FRONT-sheet boundary edges (edges where exactly
one linked face is a front face) whose screen position lies in the crack region of the user's viewport, and triangle_fill them;
reverse every new face whose normal disagrees with the sheet (PLAYBOOK 15).
Also here: fold_replace() removes a folded patch of Stomach faces (grown one ring) and re-fills the hole as an n-gon.
Take a mesh.copy() first (PLAYBOOK 11); fills add no vertices, so shape keys stay consistent.
"""
import bpy, bmesh, numpy as np
from bpy_extras import view3d_utils
import rebuild_pyloric_canal as RC


def fill_front_cracks(box, n_orig):
    """box = (x0, x1, y0, y1) in 1920x1080 render pixels of the user's viewport; n_orig = vertex count to consider."""
    win = bpy.context.window_manager.windows[0]; area = [a for a in win.screen.areas if a.type == 'VIEW_3D'][0]
    reg = [r for r in area.regions if r.type == 'WINDOW'][0]; rv3 = area.spaces[0].region_3d
    sx = reg.width / 1920; sy = reg.height / 1080
    ant = bpy.data.objects['PART_W5_Antrum']; me = ant.data; W = ant.matrix_world
    bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()

    def scr(v):
        p = view3d_utils.location_3d_to_region_2d(reg, rv3, W @ v.co); return None if p is None else (p.x / sx, 1080 - p.y / sy)
    isF = lambda f: np.array(f.normal) @ RC.A_ > 0.2
    sel = []
    for e in bm.edges:
        if max(v.index for v in e.verts) >= n_orig: continue
        if len(e.link_faces) == 1 or sum(isF(f) for f in e.link_faces) == 1:
            ps = [scr(v) for v in e.verts]
            if all(p and box[0] < p[0] < box[1] and box[2] < p[1] < box[3] for p in ps): sel.append(e)
    fn = [g for g in bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=sel)['geom'] if isinstance(g, bmesh.types.BMFace)]
    bm.normal_update()
    bad = [f for f in fn if np.array(f.normal) @ RC.A_ < 0]
    if bad: bmesh.ops.reverse_faces(bm, faces=bad)
    for f in fn: f.smooth = True; f.material_index = 0
    bm.to_mesh(me); bm.free(); me.update()
    return dict(edges=len(sel), new=len(fn), flipped=len(bad))


def fold_replace(obj, face_ids):
    """Delete face_ids plus one ring and fill the hole (used for the folded Stomach flap that showed as a dark slit)."""
    me = obj.data; bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    S = {bm.faces[i] for i in face_ids}; S1 = S | {g for f in S for v in f.verts for g in v.link_faces}
    bv = {v for f in S1 for e in f.edges if any(g not in S1 for g in e.link_faces) for v in e.verts}
    bmesh.ops.delete(bm, geom=list(S1), context='FACES'); bm.edges.ensure_lookup_table()
    bnd = [e for e in bm.edges if e.is_valid and len(e.link_faces) == 1 and e.verts[0] in bv and e.verts[1] in bv]
    fn = bmesh.ops.holes_fill(bm, edges=bnd, sides=60)['faces']; bm.normal_update()
    bad = [f for f in fn if (lambda nb: nb and f.normal.dot(nb[0].normal) < 0)([g for e in f.edges for g in e.link_faces if g is not f and g not in fn])]
    if bad: bmesh.ops.reverse_faces(bm, faces=bad)
    for f in fn: f.smooth = True
    bm.to_mesh(me); bm.free(); me.update()
    return dict(deleted=len(S1), filled=len(fn))
