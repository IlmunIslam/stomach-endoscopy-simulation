"""Flatten the SELECTED vertices of the active edit-mode mesh into a smooth membrane.

Run inside Blender (execute_blender_code or Text Editor) with the object in Edit Mode.
Unselected vertices are pinned, so the surroundings never move. Selected vertices are
solved as a harmonic (uniform-Laplacian) surface spanning the selection boundary.
`grow` frees N extra vertex rings around the selection (pinned beyond that).
Backs up original coordinates to <backup_path> (npy, object-local) for restore.
Does not save the .blend.
"""
import bpy
import bmesh
import numpy as np


def run(backup_path=None, grow=0):
    ob = bpy.context.edit_object
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    sel = [v for v in bm.verts if v.select]
    orig_sel = {v.index for v in sel}
    for _ in range(grow):  # free extra rings so off-wall boundary verts are fixed too
        add = {e.other_vert(v) for v in sel for e in v.link_edges}
        sel = list({v.index: v for v in sel + list(add)}.values())
    idx = {v.index: i for i, v in enumerate(sel)}
    n = len(sel)
    if backup_path:
        np.save(backup_path, np.array([[v.index, *v.co] for v in sel]))
    A = np.zeros((n, n))
    b = np.zeros((n, 3))
    for v in sel:
        i = idx[v.index]
        nb = [e.other_vert(v) for e in v.link_edges]
        A[i, i] = len(nb)
        for u in nb:
            if u.index in idx:
                A[i, idx[u.index]] -= 1
            else:
                b[i] += np.array(u.co)
    x = np.linalg.solve(A, b)
    before = np.array([np.array(v.co) for v in sel])
    for v, p in zip(sel, x):
        v.co = p.tolist()
    bmesh.update_edit_mesh(ob.data)
    return {"moved": n, "max_move": float(np.linalg.norm(x - before, axis=1).max()),
            "mean_move": float(np.linalg.norm(x - before, axis=1).mean())}
