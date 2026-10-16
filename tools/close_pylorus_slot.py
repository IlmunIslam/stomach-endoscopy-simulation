"""Close the V-shaped through-slot above the lumen of PART_W5_Antrum (the 'keyhole' gap).

The Antrum is a double layer (front layer + slab) with a funnel tube; a slot cut in the plane y~yc runs from the lumen up to
the edge. Its walls are ordinary faces (|normal_y| large), so there are no boundary edges. Every wall vertex on the left is
paired with its nearest right-wall vertex and both move to the midpoint (per shape key, so Close/Open keep working); the
displacement is spread over `rings` mesh rings by implicit smoothing so the wall near the slot stretches, not kinks.
Object Mode, numpy, no selection change. Never saves.
"""
import bpy, numpy as np


def _smooth(ed, n, free, vals, t=3.0, iters=200):
    v = vals.reshape(n, -1); F = np.where(free)[0]; pos = -np.ones(n, int); pos[F] = np.arange(F.size)
    ea, eb = ed[:, 0], ed[:, 1]; deg = np.bincount(np.concatenate([ea, eb]), minlength=n).astype(float)
    ff = free[ea] & free[eb]; fa, fb = pos[ea[ff]], pos[eb[ff]]; rhs = v[F].copy()
    m1 = free[ea] & ~free[eb]; np.add.at(rhs, pos[ea[m1]], t * v[eb[m1]]); m2 = free[eb] & ~free[ea]; np.add.at(rhs, pos[eb[m2]], t * v[ea[m2]])
    d = deg[F]

    def mv(x):
        y = (1 + t * d)[:, None] * x; np.add.at(y, fa, -t * x[fb]); np.add.at(y, fb, -t * x[fa]); return y
    x = v[F].copy(); r = rhs - mv(x); p = r.copy(); rs = (r * r).sum()
    for _ in range(iters):
        Ap = mv(p); al = rs / max((p * Ap).sum(), 1e-30); x += al * p; r -= al * Ap; rs2 = (r * r).sum()
        if rs2 < 1e-14 * max(r.size, 1): break
        p = r + (rs2 / rs) * p; rs = rs2
    out = v.copy(); out[F] = x; return out.reshape(vals.shape)


