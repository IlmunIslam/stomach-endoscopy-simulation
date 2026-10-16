"""Make the pylorus ring (PART_W5_Antrum, material slot 2 = MAT_W6_Pylorus_Ring) smaller, keeping its structure and the
Pylorus_Close / Pylorus_Open shape-key animation.

The same in-plane scaling (perpendicular to the pylorus axis, about the axis) is applied to EVERY shape key
(Basis, Close, Open), weighted per vertex: 1 on the ring faces, smooth falloff over `hops` mesh rings into the
surrounding wall so nothing detaches. Because every key is scaled the same way, the relative motion (animation) is kept,
just proportionally smaller. Object Mode, numpy, no selection change. Never saves.
"""
import bpy, numpy as np


def run(scale=0.55, hops=14, axis=(1.0, 0.006, -0.016), centre=(-0.447, 0.079, 0.599), backup_npz=None, apply=True):
    ob = bpy.data.objects['PART_W5_Antrum']; me = ob.data; sk = me.shape_keys; n = len(me.vertices)
    keys = [k.data for k in sk.key_blocks]
    co = []
    for kd in keys:
        x = np.empty(n * 3); kd.foreach_get('co', x); co.append(x.reshape(-1, 3))
    if backup_npz: np.savez(backup_npz, *co)
    ring = np.zeros(n, bool)
    for p in me.polygons:
        if p.material_index == 1: ring[list(p.vertices)] = True
    ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
    d = np.where(ring, 0.0, 1e9)
    for _ in range(hops + 1):
        nd = d.copy(); np.minimum.at(nd, ed[:, 1], d[ed[:, 0]] + 1); np.minimum.at(nd, ed[:, 0], d[ed[:, 1]] + 1); d = nd
    t = np.clip(1 - d / hops, 0, 1); g = t * t * (3 - 2 * t)           # 1 on ring, 0 beyond `hops` rings
    a = np.array(axis, float); a /= np.linalg.norm(a); c = np.array(centre, float)
    fac = 1 - (1 - scale) * g
    new = []
    for P in co:
        r = P - c; par = (r @ a)[:, None] * a; perp = r - par
        new.append(c + par + perp * fac[:, None])
    info = dict(ring_verts=int(ring.sum()), affected=int((g > 0).sum()), max_move=[float(np.linalg.norm(q - p, axis=1).max()) for p, q in zip(co, new)])
    if apply:
        for kd, q in zip(keys, new): kd.foreach_set('co', q.ravel())
        me.vertices.foreach_set('co', new[0].ravel()); me.update()
    return info
