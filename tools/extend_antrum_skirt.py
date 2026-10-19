"""Extend the open outer edge of the PART_W5_Antrum skirt 0.05 outward along the skin (live scene, never saves).

Why: only the inside view matters, so slits between the skirt rim and the Stomach hole lip are hidden by pushing the skin
through/behind the Stomach wall instead of welding exact seams. Same offset in every shape key. New faces are reversed where
they disagree with their neighbour (PLAYBOOK 15). Undo: mesh copy ANTRUM_BACKUP_r13 (made before the first run).
"""
import bpy, bmesh, numpy as np
from mathutils import Vector
import rebuild_pyloric_canal as RC


def run(dist=0.05, rad_min=0.35, ax_min=0.42):
    me = bpy.data.objects['PART_W5_Antrum'].data
    names = [k.name for k in me.shape_keys.key_blocks]
    bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
    lay = [bm.verts.layers.shape[n] for n in names]
    ok = lambda v: (lambda q: q[0] > ax_min and q[1] > rad_min)(RC.axrt(v.co))
    sel = [e for e in bm.edges if len(e.link_faces) == 1 and all(ok(v) for v in e.verts)]
    bm.normal_update()
    geom = bmesh.ops.extrude_edge_only(bm, edges=sel)['geom']
    for v in [g for g in geom if isinstance(g, bmesh.types.BMVert)]:
        q = np.array(v.co) - RC.C_; q = q - (q @ RC.A_) * RC.A_ - RC.OFF
        n = np.array(v.normal); d = q / np.linalg.norm(q); d = d - (d @ n) * n; d /= np.linalg.norm(d)
        off = Vector((d * dist).tolist())
        for L in lay: v[L] = v[L] + off
        v.co = v.co + off
    nf = [g for g in geom if isinstance(g, bmesh.types.BMFace)]
    for f in nf: f.material_index = 0; f.smooth = True
    bm.normal_update()
    bad = [f for f in nf if (lambda nb: nb and f.normal.dot(nb[0].normal) < 0)([g for e in f.edges for g in e.link_faces if g not in nf])]
    if bad: bmesh.ops.reverse_faces(bm, faces=bad)
    bm.to_mesh(me); bm.free(); me.update()
    return dict(edges=len(sel), faces=len(nf), flipped=len(bad))
