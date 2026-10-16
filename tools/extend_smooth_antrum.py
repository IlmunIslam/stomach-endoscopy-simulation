"""Extend the smooth wall of Stomach toward the antrum: the rugae folds (real base geometry, displace strengths are 0)
fade out with geodesic distance from the Stomach hole rim that faces PART_W5_Antrum.

weight w = wmax within r_full of the rim, smoothstep to 0 at r_fade.
Reference surface S = S1 + h_s * n1, where S1 = implicit (backward-Euler) Laplacian smoothing of the region (shrinks),
n1 = its normals and h_s = the implicit-smoothed normal offset of the original from S1 (restores the shrink, kills the folds).
P' = P + w (S - P). Rim verts (d < 0.15) and everything outside the weighted region stay fixed, so the Antrum seam stays closed.
Edit Mode (bmesh, selection untouched) or Object Mode. Never saves.
"""
import bpy, bmesh, numpy as np


def _read(obj):
    if obj.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        co = np.array([v.co[:] for v in bm.verts])
        ed = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges])
        fa = [[v.index for v in f.verts] for f in bm.faces]
        bnd = np.array([i for i, e in enumerate(bm.edges) if len(e.link_faces) == 1], int)
        bv = np.unique(ed[bnd].ravel()) if bnd.size else np.zeros(0, int)
        return bm, co, ed, bv, fa
    me = obj.data
    n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
    cnt = np.zeros(len(me.edges), int)
    pl = np.empty(len(me.loops), int); me.loops.foreach_get("edge_index", pl); np.add.at(cnt, pl, 1)
    bv = np.unique(ed[cnt == 1].ravel())
    fa = [list(p.vertices) for p in me.polygons]
    return None, co, ed, bv, fa


def geodesic(ed, co, seeds, n, rmax):
    L = np.linalg.norm(co[ed[:, 0]] - co[ed[:, 1]], axis=1)
    d = np.full(n, 1e9); d[seeds] = 0
    for _ in range(int(rmax / 0.02)):
        a = d[ed[:, 0]] + L; b = d[ed[:, 1]] + L
        nd = d.copy(); np.minimum.at(nd, ed[:, 1], a); np.minimum.at(nd, ed[:, 0], b)
        if np.array_equal(nd, d): break
        d = nd
    return d


def _cg(mv, b, x0, iters=300, tol=1e-6):
    x = x0.copy(); r = b - mv(x); p = r.copy(); rs = (r * r).sum()
    for _ in range(iters):
        Ap = mv(p); a = rs / max((p * Ap).sum(), 1e-30)
        x += a * p; r -= a * Ap; rs2 = (r * r).sum()
        if rs2 < tol * tol * max(b.size, 1): break
        p = r + (rs2 / rs) * p; rs = rs2
    return x


def _implicit_smooth(ed, n, free, vals, t, iters=300):
    """(I + t L) x = vals on free verts; non-free verts are Dirichlet at `vals`. vals: (n,) or (n,k)."""
    v = vals.reshape(n, -1)
    F = np.where(free)[0]; pos = -np.ones(n, int); pos[F] = np.arange(F.size)
    ea, eb = ed[:, 0], ed[:, 1]
    deg = np.bincount(np.concatenate([ea, eb]), minlength=n).astype(float)
    ff = free[ea] & free[eb]; fa, fb = pos[ea[ff]], pos[eb[ff]]
    rhs = v[F].copy()
    m1 = free[ea] & ~free[eb]; np.add.at(rhs, pos[ea[m1]], t * v[eb[m1]])
    m2 = free[eb] & ~free[ea]; np.add.at(rhs, pos[eb[m2]], t * v[ea[m2]])
    d = deg[F]

    def mv(x):
        y = (1 + t * d)[:, None] * x
        np.add.at(y, fa, -t * x[fb]); np.add.at(y, fb, -t * x[fa]); return y
    out = v.copy(); out[F] = _cg(mv, rhs, v[F], iters=iters)
    return out.reshape(vals.shape)


def _normals(co, fa):
    nrm = np.zeros_like(co)
    for f in fa:
        if len(f) < 3: continue
        p = co[f]; fn = np.cross(p[1] - p[0], p[2] - p[0]) if len(f) == 3 else np.cross(p[2] - p[0], p[3 % len(f)] - p[1])
        nrm[f] += fn
    return nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)


def run(pylorus=(13.68, -7.79, 27.97), r_full=6.0, r_fade=14.0, t=250.0, wmax=0.92, max_move=0.4, backup_npy=None, apply=True):
    obj = bpy.data.objects['Stomach']
    bm, co, ed, bv, fa = _read(obj); n = len(co)
    if backup_npy: np.save(backup_npy, co)
    W = np.array(obj.matrix_world); wc = co[bv] @ W[:3, :3].T + W[:3, 3]
    seeds = bv[np.linalg.norm(wc - np.array(pylorus), axis=1) < 3.0]   # only the rim facing the Antrum
    d = geodesic(ed, co, seeds, n, r_fade)
    s = np.clip((r_fade - d) / (r_fade - r_full), 0, 1); w = wmax * s * s * (3 - 2 * s)
    free = (w > 0) & (d >= 0.15)
    S1 = _implicit_smooth(ed, n, free, co, t)
    n1 = _normals(S1, fa)
    h = ((co - S1) * n1).sum(1)
    hs = _implicit_smooth(ed, n, free, h, t)
    S = S1 + hs[:, None] * n1
    dl = w[:, None] * (S - co); ln = np.linalg.norm(dl, axis=1, keepdims=True)
    new = co + dl * np.minimum(1.0, max_move / np.maximum(ln, 1e-12))   # folds are only ~0.1-0.3 deep; clamp stops outliers flying
    mv_ = np.linalg.norm(new - co, axis=1)
    info = dict(weighted=int((w > 0).sum()), full=int((w >= wmax * .999).sum()), max_move=float(mv_.max()), mean_move_full=float(mv_[w >= wmax * .999].mean()))
    if apply:
        if bm is not None:
            for v, q in zip(bm.verts, new): v.co = q
            bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        else:
            obj.data.vertices.foreach_set("co", new.ravel())
            if obj.data.shape_keys: obj.data.shape_keys.key_blocks[0].data.foreach_set("co", new.ravel())
            obj.data.update()
    return info