def run(yc=0.09, zmin=0.55, halfw=0.06, nymin=0.7, maxpair=0.12, tube_pair=0.04, tube_zmin=0.6, slab_pairs=False, unique=False, rings=5, backup_npz=None, apply=True):
    ob = bpy.data.objects['PART_W5_Antrum']; me = ob.data; n = len(me.vertices)
    keys = [k.data for k in me.shape_keys.key_blocks]; co = []
    for kd in keys:
        a = np.empty(n * 3); kd.foreach_get('co', a); co.append(a.reshape(-1, 3))
    if backup_npz: np.savez(backup_npz, *co)
    B = co[0]
    ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
    fn = np.empty(len(me.polygons) * 3); me.polygons.foreach_get('normal', fn); fn = fn.reshape(-1, 3)
    pv = [np.array(p.vertices) for p in me.polygons]; cen = np.array([B[v].mean(0) for v in pv])
    wall = (cen[:, 1] > yc - halfw) & (cen[:, 1] < yc + halfw) & (cen[:, 2] > np.where(cen[:, 0] >= 0.03, zmin + 0.07, tube_zmin)) & (cen[:, 0] > -0.4) & (np.abs(fn[:, 1]) > nymin)
    wv = np.unique(np.concatenate([pv[i] for i in np.where(wall)[0]]))
    Lm = wv[B[wv, 1] < yc]; Rm = wv[B[wv, 1] >= yc]
    def ok(a, b, dist):
        if B[a, 0] >= 0.03: return dist < maxpair                       # slab / front layer: full slot width
        # tube: only a true seam partner (same ring row, same height), never the far side of the lumen
        return dist < tube_pair and abs(B[a, 0] - B[b, 0]) < 0.006 and abs(B[a, 2] - B[b, 2]) < 0.012 and B[a, 2] > 0.6
    pair = {}
    for v in Lm:
        d = np.linalg.norm(B[Rm] - B[v], axis=1); k = int(d.argmin())
        if ok(v, Rm[k], d[k]): pair[int(v)] = int(Rm[k])
    # one-to-one-ish: every right vertex also pairs back to nearest left
    for v in Rm:
        if int(v) in pair.values(): continue
        d = np.linalg.norm(B[Lm] - B[v], axis=1); k = int(d.argmin())
        if ok(Lm[k], v, d[k]): pair[int(Lm[k])] = int(v) if int(Lm[k]) not in pair else pair[int(Lm[k])]
    # tube seam: pair by vertex (same ring row, same height) because its faces are too thin for the wall test
    tm = (B[:, 0] < 0.03) & (B[:, 0] > -0.45) & (np.abs(B[:, 1] - yc) < 0.03) & (B[:, 2] > tube_zmin)
    Lt = np.where(tm & (B[:, 1] < yc))[0]; Rt = np.where(tm & (B[:, 1] >= yc))[0]
    for v in Lt:
        d = np.linalg.norm(B[Rt] - B[v], axis=1); k = int(d.argmin())
        if ok(v, Rt[k], d[k]) and int(v) not in pair: pair[int(v)] = int(Rt[k])
    # slab seam near the ring: vertex pairs across the narrow slot (same height, same layer), not across the lumen
    sm = slab_pairs & (B[:, 0] >= 0.03) & (np.abs(B[:, 1] - yc) < 0.03) & (B[:, 2] > tube_zmin) & (B[:, 2] < 0.80)
    Ls = np.where(sm & (B[:, 1] < yc))[0]; Rs = np.where(sm & (B[:, 1] >= yc))[0]
    for v in Ls:
        d = np.linalg.norm(B[Rs] - B[v], axis=1); k = int(d.argmin())
        if d[k] < 0.05 and abs(B[v, 2] - B[Rs[k], 2]) < 0.02 and abs(B[v, 0] - B[Rs[k], 0]) < 0.03 and int(v) not in pair: pair[int(v)] = int(Rs[k])
    # one-to-one: a right vertex may be used once (greedy by distance), so every pair ends up exactly coincident
    cand = [] if not unique else sorted(((np.linalg.norm(B[a_] - B[b_]), a_, b_) for a_, b_ in pair.items()))
    used, uniq = set(), {}
    for d_, a_, b_ in cand:
        if b_ in used: continue
        used.add(b_); uniq[a_] = b_
    for a_ in [a_ for a_ in pair if a_ not in uniq]:     # re-match leftovers to the nearest unused partner
        pool = [w for w in (Rm.tolist() + Rt.tolist() + Rs.tolist()) if w not in used]
        if not pool: break
        d_ = np.linalg.norm(B[pool] - B[a_], axis=1); k = int(d_.argmin())
        if d_[k] < 0.05 and abs(B[a_, 2] - B[pool[k], 2]) < 0.02: uniq[a_] = pool[k]; used.add(pool[k])
    if unique: pair = uniq
    info = dict(wall_faces=int(wall.sum()), left=len(Lm), right=len(Rm), pairs=len(pair))
    if not pair or not apply: return info
    # fixed displacement on welded verts, spread over `rings` hops
    hop = np.full(n, 99); fixed = np.zeros(n, bool)
    for a_, b_ in pair.items(): fixed[a_] = fixed[b_] = True
    hop[fixed] = 0
    for h in range(1, rings + 1):
        m = hop == h - 1
        for u, v in ed:
            if hop[u] == h - 1 and hop[v] > h: hop[v] = h
            if hop[v] == h - 1 and hop[u] > h: hop[u] = h
    free = (hop > 0) & (hop <= rings)
    new = []
    for P in co:
        D = np.zeros_like(P)
        for a_, b_ in pair.items():
            mid = 0.5 * (P[a_] + P[b_]); D[a_] = mid - P[a_]
            D[b_] = mid - P[b_]
        Ds = _smooth(ed, n, free, D)
        new.append(P + Ds)
    info['max_move'] = float(max(np.linalg.norm(q - p, axis=1).max() for p, q in zip(co, new)))
    for kd, q in zip(keys, new): kd.foreach_set('co', q.ravel())
    me.vertices.foreach_set('co', new[0].ravel()); me.update()
    return info


def second_pass(yc=0.09, zmin=0.6, rings=4, backup_npz=None):
    """Weld pass 2 on the current state: vertex pairs across the remaining narrow slot in the slab (same height/layer)."""
    ob = bpy.data.objects['PART_W5_Antrum']; me = ob.data; n = len(me.vertices)
    keys = [k.data for k in me.shape_keys.key_blocks]; co = []
    for kd in keys:
        a = np.empty(n * 3); kd.foreach_get('co', a); co.append(a.reshape(-1, 3))
    if backup_npz: np.savez(backup_npz, *co)
    B = co[0]; ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
    m = (B[:, 0] >= 0.03) & (np.abs(B[:, 1] - yc) < 0.03) & (B[:, 2] > zmin) & (B[:, 2] < 0.80)
    V = np.where(m)[0]; L = V[B[V, 1] < yc]; R = V[B[V, 1] >= yc]; pair = {}
    for v in L:
        d = np.linalg.norm(B[R] - B[v], axis=1); k = int(d.argmin())
        if 1e-5 < d[k] < 0.05 and abs(B[v, 2] - B[R[k], 2]) < 0.02 and abs(B[v, 0] - B[R[k], 0]) < 0.03: pair[int(v)] = int(R[k])
    hop = np.full(n, 99); fixed = np.zeros(n, bool)
    for a_, b_ in pair.items(): fixed[a_] = fixed[b_] = True
    hop[fixed] = 0
    for h in range(1, rings + 1):
        for u, v in ed:
            if hop[u] == h - 1 and hop[v] > h: hop[v] = h
            if hop[v] == h - 1 and hop[u] > h: hop[u] = h
    free = (hop > 0) & (hop <= rings); new = []
    for P in co:
        D = np.zeros_like(P)
        for a_, b_ in pair.items():
            mid = 0.5 * (P[a_] + P[b_]); D[a_] = mid - P[a_]; D[b_] = mid - P[b_]
        new.append(P + _smooth(ed, n, free, D))
    for kd, q in zip(keys, new): kd.foreach_set('co', q.ravel())
    me.vertices.foreach_set('co', new[0].ravel()); me.update()
    return dict(pairs=len(pair))
