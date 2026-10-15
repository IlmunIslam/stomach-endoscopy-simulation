"""Close the narrow notch ("tongue") in PART_W5_Antrum's open-end boundary loop (the keyhole neck).

The tongue is found automatically: loop vertices whose nearest non-neighbour loop vertex (> 10 steps along the
loop) is closer than `width`. Opposite sides are paired mirror-wise around the tongue tip, both sides are moved to
their midpoint and merged. Edit-mode bmesh (shape keys survive, Ctrl+Z works). Does not save.
"""
import bpy, bmesh, numpy as np


def _loops(bm):
    adj = {}
    for e in bm.edges:
        if len(e.link_faces) == 1:
            a, b = e.verts[0].index, e.verts[1].index
            adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for s in adj:
        if s in seen: continue
        order = [s]; seen.add(s); prev = None; cur = s
        while True:
            nx = [y for y in adj[cur] if y != prev and y not in seen]
            if not nx: break
            prev, cur = cur, nx[0]; seen.add(cur); order.append(cur)
        out.append(order)
    return out


def run(span=20, maxgap=0.1, apply=True):
    """Find the tongue tip (farthest loop vertex along the loop's main axis inside the pinched stretch), then
    weld the `span` vertices on each side of the tip to their nearest partner on the other side (midpoint)."""
    ob = bpy.data.objects["PART_W5_Antrum"]
    bpy.context.view_layer.objects.active = ob
    if bpy.context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ob.data); bm.verts.ensure_lookup_table()
    L = max(_loops(bm), key=len); n = len(L)
    P = np.array([list(bm.verts[i].co) for i in L])
    nearest = np.full(n, 9.0)
    for i in range(n):
        d = np.linalg.norm(P - P[i], axis=1)
        cd = np.minimum(abs(np.arange(n) - i), n - abs(np.arange(n) - i)); d[cd <= 10] = 9
        nearest[i] = d.min()
    # pinched stretch = vertices with a very close opposite side; its tip is the one with the smallest gap's
    # farthest reach along the main axis
    c = P.mean(0); u, sv, vt = np.linalg.svd(P - c); q = (P - c) @ vt.T
    pinched = np.where(nearest < 0.08)[0]
    info = {"loop": n, "pinched": int(pinched.size)}
    if not apply or pinched.size == 0:
        bpy.ops.object.mode_set(mode='OBJECT'); return info
    t = int(pinched[np.argmax(q[pinched, 0])])
    A = [(t - k) % n for k in range(1, span + 1)]
    B = [(t + k) % n for k in range(1, span + 1)]
    pa = P[A]; pb = P[B]
    touched = [bm.verts[L[t]]]
    moved = 0
    for ia, a in zip(A, pa):
        d = np.linalg.norm(pb - a, axis=1); k = int(d.argmin())
        if d[k] < maxgap:
            m = (bm.verts[L[ia]].co + bm.verts[L[B[k]]].co) / 2
            bm.verts[L[ia]].co = m; bm.verts[L[B[k]]].co = m
            touched += [bm.verts[L[ia]], bm.verts[L[B[k]]]]; moved += 1
    bmesh.ops.remove_doubles(bm, verts=list(dict.fromkeys(touched)), dist=1e-5)
    bm.verts.ensure_lookup_table()
    be = [e for e in bm.edges if len(e.link_faces) == 1]
    bmesh.ops.holes_fill(bm, edges=be, sides=3)
    bmesh.update_edit_mesh(ob.data)
    info.update(tip=t, welded=moved, loops_after=sorted(len(c) for c in _loops(bm)))
    bpy.ops.object.mode_set(mode='OBJECT')
    return info
